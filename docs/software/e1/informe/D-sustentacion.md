## Anexo D. Evidencia de sustentación

> **Estado: PENDIENTE.** La exposición ante el jurado aún no se ha realizado. Este anexo establece el guion y las
> preguntas previstas; el registro D.3 se completará el día de la sustentación.

### D.1 Guion de la exposición (10 min)

| Min | Tema | Material de apoyo | Expositor |
| --- | --- | --- | --- |
| 0–1 | Problema: cada estación repite la misma descarga y la mayor parte del tráfico es HTTPS | Resumen ejecutivo | {{dato:autor1}} |
| 1–3 | Requisitos: 59 vigentes, alcance implementado en el código y alcance previsto para S2 | Sección 1 (1.1–1.4), columna «Estado» | {{dato:autor1}} |
| 3–5 | Prototipo: recorrido P-01 → P-03 → P-07 con sesión remota bloqueada | `navegable.html` | {{dato:autor2}} |
| 5–7 | Arquitectura: consola en el campus y nodos que solicitan su configuración firmada | DS-21, D-11, D-25 | {{dato:autor2}} |
| 7–9 | Diseño detallado: ciclo completo de una fuente que requiere descifrado | DS-15, DS-17 | {{dato:autor1}} |
| 9–10 | Trazabilidad y pendientes declarados | Anexo B; «Estado declarado» del resumen | {{dato:autor2}} |

Ambos integrantes están en condiciones de sustentar cualquier requisito, pantalla o decisión; la distribución de la
tabla solo organiza la exposición.

### D.2 Preguntas preparadas

| Pregunta previsible | Respuesta sintética | Evidencia |
| --- | --- | --- |
| ¿Por qué no se aloja la consola en AWS? | El nodo no debe depender de Internet, y la llave de firma y los datos de uso deben permanecer en el campus. En AWS solo se ubica EC2-GW, sin datos | D-25, D-24, DS-21 |
| ¿Qué impide aprobar un descifrado desde fuera del campus? | La sesión que ingresa por EC2-GW se clasifica como `remoto` y `exigir_campus` responde 403; el intento se registra en la auditoría | REQ-F-37, DS-15, T54 |
| ¿Se descifra el tráfico de la red Wi-Fi de estudiantes? | Nunca: el nodo transmite sin descifrar todo el tráfico procedente de WIFI-EST, aun cuando el dominio pertenezca a una fuente por descifrar | REQ-F-36, D-27, T56 |
| ¿Qué ocurre si CTRL01 deja de estar disponible? | Los nodos continúan con la última configuración válida y la navegación no se interrumpe | D-11, REQ-NF-03 |
| ¿Qué ocurre si falla un nodo? | El PAC redirige al otro nodo y, si ambos fallan, a `DIRECT` | D-05, T09 |
| ¿Cómo se garantiza que una copia no esté corrupta? | Cada objeto se almacena por su SHA-256 y el hash se verifica antes de servirlo | D-03, REQ-F-06, REQ-NF-04 |
| ¿Quién decide qué contenido se almacena en caché? | El encargado activa únicamente lo que no requiere descifrado; lo que se descifra requiere aprobación de la DTI | D-20, REQ-RN-07 |
| ¿Qué datos personales almacena el sistema? | Ningún dato de navegación: no se registran cookies, cuerpos ni parámetros, y los reportes son exclusivamente por laboratorio | REQ-NF-07, D-22 |
| ¿Qué alcance está implementado? | El nodo está implementado (R1). La consola, la descarga por F10 y la precarga corresponden a R2. Cada requisito declara su estado | 1.1; «Estado declarado» del resumen |
| ¿Por qué el acta de validación está pendiente? | Las sesiones con encargados aún no se han realizado; el protocolo está preparado y no se consignan resultados ficticios | Anexo A |

### D.3 Registro de la sustentación

| Campo | Valor |
| --- | --- |
| Fecha y hora | [COMPLETAR] |
| Jurado | [COMPLETAR] |
| Integrantes presentes | [COMPLETAR] |
| Preguntas del jurado e integrante que respondió | [COMPLETAR] |
| Observaciones y compromisos | [COMPLETAR] |
