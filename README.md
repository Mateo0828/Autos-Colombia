# Autos Colombia

Sistema de información para la gestión operativa del parqueadero **Autos Colombia**, desarrollado de forma incremental para la asignatura **Ingeniería de Software**.

El proyecto se construye por iteraciones sobre una misma base técnica y funcional:

- **Iteración 1 (EA1):** gestión de entrada y salida de vehículos.
- **Iteración 2 (EA2):** autenticación, perfiles, gestión de usuarios, registro y modificación de clientes/vehículos y gestión operativa de celdas.
- **Iteración 3 (EA3):** gestión de pagos y mensualidades: tarifas, fechas de corte, vigencia, historial de pagos y validación del ingreso según la mensualidad.

Cada iteración **amplía** a la anterior sin reemplazarla: la Iteración 2 protege las operaciones de la Iteración 1 con autenticación y roles, y la Iteración 3 agrega los pagos y calcula la vigencia de la mensualidad que la Iteración 1 solo consultaba.

Guía rápida para quien revisa el proyecto: instalar según §7 y §8, arrancar según §9, iniciar sesión con `admin` u `operador1`, y probar los pagos con las placas de la semilla (§14). Las funciones de pagos están descritas en §3A.

---

# 1. Evolución del proyecto

## 1.1 Iteración 1 — Entrada y salida de vehículos

La primera iteración resolvió el flujo operativo básico del parqueadero con un único actor funcional: el **Operador**.

El sistema permitió:

- consultar un vehículo por placa;
- mostrar sus datos y el cliente asociado;
- validar que el vehículo estuviera registrado;
- validar que la mensualidad estuviera `ACTIVA`;
- verificar que el vehículo no tuviera una estancia activa;
- consultar celdas disponibles según el tipo de vehículo;
- registrar la entrada;
- ocupar la celda asignada;
- consultar los vehículos actualmente dentro;
- registrar la salida;
- liberar la celda utilizada;
- consultar el estado general del parqueadero;
- consultar los operadores disponibles.

### Reglas principales de la Iteración 1

- El parqueadero funciona mediante mensualidades por vehículo.
- Un cliente puede tener varios vehículos.
- Cada vehículo posee su propio estado de mensualidad.
- Se permiten:
  - motocicletas;
  - automóviles;
  - camionetas.
- No se permiten camiones.
- El parqueadero cuenta con **80 celdas**:
  - 70 para automóviles y camionetas (`CARRO`);
  - 10 para motocicletas (`MOTO`).
- Una motocicleta solo puede usar una celda `MOTO`.
- Automóviles y camionetas utilizan celdas `CARRO`.
- Un vehículo no puede tener más de una estancia `ACTIVA`.
- Una celda no puede estar asignada simultáneamente a dos estancias activas.
- Una celda pasa a `OCUPADA` al registrar una entrada.
- Una celda vuelve a `DISPONIBLE` al registrar una salida.

### Arquitectura entregada en EA1

Desde la primera iteración se utiliza una arquitectura en capas:

```text
Frontend Next.js
      ↓
Flask Routes
      ↓
Services
      ↓
Repositories
      ↓
database.py
      ↓
PostgreSQL
```

La Iteración 2 conserva esta arquitectura y agrega componentes nuevos sin reemplazar las capas existentes.

---

## 1.2 Correcciones incorporadas después de EA1

Antes de iniciar la Iteración 2 se aplicaron las correcciones derivadas de la retroalimentación de la primera evidencia.

### Relación Operador — Estancia

Cada estancia conserva:

- un operador de entrada obligatorio;
- un operador de salida opcional mientras la estancia está activa;
- una fecha de salida opcional mientras la estancia está activa.

Esto permite que el operador que registra la salida sea diferente del operador que registró la entrada.

### Restricción `chk_cierre_estancia`

La base de datos garantiza que una estancia sea coherente con su estado:

```sql
CONSTRAINT chk_cierre_estancia
CHECK (
    (
        estado = 'ACTIVA'
        AND fecha_hora_salida IS NULL
        AND id_operador_salida IS NULL
    )
    OR
    (
        estado = 'FINALIZADA'
        AND fecha_hora_salida IS NOT NULL
        AND id_operador_salida IS NOT NULL
    )
)
```

Por tanto:

- una estancia `ACTIVA` no puede tener fecha ni operador de salida;
- una estancia `FINALIZADA` debe tener ambos datos.

También se mantienen:

- `chk_fecha_salida`;
- `chk_estado_estancia`;
- índice único parcial por vehículo con estancia activa;
- índice único parcial por celda con estancia activa.

### Pruebas de integridad P-14 a P-19

El archivo:

```text
sql/pruebas_integridad_estancia.sql
```

verifica:

```text
P-14 → ACTIVA válida: permitida
P-15 → FINALIZADA sin fecha: rechazada
P-16 → FINALIZADA sin operador: rechazada
P-17 → ACTIVA con fecha: rechazada
P-18 → ACTIVA con operador: rechazada
P-19 → FINALIZADA válida: permitida
```

Las pruebas se ejecutan dentro de una transacción y finalizan con `ROLLBACK`, por lo que no dejan datos artificiales en la base.

---

# 2. Iteración 2 — Usuarios, sesiones, clientes/vehículos y celdas

La segunda iteración amplía el sistema existente con autenticación, perfiles y nuevas funciones administrativas.

## 2.1 Perfiles

Existen dos perfiles:

```text
ADMINISTRADOR
OPERADOR
```

El **ADMINISTRADOR hereda todas las funciones del OPERADOR**.

### OPERADOR

Puede:

- iniciar y cerrar sesión;
- consultar y validar placas;
- registrar un cliente y un vehículo cuando la placa no existe;
- consultar celdas disponibles;
- registrar entradas;
- registrar salidas;
- consultar vehículos dentro;
- consultar el estado general del parqueadero.

### ADMINISTRADOR

