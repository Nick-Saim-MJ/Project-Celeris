//! Lógica del proxy: controla el acceso, decide qué descifrar, sirve HITs, guarda MISSes y revalida con ETag.

use crate::access::{blocked_destination, literal_ip, ClientDecision, ClientGate, DestinationPolicy, ResolveError};
use crate::access_log::{AccessLog, Record};
use crate::clients::ClientStats;
use crate::coalesce::{Entry, FlightGuard, Flights};
use crate::config::{canonical_host, Config};
use crate::detect::Detector;
use crate::live::LiveLog;
use crate::memory::{MemoryBudget, Reservation};
use crate::policy::{self, AbsUrl, KeyNormalizer};
use crate::security::{SecurityEvent, SecurityLog};
use crate::stats::{Outcome, Stats};
use crate::store::{now, Meta, PutOutcome, Store};
use bytes::{Bytes, BytesMut};
use http_body_util::BodyExt;
use hudsucker::futures::{stream, StreamExt};
use hudsucker::hyper::header::{self, HeaderValue};
use hudsucker::hyper::http::uri::Authority;
use hudsucker::hyper::{Method, Request, Response, StatusCode, Uri};
use hudsucker::rustls::server::ClientHello;
use hudsucker::{Body, HttpContext, HttpHandler, RequestOrResponse};
use std::net::IpAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};

pub struct Shared {
    pub cfg: Config,
    pub store: Store,
    pub stats: Arc<Stats>,
    pub normalizer: KeyNormalizer,
    pub clients: ClientGate,
    pub destinations: Arc<DestinationPolicy>,
    pub memory: MemoryBudget,
    pub flights: Flights,
    pub access_log: AccessLog,
    pub client_stats: Arc<ClientStats>,
    pub detector: Arc<Detector>,
    pub live_log: Arc<LiveLog>,
    pub security: Arc<SecurityLog>,
    /// Página de http://celeris.aviso/, generada al arrancar.
    pub notice: Bytes,
}

/// Datos de una petición para medirla y registrarla al terminar. La ruta no incluye los parámetros.
struct RequestInfo {
    client: IpAddr,
    started: Instant,
    method: Method,
    scheme: Option<String>,
    host: String,
    port: Option<u16>,
    path: String,
}

impl RequestInfo {
    fn new(client: IpAddr, started: Instant, req: &Request<Body>, scheme: Option<&str>, host: &str) -> Self {
        Self {
            client,
            started,
            method: req.method().clone(),
            scheme: scheme.map(str::to_owned),
            host: host.to_owned(),
            port: req.uri().port_u16(),
            path: req.uri().path().to_owned(),
        }
    }

    fn log(&self, sh: &Shared, outcome: Outcome, status: Option<u16>, bytes: Option<u64>, elapsed: Duration) {
        sh.client_stats.record(self.client, outcome, bytes);
        sh.detector.observe(self.client, status, bytes);
        let record = Record {
            client: self.client,
            method: self.method.as_str(),
            scheme: self.scheme.as_deref(),
            host: &self.host,
            port: self.port,
            path: Some(&self.path),
            outcome,
            status,
            bytes,
            elapsed,
        };
        sh.live_log.record(&record);
        sh.access_log.record(record);
    }

    /// Mide y registra una petición que ya terminó o cuyo tamaño ya se conoce.
    fn finish(&self, sh: &Shared, outcome: Outcome, status: Option<u16>, bytes: Option<u64>) {
        let elapsed = self.started.elapsed();
        sh.stats.observe(outcome, elapsed);
        self.log(sh, outcome, status, bytes, elapsed);
    }
}

/// Lo que se recuerda entre `handle_request` y `handle_response` del mismo intercambio.
struct Pending {
    info: Arc<RequestInfo>,
    /// Sin parámetros: se usa en el registro y en los metadatos que se guardan en disco.
    url: String,
    key_hash: String,
    /// Copia vencida que se está revalidando con If-None-Match / If-Modified-Since,
    /// con su memoria ya reservada para poder servirla si el origen responde 304.
    stale: Option<(Arc<Meta>, Arc<Reservation>)>,
    /// Quienes piden lo mismo esperan hasta que esto se suelte, con la respuesta ya guardada.
    _flight: Option<FlightGuard>,
}

