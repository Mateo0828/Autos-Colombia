
# Autos Colombia - Resultados de pruebas EA3

## 1. Identificación del proyecto

- Institución: Institución Universitaria Digital de Antioquia.
- Asignatura: Ingeniería de Software.
- Grupo: 22.
- Proyecto: Autos Colombia.
- Evidencia de Aprendizaje 3.
- Iteración 3: Gestión de pagos y mensualidades.
- Integrantes:
  - Nicolas Mateo Chavez Garcia.
  - Luis Miguel Vargas Guevara.
- Rama de desarrollo: feature/i3-backend.
- Fecha de validación por módulos: 21 de noviembre de 2026.

## 2. Objetivo

Verificar el funcionamiento del módulo de pagos y
mensualidades, su integración con las funcionalidades
implementadas durante EA1 y EA2, y el cumplimiento
de los casos establecidos en el plan de pruebas PP-03.

Las comprobaciones incluyen lógica de negocio,
integración de servicios, persistencia, seguridad,
concurrencia, atomicidad, regresión e integridad
de la información.

## 3. Entorno de pruebas

| Componente | Configuración |
|---|---|
| Sistema operativo | Windows |
| Python | 3.12.10 |
| Flask | 3.1.3 |
| Psycopg | 3.3.6 |
| PostgreSQL | 17.6 |
| Framework de pruebas | unittest |
| Cliente HTTP de pruebas | Flask Test Client |
| Simulación controlada | unittest.mock |
| Concurrencia | ThreadPoolExecutor y Barrier |
| Base de pruebas | autos_colombia_ea3_pruebas |
| Zona horaria de negocio | America/Bogota |

Las pruebas de integración se ejecutan sobre una base
aislada mediante activación explícita de RUN_E2E=1.

No se utiliza la base de datos principal para ejecutar
las pruebas automatizadas.

Las credenciales se obtienen desde variables de entorno
o desde el archivo .env local y no se incorporan al
repositorio.

## 4. Estrategia de pruebas

### 4.1. Pruebas unitarias

Verifican las reglas de negocio correspondientes a:

- Tarifas por tipo de vehículo.
- Validación de fechas.
- Cálculo de fechas de corte.
- Conservación del día original de mensualidad.
- Años bisiestos y meses de duración variable.
- Determinación del estado de vigencia.
- Proyección del primer pago.
- Renovaciones anticipadas y tardías.
- Consistencia de los períodos de cobertura.

No requieren una conexión activa a PostgreSQL.

### 4.2. Pruebas de integración

Utilizan Flask Test Client, los endpoints reales y
transacciones ejecutadas sobre PostgreSQL.

Cada prueba crea los datos independientes que necesita,
evitando depender de vehículos previamente utilizados.

Los registros ficticios generados se conservan como
historial de pruebas. Las estancias pendientes se
finalizan y las sesiones se cierran mediante las
funciones de limpieza correspondientes.

### 4.3. Pruebas de concurrencia

Utilizan solicitudes independientes y mecanismos de
sincronización para comprobar el comportamiento de
los bloqueos transaccionales de PostgreSQL.

Se verifica que dos solicitudes incompatibles no
produzcan pagos duplicados, dobles estancias ni doble
ocupación de celdas.

### 4.4. Pruebas de atomicidad

Se provocan fallos controlados después de ejecutar
escrituras reales en una transacción.

Se comprueba que PostgreSQL revierta las operaciones
incompletas y conserve la información anterior.

Las respuestas HTTP 500 provocadas intencionalmente
en estas pruebas representan el comportamiento esperado.

### 4.5. Pruebas de regresión

Comprueban que las funcionalidades evaluadas de EA1 y
EA2 se conservan después de implementar EA3.

Incluyen autenticación, permisos, clientes, vehículos,
celdas, entradas, reasignaciones, consultas y salidas.

## 5. Resultados del plan PP-03

Los siguientes resultados corresponden a las ejecuciones
por módulo realizadas sobre el backend de la iteración 3.