Puede realizar todo lo anterior y además:

- consultar usuarios;
- crear operadores y administradores;
- modificar usuarios;
- activar o inactivar usuarios;
- consultar clientes;
- modificar clientes;
- modificar vehículos;
- consultar las 80 celdas;
- filtrar celdas;
- deshabilitar celdas;
- habilitar celdas.

---

## 2.2 Autenticación y sesiones

Todos los usuarios del sistema inician sesión con:

- nombre de usuario;
- contraseña.

La autenticación utiliza un token Bearer:

```http
Authorization: Bearer <token>
```

Características implementadas:

- token opaco generado en el backend;
- almacenamiento únicamente del hash SHA-256 del token;
- duración de sesión de 8 horas;
- varias sesiones simultáneas por usuario;
- cierre de sesión con revocación efectiva;
- revocación de todas las sesiones al inactivar un usuario;
- contraseña almacenada mediante hash de Werkzeug;
- mensaje genérico ante credenciales incorrectas;
- control de rol en las rutas protegidas.

Un usuario `INACTIVO` no puede iniciar sesión, pero su historial permanece conservado.

---

## 2.3 Gestión de usuarios

La tabla histórica `operador` se amplió para funcionar también como cuenta de acceso.

Además de `id_operador` y `nombre`, ahora contiene:

- `usuario`;
- `password_hash`;
- `rol`;
- `estado`;
- `fecha_creacion`.

Esto permite conservar las claves foráneas históricas de `estancia`.

### Reglas

- el `usuario` de acceso es único;
- el `usuario` se normaliza en minúsculas;
- el nombre de acceso no se modifica después de crear la cuenta;
- una contraseña debe tener mínimo 8 caracteres;
- el retiro es lógico: `INACTIVO`;
- al inactivar un usuario se revocan sus sesiones;
- un administrador no puede inactivarse a sí mismo;
- siempre debe permanecer al menos un administrador activo;
- las respuestas nunca exponen `password` ni `password_hash`.

---

## 2.4 Registro y modificación de clientes y vehículos

Cuando una placa no está registrada, tanto OPERADOR como ADMINISTRADOR pueden registrar:

- cliente;
- vehículo.

El registro se realiza en una sola transacción.

Si el documento del cliente ya existe:

- no se crea un cliente duplicado;
- el vehículo nuevo se asocia al cliente existente.

El vehículo se crea con:

```text
estado_mensualidad = ACTIVA
```

Después del registro:

- el OPERADOR no puede modificar cliente ni vehículo;
- solo el ADMINISTRADOR puede modificar esos datos.

Si un vehículo tiene una estancia activa, no puede cambiarse su tipo mientras permanezca dentro del parqueadero.

---

## 2.5 Gestión de celdas

La Iteración 1 utilizaba:

```text
DISPONIBLE
OCUPADA
```

La Iteración 2 agrega:

```text
FUERA_DE_SERVICIO
```

Por tanto, los estados finales son:

```text
DISPONIBLE
OCUPADA
FUERA_DE_SERVICIO
```

### Reglas

- una celda `DISPONIBLE` puede pasar a `FUERA_DE_SERVICIO`;
- una celda `OCUPADA` no puede deshabilitarse;
- una celda que ya está `FUERA_DE_SERVICIO` no puede deshabilitarse nuevamente;
- solo una celda `FUERA_DE_SERVICIO` puede habilitarse;
- una celda fuera de servicio no aparece en las opciones disponibles para registrar una entrada;
- las operaciones sensibles utilizan `SELECT ... FOR UPDATE` para evitar inconsistencias concurrentes.

---

# 3. Cambio principal de EA1 a EA2: operador obtenido desde la sesión

En la Iteración 1 el frontend enviaba manualmente un `id_operador` en entrada y salida.

En la Iteración 2 este comportamiento cambia.

## Entrada actual

```http
POST /api/entradas
```

Body:

```json
{
  "placa": "ABC123",
  "codigo_celda": "C01"
}
```

El backend obtiene automáticamente:

```text
id_operador = usuario autenticado
```

desde el token de sesión.

## Salida actual

```http
POST /api/salidas
```

Body:

```json
{
  "placa": "ABC123"
}
```

El backend vuelve a obtener el responsable desde la sesión.

Esto mejora la trazabilidad y elimina la selección manual del operador.

El operador de salida puede ser diferente del operador de entrada; ambos quedan almacenados en la estancia.

---

# 3A. Iteración 3 — Gestión de pagos y mensualidades

La tercera iteración agrega el registro de pagos de mensualidad y calcula, a partir de ellos, la vigencia de cada vehículo. Conserva la autenticación, los roles y las operaciones de las iteraciones anteriores.

## 3A.1 Reglas de negocio

- **Tarifas fijas** por mes: automóvil y camioneta `$250.000`; moto `$100.000`. El valor lo calcula siempre el servidor; el cliente no lo envía.
- **Un pago cubre un mes.** El primer pago define la fecha de inicio y el día de corte; las renovaciones empiezan en la fecha de corte anterior.
- **Día de corte.** El corte de cada período se calcula desde el primer pago y conserva el día original; en meses cortos se ajusta al último día del mes (por ejemplo, el día 31 cae el 30 de noviembre y vuelve al 31 de diciembre).
- **Vigencia.** La mensualidad está `ACTIVA` si la fecha de hoy es anterior a la fecha de corte; el mismo día del corte ya es `INACTIVA`. El estado se deriva de los pagos y no se edita a mano (modificar un vehículo no permite cambiarlo).
- **Vehículos nuevos** quedan `INACTIVA` hasta registrar su primer pago.
- **Renovación tardía o anticipada.** Se permiten pagos antes o después del corte; si tras el pago la mensualidad sigue vencida, la respuesta trae una `advertencia`.
- **Pagos inmutables:** no se editan ni se eliminan.
- **Ingreso.** Solo entra un vehículo con mensualidad `ACTIVA`; la salida nunca se bloquea por la mensualidad.
- **Concurrencia.** El pago incluye `corte_esperado`; si otra persona ya pagó, el servidor responde `409` y no duplica el período (bloqueo de fila y restricción única por vehículo y período).
- **Zona horaria de negocio:** America/Bogota.

