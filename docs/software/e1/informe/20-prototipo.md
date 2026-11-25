# Sección 2: Prototipo Navegable

## 2.1 Prototipo de alta fidelidad

El prototipo es de **alta fidelidad**: sus 11 pantallas tienen datos y textos finales. Se diseñó en la
herramienta pen.dev y se exportó como una página web navegable: se recorre haciendo clic en el menú y en los
botones, como si fuera la consola real. Corresponde a la versión v0.4 de la arquitectura.

**Reglas que sigue:**

- **Datos de ejemplo.** Todos los números son de ejemplo y el pie de cada pantalla lo dice. Las cifras de negocio salen
  de los supuestos S-03, S-04, S-05, S-26 y S-27, no de una medición.
- **Trazabilidad en el pie.** Cada pantalla muestra su ID y los requisitos que cubre.
- **Etiqueta R2.** Las pantallas de la consola llevan «R2 — diseño», porque la consola se construye en S2.
- **Datos reales de la red.** Los nombres, las IP y los rangos son los del diseño de red (CE03):
  - CTRL01 10.20.20.10, EDGE01 10.20.60.10, EDGE02 10.20.60.11 y ENC01 10.20.35.10;
  - LAB-01 10.20.32.0/26 … LAB-10 10.20.34.64/26;
  - PAC en `http://pac.celeris.internal/wpad.dat`.
- **Origen de la sesión.** La barra superior siempre dice desde dónde llega la sesión (REQ-F-37):
  - verde: «Sesión desde el campus» (ENC01 o JMP01);
  - ámbar: «Acceso remoto · EC2-GW».

**Cómo se abre.** El prototipo es la página `navegable.html`, que se abre en cualquier navegador. Se mostrará en
vivo durante la sustentación.

## 2.2 Flujo de navegación

{{figura_prototipo:00-flujo-navegacion|Flujo de navegación y tabla pantalla → actor → requisitos → casos de uso|El portal (P-09, P-10) es público y no pide inicio de sesión. Dentro de la consola, la barra lateral lleva de P-02 a cualquier pantalla; los atajos siguen el trabajo del encargado: una fuente a descifrar lleva a P-07 y una solicitud de docente se convierte en precarga en P-05.}}

**Recorrido principal:**

1. P-01 «Entrar».
2. P-02 Resumen.
3. Menú lateral a P-03…P-08 y P-11.

**Atajos:**

- Desde P-03, la fila pendiente lleva a P-07.
- Desde P-06, «Crear precarga» lleva a P-05.
- Desde P-08, el intento rechazado lleva a P-07.

## 2.3 Pantallas principales

| # | Pantalla | Rol | Requisitos | CU |
| --- | --- | --- | --- | --- |
| P-01 | Inicio de sesión con segundo factor | Todos | REQ-F-33, F-37, NF-14 | CU-11 |
| P-02 | Resumen: ahorro por laboratorio, nodos, precargas | Encargado, admin, auditor | REQ-F-25, F-13, NF-13 | CU-06 |
| P-03 | Catálogo de contenido y simulador | Encargado | REQ-F-31, F-20, RN-03, RN-04, RN-07, RN-09, F-36 | CU-03 |
| P-04 | Laboratorios: acceso, rango y horario | Encargado | REQ-F-32, F-10, F-24, RN-06, NF-16 | CU-04 |
| P-05 | Precargas | Encargado | REQ-F-34, F-22, RN-10, F-05 | CU-05 |
| P-06 | Solicitudes de docentes | Encargado; el docente registra | REQ-F-35, F-34, F-31 | CU-09, CU-05 |
| P-07 | Aprobaciones pendientes y certificados | Admin DTI | REQ-RN-07, F-37, F-18, RN-04, NF-05 | CU-07, CU-11 |
| P-08 | Auditoría de cambios | Auditor, admin | REQ-F-24, F-37, RN-08, NF-16 | CU-10 |
| P-09 | Portal público: aviso de transparencia | Usuario, usuario BYOD, auditor | REQ-F-12, F-30, F-36, RN-05 | CU-02 |
| P-10 | Portal público: instalación de la CA y huella | Usuario, técnico DTI | REQ-RN-05, F-12, F-36 | CU-02 |
| P-11 | Actividad en vivo por laboratorio y nodo | Encargado, admin DTI | REQ-F-13, NF-13, NF-07 | CU-06 |

**Cobertura.** Hay pantalla para todos los casos de uso menos dos:

- **CU-01:** el navegador descarga por el PAC y no hay interfaz.
- **CU-08 (purgar):** será una acción «Purgar» en cada fila de P-03 (H-01); se agregará en la próxima versión del
  prototipo.

**P-11 es una pantalla adicional** a las planificadas en el documento de ingeniería de software del proyecto. Usa solo los agregados por laboratorio que el
nodo ya envía por F10 y no muestra URL, IP de equipos ni usuarios (REQ-NF-07). Si se considera innecesaria, se
puede quitar sin afectar a las demás.

{{rejilla:P-01-inicio-sesion|P-02-resumen|P-03-catalogo|P-04-laboratorios|P-05-precargas|P-06-solicitudes|P-07-aprobaciones|P-08-auditoria|P-09-portal-aviso|P-10-portal-instalacion-ca|P-11-actividad-en-vivo}}

**Qué observar:**

- **P-03:** el modo `nunca` de bancos e identidad aparece fijo y con candado (REQ-RN-09).
- **P-07:** la sesión llega por EC2-GW, así que «Aprobar» está deshabilitado y el navegable responde 403 (T54).
- **P-09:** el recuadro BYOD dice que el equipo personal nunca se descifra (REQ-F-36).
- **P-04:** LAB-04 está deshabilitado y el nodo responde 403 a 10.20.32.192/26 (T52).

## 2.4 Evidencia de validación con usuarios o stakeholders

> **Pendiente.** El prototipo todavía no se ha probado con encargados reales; no hay resultados, firmas ni
> cuestionario SUS. El Anexo A trae el protocolo de validación (participantes, seis tareas, medición) y el acta en
> blanco.

Lo que sí se hizo es una revisión interna del prototipo contra la arquitectura v0.4 y el diseño de red (24/11/2026). Corrigió seis
incoherencias:

- faltaba «cambiar el perfil BYOD» entre las acciones críticas;
- el aviso de P-09 listaba dominios pendientes como descifrados;
- había una fila de P-05 fuera del catálogo;
- LAB-04 aparecía con actividad estando deshabilitado;
- el indicador de P-02 no era de alertas;
- la auditoría no estaba en orden cronológico.

Esta revisión es una inspección del equipo, no una validación con usuarios, y no se presenta como tal.