/// Qué falta por contar de la petición en curso cuando llegue la respuesta o el error del origen.
#[derive(Clone, Default)]
enum Exchange {
    /// Nada: la petición no se contó o ya se contó al recibirla.
    #[default]
    Untracked,
    /// Se reenvía sin tocar la caché.
    Bypass(Arc<RequestInfo>),
    /// Puede guardarse o revalidarse según lo que responda el origen.
    Candidate(Arc<Pending>),
}

#[derive(Clone)]
pub struct CacheHandler {
    shared: Arc<Shared>,
    exchange: Exchange,
    /// Destino del CONNECT en curso, para compararlo con el SNI que llegue después.
    connect_host: Option<String>,
}

/// Registra la petición cuando el cliente termina de recibir el cuerpo o se desconecta.
struct StreamRecord {
    shared: Arc<Shared>,
    info: Arc<RequestInfo>,
    status: u16,
    elapsed: Duration,
    bytes: u64,
}

impl Drop for StreamRecord {
    fn drop(&mut self) {
        self.info.log(&self.shared, Outcome::Bypass, Some(self.status), Some(self.bytes), self.elapsed);
    }
}

/// Reenvía el cuerpo en streaming contando sus bytes como bypass; conserva tamaño y trailers.
/// `sent` son los bytes que ya se contaron antes de empezar el streaming.
fn count_bypass(shared: Arc<Shared>, info: Arc<RequestInfo>, status: StatusCode, sent: u64, body: Body) -> Body {
    let elapsed = info.started.elapsed();
    shared.stats.observe(Outcome::Bypass, elapsed);
    let mut record = StreamRecord { shared, info, status: status.as_u16(), elapsed, bytes: sent };
    Body::from(
        body.map_frame(move |frame| {
            if let Some(data) = frame.data_ref() {
                Stats::add(&record.shared.stats.bytes_bypass, data.len() as u64);
                record.bytes += data.len() as u64;
            }
            frame
        })
        .boxed(),
    )
}

/// Mantiene reservada la memoria hasta que el cliente termine de recibir el cuerpo.
fn hold<R: Send + Sync + 'static>(body: Body, reservation: R) -> Body {
    Body::from(
        body.map_frame(move |frame| {
            let _ = &reservation;
            frame
        })
        .boxed(),
    )
}

fn empty_response(status: StatusCode) -> Response<Body> {
    Response::builder().status(status).body(Body::empty()).expect("respuesta estática válida")
}

const CACHE_STATUS: &str = "cache-status";
/// Nombre de este nodo en `Cache-Status` (RFC 9211, sección 2: identifica a la caché que responde).
const CACHE_NAME: &str = "celeris";

/// Qué hizo la caché con una petición, para la cabecera `Cache-Status` (RFC 9211, REQ-NF-11).
enum CacheResult {
    /// Servida desde disco; `ttl` es lo que le queda de vida (segundos, negativo si venció).
    Hit { ttl: i64 },
    /// La copia estaba vencida, el origen respondió 304 y se sirvió la copia con `ttl` ya renovado.
    Revalidated { ttl: i64 },
    /// Pedida al origen; `stored` indica si quedó guardada.
    Miss { stored: bool },
}

/// Valor de la cabecera `Cache-Status`: una lista estructurada (RFC 8941) con un elemento por caché.
/// No incluye `key` ni `detail`: la clave de caché contiene la URL completa y no debe salir del nodo.
fn cache_status_value(result: &CacheResult) -> String {
    match result {
        CacheResult::Hit { ttl } => format!("{CACHE_NAME}; hit; ttl={ttl}"),
        CacheResult::Revalidated { ttl } => format!("{CACHE_NAME}; hit; fwd=stale; fwd-status=304; ttl={ttl}"),
        CacheResult::Miss { stored: true } => format!("{CACHE_NAME}; fwd=miss; stored"),
        CacheResult::Miss { stored: false } => format!("{CACHE_NAME}; fwd=miss"),
    }
}

/// Segundos de vida que le quedan a una copia (negativo si ya venció).
fn remaining_ttl(expires_at: u64, now: u64) -> i64 {
    i64::try_from(expires_at).unwrap_or(i64::MAX).saturating_sub(i64::try_from(now).unwrap_or(i64::MAX))
}

/// ¿La ruta es una honey-URL (REQ-F-27)? Coincide la ruta exacta o cualquier ruta que cuelgue de ella. Una entrada vacía no cuenta: coincidiría con todo.
fn is_honey_url(honey: &[String], path: &str) -> bool {
    honey.iter().map(|h| h.trim()).filter(|h| !h.is_empty() && *h != "/").any(|h| {
        let h = h.trim_end_matches('/');
        let h = if h.starts_with('/') { h.to_owned() } else { format!("/{h}") };
        path == h || path.starts_with(&format!("{h}/"))
    })
}