## 3A.2 Endpoints nuevos y modificados

Todos requieren `Authorization: Bearer <token>` y rol `ADMINISTRADOR` u `OPERADOR`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/mensualidades/{placa}` | Estado de la mensualidad y `proximo_pago` (tipo, valor, período, corte esperado, estado resultante, advertencia). Parámetro opcional `?fecha_pago=AAAA-MM-DD` (no puede ser futura). |
| POST | `/api/pagos` | Registra un pago. Cuerpo exacto: `{placa, fecha_pago, corte_esperado}` (`corte_esperado` es `null` en el primer pago). Campos adicionales (por ejemplo `valor`) devuelven `422`. |
| GET | `/api/vehiculos/{placa}/pagos` | Historial de pagos, del más reciente al más antiguo, con `registrado_por` (`id_operador`, `usuario`, `nombre`). |
| GET | `/api/vehiculos/{placa}/validar-ingreso` | Se amplía con `codigo_motivo`: `VEHICULO_NO_REGISTRADO`, `SIN_PRIMER_PAGO`, `MENSUALIDAD_VENCIDA`, `ESTANCIA_ACTIVA` o `INGRESO_PERMITIDO`. |
| POST | `/api/entradas` | Ahora rechaza con `400` el ingreso de un vehículo con mensualidad vencida o sin primer pago. |

Códigos HTTP de la Iteración 3: `200`, `201` (pago creado), `400` (ingreso rechazado), `401`, `403`, `404` (placa inexistente), `409` (el corte cambió: consultar de nuevo) y `422` (datos inválidos o campos no autorizados).

## 3A.3 Frontend de la Iteración 3

- Pantalla `/pagos`: consulta de placa, tarjeta de mensualidad (estado, inicio, día de corte, fecha de corte y número de pagos), ventana de confirmación con valor, nueva fecha de corte, estado resultante y advertencia, resultado del pago e historial.
- Pagos anticipados, renovación tardía, conflicto `409` y fecha futura (`422`) se informan en pantalla.
- `/entrada` decide según `codigo_motivo` y ofrece «Registrar primer pago» o «Registrar pago de renovación».
- `/registro` y `/clientes` muestran la mensualidad como calculada (sin selector de estado).

## 3A.4 Base de datos de la Iteración 3

- `sql/autos_colombia.sql` (instalación limpia) incluye la tabla `pago`, las columnas `fecha_inicio_mensualidad` y `fecha_corte` de `vehiculo` y los pagos de demostración con fechas relativas a hoy.
- `sql/semillas_calendario_ea3.sql` agrega los vehículos `CAL030`, `CAL031` y `CAL029` (día de corte 30, 31 y 29 de febrero).
- `sql/migracion_iteracion3.sql` migra una base de la Iteración 2 conservando sus datos (no inventa pagos históricos).
- `sql/pruebas_integridad_pago.sql` verifica las restricciones de la tabla de pagos.

---

# 4. Alcance actual y funcionalidades fuera de alcance

## Incluido en Iteración 2

- autenticación;
- cierre de sesión;
- roles;
- sesiones simultáneas;
- gestión de usuarios;
- registro de cliente y vehículo;
- modificación de clientes y vehículos;
- gestión de celdas;
- entrada y salida heredadas de EA1;
- consultas de EA1;
- control de permisos;
- integridad y concurrencia.

## Incluido en Iteración 3

- consulta de mensualidad con proyección del próximo pago;
- registro de pagos (primer pago, renovación anticipada y renovación tardía);
- cálculo de fechas de corte con conservación del día original;
- vigencia de la mensualidad derivada de los pagos;
- historial de pagos por vehículo;
- validación del ingreso según la mensualidad (con `codigo_motivo`);
- control de concurrencia con `corte_esperado`;
- pruebas automatizadas del backend y pruebas de navegador del frontend.

## Fuera de alcance

No forman parte de la entrega actual:

- facturación;
- cartera, recargos y anulación o edición de pagos;
- reportes de ingresos;
- novedades;
- reasignación de celdas como funcionalidad de entrega.

Existe código heredado para reasignación de celda:

```http
PUT /api/estancias/{placa}/reasignar-celda
```

pero **no forma parte del alcance de EA2 ni de EA3 ni debe integrarse al frontend**.

---

# 5. Tecnologías

## Backend

- Python 3.12 o superior (verificado con 3.13).
- Flask.
- Flask-CORS.
- Werkzeug.
- Psycopg 3.
- python-dotenv.

## Base de datos

- PostgreSQL 14 o superior.
- pgAdmin 4 opcional.

## Frontend

- Node.js 18.18 o superior (probado con 20.11 y 20.14).
- Next.js 15.5 (App Router), React 19.
- TypeScript.
- Tailwind CSS 4.
- lucide-react.
- Playwright (pruebas de navegador, opcional).

Pruebas del backend: `unittest` de la biblioteca estándar de Python (sin dependencias adicionales).

## Control de versiones

- Git.
- GitHub.

Repositorio:

```text
https://github.com/Mateo0828/Autos-Colombia
```

`main` contiene el sistema completo de las tres iteraciones (backend y frontend). Para ejecutarlo solo se necesita `main`.

---

# 6. Estructura del proyecto

```text
Autos Colombia/
│
├── app/
│   ├── repositories/
│   │   ├── celda_repository.py
│   │   ├── cliente_repository.py
│   │   ├── estancia_repository.py
│   │   ├── operador_repository.py
│   │   ├── pago_repository.py
│   │   ├── registro_repository.py
│   │   ├── sesion_repository.py
│   │   └── vehiculo_repository.py
│   │
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── celda_routes.py
│   │   ├── cliente_routes.py
│   │   ├── consulta_routes.py
│   │   ├── entrada_routes.py
│   │   ├── operador_routes.py
│   │   ├── pago_routes.py
│   │   ├── reasignacion_routes.py
│   │   ├── registro_routes.py
│   │   ├── salida_routes.py
│   │   ├── usuario_routes.py
│   │   └── vehiculo_routes.py
│   │
│   ├── services/              (incluye mensualidad_service, pago_service y validacion_service)
│   ├── auth_middleware.py
│   ├── database.py
│   └── __init__.py
│
├── frontend/                  (Next.js: pantallas de EA1, EA2 y EA3)
│   ├── src/app/               (rutas: login, entrada, salida, vehiculos-dentro,
│   │                           estado, usuarios, registro, clientes, celdas, pagos)
│   ├── src/components/
│   ├── src/lib/api.ts         (cliente de la API)
│   ├── src/types/
│   ├── e2e/                   (pruebas Playwright)
│   └── package.json
│
├── docs/
│   └── RESULTADOS_PRUEBAS_EA3.md
│
├── informes/
│   ├── 2026-11-11_backend_B08.md
│   └── capturas/
│       └── pruebas_i2_backend.txt
│
├── tests/                     (pruebas automatizadas de la Iteración 3)
│
├── scripts/
│   ├── seed_usuarios.py
│   └── pruebas_i2.sh
│
├── sql/
│   ├── autos_colombia.sql
│   ├── migracion_iteracion2.sql
│   ├── migracion_iteracion3.sql
│   ├── semillas_calendario_ea3.sql
│   ├── pruebas_integridad_estancia.sql
│   └── pruebas_integridad_pago.sql
│
├── .env.example
├── README.md
├── requirements.txt
└── run.py
```

---

# 7. Instalación del backend

## 7.1 Clonar el repositorio

```bash
git clone https://github.com/Mateo0828/Autos-Colombia.git
cd Autos-Colombia
```

La rama `main` contiene las tres iteraciones (backend y frontend, hasta la Iteración 3). No hace falta cambiar de rama: quien revise el proyecto clona el repositorio y trabaja sobre `main`.

---

## 7.2 Instalar PostgreSQL y crear la base

### Linux / WSL (Ubuntu)

Instalar y arrancar PostgreSQL (si ya está instalado, solo el segundo comando; hay que repetirlo cada vez que se reinicia WSL):

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start
```

