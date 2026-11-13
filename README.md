# Autos Colombia

Sistema de información para la gestión operativa del parqueadero **Autos Colombia**, desarrollado de forma incremental para la asignatura **Ingeniería de Software**.

El proyecto se construye por iteraciones sobre una misma base técnica y funcional:

- **Iteración 1 (EA1):** gestión de entrada y salida de vehículos.
- **Iteración 2 (EA2):** autenticación, perfiles, gestión de usuarios, registro y modificación de clientes/vehículos y gestión operativa de celdas.
- **Iteraciones posteriores:** funcionalidades fuera del alcance actual, como pagos y administración de mensualidades.

La Iteración 2 **no reemplaza** la Iteración 1. La amplía, conserva su arquitectura y sus reglas de integridad, y protege las operaciones existentes mediante autenticación y control de roles.

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

## Fuera de alcance

No forman parte de la entrega actual:

- pagos;
- facturación;
- CRUD de mensualidades;
- novedades;
- reasignación de celdas como funcionalidad de entrega.

Existe código heredado para reasignación de celda:

```http
PUT /api/estancias/{placa}/reasignar-celda
```

pero **no forma parte del alcance de EA2 ni debe integrarse al frontend**.

---

# 5. Tecnologías

## Backend

- Python 3.12 o superior.
- Flask.
- Flask-CORS.
- Werkzeug.
- Psycopg 3.
- python-dotenv.

## Base de datos

- PostgreSQL 14 o superior.
- pgAdmin 4 opcional.

## Frontend

- Node.js 18.18 o superior (probado con 20.14).
- Next.js 15.5 (App Router), React 19.
- TypeScript.
- Tailwind CSS 4.
- lucide-react.
- Playwright (pruebas de navegador, opcional).

## Control de versiones

- Git.
- GitHub.

Repositorio:

```text
https://github.com/Mateo0828/Autos-Colombia
```

El backend y el frontend de EA2 ya están fusionados en la rama `main`. Para ejecutar el sistema solo se necesita `main`.

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
│   │   ├── reasignacion_routes.py
│   │   ├── registro_routes.py
│   │   ├── salida_routes.py
│   │   ├── usuario_routes.py
│   │   └── vehiculo_routes.py
│   │
│   ├── services/
│   ├── auth_middleware.py
│   ├── database.py
│   └── __init__.py
│
├── frontend/                  (Next.js: pantallas de EA1 y EA2)
│   ├── src/app/               (rutas: login, entrada, salida, vehiculos-dentro,
│   │                           estado, usuarios, registro, clientes, celdas)
│   ├── src/components/
│   ├── src/lib/api.ts         (cliente de la API)
│   ├── src/types/
│   ├── e2e/                   (pruebas Playwright)
│   └── package.json
│
├── informes/
│   ├── 2026-11-11_backend_B08.md
│   └── capturas/
│       └── pruebas_i2_backend.txt
│
├── scripts/
│   ├── seed_usuarios.py
│   └── pruebas_i2.sh
│
├── sql/
│   ├── autos_colombia.sql
│   ├── migracion_iteracion2.sql
│   └── pruebas_integridad_estancia.sql
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

La rama `main` ya contiene la Iteración 2 (backend y frontend). No hace falta cambiar de rama: quien revise el proyecto clona el repositorio y trabaja sobre `main`.

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
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/autos_colombia.sql
```

Windows PowerShell (equivalente; no probado en este entorno):

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)$') { Set-Item -Path "env:$($Matches[1])" -Value $Matches[2] } }
$env:PGPASSWORD = $env:DB_PASSWORD
psql -h $env:DB_HOST -p $env:DB_PORT -U $env:DB_USER -d $env:DB_NAME -f sql/autos_colombia.sql
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
- carga los datos semilla.

Después, con el entorno virtual activo (§7.3), ejecutar:

```bash
python scripts/seed_usuarios.py
```

para generar los hashes de contraseña a partir de las variables `E2E_*_PASSWORD` del `.env`. Este mismo par de pasos (SQL + seed) deja la base limpia de nuevo cuando se necesite.

> `autos_colombia.sql` elimina y recrea las tablas. No debe ejecutarse sobre una base con información que se quiera conservar.

---

## 8.2 Migración desde una base de Iteración 1

Para conservar una base existente:

```bash
set -a; source .env; set +a
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/migracion_iteracion2.sql
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

## Iteración 2

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

Los endpoints heredados de EA1 conservan sus validaciones históricas con `400` cuando corresponde.

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

```text
ABC123
DEF456
GHI789
MOT01A
JKL321
```

`JKL321` tiene mensualidad `INACTIVA` para probar el rechazo de ingreso.

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

# 16. Concurrencia

La gestión de celdas utiliza bloqueo de fila con:

```sql
SELECT ... FOR UPDATE
```

Se comprobó que dos operaciones concurrentes sobre la misma celda no dejan un estado inconsistente.

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

scripts/seed_usuarios.py
scripts/pruebas_i2.sh

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
| `pruebas_i2.sh` borró mis datos | El script recrea la base. Úselo solo sobre una base de pruebas. |
