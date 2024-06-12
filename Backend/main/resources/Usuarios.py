from flask_restful import Resource
from flask import request, jsonify
from .. import db
from main.models import UsuarioModel
import datetime as dt
import requests
import json

class Usuario (Resource):

    def get(self, id):
        usuario = db.session.query(UsuarioModel).get_or_404(id)
        return usuario.to_json()
    
    def delete(self, id):
        usuario = db.session.query(UsuarioModel).get_or_404(id)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204
    
    def put(self, id):
        usuario = db.session.query(UsuarioModel).get_or_404(id)
        data = request.get_json()
        for key, value in data.items():
            if key in ['fecha_registro', 'fecha_cita'] and value:
                value = dt.datetime.fromisoformat(value)
            setattr(usuario, key, value)
        usuario.dias_para_cita = (usuario.fecha_cita - usuario.fecha_registro).days
        db.session.commit()

        if usuario.dias_para_cita == 1:
            print(f"Enviando mensaje a {usuario.telefono}")
            send_whatsapp_message(usuario.telefono, f"Hola {usuario.nombre}, tu cita es mañana.")

        return usuario.to_json(), 201
    
class Usuarios (Resource):

    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        usuarios = UsuarioModel.query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'usuarios': [usuario.to_json() for usuario in usuarios.items],
            'total': usuarios.total,
            'pages': usuarios.pages,
            'page': page
        })
    
    def post(self):
        usuario = UsuarioModel.from_json(request.get_json())
        db.session.add(usuario)
        db.session.commit()

        if usuario.dias_para_cita == 1:
            print(f"Enviando mensaje a {usuario.telefono}")
            send_whatsapp_message(usuario.telefono, f"Hola {usuario.nombre}, tu cita es mañana.")

        return usuario.to_json(), 201

def send_whatsapp_message(to_number, message_body):
    url = "https://api.gupshup.io/wa/api/v1/msg"

    payload = {
        "channel": "whatsapp",
        "source": 5216675014303,
        "destination": int(to_number),
        "message": json.dumps({
            "type": "text",
            "text": message_body
        }),
        "src.name": "myapp",
        "disablePreview": False,
        "encode": False
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": "o6botgtule9omsamb70z42udlyzp3cql"
    }

    response = requests.post(url, data=payload, headers=headers)

    print(response.text)