Definir la contraseña del usuario `postgres` (la misma que irá en `DB_PASSWORD` del `.env`) y crear la base:

```bash
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'TU_CONTRASENA_POSTGRES';"
sudo -u postgres psql -c "CREATE DATABASE autos_colombia;"
```

### Windows

Instalar PostgreSQL desde el instalador oficial (el servicio queda iniciado) y crear la base `autos_colombia` con pgAdmin o con `CREATE DATABASE autos_colombia;` desde `psql`.

> **Importante (Linux/WSL):** el comando `psql -U postgres -d autos_colombia ...` (sin `-h`) usa el socket local y falla con `Peer authentication failed`. Todos los comandos `psql` de este README se ejecutan por TCP (`-h localhost`) con la contraseña del `.env`.

---

## 7.3 Crear entorno virtual

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Linux / WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 7.4 Configurar `.env`

Crear `.env` tomando como base `.env.example`.

Variables de PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autos_colombia
DB_USER=postgres
DB_PASSWORD=TU_CONTRASENA_POSTGRES
```

Para los usuarios locales de demostración y pruebas:

```env
E2E_ADMIN_PASSWORD=CONTRASENA_LOCAL_ADMIN
E2E_OPERADOR1_PASSWORD=CONTRASENA_LOCAL_OPERADOR1
E2E_OPERADOR2_PASSWORD=CONTRASENA_LOCAL_OPERADOR2
E2E_OPERADOR3_PASSWORD=CONTRASENA_LOCAL_OPERADOR3
```

Son contraseñas de demostración, solo para uso local: elija usted los valores (mínimo 8 caracteres). Con ellas inicia sesión en la aplicación:

| Usuario | Rol | Variable del `.env` con su contraseña |
|---|---|---|
| `admin` | ADMINISTRADOR | `E2E_ADMIN_PASSWORD` |
| `operador1` | OPERADOR | `E2E_OPERADOR1_PASSWORD` |
| `operador2` | OPERADOR | `E2E_OPERADOR2_PASSWORD` |
| `operador3` | OPERADOR | `E2E_OPERADOR3_PASSWORD` |

La contraseña de cada usuario es la que usted escribió en el `.env` antes de ejecutar `scripts/seed_usuarios.py`. Si cambia el valor en el `.env`, vuelva a ejecutar el seed.

Estas contraseñas:

- son únicamente de desarrollo;
- no se escriben en SQL;
- no deben subirse al repositorio;
- se convierten a hash mediante `seed_usuarios.py`.

---

# 8. Base de datos

## 8.1 Instalación limpia

Desde la raíz del repositorio, con el `.env` ya creado y PostgreSQL iniciado.

Linux / WSL / Git Bash:

```bash
set -a; source .env; set +a
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f sql/autos_colombia.sql
```

Windows PowerShell (equivalente; no probado en este entorno):

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)$') { Set-Item -Path "env:$($Matches[1])" -Value $Matches[2] } }
$env:PGPASSWORD = $env:DB_PASSWORD
psql -h $env:DB_HOST -p $env:DB_PORT -U $env:DB_USER -d $env:DB_NAME -v ON_ERROR_STOP=1 -f sql/autos_colombia.sql
```

Si la base no existe (error `database "autos_colombia" does not exist`), créela primero:

```bash
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE autos_colombia;"
```

El script:

