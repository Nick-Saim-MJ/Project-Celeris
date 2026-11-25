## Anexo D. Evidencia de sustentación

> **Estado: PENDIENTE.** La exposición ante el docente aún no se realiza. Este anexo fija el guion y las preguntas
> preparadas; el registro D.3 se llena el día de la sustentación.

### D.1 Guion de la exposición (10 min)

| Min | Tema | Muestra | Quién |
| --- | --- | --- | --- |
| 0–1 | Problema: cada PC repite la misma descarga y casi todo es HTTPS | Resumen ejecutivo | {{dato:autor1}} |
| 1–3 | Requisitos: 59 vigentes, qué existe en el código y qué se construye en S2 | Sección 1 (1.1–1.4), columna «Estado» | {{dato:autor1}} |
| 3–5 | Prototipo: recorrido P-01 → P-03 → P-07 con sesión remota bloqueada | `navegable.html` | {{dato:autor2}} |
| 5–7 | Arquitectura: consola en el campus, nodos que piden su configuración firmada | DS-21, D-11, D-25 | {{dato:autor2}} |
| 7–9 | Diseño detallado: fuente que requiere descifrado de principio a fin | DS-15, DS-17 | {{dato:autor1}} |
| 9–10 | Trazabilidad y pendientes declarados | Anexo B; «Estado declarado» del resumen | {{dato:autor2}} |

Ambos integrantes deben poder defender cualquier requisito, pantalla o decisión. El reparto de la tabla solo
ordena la exposición.

### D.2 Preguntas preparadas

| Pregunta probable | Respuesta corta | Evidencia |
| --- | --- | --- |
| ¿Por qué no poner la consola en AWS? | El nodo no debe depender de Internet, y la llave de firma y los datos de uso quedan en el campus. En AWS solo está EC2-GW, sin datos | D-25, D-24, DS-21 |
| ¿Qué impide aprobar un descifrado desde casa? | La sesión que llega por EC2-GW se marca `remoto` y `exigir_campus` responde 403; queda en auditoría | REQ-F-37, DS-15, T54 |
| ¿Se descifra el Wi-Fi de los estudiantes? | Nunca: el nodo deja pasar sin descifrar todo lo que llega de WIFI-EST, aunque el dominio esté en una fuente a descifrar | REQ-F-36, D-27, T56 |
| ¿Qué pasa si CTRL01 cae? | Los nodos siguen con la última configuración válida y la navegación no se corta | D-11, REQ-NF-03 |
| ¿Y si cae un nodo? | El PAC pasa al otro nodo y, si caen los dos, a `DIRECT` | D-05, T09 |
| ¿Cómo se sabe que una copia no está corrupta? | Cada objeto se guarda por su SHA-256 y el hash se verifica antes de servirlo | D-03, REQ-F-06, REQ-NF-04 |
| ¿Quién decide qué se cachea? | El encargado activa solo lo que no se descifra; lo que se descifra lo aprueba la DTI | D-20, REQ-RN-07 |
| ¿Qué datos personales guarda el sistema? | Ninguno de navegación: sin cookies, cuerpos ni parámetros, y reportes solo por laboratorio | REQ-NF-07, D-22 |
| ¿Qué está hecho y qué no? | El nodo existe (R1). La consola, la descarga por F10 y la precarga son R2. Cada requisito dice su estado | 1.1; «Estado declarado» del resumen |
| ¿Por qué falta el acta de validación? | Las sesiones con encargados no se han realizado; el protocolo está listo y no se inventan resultados | Anexo A |

### D.3 Registro de la sustentación

| Campo | Valor |
| --- | --- |
| Fecha y hora | [COMPLETAR] |
| Docente | [COMPLETAR] |
| Integrantes presentes | [COMPLETAR] |
| Preguntas del docente y quién respondió | [COMPLETAR] |
| Observaciones y compromisos | [COMPLETAR] |
