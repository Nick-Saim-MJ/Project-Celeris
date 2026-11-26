# 3.1 Acta de Constitución

El acta de constitución autoriza formalmente el proyecto y otorga al director la autoridad para aplicar los recursos de la organización a sus actividades [1]. La {{ref:t-acta}} resume sus campos; las secciones siguientes desarrollan el sponsor, los objetivos, el alcance, las restricciones y los criterios de éxito.

{{tabla:t-acta}}

## 3.1.1 Sponsor y equipo de dirección

El sponsor propuesto es la Dirección de la EP de Ingeniería de Sistemas, que aporta el respaldo académico y aprueba los cambios que afectan los hitos de sustentación. La DTI actúa como usuario patrocinador: es la unidad que opera la red, el FortiGate y el Wi-Fi, y la que debe aprobar el piloto (H2). El director del proyecto es Henyelrey Lucio Garcia Chura, responsable del plan, del seguimiento y de los entregables de gestión e infraestructura de red; el líder técnico es Nick Saim Mayta Jara, responsable de la ingeniería de software, del centro de datos y del laboratorio. Toda pieza de trabajo la revisa el integrante que no la elaboró, porque la sustentación es individual.

## 3.1.2 Justificación estratégica

El diagnóstico del E1 (§1.5) estableció que la descarga repetida de contenido en los laboratorios es un problema de gestión antes que de capacidad: nadie mide el desperdicio ni decide qué se reutiliza. El business case del E2 comparó seis alternativas y recomendó {{dato:e2_gana}}, con un VAN de {{dato:e2_van}}, una TIR de {{dato:e2_tir}} y un periodo de recuperación de {{dato:e2_payback}}, condicionado a un piloto en un laboratorio. El proyecto se alinea con los objetivos estratégicos de infraestructura para la enseñanza, calidad académica, gestión eficiente de los recursos y seguridad de la información identificados en el E1.

## 3.1.3 Objetivos del proyecto

Los objetivos del proyecto son los objetivos OB-1…OB-5 del Marco común, formulados con criterios SMART en la {{ref:t-smart}}. Las metas provienen de `infra/trazabilidad.yaml`, la misma fuente que emplean CE02 y CE03, y los plazos se fijaron en el E2.

{{tabla:t-smart}}

## 3.1.4 Alcance preliminar

El alcance comprende el diseño completo de S1 en las tres áreas (gestión de TI, ingeniería de software e infraestructura), el prototipo validado de la consola y el laboratorio emulado; en S2, la construcción de la consola, el piloto en un laboratorio y, si el piloto lo justifica, la ampliación a los diez laboratorios del campus. Quedan fuera del alcance, conforme al Marco común (00 M3.2): el descifrado del tráfico BYOD, el rediseño del FortiGate, del Wi-Fi y de la capa de acceso, la red administrativa, el modo examen, la caché en AWS y la extensión a otras sedes. La EDT de la sección 3.2 desglosa este alcance en entregables.

## 3.1.5 Restricciones y supuestos

La {{ref:t-restricciones}} reúne las restricciones que limitan las opciones del equipo y los supuestos sobre los que descansa el plan, con su identificador del contrato de IDs. Las fechas académicas aún no publicadas se tratan como pendientes de confirmación y se gestionan mediante el riesgo RP-08.

{{tabla:t-restricciones}}

## 3.1.6 Interesados, hitos y presupuesto resumido

Los interesados son los identificados en el mapa de poder e interés del E1; la sección 3.7 define su nivel de compromiso y el plan de comunicaciones. Los hitos principales son H1 (sustentación de S1, {{dato:e3_h1}}), H2 (aprobación de la DTI para el piloto, {{dato:e3_h2}}), H3 (decisión de ampliación, {{dato:e3_h3}}) y H4 (sustentación final y cierre, {{dato:e3_h4}}). El presupuesto resumido es una línea base de {{dato:e3_linea_base}} más una reserva de gestión de {{dato:e3_gestion}}; el hardware del piloto, de {{dato:e3_hardware}}, coincide con la inversión inicial del E2.

## 3.1.7 Criterios de éxito

El proyecto se considera exitoso cuando cumple los criterios de la {{ref:t-exito}}, todos verificables con un dato del repositorio o del piloto.

{{tabla:t-exito}}

## 3.1.8 Aprobación

El acta entra en vigor con las firmas de la {{ref:t-firmas}}. Los nombres del sponsor y del usuario patrocinador se completan cuando la institución los designe.

{{tabla:t-firmas}}