- elimina las tablas existentes;
- crea el esquema completo;
- conserva las restricciones de EA1;
- incorpora usuarios y sesiones de EA2;
- incorpora `FUERA_DE_SERVICIO`;
- incorpora la tabla de pagos y las columnas de mensualidad de la Iteración 3;
- carga los datos semilla, incluidos pagos de demostración con fechas relativas a hoy.

El script anterior ya incluye los vehículos de calendario (`CAL030`, `CAL031` y `CAL029`). `sql/semillas_calendario_ea3.sql` es idempotente: puede ejecutarse para reponerlos si se borraron, pero no es obligatorio después de `autos_colombia.sql`.

Después, con el entorno virtual activo (§7.3), ejecutar:

```bash
python scripts/seed_usuarios.py
```

para generar los hashes de contraseña a partir de las variables `E2E_*_PASSWORD` del `.env`. Este mismo par de pasos (SQL y seed) deja la base limpia de nuevo cuando se necesite.

> `autos_colombia.sql` elimina y recrea las tablas. No debe ejecutarse sobre una base con información que se quiera conservar.

---

## 8.2 Migración desde una base de Iteración 1 o 2

Para conservar una base existente:

```bash
set -a; source .env; set +a
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/migracion_iteracion2.sql
```

Si la base es de la Iteración 2, aplique en su lugar (o después) `sql/migracion_iteracion3.sql`, que agrega pagos y mensualidades sin borrar datos:

```bash
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/migracion_iteracion3.sql
```

Después:

```bash
python scripts/seed_usuarios.py
```

La migración extiende el esquema sin reemplazar las relaciones históricas de `estancia`.

---

# 9. Ejecutar el backend

Con el entorno activo:

```bash
python run.py
```

Servidor:

```text
http://127.0.0.1:5000
```

Prueba de conexión con PostgreSQL:

```http
GET /api/db/test
```

```bash
curl http://127.0.0.1:5000/api/db/test
```

Debe responder `{"estado":"ok", ...}`. Si falla, vea «Solución de problemas» (§22).

## 9.1 Orden de arranque del sistema completo

1. **PostgreSQL** iniciado (WSL: `sudo service postgresql start`).
2. **Backend:** base cargada y sembrada (§8.1) y `python run.py` en `127.0.0.1:5000`.
3. **Frontend:** `npm run dev` en `localhost:3000` (siguiente sección).

## 9.2 Ejecutar el frontend

Requisitos: Node.js 18.18 o superior y `npm`. El backend debe estar corriendo.

```bash
cd frontend
npm install
```

Crear `frontend/.env.local` (no se versiona) con:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
```

> **No definir `NEXT_PUBLIC_USE_MOCK`.** Con `NEXT_PUBLIC_USE_MOCK=true` el frontend usa datos simulados y no consulta el backend.

Iniciar:

```bash
npm run dev
```

Abrir `http://localhost:3000` e iniciar sesión con `admin` o `operador1` y la contraseña definida en el `.env` del backend. Si el puerto 3000 está ocupado, Next usa 3001; el CORS del backend está abierto en desarrollo, así que funciona igual. Si el frontend se ejecuta en Windows y el backend en WSL2, `127.0.0.1:5000` se reenvía automáticamente.

Para una compilación de producción: `npm run build` y `npm start`.

---

# 10. API actual

Excepto el login y los endpoints de diagnóstico, las funciones operativas utilizan:

```http
Authorization: Bearer <token>
```

## 10.1 Autenticación

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/api/auth/login` | Público |
| GET | `/api/auth/me` | ADMINISTRADOR / OPERADOR |
| POST | `/api/auth/logout` | ADMINISTRADOR / OPERADOR |

### Login

```json
{
  "usuario": "operador1",
  "password": "..."
}
```

Respuesta:

```json
{
  "estado": "ok",
  "token": "...",
  "expira": "...",
  "usuario": {
    "id_operador": 1,
    "nombre": "Operador Mañana",
    "usuario": "operador1",
    "rol": "OPERADOR"
  }
}
```

---

## 10.2 Gestión de usuarios

Solo ADMINISTRADOR.

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/usuarios` | Consultar usuarios |
| POST | `/api/usuarios` | Crear usuario |
| PUT | `/api/usuarios/{id}` | Modificar usuario |
| PATCH | `/api/usuarios/{id}/estado` | Activar / inactivar |

---

## 10.3 Clientes y vehículos

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/api/registros` | ADMINISTRADOR / OPERADOR |
| GET | `/api/clientes/{id}` | ADMINISTRADOR |
| PUT | `/api/clientes/{id}` | ADMINISTRADOR |
| PUT | `/api/vehiculos/{placa}` | ADMINISTRADOR |

### Registrar cliente y vehículo

```json
{
  "documento": "10000001",
  "nombre": "Cliente Ejemplo",
  "placa": "ABC999",
  "marca": "Mazda",
  "color": "Rojo",
  "tipo_vehiculo": "AUTOMOVIL"
}
```

---

## 10.4 Administración de celdas

Solo ADMINISTRADOR.

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/celdas` | Listar las 80 celdas |
| PATCH | `/api/celdas/{codigo}/deshabilitar` | Poner fuera de servicio |
| PATCH | `/api/celdas/{codigo}/habilitar` | Volver a disponible |

Filtros:

```text
/api/celdas?estado=DISPONIBLE
/api/celdas?estado=FUERA_DE_SERVICIO
/api/celdas?tipo=MOTO
/api/celdas?q=C07
```

---

# 11. Operaciones de EA1 que continúan vigentes en EA2

