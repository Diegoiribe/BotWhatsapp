from .. import db
import datetime as dt

class Usuario (db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=dt.datetime.now)
    time = db.Column(db.Time, default=dt.datetime.now)
    fecha_registro = db.Column(db.DateTime, default=dt.datetime.now)
    dias_para_cita = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"{self.name}"

    def to_json(self):
        usuario_json = {
            "id": self.id,
            "name": self.name,
            "telephone": self.telephone,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "date": self.date.isoformat() if self.date else None,
            "time": self.date.strftime("%H:%M:%S") if self.date else None,
            "dias_para_cita": self.dias_para_cita
        }
        return usuario_json

    @staticmethod
    def from_json(usuario_json):
        id = usuario_json.get("id")
        name = usuario_json.get("name")
        telephone = usuario_json.get("telephone")
        fecha_registro_str = usuario_json.get("fecha_registro")
        date_str = usuario_json.get("date")
        time_str = usuario_json.get("time")
        fecha_registro = dt.datetime.fromisoformat(fecha_registro_str) if fecha_registro_str else dt.datetime.now()
        date = dt.datetime.fromisoformat(date_str) if date_str else dt.datetime.now()
        time = dt.datetime.strptime(time_str, "%H:%M:%S").time() if time_str else dt.datetime.now().time()
        
        dias_para_cita = (date - fecha_registro).days if fecha_registro and date else 0
        
        return Usuario (id=id, name=name, telephone=telephone, fecha_registro=fecha_registro, date=date, dias_para_cita=dias_para_cita, time=time)
