# Anexo A. Matriz de comunicación zona × zona

Se lee por filas: origen ↓, destino →. «✔ F-nn» indica que se permiten solo esos flujos; «✖» indica denegado y registrado (política por defecto); «✖ F-nn», tráfico bloqueado de forma explícita; «—», que no aplica (la misma zona o un tráfico que no pasa por el proyecto). El retorno de una conexión permitida no se lista, porque FW01 es un firewall con estado. DNS y NTP (F2) van de todas las zonas internas a FW01 y no ocupan celda. F33 (FW01 → PORTAL01) nace en el propio firewall y tampoco es una celda entre zonas. La matriz se genera desde `matriz_esperada` del inventario. Las validaciones V-11 y V-12 comprueban que coincide con la que se deriva de los flujos.

{{tabla:matriz_completa}}

{{tabla:matriz_notas}}
