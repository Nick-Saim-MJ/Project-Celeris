# Sección 4: Diseño Detallado

Esta sección baja la arquitectura de la Sección 3 al nivel de clases, mensajes y estados. Cada diagrama nombra en su
pie los requisitos y las pantallas que cubre; así cualquier elemento se puede seguir hasta la Sección 1 (qué se pide)
y la Sección 2 (cómo se ve).

**Cómo leer los diagramas.** Están hechos en PlantUML. Antes de generarlos, un validador automático comprueba que
existan de verdad todas las direcciones IP, equipos, flujos de red, requisitos, decisiones, casos de uso y pantallas
que mencionan. El estereotipo indica la entrega:

- **«R1»** (fondo blanco): ya existe en el código del nodo, con los nombres reales de sus clases y métodos.
- **«R2»** (fondo azul claro): diseño que se construye en el segundo semestre (S2).

| Subsección | En el cuerpo del informe | En el Anexo C |
| --- | --- | --- |
| 4.1 Diagramas UML | DS-01 modelo de dominio; por cada caso de uso, su diagrama de casos de uso (DS-23…DS-33) y su diagrama de clases (DS-34…DS-44) | DS-02 clases del nodo; DS-03 clases de la consola |
| 4.2 Diagramas de secuencia | DS-15 fuente que requiere descifrado; DS-16 precarga para una clase | DS-04 descarga compartida; DS-05 decisión de descifrado; DS-06 revalidación; DS-19 configuración y KPI |
| 4.3 Diagramas de estados | DS-17 fuente; DS-18 precarga | DS-09 entrada de caché |
| 4.4 Modelo de diseño detallado | DS-12 modelo de datos; API de la consola | DS-13 componentes del nodo y su código |

## 4.1 Diagramas UML

{{figura:DS-01|Las clases del dominio y cómo se relacionan: una fuente agrupa dominios; una precarga pertenece a un laboratorio y puede nacer de una solicitud; cada nodo aplica una versión de configuración firmada. Los indicadores se guardan por laboratorio, nunca por persona (REQ-NF-07), y cada sesión deja sus cambios en la auditoría (REQ-F-24).}}

**Reglas que el modelo hace visibles:**

- **El encargado ve solo sus laboratorios.** Un `Usuario` con rol `encargado` está asignado a uno o más
  `Laboratorio` (REQ-RN-06).
- **El docente solo crea solicitudes.** El rol `docente` registra `Solicitud` y no puede hacer nada más.
- **El nodo aplica solo lo firmado.** Un `Nodo` acepta una `VersionConfig` únicamente si su firma es válida
  (REQ-RN-08).
- **El contenido no se duplica.** Varias `CacheEntry` comparten un mismo `ContentObject`, identificado por su
  SHA-256 (D-03).

### 4.1.1 Casos de uso y clases por caso de uso

Para cada uno de los once casos de uso hay dos diagramas lado a lado. A la izquierda, el **diagrama de casos de
uso**: quién participa, qué pasos incluye siempre («include») y qué variantes pueden ocurrir («extend»). A la
derecha, el **diagrama de clases** de ese caso, ordenado en tres capas: *interfaz* (la pantalla del prototipo),
*control* (el servicio que aplica las reglas) y *entidad* (los datos que se crean o cambian). Las clases son las
mismas del modelo de dominio (DS-01) y de las clases de diseño (DS-02 y DS-03, Anexo C); ningún diagrama agrega
clases nuevas.

{{par_uml:DS-23|DS-34|el usuario de laboratorio y el BYOD usan el mismo caso, pero el BYOD nunca se descifra (REQ-F-36). En las clases, `CacheHandler` sigue cuatro pasos: verifica el laboratorio, decide si descifra, deja que un solo cliente descargue y sirve o guarda la copia.}}

{{par_uml:DS-24|DS-35|el portal no pide inicio de sesión. `Publisher` genera el sitio desde la configuración real, de modo que el aviso no puede quedar desactualizado respecto de lo que el nodo descifra (REQ-F-30).}}

{{par_uml:DS-25|DS-36|CU-07 extiende a CU-03 solo cuando la fuente pide descifrado. `ReglasCatalogo` concentra las tres reglas que pueden frenar el cambio: «nunca» siempre gana, la CA debe cubrir el dominio y una fuente fija no se toca.}}

