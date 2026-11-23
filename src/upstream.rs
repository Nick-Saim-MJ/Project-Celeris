//! Conexión del proxy hacia los orígenes (rustls + Hyper).
//!
//! Confía en las raíces públicas (webpki-roots) y, opcionalmente, en CAs extra
//! (p. ej. la CA privada de la intranet de tu campus o de un laboratorio).
//!
//! El destino se valida al resolver el nombre, justo antes de conectar. Validarlo antes no bastaría:
//! un dominio puede responder con una IP pública a la comprobación y con una interna al conectar.

use crate::access::{DestinationPolicy, ResolveError};
use crate::stats::Stats;
use anyhow::Context;
use hudsucker::rustls::{
    self,
    crypto::aws_lc_rs,
    pki_types::{pem::PemObject, CertificateDer, PrivateKeyDer},
};
use hyper::rt::ReadBufCursor;
use hyper::Uri;
use hyper_rustls::{HttpsConnector, HttpsConnectorBuilder, MaybeHttpsStream};
use hyper_util::client::legacy::connect::{dns::Name, Connected, Connection, HttpConnector};
use hyper_util::rt::TokioIo;
use pin_project_lite::pin_project;
use tokio::net::TcpStream;
use std::{
    future::Future,
    io,
    net::SocketAddr,
    path::PathBuf,
    pin::Pin,
    sync::Arc,
    task::{Context as TaskContext, Poll},
    time::Duration,
    vec,
};
use tower_service::Service;

/// Resolvedor que rechaza los nombres que apuntan a destinos internos.
#[derive(Clone)]
pub struct GuardedResolver {
    destinations: Arc<DestinationPolicy>,
    stats: Arc<Stats>,
}

impl Service<Name> for GuardedResolver {
    type Response = vec::IntoIter<SocketAddr>;
    type Error = io::Error;
    type Future = Pin<Box<dyn Future<Output = io::Result<Self::Response>> + Send>>;

    fn poll_ready(&mut self, _cx: &mut TaskContext<'_>) -> Poll<io::Result<()>> {
        Poll::Ready(Ok(()))
    }

    fn call(&mut self, name: Name) -> Self::Future {
        let this = self.clone();
        Box::pin(async move {
            // Con puerto 0, HttpConnector aplica después el puerto de la URL.
            match this.destinations.resolve(name.as_str(), 0).await {
                Ok(addrs) => Ok(addrs.into_iter()),
                Err(e) => {
                    if matches!(e, ResolveError::Blocked(_)) {
                        Stats::inc(&this.stats.blocked_destinations);
                    }
                    Err(e.into())
                }
            }
        })
    }
}

/// Ajustes del proxy padre (REQ-F-29), tomados de la configuración.
pub struct ParentSettings {
    pub addr: String,
    pub cert: PathBuf,
    pub key: PathBuf,
}

impl ParentSettings {
    /// `None` si no hay proxy padre configurado.
    pub fn from_config(cfg: &crate::config::Config) -> Option<Self> {
        let addr = cfg.upstream_parent.trim();
        (!addr.is_empty()).then(|| Self { addr: addr.to_owned(), cert: cfg.upstream_parent_cert.clone(), key: cfg.upstream_parent_key.clone() })
    }
}

#[derive(Clone)]
struct Parent {
    uri: Uri,
    connector: HttpsConnector<HttpConnector>,
}

/// Conector del nodo: sale directo al origen o, con proxy padre, abre siempre la conexión hacia él (TLS con certificado de cliente) y marca
/// la conexión como «proxied» para que Hyper envíe la URL completa en la línea de petición, como espera un proxy.
#[derive(Clone)]
pub struct Upstream {
    direct: HttpsConnector<HttpConnector<GuardedResolver>>,
    parent: Option<Parent>,
}

pin_project! {
    /// Conexión ya establecida, con la marca de si va hacia un proxy.
    pub struct UpstreamStream {
        #[pin]
        inner: MaybeHttpsStream<TokioIo<TcpStream>>,
        proxied: bool,
    }
}

impl hyper::rt::Read for UpstreamStream {
    fn poll_read(self: Pin<&mut Self>, cx: &mut TaskContext<'_>, buf: ReadBufCursor<'_>) -> Poll<io::Result<()>> {
        self.project().inner.poll_read(cx, buf)
    }
}

impl hyper::rt::Write for UpstreamStream {
    fn poll_write(self: Pin<&mut Self>, cx: &mut TaskContext<'_>, buf: &[u8]) -> Poll<io::Result<usize>> {
        self.project().inner.poll_write(cx, buf)
    }
    fn poll_flush(self: Pin<&mut Self>, cx: &mut TaskContext<'_>) -> Poll<io::Result<()>> {
        self.project().inner.poll_flush(cx)
    }
    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut TaskContext<'_>) -> Poll<io::Result<()>> {
        self.project().inner.poll_shutdown(cx)
    }
    fn is_write_vectored(&self) -> bool {
        self.inner.is_write_vectored()
    }
    fn poll_write_vectored(self: Pin<&mut Self>, cx: &mut TaskContext<'_>, bufs: &[io::IoSlice<'_>]) -> Poll<io::Result<usize>> {
        self.project().inner.poll_write_vectored(cx, bufs)
    }
}

