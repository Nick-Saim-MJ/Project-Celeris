//! Archivo PAC (REQ-F-26): varios nodos de proxy en orden de preferencia y `DIRECT` como respaldo.
//!
//! Se genera desde `pac_nodes`, `pac_direct_networks` y `pac_host` de la configuración, con `celeris-cache pac [config.toml]`, y se puede
//! servir desde el propio nodo (`pac_listen`) en `/wpad.dat`. El navegador prueba los nodos en el orden del PAC: si el primero no responde,
//! pasa al siguiente y, si todos caen, sale directo. Salir directo evita dejar a los usuarios sin red, pero esa salida no se controla (F6,
//! solo en el piloto). La IP de cada nodo y el puerto salen del inventario (F1); este archivo no inventa ninguno.

use crate::config::Config;
use anyhow::{bail, Context};
use std::net::{Ipv4Addr, SocketAddr};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

/// `10.20.0.0/14` → (`10.20.0.0`, `255.252.0.0`): el PAC usa la máscara, no el prefijo.
fn red_y_mascara(cidr: &str) -> anyhow::Result<(Ipv4Addr, Ipv4Addr)> {
    let (ip, prefijo) = cidr.split_once('/').with_context(|| format!("red inválida «{cidr}»: falta el prefijo"))?;
    let ip: Ipv4Addr = ip.parse().with_context(|| format!("red inválida «{cidr}»"))?;
    let prefijo: u32 = prefijo.parse().with_context(|| format!("prefijo inválido en «{cidr}»"))?;
    if prefijo > 32 {
        bail!("prefijo inválido en «{cidr}»");
    }
    let mascara = if prefijo == 0 { 0 } else { u32::MAX << (32 - prefijo) };
    Ok((Ipv4Addr::from(u32::from(ip) & mascara), Ipv4Addr::from(mascara)))
}

fn nodo_valido(nodo: &str) -> anyhow::Result<()> {
    nodo.parse::<SocketAddr>().map(|_| ()).with_context(|| format!("nodo del PAC inválido «{nodo}»: se espera ip:puerto"))
}

/// Genera el PAC. Falla si no hay nodos: un PAC que solo dijera `DIRECT` dejaría a todos sin caché sin avisar.
pub fn generar(cfg: &Config) -> anyhow::Result<String> {
    if cfg.pac_nodes.is_empty() {
        bail!("pac_nodes está vacío: el PAC necesita al menos un nodo (ip:puerto)");
    }
    for n in &cfg.pac_nodes {
        nodo_valido(n)?;
    }
    let cadena = cfg.pac_nodes.iter().map(|n| format!("PROXY {n}")).collect::<Vec<_>>().join("; ") + "; DIRECT";
    let mut directos = String::new();
    for red in &cfg.pac_direct_networks {
        let (ip, mascara) = red_y_mascara(red)?;
        directos.push_str(&format!("  if (isInNet(host, \"{ip}\", \"{mascara}\")) return \"DIRECT\";\n"));
    }
    let nombre = if cfg.pac_host.is_empty() { String::new() } else { format!(" || host === \"{}\"", cfg.pac_host) };
    Ok(format!(
        "function FindProxyForURL(url, host) {{\n  if (isPlainHostName(host) || host === \"localhost\"{nombre}) return \"DIRECT\";\n  \
         if (isInNet(host, \"127.0.0.0\", \"255.0.0.0\")) return \"DIRECT\";\n{directos}  return \"{cadena}\";\n}}\n"
    ))
}

/// Respuesta HTTP/1.0 de un solo uso: el PAC es chico y lo piden los navegadores al arrancar.
fn responder(peticion: &str, pac: &str) -> String {
    let primera = peticion.lines().next().unwrap_or_default();
    let ruta = primera.split_whitespace().nth(1).unwrap_or("/");
    if primera.starts_with("GET ") && (ruta == "/wpad.dat" || ruta == "/proxy.pac") {
        format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/x-ns-proxy-autoconfig\r\nCache-Control: max-age=300\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{pac}",
            pac.len()
        )
    } else {
        "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".to_owned()
    }
}