/// El Host no decide nada: el destino y la clave de caché salen de la URI, que en HTTPS es la del CONNECT.
/// Que no coincidan no daña la caché, pero un navegador normal no lo hace.
fn host_differs(host_header: &HeaderValue, uri_host: &str) -> bool {
    let declared = host_header.to_str().ok().and_then(|text| text.parse::<Authority>().ok());
    declared.is_none_or(|authority| canonical_host(authority.host()) != canonical_host(uri_host))
}

/// La URL para el registro y el disco: los valores de los parámetros pueden ser tokens o datos personales.
fn without_query(url: &str) -> &str {
    url.split('?').next().unwrap_or(url)
}

impl CacheHandler {
    pub fn new(shared: Arc<Shared>) -> Self {
        Self { shared, exchange: Exchange::Untracked, connect_host: None }
    }

    async fn serve_from_cache<R: Send + Sync + 'static>(
        &self,
        meta: &Meta,
        status: &'static str,
        cache_status: String,
        reservation: R,
    ) -> Option<Response<Body>> {
        let body = self.shared.store.read_object(meta).await?;
        let mut b = Response::builder().status(StatusCode::OK);
        for (k, v) in &meta.headers {
            // El Cache-Status guardado describe otra transacción (la del origen con su propia caché): no se repite en un HIT.
            if !k.eq_ignore_ascii_case("cache-status") {
                b = b.header(k.as_str(), v.as_str());
            }
        }
        let age = now().saturating_sub(meta.stored_at);
        let len = body.len();
        let res = b
            .header(header::CONTENT_LENGTH, len)
            .header(header::AGE, age)
            .header("x-celeris-cache", status)
            .header(CACHE_STATUS, cache_status)
            .body(hold(Body::from(body), reservation))
            .ok()?;
        Stats::add(&self.shared.stats.bytes_from_cache, len as u64);
        Some(res)
    }

    fn stats_response(&self) -> Response<Body> {
        let json = serde_json::to_string_pretty(&self.shared.stats.snapshot()).unwrap_or_default();
        Response::builder()
            .header(header::CONTENT_TYPE, "application/json")
            .body(Body::from(json))
            .expect("respuesta estática válida")
    }

    fn notice_response(&self) -> Response<Body> {
        Response::builder()
            .header(header::CONTENT_TYPE, "text/html; charset=utf-8")
            // La página no necesita scripts ni recursos externos: se prohíben por completo.
            .header(header::CONTENT_SECURITY_POLICY, "default-src 'none'; style-src 'unsafe-inline'")
            .header(header::X_CONTENT_TYPE_OPTIONS, "nosniff")
            .header(header::CACHE_CONTROL, "no-store")
            .body(Body::from(self.shared.notice.clone()))
            .expect("respuesta estática válida")
    }

    /// Valida el destino de un CONNECT antes de abrir el túnel.
    async fn guard_connect(&self, client: IpAddr, started: Instant, mut req: Request<Body>) -> RequestOrResponse {
        let sh = &self.shared;
        let Some(authority) = req.uri().authority().cloned() else {
            return req.into();
        };
        let host = authority.host();
        let info = RequestInfo::new(client, started, &req, None, host);
        // Antes de resolver el nombre: un puerto no permitido no debe generar tráfico alguno.
        let port = authority.port_u16().unwrap_or(443);
        if !sh.cfg.connect_port_allowed(port) {
            Stats::inc(&sh.stats.blocked_ports);
            tracing::debug!(host, port, "CONNECT a un puerto no permitido");
            sh.detector.rare_port(client, port);
            sh.security.record(SecurityEvent { event: "port_blocked", srcip: Some(client), host: Some(host), port: Some(port), ..Default::default() });
            info.finish(sh, Outcome::Blocked, Some(403), None);
            return empty_response(StatusCode::FORBIDDEN).into();
        }
        let addrs = match sh.destinations.resolve(host, port).await {
            Ok(addrs) => addrs,
            Err(ResolveError::Blocked(ip)) => {
                Stats::inc(&sh.stats.blocked_destinations);
                tracing::debug!(host, %ip, "CONNECT a destino interno bloqueado");
                sh.security.record(SecurityEvent { event: "destination_blocked", srcip: Some(client), dstip: Some(ip), host: Some(host), port: Some(port), ..Default::default() });
                info.finish(sh, Outcome::Blocked, Some(403), None);
                return empty_response(StatusCode::FORBIDDEN).into();
            }
            Err(ResolveError::Lookup(e)) => {
                tracing::debug!(host, error = %e, "CONNECT a un nombre que no resuelve");
                info.finish(sh, Outcome::Tunnel, Some(502), None);
                return empty_response(StatusCode::BAD_GATEWAY).into();
            }
        };
        tracing::debug!(host, "CONNECT autorizado");
        // Un túnel lo abre Hudsucker, que volvería a resolver el nombre y podría recibir una IP interna.
        // Por eso se fija la IP ya validada. A cambio, el túnel no prueba las demás IPs del nombre.
        // No afecta a TLS: el SNI y el certificado siguen siendo un asunto entre cliente y origen.
        if !sh.cfg.should_intercept(host) {
            // Hudsucker no expone los bytes de un túnel: solo se puede registrar que se abrió.
            info.finish(sh, Outcome::Tunnel, None, None);
            let target = addrs.iter().find(|a| a.is_ipv4()).or_else(|| addrs.first());
            if let Some(uri) = target.and_then(|a| a.to_string().parse::<Uri>().ok()) {
                *req.uri_mut() = uri;
            }
        }
        req.into()
    }
}