Las funciones centrales de entrada y salida no fueron reemplazadas; fueron protegidas y adaptadas a la sesión.

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/api/vehiculos/{placa}` | ADMINISTRADOR / OPERADOR |
| GET | `/api/vehiculos/{placa}/validar-ingreso` | ADMINISTRADOR / OPERADOR |
| GET | `/api/celdas/disponibles?tipo_vehiculo=...` | ADMINISTRADOR / OPERADOR |
| POST | `/api/entradas` | ADMINISTRADOR / OPERADOR |
| POST | `/api/salidas` | ADMINISTRADOR / OPERADOR |
| GET | `/api/estancias/activas` | ADMINISTRADOR / OPERADOR |
| GET | `/api/parqueadero/estado` | ADMINISTRADOR / OPERADOR |

## Validar ingreso

```http
GET /api/vehiculos/ABC123/validar-ingreso
```

Comprueba:

- vehículo registrado;
- mensualidad activa;
- ausencia de estancia activa.

Si una placa no existe, devuelve `vehiculo: null` y permite que el frontend ofrezca el registro del cliente y vehículo.

## Celdas disponibles

```http
GET /api/celdas/disponibles?tipo_vehiculo=AUTOMOVIL
```

Tipos admitidos:

```text
AUTOMOVIL
CAMIONETA
MOTO
```

Solo devuelve celdas `DISPONIBLE`; las `OCUPADA` y `FUERA_DE_SERVICIO` quedan excluidas.

## Entrada

```http
POST /api/entradas
```

```json
{
  "placa": "ABC123",
  "codigo_celda": "C01"
}
```

No recibe `id_operador`.

## Salida

```http
POST /api/salidas
```

```json
{
  "placa": "ABC123"
}
```

No recibe `id_operador`.

## Vehículos dentro

```http
GET /api/estancias/activas
```

Retorna las estancias `ACTIVA` con:

- vehículo;
- celda;
- fecha de entrada;
- operador de entrada.

## Estado del parqueadero

```http
GET /api/parqueadero/estado
```

Incluye:

- total de celdas;
- disponibles;
- ocupadas;
- fuera de servicio;
- detalle para `CARRO`;
- detalle para `MOTO`;
- vehículos dentro.

---

# 12. Endpoint heredado de operadores

```http
GET /api/operadores
```

En EA1 era utilizado por el frontend para seleccionar manualmente el operador responsable.

En EA2:

- ya no debe utilizarse para entrada o salida;
- se conserva temporalmente por compatibilidad;
- está restringido al ADMINISTRADOR.

---

# 13. Códigos HTTP

## Iteración 2 y 3

```text
200 → operación exitosa
201 → recurso creado
401 → sesión inexistente, inválida, vencida o revocada
403 → rol insuficiente
404 → recurso inexistente
409 → conflicto de negocio o estado
422 → datos inválidos
500 → error interno
```

Los endpoints heredados de EA1 conservan sus validaciones históricas con `400` cuando corresponde. En la Iteración 3, un ingreso con mensualidad vencida también responde `400`, y un pago con `corte_esperado` desactualizado responde `409`.

Todas las respuestas utilizan JSON con:

```json
{
  "estado": "ok"
}
```

o:

```json
{
  "estado": "error",
  "mensaje": "..."
}
```

---

# 14. Datos semilla

La instalación limpia crea:

## Usuarios

```text
admin       → ADMINISTRADOR
operador1   → OPERADOR
operador2   → OPERADOR
operador3   → OPERADOR
```

Las contraseñas no se almacenan en texto plano en SQL.

## Vehículos

Los pagos y las fechas de corte de la semilla se calculan con relación a la fecha de hoy (America/Bogota), por lo que el estado de cada placa depende del día en que se cargue la base.

| Placa | Situación al cargar la base |
|---|---|
| `ABC123`, `DEF456`, `GHI789`, `MOT01A` | Mensualidad vigente, con 1 pago (iniciado hace 10, 25, 15 y 12 días) |
| `JKL321` | Mensualidad vencida (corte hace unos días): rechazo de ingreso y renovación tardía |
| `XYZ987`, `MOT02A` | Sin primer pago: permiten probar el primer pago de automóvil y de moto |
| `COR001` | Fecha de corte igual a hoy: `INACTIVA` por la regla del día de corte |
| `CAL030`, `CAL031`, `CAL029` | Día original de corte 30, 31 y 29 de febrero, con 22, 22 y 33 pagos: prueban el ajuste de meses cortos y años bisiestos |

Para probar la `advertencia` de renovación tardía, registre una placa nueva con un primer pago de hace más de un mes: tras el pago la mensualidad sigue `INACTIVA`.

## Celdas

```text
C01 - C70 → CARRO
M01 - M10 → MOTO
```

Estado inicial:

```text
80 disponibles
0 ocupadas
0 fuera de servicio
0 vehículos dentro
```

---

# 15. Pruebas del backend

## 15.1 Iteración 1

La Iteración 1 fue verificada mediante pruebas de:

- consulta de placas;
- mensualidad activa/inactiva;
- celdas disponibles;
- entrada;
- rechazo de entrada duplicada;
- rechazo de celda ocupada;
- compatibilidad de tipo de vehículo;
- vehículos dentro;
- salida;
- estado del parqueadero;
- integridad de estancia.

Las correcciones de integridad se conservan y vuelven a probar en EA2.

---

## 15.2 Iteración 2 — suite automatizada

Archivo:

```text
scripts/pruebas_i2.sh
```

El script ejecuta **28 casos** distribuidos en:

- US-01 a US-13: usuarios y sesiones;
- PE-01 a PE-04: permisos;
- CV-01 a CV-03: clientes y vehículos;
- CE-01 a CE-06: celdas y concurrencia;
- RG-01 a RG-02: regresión de EA1.

Resultado validado:

```text
PASS: 28
FAIL: 0
TOTAL: 28
```

Evidencia:

```text
informes/capturas/pruebas_i2_backend.txt
```

Informe:

```text
informes/2026-11-11_backend_B08.md
```

### Advertencia

`scripts/pruebas_i2.sh` recrea la base al inicio y al final para asegurar una ejecución repetible.

No debe ejecutarse sobre una base que contenga información que se quiera conservar.

### Windows con Git Bash

```powershell
& "C:\Program Files\Git\bin\bash.exe" ./scripts/pruebas_i2.sh
```

Guardar evidencia:

```powershell
New-Item -ItemType Directory -Force .\informes\capturas | Out-Null

