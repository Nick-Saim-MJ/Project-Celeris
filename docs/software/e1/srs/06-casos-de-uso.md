## 1.10 Casos de uso, historias y criterios de aceptación

### 1.10.1 Catálogo de casos de uso

El diagrama de casos de uso es DS-14 (Sección 4). Cada caso de uso nombra las pantallas del prototipo (Sección 2) y
la secuencia UML que lo detalla.

| ID | Caso de uso | Actor | Requisitos | Pantalla | UML |
| --- | --- | --- | --- | --- | --- |
| CU-01 | Descargar a través de la caché | Usuario de laboratorio; usuario BYOD (sin descifrado) | REQ-F-01, F-02, F-03, F-05, F-36 | — (transparente) | DS-04, DS-05, DS-06 |
| CU-02 | Consultar qué se descifra y la huella de la CA antes de usar el proxy | Usuario, auditor | REQ-F-12, F-30, RN-05 | P-09, P-10 | DS-15 |
| CU-03 | Agregar una fuente al catálogo de contenido | Encargado (+ admin si descifra) | REQ-F-31, F-20, F-24, RN-04, RN-07, RN-09 | P-03 | DS-15, DS-17 |
| CU-04 | Habilitar un laboratorio y su horario | Encargado | REQ-F-32, F-10, F-24, RN-06 | P-04 | DS-19 |
| CU-05 | Programar una precarga para una clase | Encargado | REQ-F-34, F-22, RN-10 | P-05 | DS-16, DS-18 |
| CU-06 | Ver el ahorro y la actividad del laboratorio | Encargado, auditor | REQ-F-25, F-13, NF-13 | P-02, P-11 | DS-16, DS-19 |
| CU-07 | Aprobar una fuente que requiere descifrado | Administrador DTI (solo desde el campus) | REQ-F-31, F-18, F-37, RN-07 | P-07 | DS-15, DS-17 |
| CU-08 | Purgar un contenido | Encargado | REQ-F-19, F-24 | P-03 (acción «Purgar», v0.3, H-01) | DS-17 |
| CU-09 | Registrar una solicitud de preparación | Docente (rol `docente`, H-03) | REQ-F-35, F-33 | P-06 | DS-16, DS-18 |
| CU-10 | Revisar la auditoría de cambios | Auditor, admin | REQ-F-24 | P-08 | DS-15 |
| CU-11 | Usar la consola desde fuera del campus | Encargado, admin | REQ-F-33, F-37 | P-01, P-02 | DS-15 |

### 1.10.2 Especificación de los casos de uso críticos

Se detallan los cuatro casos de uso que sostienen los objetivos OB-2, OB-3 y OB-5. Los demás siguen el mismo patrón
y su secuencia está en la Sección 4.

**CU-03 Agregar una fuente al catálogo.**

- **Precondición:** el encargado inició sesión con segundo factor (P-01).
- **Flujo principal:**
  1. Ingresa el nombre, los dominios, la categoría y el modo de la fuente (P-03).
  2. Usa el simulador (REQ-F-20). La consola responde si una URL de ejemplo se cachearía, si se descifraría y si la
     CA la cubre.
  3. Guarda la fuente.
     - Si el modo es `cachear`, la fuente queda activa.
     - Si el modo es `descifrar_y_cachear`, queda pendiente (REQ-RN-07).
  4. La consola registra el cambio (REQ-F-24), compila y firma una nueva versión (D-11), y los nodos la aplican en
     ≤ 60 s (REQ-NF-16).
- **Alternos:**
  - El dominio está en una fuente fija `nunca` (bancos o identidad): la consola rechaza el cambio (REQ-RN-09).
  - La CA no cubre el dominio: la fuente no se activa (REQ-RN-04).
- **Postcondición:** el aviso del portal refleja la nueva fuente cuando esta queda activa (REQ-F-12).

**CU-05 Programar una precarga.**

- **Precondición:** el laboratorio está asignado al encargado (REQ-RN-06).
- **Flujo principal:**
  1. El encargado elige URLs o una fuente, el laboratorio, la fecha y la ventana (P-05). También puede convertir una
     solicitud del docente (P-06).
  2. La consola valida la ventana y el límite de la DTI (REQ-RN-10) y publica la precarga en la configuración firmada.
  3. Dentro de la ventana, el nodo descarga una sola vez por F8 y verifica cada objeto con SHA-256 (REQ-F-06,
     REQ-F-22).
  4. El nodo informa el avance por F10.
  5. La precarga pasa a «Completada» y la solicitud a «Lista».