| ID | Escenario | Resultado observado | Estado |
|---|---|---|---|
| PG-01 | Consultar mensualidad vigente | HTTP 200, tarifa, cobertura, estado y próxima renovación correctos. | APROBADO |
| PG-02 | Vehículo inexistente y sin pagos | HTTP 404 para placa inexistente; vehículo sin pagos en estado INACTIVA. | APROBADO |
| PG-03 | Primer pago de automóvil | HTTP 201, valor de 250000 COP y cobertura persistida correctamente. | APROBADO |
| PG-04 | Primer pago de motocicleta | HTTP 201, valor de 100000 COP y responsable autenticado. | APROBADO |
| PG-05 | Datos de pago incorrectos | HTTP 422 para datos inválidos y HTTP 404 para vehículo inexistente, sin escrituras. | APROBADO |
| PG-06 | Renovación anticipada | El nuevo período comienza en la fecha de corte anterior y agrega un mes calendario. | APROBADO |
| PG-07 | Renovación tardía | El período comienza en el corte anterior. Se conserva la advertencia cuando continúa vencida. | APROBADO |
| PG-08 | Fechas especiales | Se conserva el día original 30, 31 o 29, incluyendo meses cortos y años bisiestos. | APROBADO |
| PG-09 | Duplicidad y concurrencia | Una solicitud exitosa y una rechazada con HTTP 409, sin duplicar el período pagado. | APROBADO |
| PG-10 | Historial de pagos | HTTP 200, orden descendente y trazabilidad de pagos y responsables. | APROBADO |
| PG-11 | Historial vacío e inexistente | Lista vacía para vehículo sin pagos y HTTP 404 para placa inexistente. | APROBADO |
| PG-12 | Entrada con mensualidad vigente | HTTP 201, estancia activa, celda ocupada y responsable autenticado. | APROBADO |
| PG-13 | Entrada con mensualidad vencida | HTTP 400, sin cambios en estancias, celdas ni pagos. | APROBADO |
| PG-14 | Entrada después del primer pago | Entrada inicialmente rechazada; primer pago exitoso y posterior entrada autorizada. | APROBADO |
| PG-15 | Salida con mensualidad vencida | HTTP 200, estancia finalizada, celda liberada y cobertura conservada. | APROBADO |
| PG-16 | Límite de fecha de corte | ACTIVA antes del corte e INACTIVA desde el mismo día del corte. | APROBADO |
| PG-17 | Autenticación y roles | Operaciones autorizadas para administrador y operador; HTTP 401 sin sesión válida. | APROBADO |
| PG-18 | Valor calculado por servidor | Tarifas correctas y HTTP 422 ante campos de valor, responsable o período manipulados. | APROBADO |
| PG-19 | Atomicidad de pagos | INSERT y UPDATE revertidos ante fallos controlados, con reintentos posteriores exitosos. | APROBADO |
| PG-20 | Protección de mensualidad | HTTP 422 ante edición manual del estado o fechas de cobertura y HTTP 403 para operador sin permisos. | APROBADO |
| PG-21 | Restricciones de integridad | PostgreSQL rechaza duplicidad, valores inválidos, períodos incorrectos y referencias inexistentes. | APROBADO |
| PG-22 | Regresión de iteraciones | Autenticación, administración y operaciones anteriores conservadas e integradas con EA3. | APROBADO |

### 5.1. Consolidado académico

| Indicador | Resultado |
|---|---:|
| Casos planificados en PP-03 | 22 |
| Casos ejecutados en backend | 22 |
| Casos aprobados en backend | 22 |
| Casos fallidos | 0 |
| Porcentaje de aprobación | 100 % |

La aceptación visual de las interfaces y su integración
con Next.js se valida separadamente durante la
integración final del proyecto.

## 6. Correspondencia con el código fuente

