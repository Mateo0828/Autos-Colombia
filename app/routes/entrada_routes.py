from flask import (
    Blueprint,
    g,
    request,
    current_app
)

from psycopg.errors import UniqueViolation

from app.repositories.estancia_repository import (
    ConflictoEntradaError
)

from app.services.entrada_service import (
    crear_entrada
)

from app.auth_middleware import requerir_roles


entrada_bp = Blueprint(
    "entrada",
    __name__
)


@entrada_bp.route(
    "/api/entradas",
    methods=["POST"]
)
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def registrar_entrada():
    """
    Registra la entrada de un vehículo autorizado.

    Respuestas:
    - 201: Entrada registrada.
    - 400: Incumplimiento de condiciones ordinarias.
    - 401: Sesión inexistente o inválida.
    - 403: Rol no autorizado.
    - 409: Conflicto concurrente.
    - 500: Error interno inesperado.

    Conserva el contrato JSON de las iteraciones
    anteriores y lo alinea con DS-01 de EA3.
    """

    try:

        datos = request.get_json(
            silent=True
        )

        if not isinstance(datos, dict) or not datos:

            return {
                "estado": "error",
                "mensaje": (
                    "Debe enviar los datos de la entrada."
                )
            }, 400

        resultado = crear_entrada(

            placa=datos.get(
                "placa",
                ""
            ),

            codigo_celda=datos.get(
                "codigo_celda",
                ""
            ),

            id_operador=(
                g.usuario_actual["id_operador"]
            )
        )

        return {
            "estado": "ok",
            **resultado
        }, 201

    except ConflictoEntradaError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 409

    except ValueError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 400

    except UniqueViolation as error:

        if error.diag.constraint_name in (
            "uq_vehiculo_estancia_activa",
            "uq_celda_estancia_activa"
        ):

            return {
                "estado": "error",
                "mensaje": (
                    "No fue posible registrar la entrada "
                    "porque el vehículo o la celda ya "
                    "se encuentran en uso."
                )
            }, 409

        current_app.logger.exception(
            "Restricción inesperada al registrar entrada."
        )

        return {
            "estado": "error",
            "mensaje": (
                "No fue posible registrar la entrada."
            )
        }, 500

    except Exception:

        current_app.logger.exception(
            "Error al registrar la entrada."
        )

        return {
            "estado": "error",
            "mensaje": (
                "No fue posible registrar la entrada."
            )
        }, 500