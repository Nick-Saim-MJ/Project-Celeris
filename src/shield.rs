//! Modo shield (REQ-F-29, lado servidor): un proxy de segundo nivel que solo atiende a nodos con certificado de cliente.
//!
//! Acepta TLS en `shield_listen` exigiendo un certificado de cliente emitido por `shield_client_ca` (mTLS, F9). Lo que el nodo envía, ya
//! descifrado, pasa por una conexión local al proxy de `listen`, que es el mismo motor de caché (sin intercepción de TLS: el shield nunca
//! recibe CONNECT de usuarios, solo las peticiones de sus nodos). `listen` tiene que ser de bucle local: de otro modo habría un puerto
//! sin TLS abierto junto al protegido.
//!
//! El shield no sabe quién es el usuario final: el nodo ya quitó las cabeceras que lo identifican (REQ-F-28) y la conexión llega desde
//! 127.0.0.1.

use anyhow::{bail, Context};
use std::net::SocketAddr;
use std::path::Path;
use std::sync::Arc;
use tokio::net::{TcpListener, TcpStream};
use tokio_rustls::rustls::crypto::aws_lc_rs;
use tokio_rustls::rustls::pki_types::pem::PemObject;
use tokio_rustls::rustls::pki_types::{CertificateDer, PrivateKeyDer};
use tokio_rustls::rustls::server::WebPkiClientVerifier;
use tokio_rustls::rustls::{RootCertStore, ServerConfig};
use tokio_rustls::TlsAcceptor;

use crate::config::Config;

/// Arma el aceptador TLS con mTLS obligatorio. Se exige que existan los tres archivos: el shield no genera certificados por su cuenta.
pub fn acceptor(cert: &Path, key: &Path, client_ca: &Path) -> anyhow::Result<TlsAcceptor> {
    for (nombre, ruta) in [("shield_cert", cert), ("shield_key", key), ("shield_client_ca", client_ca)] {
        if !ruta.exists() {
            bail!("{nombre} no existe: {} (el shield necesita su certificado y la CA de los nodos)", ruta.display());
        }
    }
    let chain: Vec<CertificateDer<'static>> =
        CertificateDer::pem_file_iter(cert).with_context(|| format!("leyendo {}", cert.display()))?.collect::<Result<_, _>>()?;
    let key = PrivateKeyDer::from_pem_file(key).with_context(|| format!("llave inválida en {}", key.display()))?;
    let mut roots = RootCertStore::empty();
    for ca in CertificateDer::pem_file_iter(client_ca).with_context(|| format!("leyendo {}", client_ca.display()))? {
        roots.add(ca?)?;
    }
    let proveedor = Arc::new(aws_lc_rs::default_provider());
    let verificador = WebPkiClientVerifier::builder_with_provider(Arc::new(roots), proveedor.clone()).build()?;
    let config = ServerConfig::builder_with_provider(proveedor)
        .with_safe_default_protocol_versions()?
        .with_client_cert_verifier(verificador)
        .with_single_cert(chain, key)?;
    Ok(TlsAcceptor::from(Arc::new(config)))
}

/// Abre `shield_listen`. Si no se puede, el nodo no arranca: un shield sin su puerto es peor que uno que avisa.
pub async fn start(cfg: &Config) -> anyhow::Result<()> {
    let listen = cfg.shield_listen.trim();
    if listen.is_empty() {
        return Ok(());
    }
    let addr: SocketAddr = listen.parse().with_context(|| format!("shield_listen inválido: {listen}"))?;
    let interno: SocketAddr = cfg.listen.parse()?;
    if !interno.ip().is_loopback() {
        bail!("en modo shield `listen` ({interno}) debe ser de bucle local: el puerto sin TLS no puede quedar abierto a la red");
    }
    let tls = acceptor(&cfg.shield_cert, &cfg.shield_key, &cfg.shield_client_ca)?;
    let listener = TcpListener::bind(addr).await.with_context(|| format!("abriendo el puerto del shield {addr}"))?;
    tracing::info!("shield en {addr} (mTLS obligatorio) → proxy local {interno}");
    tokio::spawn(async move {
        loop {
            let Ok((socket, _)) = listener.accept().await else { continue };
            let tls = tls.clone();
            tokio::spawn(async move {
                // Un cliente sin certificado válido falla aquí, en el apretón de manos, y no llega al proxy.
                let Ok(mut cliente) = tls.accept(socket).await else { return };
                let Ok(mut local) = TcpStream::connect(interno).await else { return };
                let _ = tokio::io::copy_bidirectional(&mut cliente, &mut local).await;
            });
        }
    });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sin_los_archivos_el_shield_no_arranca() {
        let dir = std::env::temp_dir().join(format!("celeris-shield-test-{}", std::process::id()));
        let e = acceptor(&dir.join("a.crt"), &dir.join("a.key"), &dir.join("ca.crt")).err().unwrap().to_string();
        assert!(e.contains("shield_cert no existe"), "{e}");
    }

    #[tokio::test]
    async fn un_listen_que_no_es_de_bucle_local_se_rechaza() {
        let cfg = Config { shield_listen: "127.0.0.1:0".into(), listen: "0.0.0.0:3128".into(), ..Config::default() };
        let e = start(&cfg).await.err().unwrap().to_string();
        assert!(e.contains("bucle local"), "{e}");
    }

    #[tokio::test]
    async fn apagado_no_hace_nada() {
        assert!(start(&Config::default()).await.is_ok());
    }
}