| Casos académicos | Archivo de pruebas |
|---|---|
| PG-01 a PG-08 | tests/test_integracion_pagos.py |
| PG-10 y PG-11 | tests/test_integracion_pagos.py |
| PG-16, PG-17 y PG-18 | tests/test_integracion_pagos.py |
| PG-12, PG-13, PG-14, PG-15 y PG-20 | tests/test_integracion_operaciones.py |
| PG-09, PG-19 y PG-21 | tests/test_integridad_transaccional.py |
| PG-22 | tests/test_regresion_iteraciones.py |
| Concurrencia complementaria de entradas | tests/test_concurrencia_entradas.py |

Infraestructura común:

- tests/__init__.py
- tests/e2e_helpers.py

Pruebas unitarias:

- tests/test_mensualidad_service.py
- tests/test_proyeccion_pago.py

## 7. Consolidado de pruebas automatizadas

| Módulo | Pruebas | Aprobadas |
|---|---:|---:|
| Lógica de mensualidades | 16 | 16 |
| Proyección de pagos | 12 | 12 |
| Integración de pagos | 13 | 13 |
| Integración de operaciones | 5 | 5 |
| Concurrencia de entradas | 6 | 6 |
| Regresión de iteraciones | 6 | 6 |
| Integridad transaccional | 9 | 9 |
| Total | 67 | 67 |

Distribución:

- Pruebas unitarias: 28.
- Pruebas de integración: 39.

Los resultados fueron obtenidos inicialmente por módulo
y posteriormente confirmados mediante la ejecución
conjunta de las 67 pruebas, documentada en la sección 13.

Los 22 casos académicos y las 67 pruebas automatizadas
representan niveles distintos de evaluación y no deben
sumarse como pruebas independientes.

## 8. Pruebas complementarias de concurrencia de entradas

| Caso | Escenario | Resultado |
|---|---|---|
| CO-01 | Dos solicitudes para el mismo vehículo | HTTP 201 y 409 |
| CO-02 | Dos vehículos sobre una misma celda | HTTP 201 y 409 |
| CO-03 | Vehículo previamente dentro | HTTP 400 |
| CO-04 | Celda previamente ocupada | HTTP 400 |
| CO-05 | Celda deshabilitada después de validar | HTTP 409 |
| CO-06 | Vencimiento durante revalidación final | HTTP 400 |

Resultado: 6 de 6 pruebas aprobadas.

Estas comprobaciones respaldan el contrato HTTP del
diagrama de secuencia DS-01 y la protección de las
operaciones frente a solicitudes concurrentes.

## 9. Integridad transaccional y restricciones SQL

### 9.1. Duplicidad de pagos

Se comprobó que el uso de corte_esperado y el bloqueo
del vehículo impiden procesar dos veces una misma
proyección de pago.

Resultado: 3 de 3 pruebas aprobadas.

### 9.2. Atomicidad

Se comprobaron los siguientes escenarios:

- Fallo después de ejecutar INSERT INTO pago.
- Fallo después de ejecutar INSERT y UPDATE vehiculo.

En ambos casos se devolvió HTTP 500, las escrituras
fueron revertidas y el reintento posterior fue exitoso.

Resultado: 2 de 2 pruebas aprobadas.

### 9.3. Restricciones PostgreSQL

Se verificaron las siguientes restricciones:

- uq_pago_vehiculo_periodo.
- chk_valor_pago.
- chk_periodo_pago.
- fk_pago_vehiculo.
- fk_pago_cliente.
- fk_pago_operador.
- chk_fechas_mensualidad.

Resultado: 4 pruebas automatizadas aprobadas,
con 11 subcasos de rechazo SQL.

### 9.4. Controles financieros globales

| Control | Inconsistencias detectadas |
|---|---:|
| Pagos duplicados | 0 |
| Valores de pago inválidos | 0 |
| Períodos inválidos | 0 |
| Inconsistencias de cobertura | 0 |
| Discontinuidades entre períodos | 0 |
| Referencias inexistentes | 0 |
| Pagos asociados al cliente incorrecto | 0 |

