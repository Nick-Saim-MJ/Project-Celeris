---
titulo: "Celeris Edge — Qué es el proyecto"
version: "0.4"
fecha: "2026-11-22"
equipo: ["Nick Saim Mayta Jara", "Henyelrey Lucio Garcia Chura"]
escuela: "EP Ingeniería de Sistemas — UPeU, Campus Juliaca"
para_quien: "Cualquier lector: jurado, DTI, docentes o un integrante nuevo. No hace falta saber de redes."
---

# Celeris Edge — Qué es el proyecto

## Glosario

| Término | En palabras simples |
| --- | --- |
| **Caché** | Una copia guardada cerca de quien la necesita. Si 40 PCs piden el mismo archivo, se descarga una vez y las otras 39 lo reciben de la copia. |
| **Enlace a Internet** | La conexión del campus con el proveedor. Es limitada y la comparten todos. |
| **Proxy** | Un intermediario: la PC le pide el archivo al proxy y el proxy lo trae (o lo entrega desde su caché). |
| **HTTPS** | La forma cifrada de navegar. Casi toda la web usa HTTPS, lo que impide cachear sin un permiso especial. |
| **Descifrado selectivo** | El proxy abre el HTTPS solo de los sitios que la universidad aprueba (por ejemplo, el sitio de descargas de Docker) y solo en PCs de la universidad que fueron preparadas para eso, con aviso previo. |
| **Encargado de laboratorio** | La persona que administra los laboratorios. Con Celeris decide qué se guarda en caché y qué laboratorio puede usarlo. |
| **BYOD** | Equipos personales de los estudiantes (laptop, celular) conectados al Wi-Fi. |
| **FortiGate / FortiGuard** | El firewall que ya tiene la universidad y su filtro web, que bloquea redes sociales y otras categorías. |
| **VPN** | Un túnel cifrado entre el campus y la nube. |
| **AWS** | El proveedor de nube que usa el proyecto para el acceso remoto seguro y los respaldos. |

---

## 1. En una frase

Celeris Edge es un servidor de caché para los laboratorios del Campus Juliaca: descarga **una sola vez** lo que muchas PCs necesitan (instaladores, actualizaciones, archivos de la web) y lo reparte por la red interna. El encargado decide qué se guarda y quién lo usa, y los estudiantes pueden ver qué se inspecciona.

## 2. El problema

Al inicio de un ciclo o antes de una clase, decenas de PCs descargan lo mismo al mismo tiempo: el instalador de Docker, una actualización de Windows, las bibliotecas de Python. Cada PC lo baja por separado, el enlace se satura, la clase espera y el resto del campus navega lento.

| Ejemplo: 20 PCs de LAB-01 bajan Docker Desktop (≈ 0,6 GB [supuesto, a medir]) | Sin Celeris | Con Celeris |
| --- | --- | --- |
| Tráfico por el enlace del campus | ≈ 12 GB | ≈ 0,6 GB |
| Lo demás | Compite con todo el campus | Viaja por la red interna a 1 Gbps |
| Si las 20 piden a la vez | 20 descargas paralelas | 1 descarga; las otras 19 esperan esa copia |
| Con precarga nocturna | — | 0 GB en horario de clase |

**Por qué no basta lo que ya existe:**
- **Ampliar el ancho de banda** es un costo que se paga todos los meses y no evita la repetición.
- **Las cachés clásicas** (Squid, LanCache) se configuran a mano para HTTPS o directamente no lo cachean.
- **El FortiGate** filtra bien qué sitios se abren, pero no guarda copias para no descargar lo mismo 40 veces.

## 3. Cómo funciona