- **Alternos:**
  - La ventana termina antes de acabar: la precarga queda «Pausada» y sigue en la ventana siguiente.
  - El origen falla tras los reintentos: «Fallida», con una alerta en P-02 (DS-18).
- **Postcondición:** al iniciar la clase, las PCs reciben HIT (T50).

**CU-07 Aprobar una fuente que requiere descifrado.**

- **Precondición:**
  - El administrador DTI inició sesión desde JMP01 10.20.10.20 o desde ENC01 10.20.35.10 (origen `campus`).
  - Hay fuentes pendientes (P-07).
- **Flujo principal:**
  1. Revisa los dominios, la huella y el vencimiento de la CA del nodo.
  2. Aprueba o rechaza la fuente.
  3. La consola registra la decisión, publica una nueva versión de la configuración y un aviso actualizado
     (REQ-F-30).
- **Alterno:** si la sesión es `remoto` (por EC2-GW), la API responde 403. El intento queda en auditoría con su
  origen y P-07 muestra la acción deshabilitada (REQ-F-37, T54).
- **Postcondición:** el nodo descifra ese dominio solo para PCs institucionales, nunca para WIFI-EST (REQ-F-36).

**CU-11 Usar la consola desde fuera del campus.**

- **Precondición:** el usuario tiene contraseña y TOTP.
- **Flujo principal:**
  1. Entra por `https://` a EC2-GW 10.30.0.10 (F29). EC2-GW aplica TLS 1.3, HSTS y el WAF.
  2. EC2-GW reenvía la petición a CTRL01 10.20.20.10:443 por F30: mTLS con su certificado de cliente, dentro de
     IPsec.
  3. La API marca la sesión como `remoto`.
  4. P-01 y P-02 muestran «acceso remoto».
  5. El usuario hace las acciones no críticas (CU-03 a CU-06, CU-08 a CU-10).
- **Alternos:**
  - Falta el segundo factor, o hay 10 intentos fallidos: la sesión se rechaza (T53).
  - Se intenta una acción crítica: la API responde 403 (T54).

### 1.10.3 Historias de usuario

| Historia | CU | Prioridad |
| --- | --- | :-: |
| *Como encargado, quiero agregar «Instaladores de JetBrains» al catálogo, para que la próxima vez que 40 PCs lo descarguen solo una vaya a Internet.* | CU-03 | M |
| *Como encargado, quiero programar la descarga de un instalador la noche anterior a la clase, para que la clase empiece con todo listo.* | CU-05 | M |
| *Como encargado, quiero habilitar solo el laboratorio 3 en el horario de su curso, para controlar quién usa el servicio.* | CU-04 | M |
| *Como administrador DTI, quiero aprobar desde el campus las fuentes que se descifran, para que nadie con una contraseña robada lo haga desde fuera.* | CU-07, CU-11 | M |
| *Como docente, quiero pedir que el software de mi curso esté listo para el lunes, sin tener que escribirle a la DTI.* | CU-09 | S |
| *Como estudiante, quiero ver qué se descifra y la huella de la CA antes de usar una PC del laboratorio, para saber qué se inspecciona.* | CU-02 | M |
| *Como encargado, quiero ver cada 30 s cuántas peticiones del laboratorio salen de la caché, para saber si la precarga funcionó durante la clase.* | CU-06 | S |

### 1.10.4 Criterios de aceptación ejecutables (Gherkin)

Cada escenario lleva las etiquetas de sus requisitos. En S2 (CE024), la matriz de la sección 1.12 se genera desde
estas etiquetas. Los archivos van en `tests/features/`, que se crea en S2; hoy los escenarios solo existen en este
SRS.