impl HttpHandler for CacheHandler {
    /// Intercepción selectiva en modo proxy explícito (CONNECT host:443).
    async fn should_intercept_connect(&mut self, _ctx: &HttpContext, req: &Request<Body>) -> bool {
        let host = req.uri().host().unwrap_or_default();
        let yes = self.shared.cfg.should_intercept(host);
        // Hudsucker solo lee el SNI si se intercepta: en los demás túneles no hay nada que comparar.
        self.connect_host = yes.then(|| host.to_owned());
        if !yes {
            Stats::inc(&self.shared.stats.tls_passthrough);
        }
        tracing::debug!(host, intercept = yes, "CONNECT");
        yes
    }

    /// Segundo filtro sobre el SNI real del ClientHello: si no está en la lista, pasa cifrado.
    /// La intercepción se cuenta aquí porque recién en este punto queda decidida.
    async fn should_intercept_tls(&mut self, ctx: &HttpContext, hello: ClientHello<'_>) -> bool {
        let sni = hello.server_name();
        let yes = sni.map(|sni| self.shared.cfg.should_intercept(sni)).unwrap_or(false);
        let s = &self.shared.stats;
        Stats::inc(if yes { &s.tls_intercepted } else { &s.tls_passthrough });
        if let (Some(sni), Some(connect)) = (sni, self.connect_host.as_deref()) {
            if canonical_host(sni) != canonical_host(connect) {
                self.shared.detector.host_mismatch(ctx.client_addr.ip(), "El SNI no coincide con el destino del CONNECT.");
            }
        }
        if !yes {
            self.shared.client_stats.record(ctx.client_addr.ip(), Outcome::Tunnel, None);
            self.shared.detector.observe(ctx.client_addr.ip(), None, None);
            self.shared.access_log.record(Record {
                client: ctx.client_addr.ip(),
                method: Method::CONNECT.as_str(),
                scheme: None,
                host: sni.unwrap_or_default(),
                port: None,
                path: None,
                outcome: Outcome::Tunnel,
                status: None,
                bytes: None,
                elapsed: Duration::ZERO,
            });
        }
        yes
    }

