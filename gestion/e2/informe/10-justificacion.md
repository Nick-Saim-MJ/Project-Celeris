# 2.1 Justificación del Proyecto

La justificación sigue la estructura de caso de negocio del PMBOK [7], parte del diagnóstico del Entregable 1 [16] y no lo repite: lo resume, lo convierte en objetivos verificables y vincula cada objetivo con el beneficio que produce. Los identificadores OB-x, RE-xx y S-xx son los mismos que emplean CE02 y CE03 (Marco común M6).

## 2.1.1 Problema que se resuelve

En los {{dato:labs}} laboratorios del Campus Juliaca, cada una de las {{dato:pcs_lab}} estaciones de un laboratorio descarga de forma independiente los mismos archivos de gran tamaño. Un ciclo de actualización genera {{dato:gb_ciclo_lab}} de tráfico por laboratorio, de los cuales {{dato:gb_repetidos_lab}} son copias del mismo contenido [S-26, S-27]; en términos anuales, {{dato:gb_repetidos_anio}} atraviesan el enlace de {{dato:enlace}} [S-02] solo para transportar duplicados. Aun con la totalidad del enlace disponible, un laboratorio requiere al menos {{dato:min_lab}} para completar la descarga de un ciclo (E1, §1.4.3).

El E1 estableció que la causa raíz no es solo de capacidad, sino de gestión: no se mide el desperdicio y no existe un rol con herramientas y atribuciones para decidir qué contenido se reutiliza (brechas MEA01 y DSS01 de COBIT 2019 [8]). Mantener la situación actual tiene un costo de {{dato:usd_no_actuar}} en {{dato:horizonte_anios}}, correspondiente a la ampliación del enlace que el proyecto permitiría diferir y a las horas técnicas que hoy se consumen en cada ciclo [S-01, S-03, S-06, S-07].

Los objetivos del proyecto se derivan del árbol de objetivos, que se obtiene al transformar el árbol de problemas del E1 (Figura 1.9): cada causa se convierte en un medio, el problema central en el objetivo central y cada efecto en un fin. La {{ref:fig-arbol-objetivos}} presenta el resultado, con el mismo número de medios y de fines que causas y efectos tenía el árbol de problemas.

{{figura:fig-arbol-objetivos}}

La figura muestra que el objetivo central, reutilizar en el campus el contenido repetido y descongestionar el enlace en horario de clase, solo se alcanza si actúan simultáneamente los cuatro medios: la copia compartida y la precarga atacan el volumen y la coincidencia temporal, mientras que el descifrado controlado y la consola del encargado atacan la causa de gestión. Los fines confirman que el valor del proyecto excede el ahorro de ancho de banda e incluye clases puntuales, horas técnicas liberadas y medición del desperdicio.

## 2.1.2 Objetivos del proyecto (SMART)

La {{ref:t-smart}} expresa los objetivos del proyecto en formato SMART. El indicador y la meta se leen de la fuente única del repositorio (`infra/trazabilidad.yaml`) y no se reescriben; el plazo procede de la guía CE01 v0.4 [18].

{{tabla:t-smart}}

Los cinco objetivos son medibles con instrumentos que el propio proyecto construye: el BHR y los GB evitados se obtienen de los registros del nodo de caché; los tiempos de preparación, de las mediciones del piloto; y la transparencia y la detección de abusos, de los registros del portal y del SIEM.

## 2.1.3 Beneficios esperados

Los beneficios esperados se agrupan en dos clases, cuyo detalle se desarrolla en la §2.3:

- **Cuantificables.** La ampliación del enlace que se difiere al servir desde la caché los {{dato:e2_mbps}} que, de otro modo, se pedirían al ISP [S-40], valorada en {{dato:e2_bn1}} anuales, y las horas técnicas ahorradas en cada ciclo, valoradas en {{dato:e2_bn2}} anuales [S-07].
- **Cualitativos.** Clases que comienzan a tiempo, autonomía y visibilidad del encargado, confianza de los usuarios en el tratamiento de su tráfico, menor exposición a abusos del servicio y capacidad institucional derivada de un producto propio documentado como código.