Resultado: 7 de 7 controles aprobados.

## 10. Datos semilla especiales

El script de instalación incorpora tres escenarios
especiales de calendario.

Archivo independiente:

sql/semillas_calendario_ea3.sql

| Placa | Inicio | Día original | Corte al validar | Próximo corte |
|---|---|---:|---|---|
| CAL030 | 2025-01-30 | 30 | 2026-11-30 | 2026-12-30 |
| CAL031 | 2025-01-31 | 31 | 2026-11-30 | 2026-12-31 |
| CAL029 | 2024-02-29 | 29 | 2026-11-29 | 2026-12-29 |

Las fechas anteriores corresponden a la instalación
realizada el 21 de noviembre de 2026.

Los escenarios se generan de manera relativa a la fecha
de instalación y mantienen el día original de corte.

Se comprobó la continuidad de períodos, la vigencia,
las tarifas, las proyecciones y la idempotencia del
script independiente.

Resultado: 3 de 3 escenarios aprobados.

## 11. Validación de instalación limpia

Se creó una base independiente denominada:

autos_colombia_ea3_instalacion

Se ejecutó el script completo sql/autos_colombia.sql
y posteriormente scripts/seed_usuarios.py.

### 11.1. Inventario inicial observado

| Elemento | Cantidad |
|---|---:|
| Tablas | 7 |
| Clientes | 7 |
| Vehículos | 11 |
| Pagos | 83 |
| Celdas | 80 |
| Operadores y administradores | 4 |
| Estancias iniciales | 0 |
| Sesiones iniciales | 0 |

La cantidad de pagos dependerá de la fecha en que
se ejecute el script de instalación.

### 11.2. Comprobaciones realizadas

| ID | Comprobación | Resultado |
|---|---|---|
| IN-01 | Creación de base independiente | APROBADO |
| IN-02 | Ejecución del script principal | APROBADO |
| IN-03 | Creación de tablas | APROBADO |
| IN-04 | Inventario inicial | APROBADO |
| IN-05 | Semillas especiales | APROBADO |
| IN-06 | Consistencia de períodos | APROBADO |
| IN-07 | Configuración de usuarios | APROBADO |
| IN-08 | Autenticación | APROBADO |
| IN-09 | Flujo integrado | APROBADO |
| IN-10 | Conservación de base de pruebas | APROBADO |

Resultado: 10 de 10 comprobaciones aprobadas.

La instalación no modificó la base principal ni
la información controlada de la base de pruebas.

## 12. Ejecución de las pruebas

### 12.1. Pruebas unitarias

Desde la raíz del repositorio y con el entorno virtual
activado:

```powershell
Remove-Item Env:\RUN_E2E -ErrorAction SilentlyContinue
python -m unittest discover -s tests -v
```

Resultado esperado:

- 28 pruebas unitarias aprobadas.
- 39 pruebas de integración omitidas intencionalmente.

### 12.2. Suite completa

Es necesario disponer previamente de una base aislada
con el esquema EA3 y los usuarios de prueba configurados.

```powershell
$env:RUN_E2E = "1"
$env:DB_NAME = "autos_colombia_ea3_pruebas"

python -m unittest discover -s tests -v

Remove-Item Env:\RUN_E2E -ErrorAction SilentlyContinue
```

No ejecutar las pruebas de integración simultáneamente
con otras aplicaciones que modifiquen la base aislada.

La suite genera datos ficticios adicionales.

### 12.3. Ejecución por módulo

```powershell
$env:RUN_E2E = "1"
$env:DB_NAME = "autos_colombia_ea3_pruebas"

python -m unittest tests.test_integracion_pagos -v

python -m unittest tests.test_integracion_operaciones -v

python -m unittest tests.test_concurrencia_entradas -v

python -m unittest tests.test_regresion_iteraciones -v

python -m unittest tests.test_integridad_transaccional -v

Remove-Item Env:\RUN_E2E -ErrorAction SilentlyContinue
```

