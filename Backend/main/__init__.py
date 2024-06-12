import os
from flask import Flask
from dotenv import load_dotenv
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime

api = Api()
db = SQLAlchemy()
scheduler = APScheduler()

def create_app():
    app = Flask(__name__)

    load_dotenv()

    PATH = os.getenv("DATABASE_PATH")
    DB_NAME = os.getenv("DATABASE_NAME")
    if not os.path.exists(f"{PATH}{DB_NAME}"):
        os.makedirs(PATH, exist_ok=True)
        with open(f"{PATH}{DB_NAME}", 'a'):
            pass

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{PATH}{DB_NAME}"

    # Scheduler configuration
    app.config['SCHEDULER_API_ENABLED'] = True

    db.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    import main.resources as resources
    api.add_resource(resources.UsuariosResource, "/usuarios")
    api.add_resource(resources.UsuarioResource, "/usuario/<id>")

    api.init_app(app)

    # Schedule the update task
    from main.tasks import update_dias_para_cita

    def wrapped_update_dias_para_cita():
        with app.app_context():
            update_dias_para_cita()

    scheduler.add_job(id='update_dias_para_cita', func=wrapped_update_dias_para_cita, trigger='interval', days=1, next_run_time=datetime.now())

    return app
