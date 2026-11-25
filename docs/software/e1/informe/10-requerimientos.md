# Sección 1: Especificación de Requerimientos

La especificación se elaboró conforme a la norma ISO/IEC/IEEE 29148:2018, y los requisitos no funcionales se
clasifican según ISO/IEC 25010:2023. Se registran {{dato:n_req}} requisitos vigentes: {{dato:n_rf}} funcionales (REQ-F), {{dato:n_rnf}} no funcionales (REQ-NF) y
{{dato:n_rn}} reglas de negocio (REQ-RN).

**Columnas de las tablas:**

- **Prior. (MoSCoW):** M = debe, S = debería, C = puede.
- **Ver.:** R1 corresponde a la prueba de concepto del semestre en curso (S1), es decir, el nodo, que ya se
  encuentra implementado. R2 se construirá en el segundo semestre (S2) e incluye la consola, el agente del nodo y el
  portal.
- **Estado:** situación efectiva en el código: *Hecho*, *Parcial* o *Pendiente*.
- **Verifica:** prueba (Txx) o escenario de aceptación de la sección 1.6 que comprueba el requisito.

Los requisitos REQ-F-16, F-21, F-23, F-27 y F-29 fueron retirados en versiones anteriores y su numeración no se
reutiliza. Las direcciones IP, los flujos de red y los equipos citados corresponden al diseño de red (CE03).

## 1.1 Requerimientos funcionales

### 1.1.1 Nodo de caché (plano de datos)

{{incluir:srs/03-requisitos-funcionales.md|### 1.7.1 Nodo de caché (plano de datos)}}

### 1.1.2 Consola del encargado y portal (plano de control)

{{incluir:srs/03-requisitos-funcionales.md|### 1.7.2 Consola del encargado (plano de control)}}

### 1.1.3 Precisiones que salen del diseño

{{incluir:srs/03-requisitos-funcionales.md|### 1.7.3 Precisiones que salen del diseño}}

## 1.2 Requerimientos no funcionales

{{incluir:srs/04-requisitos-no-funcionales.md|## 1.8 Requisitos no funcionales (ISO/IEC 25010:2023)}}

## 1.3 Reglas de negocio

{{incluir:srs/05-reglas-restricciones.md|### 1.9.1 Reglas de negocio}}

## 1.4 Restricciones del sistema

{{incluir:srs/05-reglas-restricciones.md|### 1.9.2 Restricciones}}

**Supuestos y dependencias.** Los supuestos que condicionan el software (S-02, S-04, S-14, S-26, S-28, S-29 y S-32 a
S-36) se presentan en la Sección 0.2, cada uno con la consecuencia de que resulte falso. Adicionalmente, el sistema
depende de dos partes externas al proyecto de software: la DTI, que instala el PAC y la CA en las estaciones mediante
directivas de grupo (GPO), configura el FortiGate y ejecuta la contingencia de S-35; y el diseño de red (CE03), que
provee las zonas, el firewall FW01, la VPN y EC2-GW.

## 1.5 Historias de usuario o casos de uso

**Actores.** Cuatro actores disponen de cuenta en la consola, con un rol RBAC propio, y dos operan sin cuenta:

{{incluir:srs/02-descripcion-general.md|### 1.6.3 Características de los usuarios|tabla}}

{{figura:DS-14|Los once casos de uso con sus actores. Los casos «R1» están cubiertos por el nodo actual y los «R2» requieren la consola o el portal. CU-01 carece de pantalla, dado que el navegador descarga a través del PAC.}}

**Catálogo de casos de uso.** Cada caso identifica sus requisitos, su pantalla del prototipo (Sección 2) y su
diagrama de secuencia (Sección 4):

{{incluir:srs/06-casos-de-uso.md|### 1.10.1 Catálogo de casos de uso|tabla}}

**Especificación de los casos de uso críticos.** Corresponden a los cuatro casos que sustentan OB-2, OB-3 y OB-5:

{{incluir:srs/06-casos-de-uso.md|### 1.10.2 Especificación de los casos de uso críticos|sin_intro}}

**Historias de usuario.**

{{incluir:srs/06-casos-de-uso.md|### 1.10.3 Historias de usuario}}

## 1.6 Criterios de aceptación

Cada criterio de aceptación se expresa como un escenario en formato Gherkin: *Dado* un contexto, *Cuando* ocurre
una acción, *Entonces* se espera un resultado. Cada escenario se etiqueta con los requisitos que comprueba, como se
ilustra a continuación:

```gherkin
Escenario: Aprobar desde fuera del campus se rechaza
  Dado una sesión de administrador que llegó por EC2-GW con su certificado de cliente
  Cuando pide aprobar la fuente "download.jetbrains.com"
  Entonces la API responde 403
  Y la auditoría registra el intento con origen "remoto"
```

La tabla siguiente resume los 14 escenarios y el resultado que exige cada uno. En S2 se convertirán en pruebas
automatizadas, y la matriz de trazabilidad se generará a partir de sus etiquetas.

{{tabla:gherkin}}

Dos escenarios describen deliberadamente comportamientos que el código actual aún no satisface: el nodo aceptaría
una configuración con la lista de redes BYOD vacía (REQ-RN-11, parcial) y todavía no aplica horarios por laboratorio
(R2). Se mantienen documentados para que la brecha resulte visible.

Los criterios que dependen de la red corresponden a pruebas del plan compartido con el informe de infraestructura
(columna «Verifica» de las secciones 1.1 a 1.3). Las pruebas ejecutadas en el laboratorio emulado se informan como
emuladas, y ninguna prueba con resultado «no aplica» o «parcial» se presenta como aprobada.

**Cobertura de la verificación.**

{{incluir:srs/08-verificacion-trazabilidad.md|### 1.12.3 Cobertura}}
