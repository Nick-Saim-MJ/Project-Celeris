# Sección 1: Especificación de Requerimientos

La especificación sigue ISO/IEC/IEEE 29148:2018. Los RNF se clasifican según ISO/IEC 25010:2023. Hay
{{dato:n_req}} requisitos vigentes: {{dato:n_rf}} funcionales (REQ-F), {{dato:n_rnf}} no funcionales (REQ-NF) y
{{dato:n_rn}} reglas de negocio (REQ-RN).

**Columnas de las tablas:**

- **Prior. (MoSCoW):** M = debe, S = debería, C = puede.
- **Ver.:** R1 es la prueba de concepto de este semestre (S1): el nodo, que ya está programado. R2 se construye
  en el segundo semestre (S2): la consola, el agente del nodo y el portal.
- **Estado:** situación real en el código: *Hecho*, *Parcial* o *Pendiente*.
- **Verifica:** la prueba (Txx) o el escenario de aceptación de 1.6 que lo comprueba.

Los requisitos REQ-F-16, F-21, F-23, F-27 y F-29 se retiraron en versiones anteriores y sus números no se
reutilizan. Las direcciones IP, los flujos de red y los equipos que se citan son los del diseño de red (CE03).

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
S-36) están en la Sección 0.2, cada uno con lo que ocurre si resulta falso. Además, el sistema depende de dos partes
que no construye este proyecto de software: la DTI, que instala el PAC y la CA en las PCs por directiva de grupo
(GPO), configura el FortiGate y ejecuta la contingencia de S-35; y el diseño de red (CE03), que entrega las zonas,
el firewall FW01, la VPN y EC2-GW.

## 1.5 Historias de usuario o casos de uso

**Actores.** Cuatro tienen cuenta en la consola, con rol RBAC propio; dos no tienen cuenta:

{{incluir:srs/02-descripcion-general.md|### 1.6.3 Características de los usuarios|tabla}}

{{figura:DS-14|Los once casos de uso con sus actores. «R1» lo cubre el nodo actual y «R2» requiere la consola o el portal. CU-01 no tiene pantalla, porque el navegador descarga por el PAC.}}

**Catálogo de casos de uso.** Cada caso nombra sus requisitos, su pantalla del prototipo (Sección 2) y su diagrama
de secuencia (Sección 4):

{{incluir:srs/06-casos-de-uso.md|### 1.10.1 Catálogo de casos de uso|tabla}}

**Especificación de los casos de uso críticos.** Son los cuatro que sostienen OB-2, OB-3 y OB-5:

{{incluir:srs/06-casos-de-uso.md|### 1.10.2 Especificación de los casos de uso críticos|sin_intro}}

**Historias de usuario.**

{{incluir:srs/06-casos-de-uso.md|### 1.10.3 Historias de usuario}}

## 1.6 Criterios de aceptación

Cada criterio de aceptación es un escenario en formato Gherkin: *Dado* un contexto, *Cuando* ocurre una acción,
*Entonces* se espera un resultado. Cada escenario lleva como etiqueta los requisitos que comprueba. Por ejemplo:

```gherkin
Escenario: Aprobar desde fuera del campus se rechaza
  Dado una sesión de administrador que llegó por EC2-GW con su certificado de cliente
  Cuando pide aprobar la fuente "download.jetbrains.com"
  Entonces la API responde 403
  Y la auditoría registra el intento con origen "remoto"
```

La tabla resume los 14 escenarios y el resultado que cada uno exige. En S2 se convertirán en pruebas automáticas, y
la matriz de trazabilidad se generará a partir de sus etiquetas.

{{tabla:gherkin}}

Dos escenarios describen a propósito algo que el código actual todavía no cumple: el nodo aceptaría una
configuración que deja vacía la lista de redes BYOD (REQ-RN-11, parcial) y aún no aplica horarios por laboratorio
(R2). Se dejan escritos para que la brecha quede a la vista.

Los criterios que dependen de la red son pruebas del plan de pruebas compartido con el informe de infraestructura
(columna «Verifica» de 1.1 a 1.3). Las que se ejecutan en el laboratorio emulado se informan como emuladas, y ninguna
prueba que quedó como «no aplica» o «parcial» se presenta como aprobada.

**Cobertura de la verificación.**

{{incluir:srs/08-verificacion-trazabilidad.md|### 1.12.3 Cobertura}}