impl Connection for UpstreamStream {
    fn connected(&self) -> Connected {
        self.inner.connected().proxy(self.proxied)
    }
}

impl Service<Uri> for Upstream {
    type Response = UpstreamStream;
    type Error = Box<dyn std::error::Error + Send + Sync>;
    type Future = Pin<Box<dyn Future<Output = Result<UpstreamStream, Self::Error>> + Send>>;

    fn poll_ready(&mut self, _cx: &mut TaskContext<'_>) -> Poll<Result<(), Self::Error>> {
        Poll::Ready(Ok(()))
    }

    fn call(&mut self, destino: Uri) -> Self::Future {
        match &self.parent {
            Some(padre) => {
                // Con proxy padre el destino real no se resuelve aquí: lo resuelve el shield.
                let (mut conector, uri) = (padre.connector.clone(), padre.uri.clone());
                Box::pin(async move { Ok(UpstreamStream { inner: conector.call(uri).await?, proxied: true }) })
            }
            None => {
                let mut conector = self.direct.clone();
                Box::pin(async move { Ok(UpstreamStream { inner: conector.call(destino).await?, proxied: false }) })
            }
        }
    }
}

fn raices(extra_cas: &[PathBuf]) -> anyhow::Result<rustls::RootCertStore> {
    let mut roots = rustls::RootCertStore::empty();
    roots.extend(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());
    for path in extra_cas {
        for cert in CertificateDer::pem_file_iter(path).with_context(|| format!("leyendo {}", path.display()))? {
            roots.add(cert?)?;
        }
        tracing::info!("CA extra de confianza para orígenes: {}", path.display());
    }
    Ok(roots)
}

/// Conexión hacia el shield: TLS con certificado de cliente (mTLS). Es una conexión de confianza configurada por el operador, por eso
/// no pasa por la protección contra destinos internos: el shield vive en una red privada (AWS, por la VPN).
fn conector_del_padre(roots: rustls::RootCertStore, ajustes: &ParentSettings) -> anyhow::Result<Parent> {
    for (nombre, ruta) in [("upstream_parent_cert", &ajustes.cert), ("upstream_parent_key", &ajustes.key)] {
        if !ruta.exists() {
            anyhow::bail!("{nombre} no existe: {} (REQ-F-29: el proxy padre exige certificado de cliente)", ruta.display());
        }
    }
    let cadena: Vec<CertificateDer<'static>> = CertificateDer::pem_file_iter(&ajustes.cert)
        .with_context(|| format!("leyendo {}", ajustes.cert.display()))?
        .collect::<Result<_, _>>()?;
    let llave = PrivateKeyDer::from_pem_file(&ajustes.key).with_context(|| format!("llave inválida en {}", ajustes.key.display()))?;
    let tls = rustls::ClientConfig::builder_with_provider(Arc::new(aws_lc_rs::default_provider()))
        .with_safe_default_protocol_versions()?
        .with_root_certificates(roots)
        .with_client_auth_cert(cadena, llave)?;
    let mut http = HttpConnector::new();
    http.enforce_http(false);
    http.set_nodelay(true);
    http.set_connect_timeout(Some(Duration::from_secs(10)));
    let connector = HttpsConnectorBuilder::new().with_tls_config(tls).https_only().enable_http1().wrap_connector(http);
    let uri: Uri = format!("https://{}", ajustes.addr).parse().with_context(|| format!("upstream_parent inválido: {}", ajustes.addr))?;
    tracing::info!("proxy padre (shield): {} con mTLS", ajustes.addr);
    Ok(Parent { uri, connector })
}

pub fn connector(
    extra_cas: &[PathBuf],
    destinations: Arc<DestinationPolicy>,
    stats: Arc<Stats>,
    padre: Option<&ParentSettings>,
) -> anyhow::Result<Upstream> {
    let roots = raices(extra_cas)?;
    let parent = padre.map(|a| conector_del_padre(roots.clone(), a)).transpose()?;

    let tls = rustls::ClientConfig::builder_with_provider(Arc::new(aws_lc_rs::default_provider()))
        .with_safe_default_protocol_versions()?
        .with_root_certificates(roots)
        .with_no_client_auth();

    let mut http = HttpConnector::new_with_resolver(GuardedResolver { destinations, stats });
    http.enforce_http(false);
    http.set_nodelay(true);
    http.set_connect_timeout(Some(Duration::from_secs(10)));

    let direct = HttpsConnectorBuilder::new().with_tls_config(tls).https_or_http().enable_http1().wrap_connector(http);
    Ok(Upstream { direct, parent })
}