    async fn handle_request(&mut self, ctx: &HttpContext, mut req: Request<Body>) -> RequestOrResponse {
        let sh = self.shared.clone();
        self.exchange = Exchange::Untracked;
        let started = Instant::now();

        // El control de acceso va primero: un cliente no permitido no llega a nada más, ni a las estadísticas.
        let client = ctx.client_addr.ip();
        match sh.clients.check(client) {
            ClientDecision::Allow => {}
            ClientDecision::Denied => {
                Stats::inc(&sh.stats.denied_clients);
                tracing::debug!(%client, "cliente no permitido");
                sh.security.record(SecurityEvent { event: "client_denied", srcip: Some(client), ..Default::default() });
                sh.detector.observe(client, Some(403), None);
                return empty_response(StatusCode::FORBIDDEN).into();
            }
            ClientDecision::RateLimited => {
                Stats::inc(&sh.stats.rate_limited);
                sh.client_stats.record_rate_limited(client);
                sh.detector.observe(client, Some(429), None);
                tracing::debug!(%client, "límite de peticiones superado");
                sh.security.record(SecurityEvent { event: "rate_limited", srcip: Some(client), ..Default::default() });
                let mut res = empty_response(StatusCode::TOO_MANY_REQUESTS);
                res.headers_mut().insert(header::RETRY_AFTER, HeaderValue::from_static("60"));
                return res.into();
            }
        }

        // req: REQ-F-28: nada que identifique al cliente sale hacia el origen ni hacia el shield. Las cabeceras que el cliente
        // (o un proxy anterior) haya puesto se eliminan aquí, antes de cualquier camino que reenvíe la petición.
        let quitadas = policy::strip_client_identity(req.headers_mut());
        if quitadas > 0 {
            tracing::debug!(%client, quitadas, "cabeceras de identidad del cliente eliminadas (REQ-F-28)");
        }

        // Hudsucker también pasa aquí el CONNECT inicial del túnel: no es contenido.
        if req.method() == Method::CONNECT {
            return self.guard_connect(client, started, req).await;
        }

        // Las IPs literales no pasan por el resolvedor protegido: se validan aquí.
        if let Some(ip) = req.uri().host().and_then(literal_ip) {
            if !sh.destinations.permits(ip) {
                Stats::inc(&sh.stats.blocked_destinations);
                tracing::debug!(%ip, "petición a destino interno bloqueada");
                sh.security.record(SecurityEvent { event: "destination_blocked", srcip: Some(client), dstip: Some(ip), port: req.uri().port_u16(), ..Default::default() });
                let info = RequestInfo::new(client, started, &req, req.uri().scheme_str(), req.uri().host().unwrap_or_default());
                info.finish(&sh, Outcome::Blocked, Some(403), None);
                return empty_response(StatusCode::FORBIDDEN).into();
            }
        }

        let Some(url) = AbsUrl::from_request(&req) else {
            return req.into();
        };
        if url.hostname() == sh.cfg.stats_host {
            return self.stats_response().into();
        }
        if url.hostname() == sh.cfg.notice_host {
            return self.notice_response().into();
        }
        // req: REQ-F-27: ninguna persona pide estas rutas; quien lo hace está recorriendo el sitio en busca de algo. No se reenvía nada.
        if is_honey_url(&sh.cfg.honey_urls, req.uri().path()) {
            sh.security.record(SecurityEvent { event: "honey_url", srcip: Some(client), host: Some(url.hostname()), path: Some(req.uri().path()), ..Default::default() });
            sh.detector.observe(client, Some(404), None);
            return empty_response(StatusCode::NOT_FOUND).into();
        }
        Stats::inc(&sh.stats.requests);
        let host = req.uri().host().unwrap_or(url.hostname());
        if sh.detector.enabled() {
            if let Some(declared) = req.headers().get(header::HOST) {
                if host_differs(declared, host) {
                    sh.detector.host_mismatch(client, "El Host no coincide con el destino de la petición.");
                }
            }
        }
        let info = Arc::new(RequestInfo::new(client, started, &req, Some(&url.scheme), host));

        let scope_ok = match url.scheme.as_str() {
            // HTTPS solo llega aquí si pasó el filtro de intercepción.
            "https" => true,
            "http" => sh.cfg.cache_plain_http && !sh.cfg.is_never_intercept(url.hostname()),
            _ => false,
        };
        if !scope_ok || !policy::request_is_cacheable(&req) {
            if req.headers().contains_key(header::UPGRADE) {
                // Hudsucker no llama a handle_response en un WebSocket: se cuenta ahora.
                Stats::inc(&sh.stats.bypass);
                info.log(&sh, Outcome::Bypass, None, None, Duration::ZERO);
            } else {
                self.exchange = Exchange::Bypass(info);
            }
            return req.into();
        }

        let normalized = sh.normalizer.normalize(&url);
        let key_hash = Store::key_hash(&format!("{normalized}|{}", policy::encoding_bucket(req.headers())));
        let log_url = without_query(&normalized).to_owned();
        let client_conditional =
            req.headers().contains_key(header::IF_NONE_MATCH) || req.headers().contains_key(header::IF_MODIFIED_SINCE);

        let mut cached = sh.store.get(&key_hash).await;
        let mut flight = None;
        // Si el cliente valida su propia copia, el origen le responde solo a él: no hay nada que compartir.
        if !client_conditional && !cached.as_ref().is_some_and(|m| m.is_fresh()) {
            match sh.flights.enter(&key_hash).await {
                Entry::Leader(guard) => flight = Some(guard),
                Entry::Waited => {
                    Stats::inc(&sh.stats.coalesced);
                    cached = sh.store.get(&key_hash).await;
                }
                Entry::Disabled => {}
            }
        }

        let mut stale = None;
        if let Some(meta) = cached {
            let needs_read = meta.is_fresh()
                || (!client_conditional && (meta.etag.is_some() || meta.last_modified.is_some()));
            if needs_read {
                let Some(reservation) = sh.memory.try_reserve(meta.size) else {
                    Stats::inc(&sh.stats.over_budget);
                    self.exchange = Exchange::Bypass(info);
                    return req.into();
                };
                if meta.is_fresh() {
                    let value = cache_status_value(&CacheResult::Hit { ttl: remaining_ttl(meta.expires_at, now()) });
                    if let Some(res) = self.serve_from_cache(&meta, "HIT", value, reservation).await {
                        Stats::inc(&sh.stats.hits);
                        info.finish(&sh, Outcome::Hit, Some(200), Some(meta.size));
                        tracing::info!(url = %log_url, "HIT");
                        return res.into();
                    }
                // Vencido: se pide al origen solo si cambió (ahorra el cuerpo completo si responde 304).
                // Antes se verifica la copia: si está dañada, un 304 no serviría de nada y hay que pedir el cuerpo.
                } else if sh.store.read_object(&meta).await.is_some() {
                    let h = req.headers_mut();
                    if let Some(v) = meta.etag.as_deref().and_then(|e| HeaderValue::from_str(e).ok()) {
                        h.insert(header::IF_NONE_MATCH, v);
                    }
                    if let Some(v) = meta.last_modified.as_deref().and_then(|e| HeaderValue::from_str(e).ok()) {
                        h.insert(header::IF_MODIFIED_SINCE, v);
                    }
                    stale = Some((meta, Arc::new(reservation)));
                }
            }
        }

        self.exchange = Exchange::Candidate(Arc::new(Pending { info, url: log_url, key_hash, stale, _flight: flight }));
        req.into()
    }