## 13. Regresión final y rendimiento

### 13.1. Ejecución conjunta de pruebas automatizadas

Fecha: 21 de noviembre de 2026.

Se ejecutó la suite completa de pruebas unitarias y de
integración mediante unittest, con RUN_E2E=1 y sobre
la base aislada autos_colombia_ea3_pruebas.

| Indicador | Resultado |
|---|---:|
| Pruebas unitarias | 28 |
| Pruebas de integración | 39 |
| Pruebas ejecutadas | 67 |
| Pruebas aprobadas | 67 |
| Pruebas fallidas | 0 |
| Pruebas omitidas | 0 |
| Duración total | 157.033 segundos |
| Porcentaje de aprobación | 100 % |

Resultado observado en la terminal:

```text
Ran 67 tests in 157.033s

OK
```

La ejecución conjunta confirma los resultados
previamente obtenidos por módulo.

Los fallos controlados de las pruebas PG-19.1 y
PG-19.2 produjeron las respuestas HTTP 500 esperadas
y la reversión de las escrituras correspondientes.

### 13.2. Metodología de rendimiento RNF-I3-11

Se realizaron 90 mediciones distribuidas en tres
endpoints del módulo de pagos.

- 30 consultas de mensualidades.
- 15 registros de primer pago.
- 15 registros de renovación.
- 30 consultas de historial.

Se utilizaron solicitudes autenticadas con los roles
OPERADOR y ADMINISTRADOR, Flask Test Client,
PostgreSQL real y perf_counter.

Se realizó un calentamiento previo no contabilizado.

Se excluyeron las operaciones de preparación de
vehículos, autenticación inicial y consultas previas
necesarias para confirmar las renovaciones.

El tiempo medido incluye la llamada a la infraestructura
de solicitudes de prueba y el procesamiento del backend.

El criterio de aceptación corresponde a un tiempo
individual estrictamente inferior a 3000 milisegundos.

### 13.3. Resultados estadísticos por endpoint

Todos los valores están expresados en milisegundos.

| Endpoint | Solicitudes | Mínimo | Promedio | Mediana | P95 | Máximo |
|---|---:|---:|---:|---:|---:|---:|
| GET /api/mensualidades/{placa} | 30 | 80.398 | 181.630 | 188.536 | 301.685 | 394.198 |
| POST /api/pagos | 30 | 82.152 | 169.244 | 187.409 | 297.861 | 302.666 |
| GET /api/vehiculos/{placa}/pagos | 30 | 80.969 | 149.486 | 138.297 | 292.778 | 293.406 |

El percentil 95 se calculó mediante el método
de rango más próximo (nearest rank).

### 13.4. Desglose del registro de pagos

