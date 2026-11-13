import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash


# Cargar el archivo .env ubicado en la raíz del proyecto.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ_PROYECTO / ".env")


def obtener_conexion():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def obtener_password(nombre_variable):
    password = os.getenv(nombre_variable)

    if not password:
        raise ValueError(
            f"Falta configurar la variable de entorno {nombre_variable}."
        )

    if len(password) < 8:
        raise ValueError(
            f"La contraseña configurada en {nombre_variable} "
            "debe tener mínimo 8 caracteres."
        )

    return password


def asignar_passwords():
    usuarios = {
        "admin": obtener_password("E2E_ADMIN_PASSWORD"),
        "operador1": obtener_password("E2E_OPERADOR1_PASSWORD"),
        "operador2": obtener_password("E2E_OPERADOR2_PASSWORD"),
        "operador3": obtener_password("E2E_OPERADOR3_PASSWORD"),
    }

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            for usuario, password in usuarios.items():
                password_hash = generate_password_hash(password)

                cursor.execute(
                    """
                    UPDATE operador
                    SET password_hash = %s
                    WHERE usuario = %s;
                    """,
                    (password_hash, usuario)
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"No se encontró exactamente un usuario '{usuario}'."
                    )

        conexion.commit()

    print("Contraseñas de usuarios de prueba configuradas correctamente.")


if __name__ == "__main__":
    try:
        asignar_passwords()
    except Exception as error:
        print(f"Error al configurar usuarios: {error}")
        raise