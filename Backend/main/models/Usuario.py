from .. import db
import datetime as dt

class Usuario (db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    fecha_cita = db.Column(db.DateTime, default=dt.datetime.now)
    fecha_registro = db.Column(db.DateTime, default=dt.datetime.now)
    dias_para_cita = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"{self.nombre}"

    def to_json(self):
        usuario_json = {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "fecha_cita": self.fecha_cita.isoformat() if self.fecha_cita else None,
            "dias_para_cita": self.dias_para_cita
        }
        return usuario_json

    @staticmethod
    def from_json(usuario_json):
        id = usuario_json.get("id")
        nombre = usuario_json.get("nombre")
        telefono = usuario_json.get("telefono")
        fecha_registro_str = usuario_json.get("fecha_registro")
        fecha_cita_str = usuario_json.get("fecha_cita")
        
        fecha_registro = dt.datetime.fromisoformat(fecha_registro_str) if fecha_registro_str else dt.datetime.now()
        fecha_cita = dt.datetime.fromisoformat(fecha_cita_str) if fecha_cita_str else dt.datetime.now()
        
        dias_para_cita = (fecha_cita - fecha_registro).days if fecha_registro and fecha_cita else 0
        
        return Usuario (id=id, nombre=nombre, telefono=telefono, fecha_registro=fecha_registro, fecha_cita=fecha_cita, dias_para_cita=dias_para_cita)