& "C:\Program Files\Git\bin\bash.exe" ./scripts/pruebas_i2.sh 2>&1 |
    Tee-Object -FilePath .\informes\capturas\pruebas_i2_backend.txt
```

### Linux / WSL

Con el entorno virtual activo (el script usa el `python` del PATH), PostgreSQL iniciado y el backend corriendo:

```bash
source .venv/bin/activate
bash scripts/pruebas_i2.sh
```

Al terminar, la base queda recreada y sembrada con las contraseñas del `.env`.

---

## 15.3 Iteración 3 — suite automatizada

Directorio:

```text
tests/
```

Resultado validado (rama `feature/i3-backend`, commit `f4e988e`): **67 pruebas aprobadas** (28 unitarias y 39 de integración) y **22 de 22 casos** del plan de pruebas PP-03. El detalle y la correspondencia con los casos PG-01 a PG-22 están en:

```text
docs/RESULTADOS_PRUEBAS_EA3.md
```

Archivos principales: `test_mensualidad_service.py` y `test_proyeccion_pago.py` (reglas, sin base de datos); `test_integracion_pagos.py`, `test_integracion_operaciones.py`, `test_concurrencia_entradas.py`, `test_integridad_transaccional.py` y `test_regresion_iteraciones.py` (con base de datos).

Pruebas unitarias (no necesitan base de datos), con el entorno virtual activo:

```bash
python -m unittest discover -s tests -v
```

Resultado esperado: «Ran 67 tests … OK (skipped=39)», es decir, 28 aprobadas y 39 omitidas (las de integración).

Suite completa (usa una **base aislada**, nunca la principal). Primero cree y cargue esa base:

```bash
set -a; source .env; set +a
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE autos_colombia_ea3_pruebas;"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d autos_colombia_ea3_pruebas -v ON_ERROR_STOP=1 -f sql/autos_colombia.sql
DB_NAME=autos_colombia_ea3_pruebas python scripts/seed_usuarios.py
```

Después ejecute la suite:

```bash
export RUN_E2E=1
export DB_NAME=autos_colombia_ea3_pruebas
python -m unittest discover -s tests -v
unset RUN_E2E
```

En Windows PowerShell: `$env:RUN_E2E = "1"` y `$env:DB_NAME = "autos_colombia_ea3_pruebas"`. Resultado esperado con `RUN_E2E=1`: 67 pruebas aprobadas.

La suite deja datos de prueba en la base aislada; para repetirla, recárguela antes (`autos_colombia.sql` y el seed con esa `DB_NAME`).

Frontend: las pruebas de navegador de la Iteración 3 están en `frontend/e2e/` (`iteration3.spec.ts` en modo mock e `iteration3.real.spec.ts` contra el backend real); resultado: 12 de 12 aprobadas contra el backend real y 26 de 26 en modo mock. Ejecución del frontend en modo mock: `cd frontend && npx playwright install chromium && npx playwright test`. Para las pruebas contra el backend real, con la API en marcha, defina `E2E_MODE=real`, `NEXT_PUBLIC_API_URL=http://127.0.0.1:5000`, `NEXT_PUBLIC_USE_MOCK=false` y las contraseñas `E2E_*` del `.env`, y ejecute `npx playwright test e2e/iteration3.real.spec.ts`. La regresión de la Iteración 2 en modo real (`e2e/iteration2.spec.ts`) crea usuarios y modifica celdas: úsela solo sobre una base de pruebas y recárguela después.

---

# 16. Concurrencia

La gestión de celdas utiliza bloqueo de fila con:

```sql
SELECT ... FOR UPDATE
```

Se comprobó que dos operaciones concurrentes sobre la misma celda no dejan un estado inconsistente.

Los pagos usan el mismo principio: el servidor bloquea la fila del vehículo y compara `corte_esperado`; si dos personas pagan a la vez, solo una prospera y la otra recibe `409` sin duplicar el período (además existe la restricción única `UNIQUE(id_vehiculo, periodo_inicio)`).

En la prueba automatizada:

- solo una operación prospera;
- la otra recibe un conflicto;
- la celda termina en un único estado coherente.

---

# 17. Seguridad

- Las contraseñas se almacenan mediante hash.
- Las respuestas no exponen contraseñas ni hashes.
- El token original no se guarda en PostgreSQL.
- Solo se almacena el hash SHA-256 del token.
- Las sesiones tienen vencimiento.
- El logout revoca el token.
- Inactivar un usuario revoca sus sesiones.
- Los permisos se verifican también en el servidor.
- `.env` está excluido de Git.
- No deben versionarse contraseñas reales.

---

# 18. Frontend: estado por iteración

## Frontend de Iteración 1

Pantallas de EA1: `/entrada`, `/salida`, `/vehiculos-dentro` y `/estado`.

## Frontend de Iteración 2

Implementado en `frontend/` y fusionado en `main`. Incorpora:

- `/login`, sesión con token en `Authorization` y cierre de sesión;
- menú y rutas según rol (el OPERADOR no accede a funciones administrativas; el ADMINISTRADOR puede además operar entradas y salidas);
- `/usuarios`: gestión de usuarios;
- `/registro`: registro de cliente y vehículo;
- `/clientes`: modificación de clientes y vehículos;
- `/celdas`: administración de celdas, con el estado `FUERA_DE_SERVICIO`;
- Entrada y Salida sin selector de operador (se envía solo `placa` y `codigo_celda`, o solo `placa`);
- ante un `401`, limpieza de sesión y regreso al login.

Verificación: 17 pruebas Playwright en modo real contra el backend, sobre `main` en el commit `74c738a` [real]. Cómo ejecutar el frontend: §9.2.

## Frontend de Iteración 3