    async fn handle_response(&mut self, _ctx: &HttpContext, res: Response<Body>) -> Response<Body> {
        let sh = self.shared.clone();
        let status = res.status();
        let p = match std::mem::take(&mut self.exchange) {
            Exchange::Untracked => return res,
            Exchange::Bypass(info) => {
                Stats::inc(&sh.stats.bypass);
                return res.map(|body| count_bypass(sh, info, status, 0, body));
            }
            Exchange::Candidate(p) => p,
        };
        let log_url = &p.url;

        // 1) Revalidación exitosa: el origen confirma que nuestra copia sigue válida.
        if status == StatusCode::NOT_MODIFIED {
            let Some((meta, reservation)) = &p.stale else {
                // El 304 responde a la validación que envió el propio cliente, no a la nuestra.
                Stats::inc(&sh.stats.bypass);
                p.info.finish(&sh, Outcome::Bypass, Some(304), Some(0));
                return res;
            };
            let ttl = policy::ttl_secs(res.headers(), sh.cfg.default_ttl_secs);
            if let Err(e) = sh.store.refresh(&p.key_hash, meta, ttl).await {
                Stats::inc(&sh.stats.store_write_errors);
                tracing::warn!(url = %log_url, error = %e, "no se pudo extender la vigencia");
            }
            let value = cache_status_value(&CacheResult::Revalidated { ttl: i64::try_from(ttl).unwrap_or(i64::MAX) });
            if let Some(cached) = self.serve_from_cache(meta, "REVALIDATED", value, reservation.clone()).await {
                Stats::inc(&sh.stats.revalidated);
                p.info.finish(&sh, Outcome::Revalidated, Some(200), Some(meta.size));
                tracing::info!(url = %log_url, "REVALIDATED (304)");
                return cached;
            }
            // La copia se verificó al enviar la petición, pero dejó de poder leerse. El cliente
            // no pidió un 304, así que no se le puede reenviar: recibe un error y puede reintentar.
            Stats::inc(&sh.stats.cache_errors);
            p.info.finish(&sh, Outcome::CacheError, Some(502), None);
            tracing::warn!(url = %log_url, "copia ilegible tras un 304 del origen");
            return empty_response(StatusCode::BAD_GATEWAY);
        }

        // 2) No cacheable: se reenvía tal cual, en streaming.
        if !policy::response_is_cacheable(&res, sh.cfg.max_object_bytes) {
            Stats::inc(&sh.stats.bypass);
            let info = p.info.clone();
            return res.map(|body| count_bypass(sh, info, status, 0, body));
        }

        // 3) Se acumula el cuerpo hasta el límite o hasta agotar la memoria disponible.
        //    Si no cabe, se reenvía sin guardar.
        let (mut parts, mut body) = res.into_parts();
        let mut buf = BytesMut::new();
        let mut reservation: Option<Reservation> = None;
        let max = sh.cfg.max_object_bytes;
        let complete = loop {
            match body.frame().await {
                None => break true,
                Some(Ok(frame)) => {
                    if let Ok(data) = frame.into_data() {
                        let more = sh.memory.try_reserve(data.len() as u64);
                        let reserved = more.is_some();
                        match (&mut reservation, more) {
                            (Some(held), Some(more)) => held.merge(more),
                            (held, more) if more.is_some() => *held = more,
                            _ => {}
                        }
                        buf.extend_from_slice(&data);
                        if !reserved {
                            Stats::inc(&sh.stats.over_budget);
                            break false;
                        }
                        if buf.len() > max {
                            break false;
                        }
                    }
                }
                Some(Err(e)) => {
                    Stats::inc(&sh.stats.origin_errors);
                    p.info.finish(&sh, Outcome::OriginError, Some(502), None);
                    tracing::warn!(url = %log_url, error = %e, "error leyendo cuerpo del origen");
                    return empty_response(StatusCode::BAD_GATEWAY);
                }
            }
        };

        if !complete {
            Stats::inc(&sh.stats.bypass);
            let sent = buf.len() as u64;
            Stats::add(&sh.stats.bytes_bypass, sent);
            let head = stream::once(async move { Ok::<Bytes, hudsucker::Error>(buf.freeze()) });
            let rest = count_bypass(sh, p.info.clone(), status, sent, body).into_data_stream();
            return Response::from_parts(parts, hold(Body::from_stream(head.chain(rest)), reservation));
        }

        let bytes = buf.freeze();
        Stats::inc(&sh.stats.misses);
        Stats::add(&sh.stats.bytes_from_origin, bytes.len() as u64);

        let h = &parts.headers;
        let ttl = policy::ttl_secs(h, sh.cfg.default_ttl_secs);
        let meta = Meta {
            url: p.url.clone(),
            object: String::new(),
            size: 0,
            headers: h
                .iter()
                .filter(|(k, _)| !policy::is_hop_by_hop(k.as_str()))
                .filter_map(|(k, v)| Some((k.as_str().to_owned(), v.to_str().ok()?.to_owned())))
                .collect(),
            stored_at: now(),
            expires_at: now() + ttl,
            etag: h.get(header::ETAG).and_then(|v| v.to_str().ok()).map(str::to_owned),
            last_modified: h.get(header::LAST_MODIFIED).and_then(|v| v.to_str().ok()).map(str::to_owned),
        };

        let stored = match sh.store.put(&p.key_hash, meta, &bytes).await {
            Ok(PutOutcome::New) => {
                Stats::inc(&sh.stats.stored_new);
                true
            }
            Ok(PutOutcome::Deduplicated) => {
                Stats::inc(&sh.stats.dedup);
                tracing::info!(url = %log_url, "contenido idéntico ya almacenado (dedup)");
                true
            }
            Err(e) => {
                Stats::inc(&sh.stats.store_write_errors);
                tracing::warn!(url = %log_url, error = %e, "no se pudo guardar");
                false
            }
        };
        p.info.finish(&sh, Outcome::Miss, Some(status.as_u16()), Some(bytes.len() as u64));
        tracing::info!(url = %log_url, bytes = bytes.len(), ttl, "MISS → guardado");

        parts.headers.remove(header::TRANSFER_ENCODING);
        parts.headers.insert(header::CONTENT_LENGTH, HeaderValue::from(bytes.len()));
        parts.headers.insert("x-celeris-cache", HeaderValue::from_static("MISS"));
        // Se añade al final de la lista: si el origen ya trae `Cache-Status` de otra caché, se conserva (RFC 9211, sección 2).
        if let Ok(value) = HeaderValue::from_str(&cache_status_value(&CacheResult::Miss { stored })) {
            parts.headers.append(CACHE_STATUS, value);
        }
        Response::from_parts(parts, hold(Body::from(bytes), reservation))
    }

