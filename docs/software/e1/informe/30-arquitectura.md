# Sección 3: Diseño Arquitectónico

La arquitectura propuesta responde a las cuatro causas del problema descritas en el resumen ejecutivo:

| Causa del problema | Respuesta de la arquitectura | Decisión |
| --- | --- | --- |
| Cada estación repite la misma descarga | Un nodo de caché por campus descarga una sola vez y distribuye por la LAN | D-03, D-05 |
| Las descargas ocurren en horario de clase | Precargas nocturnas ejecutadas en el propio nodo | D-21 |
| La mayor parte del tráfico es HTTPS | Descifrado selectivo, aprobado por la DTI, con CA por nodo | D-02, D-04, D-20 |
| No existe un rol que decida qué se reutiliza | Una consola para el encargado, alojada en el campus | D-25 |

**Lectura de los diagramas.** Los diagramas siguen el modelo C4, que describe el sistema en niveles de detalle
creciente: contexto (C1), contenedores (C2) y componentes (C3). «R1» identifica los elementos ya implementados en el
código y «R2» los que se construirán en S2; el color se acompaña siempre de la etiqueta escrita. Un validador
automático comprueba que toda dirección IP, equipo, flujo, requisito, decisión, caso de uso y pantalla representados
en un diagrama exista efectivamente en el registro del proyecto.

## 3.1 Vistas arquitectónicas C4

### 3.1.1 Contexto (C1)

{{incluir:arquitectura/seccion-3.md|## 3.1 Vista de contexto (C1) — DS-20}}

{{figura:DS-20|Celeris Edge constituye un único sistema integrado por nodos, consola y portal. El tráfico BYOD se representa con línea discontinua y nunca se descifra. El administrador aprueba únicamente desde JMP01 o ENC01.}}

### 3.1.2 Contenedores (C2), que cumple el rol de vista de despliegue

{{incluir:arquitectura/seccion-3.md|## 3.2 Vista de contenedores (C2), que cumple el rol de vista de despliegue — DS-21}}

{{figura:DS-21|Cada contenedor se representa con su VM, su dirección IP y su puerto. En AWS se ubican únicamente EC2-GW y S3; la consola, la base de datos y la llave de firma permanecen en CTRL01.}}

### 3.1.3 Componentes (C3)

{{incluir:arquitectura/seccion-3.md|## 3.3 Vista de componentes (C3) — DS-22 y DS-13}}

{{figura:DS-22|`router + origen` clasifica cada sesión como de campus o remota. `catalog` invoca `exigir_campus` antes de aprobar y `publisher` firma cada versión.}}

## 3.2 Registro de decisiones arquitectónicas (ADR)

{{incluir:arquitectura/seccion-3.md|## 3.4 Registro de decisiones arquitectónicas (ADR)}}

**Respuesta de las decisiones a los atributos de calidad:**

{{incluir:arquitectura/seccion-3.md|## 3.5 Cómo responde la arquitectura a los atributos de calidad}}
