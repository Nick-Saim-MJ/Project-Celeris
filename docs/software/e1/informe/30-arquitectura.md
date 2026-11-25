# Sección 3: Diseño Arquitectónico

La arquitectura responde a las cuatro causas del problema descritas en el resumen ejecutivo:

| Causa del problema | Respuesta de la arquitectura | Decisión |
| --- | --- | --- |
| Cada PC repite la misma descarga | Un nodo de caché por campus descarga una sola vez y reparte por la LAN | D-03, D-05 |
| Se descarga en horario de clase | Precargas nocturnas en el propio nodo | D-21 |
| Casi todo es HTTPS | Descifrado selectivo, aprobado por la DTI, con CA por nodo | D-02, D-04, D-20 |
| Nadie puede decidir qué se reutiliza | Una consola para el encargado, en el campus | D-25 |

**Cómo leer los diagramas.** Siguen el modelo C4, que describe el sistema en niveles de detalle creciente:
contexto (C1), contenedores (C2) y componentes (C3). «R1» indica lo que ya existe en el código y «R2» lo que se
construye en S2; el color siempre va acompañado de esa etiqueta escrita. Un validador automático comprueba que toda
IP, equipo, flujo, requisito, decisión, caso de uso y pantalla que aparece en un diagrama exista de verdad.

## 3.1 Vistas arquitectónicas C4

### 3.1.1 Contexto (C1)

{{incluir:arquitectura/seccion-3.md|## 3.1 Vista de contexto (C1) — DS-20}}

{{figura:DS-20|Celeris Edge es un solo sistema: nodos, consola y portal. El BYOD entra con línea discontinua y nunca se descifra. El administrador aprueba solo desde JMP01 o ENC01.}}

### 3.1.2 Contenedores (C2), que cumple el rol de vista de despliegue

{{incluir:arquitectura/seccion-3.md|## 3.2 Vista de contenedores (C2), que cumple el rol de vista de despliegue — DS-21}}

{{figura:DS-21|Cada contenedor aparece con su VM, su IP y su puerto. En AWS solo están EC2-GW y S3; la consola, la base y la llave de firma quedan en CTRL01.}}

### 3.1.3 Componentes (C3)

{{incluir:arquitectura/seccion-3.md|## 3.3 Vista de componentes (C3) — DS-22 y DS-13}}

{{figura:DS-22|`router + origen` marca cada sesión como campus o remoto. `catalog` pide `exigir_campus` antes de aprobar y `publisher` firma cada versión.}}

## 3.2 Registro de decisiones arquitectónicas (ADR)

{{incluir:arquitectura/seccion-3.md|## 3.4 Registro de decisiones arquitectónicas (ADR)}}

**Cómo responden las decisiones a los atributos de calidad:**

{{incluir:arquitectura/seccion-3.md|## 3.5 Cómo responde la arquitectura a los atributos de calidad}}
