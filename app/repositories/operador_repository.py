from app.database import get_connection


def consultar_operadores():
    consulta = """
        SELECT
            id_operador,
            nombre
        FROM operador
        ORDER BY id_operador;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            filas = cursor.fetchall()

    return [
        {
            "id_operador": fila[0],
            "nombre": fila[1]
        }
        for fila in filas
    ]

def buscar_operador_por_usuario(usuario):
    consulta = """
        SELECT
            id_operador,
            nombre,
            usuario,
            password_hash,
            rol,
            estado,
            fecha_creacion
        FROM operador
        WHERE usuario = %s;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (usuario,))
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_operador": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "password_hash": fila[3],
        "rol": fila[4],
        "estado": fila[5],
        "fecha_creacion": fila[6]
    }

def consultar_usuarios():
    consulta = """
        SELECT
            id_operador,
            nombre,
            usuario,
            rol,
            estado,
            fecha_creacion
        FROM operador
        ORDER BY id_operador;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            filas = cursor.fetchall()

    return [
        {
            "id_operador": fila[0],
            "nombre": fila[1],
            "usuario": fila[2],
            "rol": fila[3],
            "estado": fila[4],
            "fecha_creacion": fila[5]
        }
        for fila in filas
    ]

def crear_usuario(nombre, usuario, password_hash, rol):
    consulta = """
        INSERT INTO operador (
            nombre,
            usuario,
            password_hash,
            rol,
            estado
        )
        VALUES (%s, %s, %s, %s, 'ACTIVO')
        RETURNING
            id_operador,
            nombre,
            usuario,
            rol,
            estado,
            fecha_creacion;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                (
                    nombre,
                    usuario,
                    password_hash,
                    rol
                )
            )
            fila = cursor.fetchone()

        conexion.commit()

    return {
        "id_operador": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "rol": fila[3],
        "estado": fila[4],
        "fecha_creacion": fila[5]
    }

def buscar_operador_por_id(id_operador):
    consulta = """
        SELECT
            id_operador,
            nombre,
            usuario,
            password_hash,
            rol,
            estado,
            fecha_creacion
        FROM operador
        WHERE id_operador = %s;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (id_operador,))
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_operador": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "password_hash": fila[3],
        "rol": fila[4],
        "estado": fila[5],
        "fecha_creacion": fila[6]
    }

def actualizar_usuario(
    id_operador,
    nombre,
    rol,
    password_hash=None
):
    if password_hash is None:
        consulta = """
            UPDATE operador
            SET
                nombre = %s,
                rol = %s
            WHERE id_operador = %s
            RETURNING
                id_operador,
                nombre,
                usuario,
                rol,
                estado,
                fecha_creacion;
        """

        parametros = (
            nombre,
            rol,
            id_operador
        )

    else:
        consulta = """
            UPDATE operador
            SET
                nombre = %s,
                rol = %s,
                password_hash = %s
            WHERE id_operador = %s
            RETURNING
                id_operador,
                nombre,
                usuario,
                rol,
                estado,
                fecha_creacion;
        """

        parametros = (
            nombre,
            rol,
            password_hash,
            id_operador
        )

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                parametros
            )
            fila = cursor.fetchone()

        conexion.commit()

    if fila is None:
        return None

    return {
        "id_operador": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "rol": fila[3],
        "estado": fila[4],
        "fecha_creacion": fila[5]
    }

def contar_administradores_activos():
    consulta = """
        SELECT COUNT(*)
        FROM operador
        WHERE rol = 'ADMINISTRADOR'
          AND estado = 'ACTIVO';
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            fila = cursor.fetchone()

    return fila[0]

def actualizar_estado_usuario(id_operador, estado):
    consulta = """
        UPDATE operador
        SET estado = %s
        WHERE id_operador = %s
        RETURNING
            id_operador,
            nombre,
            usuario,
            rol,
            estado,
            fecha_creacion;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                (
                    estado,
                    id_operador
                )
            )
            fila = cursor.fetchone()

        conexion.commit()

    if fila is None:
        return None

    return {
        "id_operador": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "rol": fila[3],
        "estado": fila[4],
        "fecha_creacion": fila[5]
    }
