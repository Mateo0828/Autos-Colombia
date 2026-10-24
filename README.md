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
- Reasignar una celda cuando el vehículo ocupa una diferente a la asignada inicialmente.
- Consultar el estado general del parqueadero.
- Consultar los operadores disponibles.

Esta iteración **no incluye**:

- Gestión completa de clientes.
- Gestión completa de usuarios.
- Gestión completa de celdas.
- Pagos o facturación.
- Administración de mensualidades.
- Registro de novedades.

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
- Si el vehículo se estaciona en una celda diferente a la asignada, se puede realizar una reasignación.

## Tecnologías utilizadas

### Backend

- Python 3.12
- Flask
- Flask-CORS
- Psycopg 3
- python-dotenv

### Base de datos

- PostgreSQL 17
- pgAdmin 4

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

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Mateo0828/Autos-Colombia.git
```

Entrar a la carpeta:

```bash
cd Autos-Colombia
```

## 2. Crear el entorno virtual

En Windows:

```powershell
py -m venv .venv
```

Activarlo:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

## 4. Crear la base de datos

En PostgreSQL se debe crear una base de datos llamada:

```text
autos_colombia
```

Puede realizarse desde pgAdmin.

Después se debe abrir el **Query Tool** de la base de datos y ejecutar el archivo:

```text
sql/autos_colombia.sql
```

El script crea las tablas:

- `cliente`
- `vehiculo`
- `celda`
- `operador`
- `estancia`

También crea datos iniciales para realizar pruebas.

## 5. Configurar variables de entorno

Crear un archivo llamado:

```text
.env
```

tomando como referencia:

```text
.env.example
```

Contenido esperado:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autos_colombia
DB_USER=postgres
DB_PASSWORD=TU_CONTRASENA
```

La contraseña debe corresponder al usuario configurado en PostgreSQL.

El archivo `.env` no debe subirse al repositorio.

## 6. Ejecutar el backend

Con el entorno virtual activo:

```powershell
python run.py
```

El servidor se ejecutará por defecto en:

```text
http://127.0.0.1:5000
```

Para verificar que el backend se encuentra funcionando:

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

### Reasignar celda

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

El backend utiliza Flask-CORS para permitir peticiones desde un frontend ejecutado en otro puerto durante el desarrollo.

Por ejemplo:

```text
Frontend:
http://localhost:4200

Backend:
http://127.0.0.1:5000
```

Los endpoints intercambian información mediante JSON, por lo que el frontend puede implementarse utilizando Angular, JavaScript u otra tecnología que permita realizar solicitudes HTTP.

## Seguridad de configuración

Las credenciales de PostgreSQL se almacenan localmente en:

```text
.env
```

Este archivo se encuentra excluido mediante `.gitignore`.

Nunca deben almacenarse contraseñas reales dentro del código fuente ni dentro del repositorio.

## Estado del proyecto

El backend de la **Iteración 1** implementa las funcionalidades previstas para la gestión de entrada y salida de vehículos.

El proyecto se encuentra preparado para integrarse con el frontend y para evolucionar en futuras iteraciones con funcionalidades adicionales como gestión completa de usuarios, celdas, mensualidades y pagos.