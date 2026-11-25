# Resumen ejecutivo

**Problema.** En los laboratorios de cómputo del Campus Juliaca hay 10 laboratorios de 40 PCs [S-26] y un enlace de
300 Mbps [S-02]. Cada PC descarga por separado lo mismo: actualizaciones, instaladores de los cursos y paquetes.
Cuando un laboratorio entero descarga a la vez, el enlace se satura y las clases se retrasan. Una caché clásica no
sirve, porque casi todo viaja por HTTPS. Además, nadie en el laboratorio puede decidir qué se reutiliza ni medir cuánto
se desperdicia.

**Usuarios.**

- **Encargado de laboratorio (usuario principal):** decide qué contenido se reutiliza, habilita sus laboratorios y
  programa precargas.
- **Administrador de la DTI:** aprueba lo que se descifra y opera la red.
- **Docente:** pide que se prepare un laboratorio.
- **Auditor:** revisa reportes y auditoría.
- **Usuarios de laboratorio y del Wi-Fi de estudiantes (BYOD):** usan el servicio sin cuenta.

**Alcance.**

- **Incluye:** el nodo de caché (EDGE01 10.20.60.10, EDGE02 10.20.60.11), la consola del encargado (CTRL01
  10.20.20.10), el portal de transparencia (PORTAL01 10.20.40.10) y el perfil BYOD sin descifrado.
- **Excluye:** descifrar equipos personales, rediseñar el FortiGate de la DTI, el modo examen y una caché en AWS.

**Solución propuesta.** Celeris Edge es un proxy de caché por campus:

- Descarga una sola vez y reparte por la LAN (coalescencia y almacenamiento por SHA-256, D-03).
- Descifra TLS solo para las fuentes que aprueba la DTI, con una CA intermedia por nodo (D-02, D-04, D-20).
- Mueve las descargas grandes a la madrugada con precargas (D-21).
- La consola vive completa en el campus (D-25). Los nodos le piden su configuración firmada con ed25519 por F10
  (TCP 8443, mTLS) y siguen funcionando si la consola cae (D-11).
- El acceso remoto entra solo por EC2-GW y sin datos en AWS. Desde fuera no se aprueban descifrados (D-24,
  REQ-F-37).

| Sección | Contenido | Cantidad |
| --- | --- | --- |
| 0. Identificadores | Prefijos de los códigos, supuestos y decisiones de arquitectura | {{dato:n_sup}} supuestos, {{dato:n_dec}} decisiones |
| 1. Requerimientos | RF, RNF (ISO/IEC 25010), reglas, restricciones, casos de uso, historias, criterios de aceptación | {{dato:n_req}} requisitos ({{dato:n_rf}} RF, {{dato:n_rnf}} RNF, {{dato:n_rn}} RN), {{dato:n_cu}} CU |
| 2. Prototipo navegable | Alta fidelidad (pen.dev), flujo de navegación, prototipo clicable | {{dato:n_pantallas}} pantallas |
| 3. Diseño arquitectónico | C4: contexto, contenedores (despliegue) y componentes; ADR en MADR | 3 vistas, {{dato:n_adr}} ADR |
| 4. Diseño detallado | Dominio; casos de uso y clases por cada caso de uso; secuencias, estados, modelo de datos y API | {{dato:n_uml}} diagramas UML |
| Anexos | Acta de validación, matriz de trazabilidad, diagramas complementarios, sustentación | {{dato:n_req}} filas en la matriz |

**Estado declarado.**

- **Código:** el nodo existe («R1»). De los {{dato:n_rf_rn}} RF y RN, {{dato:n_hecho}} están hechos,
  {{dato:n_parcial}} parciales y {{dato:n_pendiente}} quedan para S2.
- **Consola:** es diseño («R2») y se construye en S2.
- **Validación:** la validación con encargados aún no se hizo. El Anexo A trae el protocolo y el acta en blanco, sin
  resultados inventados.
- **Pruebas:** las del laboratorio emulado se rotulan como emuladas.
