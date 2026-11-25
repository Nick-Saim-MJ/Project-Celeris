# 1.3 Diagnóstico digital / TI

El diagnóstico de TI responde cuatro preguntas: qué sistemas existen hoy alrededor de los laboratorios, qué tan maduros son los procesos de TI que el proyecto toca, qué brechas hay entre lo actual y lo que se necesita, y qué problemas operativos produce esa distancia.

## 1.3.1 Inventario de sistemas de información existentes

La {{ref:t-inventario}} lista los sistemas relacionados con los laboratorios, con su dueño, versión, soporte, dependencia de Internet y criticidad. La última columna dice qué tan firme es cada dato: un supuesto del registro común o un dato por levantar con la DTI.

{{tabla:t-inventario}}

Tres datos de este inventario cambian decisiones. Primero, el modelo del FortiGate y si tiene caché web, porque eso define si la alternativa A5 es real. Segundo, si existe un servidor de actualizaciones (WSUS o similar), porque cubriría las actualizaciones de Windows (A3). Tercero, la herramienta de imágenes y políticas de las PCs, porque por ella se reparte el PAC (D-05). Los tres están en la guía de entrevista con la DTI.

## 1.3.2 Nivel de madurez digital (COBIT 2019)

La madurez se mide con la escala de capacidad de COBIT 2019 (0 a 5) en los seis objetivos que el proyecto toca. El nivel actual no se supone: se obtiene en una entrevista estructurada con evidencia, y el instrumento está en `gestion/e1/instrumentos/entrevista-cobit.md`. La {{ref:t-cobit}} muestra, por objetivo, la pregunta guía, la evidencia que se pedirá y el nivel que el proyecto necesita al cierre del piloto.

{{tabla:t-cobit}}

La {{ref:fig-radar-cobit}} dibuja el nivel objetivo de cada proceso. El nivel actual aparecerá como segunda línea cuando se registre la entrevista en `gestion/e1/datos/madurez.yaml`; hasta entonces la figura lo marca como pendiente.

{{figura:fig-radar-cobit}}

La figura muestra un objetivo casi uniforme en el nivel definido (3): los procesos tienen que estar documentados, tener responsable y medirse. La excepción es APO12, para el que basta un registro de riesgos gestionado (2). La brecha que importa no es la forma del polígono, sino la distancia que dé la entrevista. Por eso el criterio «brechas con evidencia objetiva» de la rúbrica depende de esa medición.

## 1.3.3 Brechas tecnológicas

El análisis de brechas de la {{ref:t-brechas}} une cada situación actual con el estado deseado, la acción que la cierra, el componente de Celeris que la ejecuta y el objetivo del proyecto que sirve. La columna COBIT conecta cada brecha con el proceso que la entrevista va a medir.

{{tabla:t-brechas}}

La {{ref:fig-brechas}} cuantifica las brechas que ya se pueden calcular con los supuestos y las metas del repositorio, y deja visible la brecha COBIT que falta medir.

{{figura:fig-brechas}}

La brecha más grande es la de volumen: hoy cruzan el enlace {{dato:gb_ciclo_lab}} por laboratorio y ciclo, cuando bastaría con traer una copia de {{dato:gb_pc}}. La de tiempo se reduce de {{dato:min_lab}} a {{dato:min_lab_meta}} con la meta de OB-2, y la de transparencia pasa de ninguna PC avisada a todas. Las tres son cotas que salen de supuestos y se reemplazan por medidas en el piloto.

Pensar en lateral obliga a reconocer lo que ya funciona. La {{ref:t-ya-resuelto}} registra lo que la infraestructura actual ya resuelve y que Celeris no debe duplicar.

{{tabla:t-ya-resuelto}}

## 1.3.4 Problemas operativos asociados a TI

La {{ref:t-problemas}} lista los cinco problemas operativos que el diagnóstico relaciona con TI, con su impacto y frecuencia (valoración del equipo) y la evidencia que los confirmará.

{{tabla:t-problemas}}

La {{ref:fig-impacto-frecuencia}} ubica esos problemas en una matriz de impacto × frecuencia con los mismos umbrales que la matriz de riesgos.

{{figura:fig-impacto-frecuencia}}

Dos problemas quedan en la zona alta: la saturación del enlace en clase (PO-1), por su impacto, y la falta de medición del desperdicio (PO-5), porque ocurre siempre. Los otros tres están en la zona media y son consecuencia de los dos primeros. Si el desperdicio se midiera, la saturación tendría dueño y solución; por eso la causa raíz del §1.4 apunta a la medición y a la decisión, no solo al enlace.
