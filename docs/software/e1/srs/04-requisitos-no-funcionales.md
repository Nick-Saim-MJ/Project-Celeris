## 1.8 Requisitos no funcionales (ISO/IEC 25010:2023)

Los requisitos se agrupan por característica del modelo de calidad de producto. Cada uno tiene una métrica, un
umbral y un método de verificación. Una meta sin medir se informa como pendiente, nunca como cumplida.

| Característica (subcaracterística) | ID | Requisito medible | Estado | Verificación |
| --- | --- | --- | --- | --- |
| Eficiencia de desempeño (comportamiento temporal) | REQ-NF-01 | Latencia añadida p95 ≤ 5 ms en HIT desde memoria y ≤ 20 ms desde disco, en LAN | Sin medir | k6 / oha |
| Eficiencia de desempeño (capacidad) | REQ-NF-02 | Un nodo de 4 vCPU y 8 GB atiende un laboratorio de 40 PCs descargando a la vez a ≥ 900 Mbps agregados desde caché | Sin medir | iperf3 + prueba de carga |
| Compatibilidad (interoperabilidad) | REQ-NF-11 | HTTP/1.1 y HTTP/2 con los clientes; cabecera `Cache-Status` (RFC 9211); eventos OCSF 1.x | Parcial: `Cache-Status` hecho (`handler.rs`, sin `key` ni `detail`); HTTP/2 sin verificar; eventos en JSONL propio, no OCSF (REQ-F-14) | Prueba de cabeceras; validación del esquema OCSF |
| Capacidad de interacción (facilidad de aprendizaje y de operación) | REQ-NF-12 | La consola obtiene un SUS ≥ 75 con encargados reales, y las tareas de CU-03 a CU-06 se completan sin ayuda en ≤ 5 min | Pendiente (validación de la Sección 2) | Prueba de usabilidad con acta |
| Fiabilidad (disponibilidad) | REQ-NF-03 | La navegación del laboratorio sigue disponible ≥ 99,5 % gracias al segundo nodo y al `DIRECT` del PAC | Sin medir | Tiempo de cambio medido en T09 |
| Fiabilidad (tolerancia a fallos) | REQ-NF-04 | Tras un corte de energía, no se sirve ningún objeto corrupto | Hecho por diseño (REQ-F-06); sin prueba de corte | kill -9 + verificación de hash |
| Fiabilidad (madurez) | REQ-NF-16 | Un cambio en la consola llega a los nodos en ≤ 60 s | Pendiente (el nodo consulta cada 30 s, DS-19) | Prueba de integración, T51 |
| Seguridad (confidencialidad) | REQ-NF-05 | La llave de la CA nunca sale de su nodo; la raíz vive offline | Diseño (D-04) | Revisión de diseño |
| Seguridad (confidencialidad, integridad) | REQ-NF-06 | TLS ≥ 1.2 hacia clientes y orígenes | Hecho: rustls con versiones seguras por defecto (TLS 1.2 y 1.3) en `upstream.rs` y `admin.rs` | testssl.sh |
| Seguridad (confidencialidad): privacidad | REQ-NF-07 | No se guardan cookies, credenciales, cuerpos ni parámetros de URL; los reportes son por laboratorio, no por persona | Hecho en el registro del nodo (`access_log.rs`: sin parámetros, cookies, credenciales ni cuerpos; IP seudonimizada por defecto); la consola se diseña así (D-22) | Prueba sobre los registros; T26 |
| Seguridad (autenticidad) | REQ-NF-14 | La API de la consola (F28, F30) y el puerto de administración del nodo solo aceptan TLS; F30 exige además certificado de cliente | Hecho en el nodo: puerto 9128 con `admin_tls` (H-08 cerrado); consola pendiente | T27 |
| Seguridad (integridad) | REQ-NF-15 | Imagen OCI sin usuario root, firmada y con SBOM | Pendiente | `cosign verify` |
| *Safety* (falla segura) | REQ-NF-08 | Ante un error de política, el nodo no descifra (passthrough) | Hecho: `tls_decision` devuelve `false` por defecto | Inyección de fallos |
| Mantenibilidad (capacidad de prueba, analizabilidad) | REQ-NF-09 | Cobertura ≥ 70 % en política, caché y TLS; `clippy` sin advertencias | Pendiente de medir | CI (`cargo-llvm-cov`) |
| Mantenibilidad (analizabilidad) | REQ-NF-13 | Cada decisión (HIT, MISS, bypass, rechazo) produce una métrica etiquetada por laboratorio | Parcial (métricas globales) | Revisión de métricas; P-11 |
| Flexibilidad (adaptabilidad) | REQ-NF-10 | Linux x86_64 y aarch64; imagen OCI multiarquitectura | Pendiente | CI |

**Cómo se ven en el producto.**

- **REQ-NF-07 y D-22**: P-02 y P-11 solo muestran cifras por laboratorio y por nodo.
- **REQ-NF-08**: está dibujado en DS-05. Sin SNI, o con un SNI que no coincide con el `CONNECT`, el nodo no descifra.
- **REQ-NF-16**: está dibujado en DS-19. La consola publica la configuración y cada nodo la recoge en su siguiente
  consulta (cada 30 s), lo que deja margen dentro de los 60 s.
- **REQ-NF-12**: es la meta de la validación con usuarios. Mientras no haya acta, no se presenta como cumplido.
