//! Política viva del nodo: lo que la consola puede cambiar sin reiniciar (REQ-F-17, mínimo verificable) y la regla del Wi-Fi de estudiantes (REQ-F-36).
//!
//! * `byod_networks`: redes de origen BYOD. El tráfico de esos clientes NUNCA se descifra, aunque el dominio esté en `intercept_domains`
//!   (REQ-F-36). La regla no depende de la configuración que llegue: se aplica después de ella (REQ-RN-11).
//! * Configuración firmada: `config.toml` + `config.toml.sig` (ed25519, en hexadecimal) y una llave pública fijada en el arranque.
//!   Se recarga por intervalo o con SIGHUP. Si la firma no verifica, la versión es menor que la aplicada o la configuración es inválida,
//!   se rechaza, se conserva la anterior y se emite un evento de seguridad. Solo cambian `allowed_clients`, `intercept_domains`,
//!   `never_intercept` y `byod_networks`; el resto exige reiniciar.

use crate::access::{ClientGate, Network};
use crate::config::{canonical_host, matches_suffix, Config};
use crate::security::{SecurityEvent, SecurityLog};
use anyhow::{bail, Context};
use aws_lc_rs::signature::{UnparsedPublicKey, ED25519};
use std::net::IpAddr;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, RwLock};

/// Instantánea de la política que consultan los manejadores en cada petición.
#[derive(Debug, Clone)]
pub struct Policy {
    pub intercept_domains: Vec<String>,
    pub never_intercept: Vec<String>,
    byod: Vec<Network>,
}

impl Policy {
    pub fn from_config(cfg: &Config) -> anyhow::Result<Self> {
        let byod = cfg.byod_networks.iter().map(|s| s.parse()).collect::<anyhow::Result<Vec<Network>>>().context("byod_networks inválido")?;
        Ok(Self { intercept_domains: cfg.intercept_domains.clone(), never_intercept: cfg.never_intercept.clone(), byod })
    }

    /// ¿La IP del cliente pertenece a una red BYOD?
    pub fn is_byod(&self, ip: IpAddr) -> bool {
        self.byod.iter().any(|n| n.contains(ip))
    }

    /// Dominios protegidos: no se descifran ni se cachean, tampoco por HTTP plano.
    pub fn is_never_intercept(&self, host: &str) -> bool {
        let host = canonical_host(host);
        self.never_intercept.iter().any(|s| matches_suffix(&host, s))
    }

    /// Solo por la lista de dominios (sin mirar al cliente).
    pub fn domain_allowed(&self, host: &str) -> bool {
        if self.is_never_intercept(host) {
            return false;
        }
        let host = canonical_host(host);
        self.intercept_domains.iter().any(|s| matches_suffix(&host, s))
    }

    /// ¿Se descifra el TLS de este cliente hacia este host? Un cliente BYOD nunca (REQ-F-36).
    // req: REQ-F-36
    pub fn should_intercept(&self, host: &str, client: IpAddr) -> bool {
        !self.is_byod(client) && self.domain_allowed(host)
    }
}

/// Política en vigor; se sustituye entera al aplicar una configuración firmada.
pub struct LivePolicy(RwLock<Arc<Policy>>);

impl LivePolicy {
    pub fn new(p: Policy) -> Self {
        Self(RwLock::new(Arc::new(p)))
    }

    pub fn current(&self) -> Arc<Policy> {
        self.0.read().expect("la política no se envenena").clone()
    }

