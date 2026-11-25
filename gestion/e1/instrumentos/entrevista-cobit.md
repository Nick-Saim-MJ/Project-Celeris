# Instrumento de entrevista: madurez COBIT 2019 de los procesos de TI de los laboratorios (CE01 E1, §1.3.2)

**Para qué sirve.** Mide el nivel de capacidad actual (0–5) de los seis objetivos COBIT 2019 que toca Celeris Edge. El
resultado se registra en `gestion/e1/datos/madurez.yaml` (`actual`, `fecha_entrevista`, `entrevistados`) y
`make figuras-ce01` redibuja el radar y el gráfico de brechas.

**A quién.** Jefe de Infraestructura de la DTI (APO02, APO12, BAI03, DSS01, DSS05), jefe de Soporte (DSS01, MEA01) y
dos encargados de laboratorio (DSS01, MEA01). Se registran roles, no nombres.

**Duración.** 45 minutos por persona. Se pide la evidencia antes de la reunión.

**Regla de puntaje.** Un nivel se otorga solo si se **vio la evidencia** (documento, registro, captura). Lo que solo se
afirma sin evidencia vale como máximo nivel 1. Si los entrevistados no coinciden, se registra el nivel más bajo con
evidencia y la diferencia se anota.

## Escala de capacidad (COBIT 2019)

| Nivel | Nombre | Qué se tiene que ver |
| --- | --- | --- |
| 0 | Incompleto | La actividad no se hace o no logra su propósito |
| 1 | Inicial | Se hace, pero de forma informal y dependiente de una persona |
| 2 | Gestionado | Se planifica, tiene responsable y deja registro |
| 3 | Definido | Está documentado como procedimiento de la organización, se sigue y se mide |
| 4 | Cuantitativo | Se gestiona con indicadores y metas numéricas que se revisan |
| 5 | Optimizado | Se mejora de forma continua a partir de los indicadores |

## Preguntas por objetivo

### APO02 Estrategia gestionada (objetivo: nivel 3)

1. ¿Existe un plan estratégico de TI vigente? ¿Qué periodo cubre?
2. ¿El plan incluye a los laboratorios de cómputo (capacidad, renovación, conectividad)?
3. ¿Cómo se decide hoy una inversión en conectividad o en servidores para los laboratorios?
4. ¿Quién aprueba ese plan y cada cuánto se revisa?

**Evidencia esperada:** el plan de TI con la línea de laboratorios; acta de aprobación o revisión.

### APO12 Riesgo gestionado (objetivo: nivel 2)

1. ¿Existe un registro de riesgos de TI? ¿Quién lo mantiene?
2. ¿Incluye la saturación del enlace, la caída del perímetro o la privacidad de los usuarios?
3. ¿Cada riesgo tiene dueño, probabilidad, impacto y fecha de revisión?

**Evidencia esperada:** registro de riesgos (aunque sea una hoja de cálculo) con fecha de la última revisión.

### BAI03 Soluciones gestionadas (objetivo: nivel 3)

1. Cuando la DTI implementa una solución nueva, ¿se escriben requisitos antes?
2. ¿Hay un plan de pruebas y una aceptación formal antes de pasar a producción?
3. ¿Se documenta la configuración final (por ejemplo, del FortiGate o de las imágenes de laboratorio)?

**Evidencia esperada:** requisitos y plan de pruebas de una solución reciente; documento de configuración.

### DSS01 Operaciones gestionadas (objetivo: nivel 3)

1. ¿Se monitorea el uso del enlace por hora? ¿Con qué herramienta (FortiGate, ISP, otra)?
2. ¿Se sabe qué laboratorio o qué tipo de tráfico satura el enlace en horas de clase?
3. ¿Se programan las actualizaciones masivas fuera del horario de clase? ¿Quién lo decide?
4. ¿Cuánto tarda, en promedio, dejar listo un laboratorio para una clase que pide software nuevo?

**Evidencia esperada:** gráfico de uso del enlace por hora de una semana de clases; calendario de actualizaciones.

### DSS05 Servicios de seguridad gestionados (objetivo: nivel 3)

1. ¿Hay detección de incidentes en la red de laboratorios (IDS, registros del FortiGate, SIEM)?
2. ¿Existe un procedimiento de respuesta a incidentes? ¿Se usó en el último año?
3. ¿El FortiGate inspecciona SSL hoy? ¿Con qué alcance y con qué aviso a los usuarios?

**Evidencia esperada:** registro de incidentes; procedimiento de respuesta; política de inspección SSL.

### MEA01 Monitoreo del desempeño (objetivo: nivel 3)

1. ¿Se reportan indicadores de los laboratorios (disponibilidad, tiempo de preparación, uso del enlace)?
2. ¿Quién recibe ese reporte y qué decisiones se tomaron con él?
3. ¿Se mide de alguna forma cuánto ancho de banda se gasta en descargas repetidas?

**Evidencia esperada:** reporte periódico de indicadores con fecha.

## Datos de contexto que se levantan en la misma reunión

Estos datos completan las marcas [levantar con la DTI] del informe E1:

| Dato | Para qué sección | Decide |
| --- | --- | --- |
| Modelo y versión del FortiGate; licencias FortiGuard; si tiene disco y caché web | §1.3.1, §1.3.3 | Si la alternativa A5 es real (E2) |
| Si existe WSUS o un servidor de actualizaciones similar | §1.3.1, §1.3.3 | Alternativa A3 (E2) |
| Herramienta de imágenes y políticas de las PCs (directorio, GPO) | §1.3.1 | Cómo se reparte el PAC (D-05) |
| Sistema operativo de las PCs de laboratorio | §1.3.1 | Compatibilidad del certificado de la CA |
| Plataforma virtual de aprendizaje y mesa de ayuda (producto y versión) | §1.3.1 | Inventario completo |
| De quién dependen los encargados y dónde está el oficial de datos personales | §1.1.2 | Organigrama y RACI (E3) |
| Contrato del ISP: ancho de banda, costo por Mbps adicional, plazo, número de proveedores con fibra | §1.1.1 | S-02, S-03 |
| Horas de clase retrasadas por descargas (estimación de docentes o registros) | §1.4.3 | Impacto en la enseñanza |
| Misión, visión y objetivos estratégicos del plan vigente de la UPeU | §1.2.1 | Rótulos OE-a…OE-d |

## Registro

Al terminar, completar `gestion/e1/datos/madurez.yaml`:

```yaml
estado_entrevista: realizada
fecha_entrevista: "AAAA-MM-DD"
entrevistados: ["Jefe de Infraestructura DTI", "Jefe de Soporte DTI", "Encargado lab. N", "Encargado lab. M"]
objetivos:
  - id: APO02
    actual: 1          # nivel con evidencia vista
```

y guardar la evidencia (sin datos personales) en una carpeta fuera del repositorio, citada por nombre en el informe.
