# Autos Colombia

Sistema de información para la gestión de entrada y salida de vehículos del parqueadero **Autos Colombia**.

Este proyecto corresponde a la **Evidencia de Aprendizaje 1 – Iteración 1** de la asignatura **Ingeniería de Software**.

## Alcance de la Iteración 1

La primera iteración se concentra exclusivamente en la gestión de entrada y salida de vehículos.

El sistema permite:

- Consultar un vehículo mediante su placa.
- Mostrar placa, marca, color, tipo y cliente asociado.
- Validar que el vehículo se encuentre registrado.
- Validar que la mensualidad se encuentre activa.
- Verificar que el vehículo no tenga una estancia activa.
- Consultar celdas disponibles según el tipo de vehículo.
- Registrar la entrada de un vehículo.
- Marcar la celda asignada como ocupada.
- Consultar los vehículos actualmente dentro del parqueadero.
- Registrar la salida de un vehículo.
- Liberar la celda utilizada.
- Consultar el estado general del parqueadero.
- Consultar los operadores disponibles.

Esta iteración **no incluye**:

- Gestión completa de clientes.
- Gestión completa de usuarios.
- Gestión completa de celdas.
- Pagos o facturación.
- Administración de mensualidades.
- Reasignación de celdas (la ruta existe en el código, pero queda fuera del alcance de la entrega; ver más abajo).

## Reglas principales del negocio

- El parqueadero funciona mediante mensualidades por vehículo.
- Un cliente puede tener varios vehículos.
- Cada vehículo requiere su propia mensualidad.
- Se permiten motocicletas, automóviles y camionetas.
- No se permiten camiones.
- El parqueadero dispone de 80 celdas:
  - 70 para automóviles y camionetas.
  - 10 para motocicletas.
- Las motocicletas solo pueden utilizar celdas de tipo `MOTO`.
- Los automóviles y camionetas utilizan celdas de tipo `CARRO`.
- Un vehículo no puede tener más de una estancia activa.
- Una celda no puede ser utilizada simultáneamente por más de un vehículo.
- Una celda se marca como `OCUPADA` al registrar una entrada.
- Una celda vuelve a `DISPONIBLE` al registrar una salida.
- La reasignación de celda existe en el código (`PUT /api/estancias/{placa}/reasignar-celda`), pero **no forma parte de la entrega ni del frontend**.

## Tecnologías utilizadas

### Backend

- Python 3.12 o superior (probado con Python 3.13.9)
- Flask
- Flask-CORS
- Psycopg 3
- python-dotenv

### Base de datos

- PostgreSQL 14 o superior (probado con 14.24 en Ubuntu 22.04 sobre WSL2; el desarrollo original usó PostgreSQL 17)
- pgAdmin 4 (opcional)

### Frontend

- Next.js (App Router), TypeScript y Tailwind CSS, en la carpeta `frontend/` (rama `feature/frontend` hasta que se fusione).

### Control de versiones

- Git
- GitHub

## Arquitectura del backend

El backend se encuentra organizado en capas:

```text
Frontend
   ↓
Routes
   ↓
Services
   ↓
Repositories
   ↓
database.py
   ↓
PostgreSQL
```

### Routes

Reciben las peticiones HTTP y generan las respuestas de la API.

### Services

Contienen las validaciones y reglas de negocio.

### Repositories

Realizan las consultas y operaciones sobre PostgreSQL.

### database.py

Administra la conexión del backend con la base de datos.

## Estructura del proyecto