/// Sirve el PAC en `pac_listen`. Si no se puede abrir el puerto, el nodo no arranca.
pub async fn start(cfg: &Config) -> anyhow::Result<()> {
    let listen = cfg.pac_listen.trim();
    if listen.is_empty() {
        return Ok(());
    }
    let addr: SocketAddr = listen.parse().with_context(|| format!("pac_listen inválido: {listen}"))?;
    let pac: std::sync::Arc<str> = generar(cfg)?.into();
    let listener = TcpListener::bind(addr).await.with_context(|| format!("abriendo el servidor del PAC {addr}"))?;
    tracing::info!("PAC en http://{addr}/wpad.dat: {} nodo(s) y DIRECT de respaldo", cfg.pac_nodes.len());
    tokio::spawn(async move {
        loop {
            let Ok((mut socket, _)) = listener.accept().await else { continue };
            let pac = pac.clone();
            tokio::spawn(async move {
                let mut buf = [0u8; 2048];
                let leidos = tokio::time::timeout(std::time::Duration::from_secs(5), socket.read(&mut buf)).await;
                if let Ok(Ok(n)) = leidos {
                    let respuesta = responder(&String::from_utf8_lossy(&buf[..n]), &pac);
                    let _ = socket.write_all(respuesta.as_bytes()).await;
                }
                let _ = socket.shutdown().await;
            });
        }
    });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cfg() -> Config {
        Config {
            pac_nodes: vec!["10.20.60.10:3128".into(), "10.20.60.11:3128".into()],
            pac_direct_networks: vec!["10.20.0.0/14".into(), "10.30.0.0/16".into()],
            pac_host: "wpad.celeris.internal".into(),
            ..Config::default()
        }
    }

    #[test]
    fn el_pac_lista_los_nodos_en_orden_y_termina_en_direct() {
        let pac = generar(&cfg()).unwrap();
        assert!(pac.contains("return \"PROXY 10.20.60.10:3128; PROXY 10.20.60.11:3128; DIRECT\";"), "{pac}");
        assert!(pac.starts_with("function FindProxyForURL(url, host) {"));
    }

    #[test]
    fn las_redes_internas_y_el_nombre_del_pac_van_directos() {
        let pac = generar(&cfg()).unwrap();
        assert!(pac.contains("isInNet(host, \"10.20.0.0\", \"255.252.0.0\")"));
        assert!(pac.contains("isInNet(host, \"10.30.0.0\", \"255.255.0.0\")"));
        assert!(pac.contains("host === \"wpad.celeris.internal\""));
        assert!(pac.contains("isInNet(host, \"127.0.0.0\", \"255.0.0.0\")"));
    }

    #[test]
    fn la_red_se_normaliza_a_su_direccion_de_red() {
        assert_eq!(red_y_mascara("10.20.7.9/16").unwrap(), ("10.20.0.0".parse().unwrap(), "255.255.0.0".parse().unwrap()));
        assert_eq!(red_y_mascara("0.0.0.0/0").unwrap().1, Ipv4Addr::new(0, 0, 0, 0));
        assert!(red_y_mascara("10.20.0.0").is_err());
        assert!(red_y_mascara("10.20.0.0/33").is_err());
    }

    #[test]
    fn sin_nodos_o_con_un_nodo_invalido_no_se_genera() {
        assert!(generar(&Config::default()).is_err());
        assert!(generar(&Config { pac_nodes: vec!["edge01:3128".into()], ..Config::default() }).is_err());
    }

    #[test]
    fn solo_se_sirve_el_pac_por_get() {
        let pac = "function FindProxyForURL(u, h) { return \"DIRECT\"; }\n";
        let ok = responder("GET /wpad.dat HTTP/1.1\r\nHost: x\r\n\r\n", pac);
        assert!(ok.starts_with("HTTP/1.1 200 OK") && ok.contains("application/x-ns-proxy-autoconfig") && ok.ends_with(pac));
        assert!(responder("GET /otra HTTP/1.1\r\n\r\n", pac).starts_with("HTTP/1.1 404"));
        assert!(responder("POST /wpad.dat HTTP/1.1\r\n\r\n", pac).starts_with("HTTP/1.1 404"));
    }
}