Agrega `/pagos` y adapta `/entrada`, `/registro` y `/clientes` a la mensualidad calculada (§3A.3). Verificación: 12 de 12 pruebas Playwright contra el backend real de la Iteración 3 y 26 de 26 en modo mock.

---

# 19. Flujo funcional actual

## Ingreso de un vehículo registrado

```text
Login
  ↓
Consultar placa
  ↓
Validar mensualidad y estancia
  ↓
Consultar celdas disponibles
  ↓
Seleccionar celda
  ↓
Registrar entrada
  ↓
Backend obtiene operador desde la sesión
  ↓
Celda pasa a OCUPADA
```

## Ingreso de una placa no registrada

```text
Login
  ↓
Consultar placa
  ↓
vehiculo = null
  ↓
Registrar cliente + vehículo
  ↓
Continuar flujo de entrada
```

## Salida

```text
Login
  ↓
Consultar vehículo/estancia activa
  ↓
Registrar salida
  ↓
Backend obtiene operador desde la sesión
  ↓
Estancia pasa a FINALIZADA
  ↓
Celda vuelve a DISPONIBLE
```

---

# 20. Evidencias técnicas

```text
sql/autos_colombia.sql
sql/migracion_iteracion2.sql
sql/pruebas_integridad_estancia.sql

sql/migracion_iteracion3.sql
sql/semillas_calendario_ea3.sql
sql/pruebas_integridad_pago.sql

scripts/seed_usuarios.py
scripts/pruebas_i2.sh

tests/
docs/RESULTADOS_PRUEBAS_EA3.md

informes/2026-11-11_backend_B08.md
informes/capturas/pruebas_i2_backend.txt
```

---

# 21. Estado actual del proyecto

## Iteración 1

```text
COMPLETADA
```

- entrada y salida funcionales;
- consultas funcionales;
- correcciones de integridad incorporadas;
- base para la evolución del sistema.

## Backend Iteración 2

```text
IMPLEMENTADO Y PROBADO
```

Resultado:

```text
28/28 PASS
0 fallos
```

Incluye:

- autenticación;
- roles;
- sesiones;
- usuarios;
- clientes y vehículos;
- celdas;
- concurrencia;
- integración con las operaciones de EA1;
- regresión e integridad.

## Frontend Iteración 2

```text
IMPLEMENTADO Y VERIFICADO
```

Resultado: 17 pruebas Playwright [real] contra el backend, sobre `main` (commit `74c738a`).

Incluye login y sesión, permisos por rol, gestión de usuarios, registro de cliente y vehículo, modificación de clientes, administración de celdas, entrada y salida.

## Backend Iteración 3

```text
IMPLEMENTADO Y PROBADO
```

Resultado: 22 de 22 casos del plan PP-03 y 67 pruebas automatizadas aprobadas (`docs/RESULTADOS_PRUEBAS_EA3.md`).

Incluye consulta de mensualidad, registro de pagos, cálculo de fechas de corte, vigencia, historial, validación de ingreso, concurrencia y regresión de las iteraciones anteriores.

## Frontend Iteración 3

```text
IMPLEMENTADO Y VERIFICADO
```

Resultado: 12 de 12 pruebas Playwright contra el backend real; 26 de 26 en modo mock.

---

# 22. Solución de problemas

| Síntoma | Causa y solución |
|---|---|
| `psql: ... Peer authentication failed for user "postgres"` | Se usó `psql -U postgres` sin `-h` (socket local). Use TCP: `PGPASSWORD="$DB_PASSWORD" psql -h localhost -p 5432 -U postgres -d autos_colombia ...` (§8.1). |
| `connection refused` / `could not connect to server` | PostgreSQL no está iniciado. En WSL: `sudo service postgresql start`. |
| `password authentication failed` | `DB_PASSWORD` del `.env` no coincide con la clave de `postgres`. Cámbiela con `sudo -u postgres psql -c "ALTER USER postgres PASSWORD '...';"` o corrija el `.env`. |
| `database "autos_colombia" does not exist` | Créela: `CREATE DATABASE autos_colombia;` (§7.2 y §8.1). |
| El backend no arranca: puerto 5000 ocupado | Hay otro proceso en el 5000. Búsquelo con `ss -ltnp | grep 5000` (Linux/WSL) o `netstat -ano | findstr :5000` (Windows) y ciérrelo. |
| No puedo iniciar sesión (401 «Usuario o contraseña incorrectos») | Los hashes no corresponden a las contraseñas del `.env` (se cambiaron después del seed, o se cargó el SQL y no se hizo el seed). Re-ejecute `python scripts/seed_usuarios.py` y use esas contraseñas. |
| `seed_usuarios.py`: «Falta configurar la variable E2E_…» | Agregue las cuatro `E2E_*_PASSWORD` al `.env` (mínimo 8 caracteres). |
| El frontend muestra datos de ejemplo o no refleja el backend | `NEXT_PUBLIC_USE_MOCK=true` está definida. Quítela de `frontend/.env.local` (y del entorno) y reinicie `npm run dev`. |
| El frontend muestra «No se pudo conectar con el servidor» o errores de CORS | El backend no está corriendo o `NEXT_PUBLIC_API_URL` es incorrecta. Debe ser `http://127.0.0.1:5000` en `frontend/.env.local`; reinicie `npm run dev` después de cambiarla. |
| El pago responde `409` («La mensualidad ya fue actualizada») | Otra persona registró un pago antes. Consulte de nuevo la placa y confirme otra vez. |
| La placa de la semilla ya no aparece vencida o vigente como se describe | Las fechas de la semilla son relativas al día en que se cargó la base. Vuelva a cargar `sql/autos_colombia.sql`, `sql/semillas_calendario_ea3.sql` y `scripts/seed_usuarios.py` (§8.1). |
| `pruebas_i2.sh` borró mis datos | El script recrea la base. Úselo solo sobre una base de pruebas. |