```text
Autos Colombia/
│
├── app/
│   ├── repositories/
│   │   ├── celda_repository.py
│   │   ├── estancia_repository.py
│   │   ├── operador_repository.py
│   │   └── vehiculo_repository.py
│   │
│   ├── routes/
│   │   ├── celda_routes.py
│   │   ├── consulta_routes.py
│   │   ├── entrada_routes.py
│   │   ├── operador_routes.py
│   │   ├── reasignacion_routes.py
│   │   ├── salida_routes.py
│   │   └── vehiculo_routes.py
│   │
│   ├── services/
│   │   ├── celda_service.py
│   │   ├── consulta_service.py
│   │   ├── entrada_service.py
│   │   ├── operador_service.py
│   │   ├── reasignacion_service.py
│   │   ├── salida_service.py
│   │   ├── validacion_service.py
│   │   └── vehiculo_service.py
│   │
│   ├── __init__.py
│   └── database.py
│
├── sql/
│   └── autos_colombia.sql
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## Instalación del backend (WSL / Ubuntu)

Pasos probados [real] en Ubuntu 22.04 sobre WSL2.

### 1. Clonar el repositorio

```bash
git clone https://github.com/Mateo0828/Autos-Colombia.git
cd Autos-Colombia
```

### 2. Instalar PostgreSQL y crear la base de datos

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'TU_CONTRASENA';"
sudo -u postgres createdb autos_colombia
```

### 3. Cargar el script SQL

Desde la raíz del repositorio:

```bash
PGPASSWORD=TU_CONTRASENA psql -h 127.0.0.1 -U postgres -d autos_colombia -f sql/autos_colombia.sql
```

El script crea las tablas `cliente`, `vehiculo`, `celda`, `operador` y `estancia`, y carga datos iniciales de prueba (5 vehículos, 80 celdas, 3 operadores, 0 estancias).

**Atención:** el script **borra y vuelve a crear** las tablas (`DROP TABLE ... CASCADE`). Para dejar la base limpia después de probar (por ejemplo, tras registrar entradas y salidas), basta con volver a ejecutar el mismo comando.

### 4. Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

El archivo `requirements.txt` está en UTF-8.

### 5. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y reemplazar `TU_CONTRASENA` por la contraseña del usuario `postgres`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autos_colombia
DB_USER=postgres
DB_PASSWORD=TU_CONTRASENA
```

El archivo `.env` no debe subirse al repositorio (está en `.gitignore`).

### 6. Ejecutar el backend

Con el entorno virtual activo:

```bash
python run.py
```

El servidor se ejecuta en `http://127.0.0.1:5000`. Para comprobar que está funcionando:

```text
http://127.0.0.1:5000
```

Respuesta esperada:

```json
{
  "estado": "Backend funcionando",
  "iteracion": 1,
  "sistema": "Autos Colombia"
}
```

### Alternativa en Windows (pgAdmin)

También puede instalarse en Windows: crear la base `autos_colombia` desde pgAdmin, ejecutar `sql/autos_colombia.sql` en el Query Tool, crear el entorno con `py -m venv .venv`, activarlo con `.venv\Scripts\Activate.ps1` e instalar con `python -m pip install -r requirements.txt`. El resto de pasos (`.env` y `python run.py`) es igual. Esta alternativa no se volvió a probar en esta verificación [no probado].

## Ejecución del sistema completo

**(a) Backend, en WSL**, con la base cargada y el entorno virtual activo:

```bash
python run.py
```

Queda en `http://127.0.0.1:5000`.

**(b) Frontend, en Windows** (carpeta `frontend/`, rama `feature/frontend`):

```powershell
cd frontend
npm install
```

Crear el archivo `frontend/.env.local` con:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
```

Luego:

```powershell
npm run dev
```

Abrir `http://localhost:3000`.

**(c) Nota:** WSL2 reenvía `localhost` hacia Windows, por lo que el frontend en Windows alcanza el backend en `http://127.0.0.1:5000` [real para el backend: `http://127.0.0.1:5000/api/db/test` respondió 200 desde PowerShell]. El frontend aún no se ha probado de punta a punta contra este backend [no probado].

La carpeta `frontend/` está en la rama `feature/frontend` hasta que se fusione con `main`.

## Verificación de conexión con PostgreSQL

Puede comprobarse mediante:

```text
GET /api/db/test
```

URL:

```text
http://127.0.0.1:5000/api/db/test
```

## Endpoints principales

### Consultar vehículo

```http
GET /api/vehiculos/{placa}
```

Ejemplo:

```text
GET /api/vehiculos/ABC123
```

---

### Validar ingreso

```http
GET /api/vehiculos/{placa}/validar-ingreso
```

Comprueba:

- vehículo registrado;
- mensualidad activa;
- ausencia de estancia activa.

---

