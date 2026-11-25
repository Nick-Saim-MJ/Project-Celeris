## 1.9 Reglas de negocio y restricciones

### 1.9.1 Reglas de negocio

Una regla de negocio es una condición que el sistema hace cumplir sin excepción, con independencia de quién realice
la solicitud. La columna «Quién la aplica» indica el elemento en que se comprueba. Cuando intervienen dos elementos,
el nodo actúa como última barrera y rechaza lo que la consola no debió admitir.

| ID | Regla | Quién la aplica | Estado | Verifica |
| --- | --- | --- | --- | --- |
| REQ-RN-01 | Nunca se guarda una respuesta con `Set-Cookie`, `Cache-Control: private` o `no-store` | Nodo | Hecho (`policy.rs`) | Pruebas del nodo |
| REQ-RN-02 | Nunca se sirve desde caché una petición con `Authorization` o `Cookie` | Nodo | Hecho (`request_is_cacheable`) | Pruebas del nodo |
| REQ-RN-03 | El modo `nunca` gana siempre sobre cualquier otra fuente | Consola y nodo | Hecho en el nodo (`never_intercept` se evalúa primero) | `intercepcion.feature` |
| REQ-RN-04 | Un dominio en modo `descifrar_y_cachear` exige una CA que lo cubra; si no la hay, la fuente no se activa | Consola (simulador) y nodo | Hecho en el nodo: rechaza la configuración (`ca_no_cubre`) | `catalogo.feature` |
| REQ-RN-05 | El aviso debe estar publicado y entregado **antes** de instalar la CA y de configurar el proxy en una PC | Proceso de la DTI (GPO) y portal | Pendiente: lo comprueba la validación de OB-4 | T15, T16 |
| REQ-RN-06 | Un encargado solo gestiona los laboratorios que tiene asignados | Consola (RBAC) | Pendiente | `auth.feature` |
| REQ-RN-07 | El encargado puede activar sin aprobación fuentes en modo `cachear`; una fuente en modo `descifrar_y_cachear` queda pendiente hasta que la aprueba un administrador DTI | Consola | Pendiente | `catalogo.feature` |
| REQ-RN-08 | Una configuración sin firma válida se rechaza en el nodo | Nodo | Hecho (`signed.rs`: `sin_firma`, `firma_invalida`) | T51 |
| REQ-RN-09 | Bancos, inicios de sesión y servicios de identidad están en `nunca` por defecto y no se pueden mover a otro modo desde la consola | Consola (`fuente.fija`) | Pendiente | `catalogo.feature` |
| REQ-RN-10 | Una precarga no puede superar el límite de ancho de banda ni salir de la ventana horaria configurada por la DTI | Nodo (precarga) y consola (validación) | Pendiente | T50 |
| REQ-RN-11 | Ninguna configuración puede habilitar el descifrado para redes de origen BYOD; la consola no ofrece esa opción y el nodo la rechaza aunque llegue firmada | Consola y nodo | Parcial: el nodo nunca descifra las redes de `byod_networks`, pero aún no rechaza una configuración que vacíe esa lista | T56 |

**Parámetros de la DTI empleados por las reglas.** La ventana de precarga comprende de 00:00 a 05:00 y el límite es
de 50 Mbps, sobre un enlace de 300 Mbps [S-02]. Ambos valores son definidos por la DTI, se incorporan a la
configuración firmada y no pueden ser modificados por el encargado (DS-18).

### 1.9.2 Restricciones

| ID | Restricción | Origen | Efecto en el diseño |
| --- | --- | --- | --- |
| RS-01 | Rust estable; nodo sobre Hudsucker + rustls + Hyper + Tokio | D-01, D-02 | La consola también va en Rust (axum) para compartir tipos y la verificación ed25519 |
| RS-02 | ESXi gratuito: máximo 8 vCPU por VM | Licencia | Nodos de 4 vCPU (REQ-NF-02) |
| RS-03 | Ningún secreto en el repositorio | Rúbricas | Las llaves de firma, de la CA y TOTP quedan fuera de Git; el repositorio solo trae llaves de laboratorio |
| RS-04 | Equipo de dos integrantes | Proyecto | R2 se limita a la consola mínima; R3 queda fuera del alcance |
| RS-05 | Ley 29733 y su reglamento | Normativa | Aviso previo (REQ-RN-05), minimización (REQ-NF-07) y reportes por laboratorio (D-22) |
| RS-06 | La consola completa (SPA, API y PostgreSQL) corre en CTRL01, en el campus. En AWS solo hay un proxy inverso sin datos (EC2-GW) y respaldos en S3 | D-24, D-25 | REQ-F-37 distingue el origen de la sesión; los datos de uso no salen del campus, salvo el respaldo cifrado (F18) |
