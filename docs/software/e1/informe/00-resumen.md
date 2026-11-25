# Resumen ejecutivo

**Problema.** El Campus Juliaca cuenta con 10 laboratorios de cómputo de 40 estaciones cada uno [S-26] y un enlace
a Internet de 300 Mbps [S-02]. Cada estación descarga de forma independiente el mismo contenido: actualizaciones,
instaladores de los cursos y paquetes de software. Cuando todas las estaciones de un laboratorio descargan
simultáneamente, el enlace se satura y el inicio de las clases se retrasa. Una caché convencional no resuelve el
problema, dado que la mayor parte del tráfico viaja cifrado mediante HTTPS. Asimismo, en el nivel del laboratorio no
existe un rol facultado para decidir qué contenido se reutiliza ni un mecanismo para medir el volumen desperdiciado.

**Usuarios.**

- **Encargado de laboratorio (usuario principal):** decide qué contenido se reutiliza, habilita sus laboratorios y
  programa las precargas.
- **Administrador de la DTI:** aprueba el contenido que se descifra y opera la red.
- **Docente:** solicita la preparación de un laboratorio.
- **Auditor:** revisa los reportes y los registros de auditoría.
- **Usuarios de laboratorio y de la red Wi-Fi de estudiantes (BYOD):** utilizan el servicio sin cuenta.

**Alcance.**

- **Incluye:** el nodo de caché (EDGE01 10.20.60.10, EDGE02 10.20.60.11), la consola del encargado (CTRL01
  10.20.20.10), el portal de transparencia (PORTAL01 10.20.40.10) y el perfil BYOD sin descifrado.
- **Excluye:** el descifrado de equipos personales, el rediseño del FortiGate de la DTI, el modo examen y una caché
  en AWS.

**Solución propuesta.** Celeris Edge es un proxy de caché desplegado en cada campus que:

- Descarga cada objeto una sola vez y lo distribuye por la LAN (coalescencia y almacenamiento direccionado por
  SHA-256, D-03).
- Descifra TLS únicamente para las fuentes aprobadas por la DTI, con una CA intermedia por nodo (D-02, D-04, D-20).
- Traslada las descargas de gran tamaño a la madrugada mediante precargas programadas (D-21).
- Mantiene la consola íntegramente en el campus (D-25). Los nodos obtienen su configuración, firmada con ed25519,
  por el flujo F10 (TCP 8443, mTLS) y continúan operando si la consola deja de estar disponible (D-11).
- Restringe el acceso remoto a EC2-GW, sin almacenar datos en AWS. Desde el exterior no es posible aprobar
  descifrados (D-24, REQ-F-37).

| Sección | Contenido | Cantidad |
| --- | --- | --- |
| 0. Identificadores | Prefijos de los códigos, supuestos y decisiones de arquitectura | {{dato:n_sup}} supuestos, {{dato:n_dec}} decisiones |
| 1. Requerimientos | RF, RNF (ISO/IEC 25010), reglas, restricciones, casos de uso, historias, criterios de aceptación | {{dato:n_req}} requisitos ({{dato:n_rf}} RF, {{dato:n_rnf}} RNF, {{dato:n_rn}} RN), {{dato:n_cu}} CU |
| 2. Prototipo navegable | Alta fidelidad (pen.dev), flujo de navegación, prototipo clicable | {{dato:n_pantallas}} pantallas |
| 3. Diseño arquitectónico | C4: contexto, contenedores (despliegue) y componentes; ADR en formato MADR | 3 vistas, {{dato:n_adr}} ADR |
| 4. Diseño detallado | Dominio; casos de uso y clases por caso de uso; secuencias, estados, modelo de datos y API | {{dato:n_uml}} diagramas UML |
| Anexos | Acta de validación, matriz de trazabilidad, diagramas complementarios, sustentación | {{dato:n_req}} filas en la matriz |

**Estado declarado.**

- **Código:** el nodo se encuentra implementado («R1»). De los {{dato:n_rf_rn}} RF y RN, {{dato:n_hecho}} están
  completos, {{dato:n_parcial}} son parciales y {{dato:n_pendiente}} se difieren a S2.
- **Consola:** se encuentra en fase de diseño («R2») y se construirá en S2.
- **Validación:** la validación con los encargados aún no se ha realizado. El Anexo A presenta el protocolo y el acta
  en blanco, sin resultados ficticios.
- **Pruebas:** las ejecutadas en el laboratorio emulado se identifican expresamente como emuladas.