| Operación | Solicitudes | Mínimo (ms) | Promedio (ms) | Mediana (ms) | P95 (ms) | Máximo (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Primer pago | 15 | 82.666 | 168.704 | 187.543 | 295.585 | 295.585 |
| Renovación | 15 | 82.152 | 169.784 | 186.743 | 302.666 | 302.666 |

Las 30 operaciones de registro de pagos devolvieron
HTTP 201 y conservaron la integridad de sus
respectivos períodos de cobertura.

### 13.5. Cumplimiento de RNF-I3-11

| Indicador | Resultado |
|---|---:|
| Solicitudes medidas | 90 |
| Solicitudes dentro del umbral | 90 |
| Solicitudes fuera del umbral | 0 |
| Tiempo máximo global | 394.198 ms |
| Umbral permitido | 3000 ms |
| Cumplimiento | 100 % |

Resultado RNF-I3-11: **APROBADO**.

Estas mediciones corresponden al entorno local de
backend evaluado. No incluyen latencia de red,
renderización de Next.js ni pruebas de carga masiva.

### 13.6. Integridad financiera definitiva

| Control | Inconsistencias detectadas |
|---|---:|
| Pagos duplicados | 0 |
| Valores inválidos | 0 |
| Períodos inválidos | 0 |
| Coberturas inconsistentes | 0 |
| Discontinuidades entre períodos | 0 |
| Referencias inexistentes | 0 |
| Cliente asociado incorrectamente | 0 |

Resultado: 7 de 7 controles aprobados.

### 13.7. Validación independiente de calendario

| Indicador | Resultado |
|---|---:|
| Vehículos con historial de pagos | 119 |
| Vehículos sin pagos | 12 |
| Períodos históricos verificados | 269 |
| Inconsistencias de calendario | 0 |

Cada período fue verificado mediante un cálculo
independiente del algoritmo del backend, conservando
el día original de inicio de la mensualidad.

### 13.8. Integridad operativa definitiva

| Indicador | Resultado |
|---|---:|
| Celdas disponibles para carros | 70 |
| Celdas disponibles para motos | 10 |
| Total de celdas disponibles | 80 |
| Estancias activas pendientes | 0 |
| Estancias históricas consistentes | 39 |

No se identificaron estancias incompletas ni
celdas ocupadas pendientes de liberación.

### 13.9. Inventario final del entorno de pruebas

| Entidad | Cantidad |
|---|---:|
| Clientes | 124 |
| Vehículos | 131 |
| Pagos | 269 |
| Celdas | 80 |
| Estancias | 39 |

Este inventario corresponde a la base aislada donde
se conservaron los registros ficticios creados
durante las pruebas.

No corresponde al inventario inicial de una
instalación nueva.

La base principal no fue intervenida y las consultas
de verificación final no modificaron registros.

### 13.10. Consolidado final de validación del backend

| Componente evaluado | Resultado |
|---|---|
| Plan académico PP-03 | 22/22 aprobados |
| Suite automatizada conjunta | 67/67 aprobadas |
| Rendimiento RNF-I3-11 | 90/90 dentro del umbral |
| Concurrencia de entradas | 6/6 aprobadas |
| Regresión de iteraciones anteriores | 6/6 aprobadas |
| Integridad transaccional | 9/9 aprobadas |
| Restricciones SQL | 11 subcasos satisfactorios |
| Controles financieros globales | 7/7 aprobados |
| Semillas especiales de calendario | 3/3 aprobadas |
| Instalación limpia | 10/10 comprobaciones |
| Períodos históricos | 269/269 verificados |

Los indicadores corresponden a diferentes niveles
de evaluación y no deben sumarse como pruebas
independientes.

Estado de validación técnica del backend: APROBADO.

La integración visual y funcional del frontend
se valida separadamente durante la fase final
del proyecto.

## 14. Conclusiones

La ejecución conjunta de las 67 pruebas automatizadas,
sin fallos ni omisiones, confirma el funcionamiento
satisfactorio del backend de la iteración 3 dentro
del alcance evaluado.

Los 22 casos académicos del plan PP-03 fueron
aprobados a nivel de backend, cubriendo las reglas
de negocio, operaciones de pago, seguridad,
concurrencia, atomicidad e integridad de datos.

Las pruebas de regresión demuestran que las
funcionalidades evaluadas de EA1 y EA2 se conservan
y se integran adecuadamente con el nuevo módulo.

El requerimiento RNF-I3-11 fue aprobado mediante
90 solicitudes medidas. El tiempo máximo observado
fue de 394.198 milisegundos, inferior al umbral
individual de 3000 milisegundos.

La verificación independiente de 269 períodos
históricos no identificó inconsistencias de
calendario, cobertura ni continuidad.

La instalación limpia confirma que el esquema,
los usuarios y los escenarios de demostración
pueden reproducirse en otro entorno sin depender
de la base utilizada durante el desarrollo.

En conclusión, el backend se encuentra validado
técnicamente para continuar con su integración
con el frontend.

La aceptación definitiva del sistema completo
requiere comprobar las interfaces, los flujos
integrados desde Next.js y las evidencias
académicas de la entrega final.