### Consultar celdas disponibles

```http
GET /api/celdas/disponibles?tipo_vehiculo=AUTOMOVIL
```

Valores permitidos:

```text
AUTOMOVIL
CAMIONETA
MOTO
```

---

### Registrar entrada

```http
POST /api/entradas
```

Ejemplo de cuerpo JSON:

```json
{
  "placa": "ABC123",
  "codigo_celda": "C01",
  "id_operador": 1
}
```

---

### Registrar salida

```http
POST /api/salidas
```

Ejemplo:

```json
{
  "placa": "ABC123",
  "id_operador": 2
}
```

El operador de salida puede ser diferente al operador que realizó la entrada.

---

### Consultar vehículos dentro

```http
GET /api/estancias/activas
```

Retorna únicamente las estancias cuyo estado es:

```text
ACTIVA
```

---

### Consultar estado del parqueadero

```http
GET /api/parqueadero/estado
```

Retorna:

- total de celdas;
- celdas disponibles;
- celdas ocupadas;
- disponibilidad de celdas para carro;
- disponibilidad de celdas para moto;
- cantidad de vehículos dentro.

---

### Reasignar celda (fuera del alcance de la entrega)

> Esta ruta existe en el código, pero **no forma parte de la entrega ni del frontend**. No se verificó en la prueba de las 13 pruebas de aceptación.

```http
PUT /api/estancias/{placa}/reasignar-celda
```

Ejemplo:

```json
{
  "nueva_celda": "C02"
}
```

La operación:

1. Verifica que el vehículo tenga una estancia activa.
2. Verifica que la nueva celda exista.
3. Verifica que se encuentre disponible.
4. Verifica compatibilidad con el tipo de vehículo.
5. Libera la celda anterior.
6. Ocupa la nueva celda.
7. Actualiza la estancia activa.

---

### Consultar operadores

```http
GET /api/operadores
```

Permite que el frontend obtenga los operadores disponibles para registrar entradas y salidas.

## Datos de prueba

El script SQL incluye vehículos de prueba.

Ejemplos:

```text
ABC123
DEF456
GHI789
MOT01A
JKL321
```

`JKL321` posee una mensualidad `INACTIVA`, lo que permite probar el rechazo de ingreso por mensualidad vencida o inactiva.

También se incluyen tres operadores:

```text
Operador Mañana
Operador Tarde
Operador Noche
```

## Estados utilizados

### Vehículo

```text
ACTIVA
INACTIVA
```

Corresponde al estado de la mensualidad.

### Celda

```text
DISPONIBLE
OCUPADA
```

### Estancia

```text
ACTIVA
FINALIZADA
```

## Integración con frontend

El frontend está hecho con **Next.js** y se ejecuta en desarrollo en `http://localhost:3000`. Consume el backend en `http://127.0.0.1:5000` (variable `NEXT_PUBLIC_API_URL`).

El backend utiliza Flask-CORS con CORS abierto en desarrollo [real: responde `Access-Control-Allow-Origin` para el origen `http://localhost:3000`].

Los endpoints intercambian información mediante JSON.

## Seguridad de configuración

Las credenciales de PostgreSQL se almacenan localmente en:

```text
.env
```

Este archivo se encuentra excluido mediante `.gitignore`.

Nunca deben almacenarse contraseñas reales dentro del código fuente ni dentro del repositorio.

## Estado del proyecto

- **Backend:** implementa la gestión de entrada y salida de vehículos de la Iteración 1. Se verificó con curl contra PostgreSQL con los datos semilla: los endpoints usados por el frontend y las 13 pruebas de aceptación (P-01 a P-13) a nivel de API funcionan [real]. Una desviación conocida: `GET /api/vehiculos/{placa}/validar-ingreso` no devuelve 400 con placas de formato inválido (devuelve 200 «no registrado»); la validación de formato está en `/api/entradas` y `/api/salidas`.
- **Frontend:** en desarrollo en la rama `feature/frontend`; aún no está fusionado con `main`.
- **Fuera de alcance de esta iteración:** gestión completa de clientes, usuarios, celdas y mensualidades, pagos y facturación y reasignación de celdas.