    fn set(&self, p: Policy) {
        *self.0.write().expect("la política no se envenena") = Arc::new(p);
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum Resultado {
    Aplicada(u64),
    SinCambios,
    Rechazada(&'static str),
}

/// Configuración firmada por la consola: ruta, llave pública fijada y versión aplicada.
pub struct Firmada {
    ruta: PathBuf,
    llave: Vec<u8>,
    version: Mutex<u64>,
    /// Dominios que la CA del nodo puede firmar (`None` = sin límites).
    ca_permitidos: Option<Vec<String>>,
}

/// Verifica una firma ed25519 (hex) sobre los bytes exactos del archivo.
// req: REQ-F-17
pub fn verificar(bytes: &[u8], firma_hex: &str, llave: &[u8]) -> anyhow::Result<()> {
    let firma = hex::decode(firma_hex.trim()).context("la firma no es hexadecimal")?;
    UnparsedPublicKey::new(&ED25519, llave).verify(bytes, &firma).map_err(|_| anyhow::anyhow!("la firma no verifica"))
}

fn leer_llave(ruta: &Path) -> anyhow::Result<Vec<u8>> {
    let llave = hex::decode(std::fs::read_to_string(ruta).with_context(|| format!("leyendo {}", ruta.display()))?.trim()).context("la llave pública no es hexadecimal")?;
    if llave.len() != 32 {
        bail!("la llave pública ed25519 debe tener 32 bytes y tiene {}", llave.len());
    }
    Ok(llave)
}

impl Firmada {
    /// `None` si el nodo no usa configuración firmada. Falla si se pidió y falta la llave pública.
    pub fn desde_config(cfg: &Config, ca_permitidos: Option<Vec<String>>) -> anyhow::Result<Option<Self>> {
        let Some(ruta) = cfg.signed_config.clone() else { return Ok(None) };
        let llave_ruta = cfg.config_public_key.as_ref().context("signed_config exige config_public_key (llave pública fijada en el arranque)")?;
        Ok(Some(Self { ruta, llave: leer_llave(llave_ruta)?, version: Mutex::new(cfg.config_version), ca_permitidos }))
    }

    fn firma_ruta(&self) -> PathBuf {
        let mut s = self.ruta.clone().into_os_string();
        s.push(".sig");
        PathBuf::from(s)
    }

    /// Lee, verifica y aplica la configuración firmada. Nunca deja la política a medias: o se aplica entera o se conserva la anterior.
    pub fn recargar(&self, politica: &LivePolicy, clientes: &ClientGate, seguridad: &SecurityLog) -> Resultado {
        let rechazo = |motivo: &'static str, detalle: String| {
            seguridad.record(SecurityEvent { event: "config_rejected", reason: Some(motivo), detail: Some(&detalle), ..Default::default() });
            tracing::warn!("configuración firmada rechazada ({motivo}): {detalle}");
            Resultado::Rechazada(motivo)
        };
        let bytes = match std::fs::read(&self.ruta) {
            Ok(b) => b,
            // La consola todavía no publicó nada: se sigue con la configuración de arranque, sin ruido.
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Resultado::SinCambios,
            Err(e) => return rechazo("ilegible", format!("{}: {e}", self.ruta.display())),
        };
        let firma = match std::fs::read_to_string(self.firma_ruta()) {
            Ok(s) => s,
            Err(e) => return rechazo("sin_firma", format!("{}: {e}", self.firma_ruta().display())),
        };
        if let Err(e) = verificar(&bytes, &firma, &self.llave) {
            return rechazo("firma_invalida", format!("{e:#}"));
        }
        let nueva: Config = match std::str::from_utf8(&bytes).map_err(anyhow::Error::from).and_then(|t| toml::from_str(t).map_err(anyhow::Error::from)) {
            Ok(c) => c,
            Err(e) => return rechazo("invalida", format!("{e:#}")),
        };
        let mut aplicada = self.version.lock().expect("la versión no se envenena");
        if nueva.config_version < *aplicada {
            return rechazo("version_anterior", format!("versión {} menor que la aplicada ({})", nueva.config_version, *aplicada));
        }
        if nueva.config_version == *aplicada {
            return Resultado::SinCambios;
        }
        let pol = match Policy::from_config(&nueva) {
            Ok(p) => p,
            Err(e) => return rechazo("invalida", format!("{e:#}")),
        };
        if let Some(permitidos) = &self.ca_permitidos {
            let sin_cubrir = crate::ca::uncovered_domains(&nueva.intercept_domains, permitidos);
            if !sin_cubrir.is_empty() {
                return rechazo("ca_no_cubre", format!("la CA del nodo no puede firmar para {sin_cubrir:?} (REQ-RN-04)"));
            }
        }
        if let Err(e) = clientes.reload(&nueva.allowed_clients) {
            return rechazo("clientes_invalidos", format!("{e:#}"));
        }
        politica.set(pol);
        *aplicada = nueva.config_version;
        let detalle = format!("versión {}", nueva.config_version);
        seguridad.record(SecurityEvent { event: "config_applied", detail: Some(&detalle), ..Default::default() });
        tracing::info!("configuración firmada aplicada: {detalle}");
        Resultado::Aplicada(nueva.config_version)
    }
}

/// Recarga por intervalo y con SIGHUP.
pub fn iniciar(firmada: Arc<Firmada>, politica: Arc<LivePolicy>, clientes: Arc<ClientGate>, seguridad: Arc<SecurityLog>, cada_segundos: u64) {
    tokio::spawn(async move {
        let mut tic = tokio::time::interval(std::time::Duration::from_secs(cada_segundos.max(1)));
        #[cfg(unix)]
        let mut hup = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::hangup()).ok();
        loop {
            #[cfg(unix)]
            {
                tokio::select! {
                    _ = tic.tick() => {}
                    _ = async { match hup.as_mut() { Some(h) => { h.recv().await; } None => std::future::pending::<()>().await } } => {}
                }
            }
            #[cfg(not(unix))]
            tic.tick().await;
            let (f, p, c, s) = (firmada.clone(), politica.clone(), clientes.clone(), seguridad.clone());
            let _ = tokio::task::spawn_blocking(move || f.recargar(&p, &c, &s)).await;
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;
    use aws_lc_rs::signature::{Ed25519KeyPair, KeyPair};

    fn par() -> Ed25519KeyPair {
        Ed25519KeyPair::generate().unwrap()
    }

    fn escribir(dir: &Path, k: &Ed25519KeyPair, toml: &str) {
        std::fs::write(dir.join("config.toml"), toml).unwrap();
        std::fs::write(dir.join("config.toml.sig"), hex::encode(k.sign(toml.as_bytes()).as_ref())).unwrap();
    }

    fn montaje(dir: &Path, k: &Ed25519KeyPair) -> (Firmada, LivePolicy, Arc<ClientGate>, Arc<SecurityLog>) {
        std::fs::write(dir.join("llave.pub"), hex::encode(k.public_key().as_ref())).unwrap();
        let cfg = Config {
            signed_config: Some(dir.join("config.toml")),
            config_public_key: Some(dir.join("llave.pub")),
            intercept_domains: vec!["cdn.example".into()],
            ..Config::default()
        };
        let stats = Arc::new(crate::stats::Stats::default());
        let clientes = Arc::new(ClientGate::new(&cfg, "127.0.0.1:3128".parse().unwrap()).unwrap());
        let f = Firmada::desde_config(&cfg, None).unwrap().unwrap();
        (f, LivePolicy::new(Policy::from_config(&cfg).unwrap()), clientes, Arc::new(SecurityLog::disabled(stats)))
    }

    fn ip(s: &str) -> IpAddr {
        s.parse().unwrap()
    }

    // req: REQ-F-36
    #[test]
    fn un_cliente_byod_nunca_se_descifra_aunque_el_dominio_este_en_la_lista() {
        let cfg = Config { intercept_domains: vec!["cdn.example".into()], byod_networks: vec!["172.16.0.0/16".into()], ..Config::default() };
        let p = Policy::from_config(&cfg).unwrap();
        assert!(p.should_intercept("cdn.example", ip("10.20.32.5")), "un PC de laboratorio sí se descifra");
        assert!(!p.should_intercept("cdn.example", ip("172.16.0.50")), "un equipo del Wi-Fi nunca");
        assert!(!p.should_intercept("CDN.example.", ip("172.16.255.254")));
        assert!(p.domain_allowed("cdn.example"), "la lista de dominios no cambia: lo que cambia es el cliente");
    }

    // req: REQ-F-36
    #[test]
    fn un_byod_invalido_se_rechaza() {
        let cfg = Config { byod_networks: vec!["no-es-una-red".into()], ..Config::default() };
        assert!(Policy::from_config(&cfg).is_err());
    }

    // req: REQ-F-17
    #[test]
    fn la_firma_ed25519_se_verifica_y_una_alteracion_se_detecta() {
        let k = par();
        let firma = hex::encode(k.sign(b"a = 1").as_ref());
        assert!(verificar(b"a = 1", &firma, k.public_key().as_ref()).is_ok());
        assert!(verificar(b"a = 2", &firma, k.public_key().as_ref()).is_err());
        assert!(verificar(b"a = 1", "zz", k.public_key().as_ref()).is_err());
        assert!(verificar(b"a = 1", &firma, par().public_key().as_ref()).is_err(), "otra llave no sirve");
    }

    // req: REQ-F-17
    #[test]
    fn una_configuracion_firmada_con_version_mayor_se_aplica() {
        let d = tempdir("aplica");
        let k = par();
        let (f, pol, clientes, seg) = montaje(&d, &k);
        escribir(&d, &k, "config_version = 2\nallowed_clients = [\"127.0.0.1/32\", \"10.20.32.0/26\"]\nintercept_domains = [\"cdn.example\", \"nuevo.example\"]\nbyod_networks = [\"172.16.0.0/16\"]\n");
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Aplicada(2));
        assert!(pol.current().domain_allowed("nuevo.example") && pol.current().is_byod(ip("172.16.1.1")));
        assert_eq!(clientes.check(ip("10.20.32.9")), crate::access::ClientDecision::Allow);
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::SinCambios, "la misma versión no se vuelve a aplicar");
    }

    // req: REQ-F-17
    #[test]
    fn sin_firma_valida_se_conserva_la_configuracion_anterior() {
        let d = tempdir("sinfirma");
        let k = par();
        let (f, pol, clientes, seg) = montaje(&d, &k);
        // firmada por otra llave
        escribir(&d, &par(), "config_version = 5\nallowed_clients = [\"127.0.0.1/32\"]\nintercept_domains = [\"malo.example\"]\n");
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Rechazada("firma_invalida"));
        assert!(!pol.current().domain_allowed("malo.example") && pol.current().domain_allowed("cdn.example"));
        // firmada y luego alterada
        escribir(&d, &k, "config_version = 5\nallowed_clients = [\"127.0.0.1/32\"]\nintercept_domains = [\"bueno.example\"]\n");
        std::fs::write(d.join("config.toml"), "config_version = 5\nallowed_clients = [\"127.0.0.1/32\"]\nintercept_domains = [\"otro.example\"]\n").unwrap();
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Rechazada("firma_invalida"));
        // sin archivo de firma
        std::fs::remove_file(d.join("config.toml.sig")).unwrap();
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Rechazada("sin_firma"));
        assert!(pol.current().domain_allowed("cdn.example"));
    }

    // req: REQ-F-17
    #[test]
    fn una_version_menor_que_la_aplicada_se_rechaza() {
        let d = tempdir("version");
        let k = par();
        let (f, pol, clientes, seg) = montaje(&d, &k);
        escribir(&d, &k, "config_version = 7\nallowed_clients = [\"127.0.0.1/32\"]\nintercept_domains = [\"v7.example\"]\n");
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Aplicada(7));
        escribir(&d, &k, "config_version = 6\nallowed_clients = [\"127.0.0.1/32\"]\nintercept_domains = [\"v6.example\"]\n");
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Rechazada("version_anterior"));
        assert!(pol.current().domain_allowed("v7.example") && !pol.current().domain_allowed("v6.example"));
    }

    // req: REQ-F-17
    #[test]
    fn una_configuracion_que_abre_el_proxy_a_todos_se_rechaza_entera() {
        let d = tempdir("abierto");
        let k = par();
        let (f, pol, clientes, seg) = montaje(&d, &k);
        escribir(&d, &k, "config_version = 3\nallowed_clients = [\"0.0.0.0/0\"]\nintercept_domains = [\"abierto.example\"]\n");
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::Rechazada("clientes_invalidos"));
        assert!(!pol.current().domain_allowed("abierto.example"), "la política no se aplica a medias");
    }

    #[test]
    fn sin_archivo_firmado_se_sigue_con_la_configuracion_de_arranque() {
        let d = tempdir("vacio");
        let k = par();
        let (f, pol, clientes, seg) = montaje(&d, &k);
        assert_eq!(f.recargar(&pol, &clientes, &seg), Resultado::SinCambios);
        assert!(pol.current().domain_allowed("cdn.example"));
    }

    #[test]
    fn una_llave_que_no_es_de_32_bytes_impide_arrancar() {
        let d = tempdir("llave");
        std::fs::write(d.join("llave.pub"), "abcd").unwrap();
        let cfg = Config { signed_config: Some(d.join("c.toml")), config_public_key: Some(d.join("llave.pub")), ..Config::default() };
        assert!(Firmada::desde_config(&cfg, None).is_err());
        assert!(Firmada::desde_config(&Config::default(), None).unwrap().is_none());
    }

    fn tempdir(n: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("celeris-firmada-{n}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }
}
