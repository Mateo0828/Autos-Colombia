import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

try:
    conexion = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    print("Conexión exitosa con PostgreSQL")
    conexion.close()

except Exception as error:
    print("Error de conexión:")
    print(error)