    async fn handle_error(&mut self, _ctx: &HttpContext, err: hyper_util::client::legacy::Error) -> Response<Body> {
        let info = match std::mem::take(&mut self.exchange) {
            Exchange::Untracked => None,
            Exchange::Bypass(info) => Some(info),
            Exchange::Candidate(p) => Some(p.info.clone()),
        };
        if let Some(info) = info {
            // Un nombre que apunta a la red interna se bloquea al resolverlo, sin llegar a conectarse.
            if let Some(ip) = blocked_destination(&err) {
                self.shared.security.record(SecurityEvent {
                    event: "destination_blocked",
                    srcip: Some(info.client),
                    dstip: Some(ip),
                    host: Some(&info.host),
                    port: info.port,
                    ..Default::default()
                });
            }
            Stats::inc(&self.shared.stats.origin_errors);
            info.finish(&self.shared, Outcome::OriginError, Some(502), None);
        }
        tracing::warn!(error = ?err, "no se pudo contactar al origen");
        empty_response(StatusCode::BAD_GATEWAY)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compara_el_host_sin_contar_puerto_mayusculas_ni_punto_final() {
        let differs = |value: &str, uri: &str| host_differs(&HeaderValue::from_str(value).unwrap(), uri);
        assert!(!differs("cdn.example.com", "cdn.example.com"));
        assert!(!differs("CDN.example.com:8443", "cdn.example.com"));
        assert!(!differs("cdn.example.com.", "cdn.example.com"));
        assert!(!differs("[::1]:8080", "[::1]"));
        assert!(differs("otro.example.com", "cdn.example.com"));
        assert!(differs("no es un host", "cdn.example.com"));
    }

    #[test]
    fn cache_status_sigue_la_sintaxis_de_rfc_9211() {
        assert_eq!(cache_status_value(&CacheResult::Hit { ttl: 120 }), "celeris; hit; ttl=120");
        assert_eq!(cache_status_value(&CacheResult::Hit { ttl: -5 }), "celeris; hit; ttl=-5");
        assert_eq!(cache_status_value(&CacheResult::Miss { stored: true }), "celeris; fwd=miss; stored");
        assert_eq!(cache_status_value(&CacheResult::Miss { stored: false }), "celeris; fwd=miss");
        assert_eq!(
            cache_status_value(&CacheResult::Revalidated { ttl: 60 }),
            "celeris; hit; fwd=stale; fwd-status=304; ttl=60"
        );
    }

    #[test]
    fn cache_status_no_revela_la_clave_ni_detalles() {
        for r in [CacheResult::Hit { ttl: 1 }, CacheResult::Revalidated { ttl: 1 }, CacheResult::Miss { stored: true }] {
            let v = cache_status_value(&r);
            assert!(!v.contains("key") && !v.contains("detail") && !v.contains("http"), "{v}");
            assert!(HeaderValue::from_str(&v).is_ok());
        }
    }

    #[test]
    fn la_vida_restante_puede_ser_negativa_y_no_desborda() {
        assert_eq!(remaining_ttl(100, 40), 60);
        assert_eq!(remaining_ttl(40, 100), -60);
        assert_eq!(remaining_ttl(u64::MAX, 0), i64::MAX);
    }

    #[test]
    fn las_honey_urls_coinciden_por_ruta_y_por_prefijo() {
        let honey = vec!["/admin-backup.zip".to_owned(), "wp-login-trampa/".to_owned(), "".to_owned(), "/".to_owned()];
        assert!(is_honey_url(&honey, "/admin-backup.zip"));
        assert!(is_honey_url(&honey, "/wp-login-trampa"));
        assert!(is_honey_url(&honey, "/wp-login-trampa/entrar"));
        assert!(!is_honey_url(&honey, "/wp-login-trampa-otra"), "un prefijo de texto no es un prefijo de ruta");
        assert!(!is_honey_url(&honey, "/"), "una entrada vacía o «/» no puede marcar todo el sitio como señuelo");
        assert!(!is_honey_url(&honey, "/static.js"));
        assert!(!is_honey_url(&[], "/admin-backup.zip"));
    }

    #[test]
    fn el_registro_no_incluye_parametros() {
        assert_eq!(without_query("https://a.example/b.js?token=secreto&x=1"), "https://a.example/b.js");
        assert_eq!(without_query("https://a.example/b.js"), "https://a.example/b.js");
    }
}