1. **El encargado configura** en la consola web: qué fuentes se cachean (por ejemplo, "Docker", "repositorios de Ubuntu"), qué laboratorios están habilitados y qué descargar de noche.
2. **La consola firma esa configuración** y el servidor de caché la aplica. Si alguien altera la configuración en el camino, el servidor la rechaza.
3. **Las PCs del laboratorio** usan el servidor de caché de forma automática, porque la universidad configura las PCs institucionales.
4. **La primera PC** que pide un archivo hace que el servidor lo descargue una vez. Las demás lo reciben de la copia a velocidad de red interna.
5. **De noche**, el servidor puede precargar lo que el encargado programó, sin saturar el enlace en horario de clase.
6. **Si el servidor de caché falla**, las PCs siguen navegando directo a Internet: se pierde el ahorro, no la conexión.
7. **Cualquier estudiante** puede leer en el portal de transparencia qué se inspecciona y qué no, antes de usar una PC.

## 4. Quién lo usa

| Actor | Qué hace |
| --- | --- |
| Encargado de laboratorio | Configura fuentes, laboratorios y precargas; ve el ahorro por laboratorio |
| Administrador de la DTI | Aprueba qué fuentes se pueden descifrar; administra servidores y red |
| Estudiantes y docentes | Usan las PCs y el Wi-Fi como siempre; consultan el aviso de transparencia |
| Auditor | Revisa el historial de cambios y el cumplimiento de privacidad |

## 5. Alcance

**Incluye:**
- Los laboratorios de cómputo del Campus Juliaca y sus PCs institucionales (10 laboratorios × 40 PCs [supuesto]).
- Los dispositivos personales (BYOD) y el Wi-Fi de estudiantes, con un perfil limitado: el proxy es opcional y su tráfico **nunca** se descifra.
- Los servidores del proyecto en el campus y una pequeña parte en AWS.

**No incluye (por ahora):** la red administrativa, las PCs de los docentes, el rediseño del FortiGate y de la red Wi-Fi existentes, y el modo examen (sección 10).

## 6. Dónde vive cada parte

| En el campus | En la nube (AWS) |
| --- | --- |
| Servidor de caché | Puerta de entrada segura al panel para cuando el encargado está fuera del campus (no guarda datos) |
| Consola completa: pantallas, lógica y base de datos | Respaldos cifrados que no se pueden borrar durante 30 días |
| Firewall del proyecto, portal de transparencia, detección de ataques | — |

**Por qué casi todo está en el campus:** el servidor de caché necesita a la consola, y la consola debe seguir funcionando aunque se caiga Internet. Además, los datos de uso de los laboratorios no salen del país. La nube se usa para lo que el campus no puede hacer solo: recibir conexiones de Internet sin gastar el enlace del campus y guardar una copia fuera del sitio. El detalle está en `Celeris-Arquitectura-v0.4.md`, sección 1.

## 7. Seguridad y privacidad

| Compromiso | Cómo se cumple |
| --- | --- |
| Solo se abre el HTTPS de sitios aprobados | Lista aprobada por la DTI; bancos, inicios de sesión, correo y plataformas con sesión nunca se descifran |
| Los equipos personales no se inspeccionan | El tráfico del Wi-Fi de estudiantes pasa siempre cifrado |
| El usuario sabe antes | Portal de transparencia con el aviso y la huella del certificado, consultable antes de usar el proxy |
| Nada de cookies ni contraseñas en la caché | No se guardan respuestas con sesión ni peticiones con credenciales |
| La IP del estudiante no sale del campus | El servidor quita las cabeceras que la revelarían |
| Nadie puede cambiar la configuración por la red | Configuración firmada; el servidor rechaza lo que no tiene firma válida |
| El panel no es un punto débil | Segundo factor obligatorio, permisos por laboratorio, auditoría; las acciones críticas solo desde el campus |
| Los ataques se detectan | Firewall con detección de intrusiones, señuelos (honeypots) y un centro de alertas (Wazuh) |
| Los datos viajan protegidos en todo el trayecto | Cada tramo tiene cifrado o una justificación documentada (ver la sección 8 de la arquitectura) |

## 8. Cómo se evalúa (EPE)

El proyecto cubre las tres áreas de la Evaluación de Perfil de Egreso:

