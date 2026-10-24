from flask import Flask

from app.database import get_connection
from app.routes.vehiculo_routes import vehiculo_bp
from app.routes.celda_routes import celda_bp
from app.routes.entrada_routes import entrada_bp
from app.routes.salida_routes import salida_bp
from app.routes.consulta_routes import consulta_bp
from app.routes.reasignacion_routes import reasignacion_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(vehiculo_bp)
    app.register_blueprint(celda_bp)
    app.register_blueprint(entrada_bp)
    app.register_blueprint(salida_bp)
    app.register_blueprint(consulta_bp)
    app.register_blueprint(reasignacion_bp)

    @app.route("/")
    def inicio():
        return {
            "sistema": "Autos Colombia",
            "estado": "Backend funcionando",
            "iteracion": 1
        }

    @app.route("/api/db/test")
    def probar_base_datos():
        try:
            with get_connection() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                    cursor.fetchone()

            return {
                "estado": "ok",
                "mensaje": "Conexión con PostgreSQL exitosa"
            }

        except Exception as error:
            return {
                "estado": "error",
                "mensaje": str(error)
            }, 500

    return app