```gherkin
# catalogo.feature    @REQ-F-31 @REQ-RN-07 @REQ-RN-09 @REQ-F-24
Característica: Catálogo de contenido del encargado

  Escenario: Una fuente sin descifrado se activa de inmediato
    Dado que el encargado de LAB-03 inició sesión con segundo factor
    Cuando agrega la fuente "Repos de Ubuntu" con el dominio "archive.ubuntu.com" en modo cachear
    Entonces la fuente queda activa
    Y los nodos EDGE01 y EDGE02 aplican la nueva versión en menos de 60 segundos
    Y el cambio queda en la auditoría con su autor, antes y después

  Escenario: Una fuente que requiere descifrado espera aprobación
    Cuando el encargado agrega "download.jetbrains.com" en modo descifrar_y_cachear
    Entonces la fuente queda "pendiente de aprobación"
    Y el nodo no descifra ese dominio hasta que un administrador DTI la apruebe

  Escenario: Un banco no se puede sacar de "nunca"
    Cuando el encargado intenta cambiar a cachear una fuente fija de banca
    Entonces la consola rechaza el cambio
    Y el intento queda en la auditoría como rechazado

# origen.feature    @REQ-F-37 @REQ-F-24
Característica: Acciones críticas solo desde el campus

  Escenario: Aprobar desde fuera del campus se rechaza
    Dado una sesión de administrador que llegó por EC2-GW con su certificado de cliente
    Cuando pide aprobar la fuente "download.jetbrains.com"
    Entonces la API responde 403
    Y la auditoría registra el intento con origen "remoto"

  Escenario: Aprobar desde JMP01 se acepta
    Dado una sesión de administrador con origen "campus" desde 10.20.10.20
    Cuando aprueba la fuente
    Entonces la fuente pasa a activa y se publica una nueva versión firmada

# laboratorios.feature    @REQ-F-32 @REQ-F-10 @REQ-RN-06
Característica: Acceso por laboratorio y horario

  Escenario: Laboratorio deshabilitado
    Dado que el encargado deshabilitó LAB-03 (10.20.32.128/26) y LAB-01 (10.20.32.0/26) sigue habilitado
    Cuando una PC de cada rango pide un recurso por el proxy 10.20.60.10:3128
    Entonces la PC de LAB-03 recibe 403 y la de LAB-01 recibe 200

  Escenario: Fuera del horario
    Dado que LAB-03 está habilitado de lunes a viernes de 07:00 a 22:00
    Cuando una PC de LAB-03 pide un recurso un lunes a las 22:30
    Entonces recibe 403 y el nodo registra el rechazo como "fuera de horario"

  Escenario: Un encargado no toca un laboratorio ajeno
    Dado que el encargado solo tiene asignado LAB-03
    Cuando intenta deshabilitar LAB-04
    Entonces la API responde 403

# precarga.feature    @REQ-F-34 @REQ-F-22 @REQ-RN-10
Característica: Precarga nocturna
  Escenario: Precarga en la ventana de la DTI
    Dado una precarga del instalador "ide.tar.gz" para LAB-03 entre 00:00 y 05:00
    Cuando llega la ventana
    Entonces el nodo descarga el archivo una sola vez sin superar 50 Mbps
    Y a la mañana siguiente la primera PC de LAB-03 recibe un HIT

# byod.feature    @REQ-F-36 @REQ-RN-11
Característica: El Wi-Fi de estudiantes nunca se descifra
  Escenario: Dominio aprobado, cliente BYOD
    Dado que "download.jetbrains.com" está en una fuente descifrar_y_cachear activa
    Cuando un equipo de WIFI-EST abre un CONNECT a ese dominio por el proxy
    Entonces el nodo crea un túnel sin descifrar
  Escenario: Configuración que intenta descifrar BYOD
    Cuando llega una configuración firmada que quita la red WIFI-EST de las redes BYOD
    Entonces el nodo la rechaza y sigue con la versión anterior

# purga.feature    @REQ-F-19 @REQ-F-24
Característica: Purga de contenido
  Escenario: Purgar una fuente
    Dado que la fuente "Repos de Ubuntu" tiene objetos en caché
    Cuando el encargado elige "Purgar" en su fila del catálogo
    Entonces tras la siguiente versión aplicada, la próxima petición a esa fuente es MISS
    Y la purga queda en la auditoría

# solicitudes.feature    @REQ-F-35 @REQ-F-33
Característica: Solicitudes de los docentes
  Escenario: El docente solo ve sus solicitudes
    Dado un docente con rol "docente"
    Cuando registra una solicitud para LAB-03 con fecha de clase
    Entonces la solicitud queda "Nueva" y el encargado de LAB-03 la ve en P-06
    Y el docente no puede abrir el catálogo, las precargas ni la auditoría

# envivo.feature    @REQ-F-13 @REQ-NF-07 @REQ-NF-13
Característica: Actividad en vivo sin datos personales
  Escenario: Agregados por laboratorio
    Cuando el nodo envía su KPI de 30 s
    Entonces la consola muestra peticiones, HIT, MISS, BYPASS y 403 por laboratorio y por nodo
    Y la respuesta no contiene URL, IP de equipos ni nombres de usuario
```

Con el código actual, el nodo no cumpliría el segundo escenario de `byod.feature`: acepta una configuración que vacía
`byod_networks` (REQ-RN-11 parcial, sección 1.9.1). Tampoco aplica horarios, porque el horario por laboratorio es R2.
Los dos escenarios se dejan escritos para que la brecha quede a la vista.