| Área | Qué demuestra Celeris | Entregables S1 |
| --- | --- | --- |
| CE01 Gestión de TI | Por qué conviene invertir: diagnóstico, business case (ahorro frente a ampliar el enlace), plan del proyecto, procesos antes y después | Diagnóstico, business case, plan de gestión, AS-IS/TO-BE |
| CE02 Ingeniería de Software | Cómo se construye la consola y el nodo: requisitos, prototipo, arquitectura, diseño | SRS, prototipo, C4/ADR, UML |
| CE03 Infraestructura | Cómo se instala con seguridad: red segmentada, firewall, DMZ, VPN a AWS, detección, centro de datos híbrido | Diseño de red, diseño de centro de datos |

## 9. Estado actual (22 nov 2026)

| Pieza | Estado |
| --- | --- |
| Servidor de caché (Rust) | Funciona: proxy, descifrado selectivo, caché, copia única para pedidos simultáneos, verificación de integridad, PAC, privacidad de cabeceras, administración con TLS |
| Laboratorio emulado | Levanta la red del diseño en una laptop. Último ensayo: 31 pruebas aprobadas, 0 fallidas, 1 parcial y 17 que solo aplican en AWS o en el campus |
| Infraestructura como código | Módulos OpenTofu para el laboratorio efímero en AWS (sin aplicar) |
| Diagramas, matrices, prototipo y UML | Hechos en ramas separadas, sobre la versión anterior del diseño (v0.2) |
| Consola del encargado | Diseñada y con prototipo; no implementada |
| Pendiente inmediato | Unir las ramas en `main` y actualizar la fuente única a la v0.4 |

## 10. Hacia dónde va

**Modo examen (plan futuro).** El problema mayor de la universidad no es solo el ancho de banda: durante un examen, un estudiante puede usar IA, buscar respuestas o intentar acceder a los sistemas de los docentes. El FortiGate bloquea categorías como redes sociales, pero no sabe que en un laboratorio hay un examen.

La idea es que el docente active, para su laboratorio y su horario, un perfil que permita solo el material educativo. Celeris ya deja la base lista:
- control por laboratorio;
- configuración firmada y auditada;
- roles;
- filtrado por dominio sin necesidad de descifrar.

Falta decidir si el cierre se hace en el servidor de caché, en el firewall del proyecto, en el FortiGate o en una combinación. Ninguna opción es la mejor en todos los casos.

**Límite declarado:** el modo examen controla la red, no el aula. Un celular con datos móviles no pasa por la red del campus.

**Otras mejoras posibles:**
- un segundo servidor de caché;
- caché de imágenes de contenedor (`docker pull`);
- solicitudes de contenido de los docentes;
- extender el servicio a otras sedes.

## 11. Riesgos principales

| Riesgo | Respuesta |
| --- | --- |
| El proyecto depende de dos personas | Todo está documentado como código, con pruebas automáticas y un diseño que la DTI puede operar o migrar a Squid |
| La web cifra cada vez más (ECH, QUIC) | Proxy explícito, bloqueo de QUIC en los laboratorios y medición mensual del ahorro |
| Rechazo por privacidad | Descifrado solo de sitios aprobados, solo en PCs institucionales, con aviso previo y portal público |
| La DTI no aprueba cambios en el FortiGate | Las piezas que dependen de esos cambios (VPN, portal público) se piden de forma mínima y tienen alternativas documentadas |

## 12. Documentos del proyecto

| Documento | Para qué |
| --- | --- |
| `Celeris-Que-es-el-proyecto.md` | Este resumen |
| `Celeris-Arquitectura-v0.4.md` | Arquitectura definitiva: componentes, red, flujos, seguridad del trayecto, pruebas |
| `Celeris-00-Marco-Comun.md` | Problema, alcance, supuestos y contrato de IDs (a actualizar a la v0.4) |
| `Celeris-CE01-Gestion-TI.md`, `Celeris-CE02-Ingenieria-Software.md`, `Celeris-CE03-Infraestructura.md` | Guía de cada área de evaluación |
| Repositorio `Project-Celeris` | Código, fuente única de red (`infra/*.yaml`), laboratorio y entregables |