{{par_uml:DS-26|DS-37|el cambio llega a los nodos por F10 en ≤ 60 s (REQ-NF-16). Quien lo aplica en el nodo es `ClientGate`, que ya existe («R1»): responde 403 a una PC de un laboratorio deshabilitado o fuera de horario.}}

{{par_uml:DS-27|DS-38|una precarga puede nacer de una solicitud del docente («extend»). La ventana y el límite de la DTI se validan antes de publicar (REQ-RN-10); la descarga la hace el nodo, no la consola.}}

{{par_uml:DS-28|DS-39|los indicadores salen del nodo cada 30 s, ya agrupados por laboratorio. Ninguna clase guarda URL ni IP de equipos (REQ-NF-07).}}

{{par_uml:DS-29|DS-40|aprobar exige origen campus: `OrigenMiddleware` marca la sesión y `Rbac.exigir_campus` responde 403 a una sesión remota (REQ-F-37, T54). Cada decisión queda en la auditoría.}}

{{par_uml:DS-30|DS-41|la orden de purga no viaja sola: va dentro de la siguiente versión firmada de la configuración, y el nodo la aplica sobre su `Store` (REQ-F-19).}}

{{par_uml:DS-31|DS-42|el docente solo registra y sigue sus solicitudes; convertirlas en precarga le corresponde al encargado (CU-05).}}

{{par_uml:DS-32|DS-43|la auditoría se lee por la API, pero `AuditLog` solo inserta: ninguna clase ofrece editar ni borrar una entrada (REQ-F-24).}}

{{par_uml:DS-33|DS-44|desde fuera del campus se puede trabajar, pero las acciones críticas se rechazan. La sesión sabe de dónde viene porque EC2-GW presenta su propio certificado de cliente.}}

## 4.2 Diagramas de secuencia

{{figura:DS-15|El encargado crea en P-03 una fuente que requiere descifrado; queda «Pendiente DTI» (REQ-RN-07) y el simulador avisa que la CA no cubre el dominio (REQ-RN-04). El administrador intenta aprobarla desde fuera del campus y recibe 403 (REQ-F-37, T54). Desde el campus, la aprobación activa la fuente solo si la CA de cada nodo la cubre, y `publisher` firma la versión siguiente.}}

{{figura:DS-16|El docente registra la solicitud SOL-12 y el encargado la convierte en precarga. En la ventana nocturna, el nodo descarga 1,1 GB una sola vez; al iniciar la clase, las 40 PCs reciben la copia local en lugar de traer 44 GB por el enlace. La rama alternativa muestra por qué una fuente no aprobada no ahorra: su tráfico no se descifra.}}

## 4.3 Diagramas de estados

{{figura:DS-17|Los estados de una fuente, con los mismos nombres que muestra P-03. Una fuente en modo `cachear` se activa sin aprobación; una en `descifrar_y_cachear` espera a la DTI. Un intento de aprobación desde fuera del campus no cambia el estado y queda en la auditoría. Las fuentes fijas de la DTI no se pueden mover (REQ-RN-09).}}

{{figura:DS-18|Una precarga solo corre entre las 00:00 y las 05:00 y con un máximo de 50 Mbps por nodo (REQ-RN-10). Si la ventana termina, se pausa y sigue la noche siguiente. «Fallida» vuelve a «Programada» cuando el encargado corrige la URL.}}

## 4.4 Modelo de diseño detallado

{{figura:DS-12@0.85|Modelo de datos de la consola. La base PostgreSQL corre en CTRL01 10.20.20.10 y solo se accede localmente, sin puerto de red (D-12). La tabla `cambio` solo admite inserciones (REQ-F-24) y `kpi_intervalo` guarda agregados de 30 s por laboratorio y nodo, sin URL ni IP de equipos (REQ-NF-07).}}

**Del código al diseño.** DS-13 (Anexo C) relaciona cada componente del nodo con el archivo de código que lo
implementa hoy y con el módulo al que pasará. Faltan tres piezas, que se construyen en S2: el agente que descarga la
configuración por F10, la precarga y las descargas parciales (REQ-F-08).

**API de la consola.** La consola publica sus rutas `/v1/…` en el puerto TCP 443 de CTRL01. El equipo del encargado
(ENC01) llega por F28 y el acceso remoto por EC2-GW llega por F30. Los nodos usan otro puerto, TCP 8443, con
autenticación mutua (mTLS) por F10. Las acciones críticas responden 403 a una sesión remota.

{{incluir:srs/07-datos-interfaces.md|### 1.11.3 API de la consola (cierra H-11)|tabla}}
