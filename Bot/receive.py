import requests
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Configura tu clave API de Gupshup
API_KEY = 'o6botgtule9omsamb70z42udlyzp3cql'  # Reemplaza con tu clave API de Gupshup
SOURCE_NUMBER = '5216675014303'  # Reemplaza con tu número registrado en Gupshup

# Lista para almacenar las citas reservadas
citas_reservadas = []

# Diccionario para almacenar temporalmente la información del usuario
usuario_info = {}

cita = False

API_URL = "http://127.0.0.1:6000/usuarios"  # URL de tu API

def cargar_citas_desde_api():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            global citas_reservadas
            citas_reservadas = response.json()
            print("Citas cargadas exitosamente desde la API")
        else:
            print(f"Error al cargar citas desde la API: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Excepción al cargar citas desde la API: {e}")

@app.before_request
def before_request():
    if not hasattr(app, 'before_first_request_handled'):
        cargar_citas_desde_api()
        app.before_first_request_handled = True

@app.route('/', methods=['GET'])
def home():
    return "Servidor funcionando correctamente"

@app.route('/webhook', methods=['GET'])
def webhook_get():
    return 'Método no permitido', 405

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print('Datos recibidos del webhook:', json.dumps(data, indent=4))

    # Manejar solo eventos donde se recibe un mensaje de texto
    if data.get('type') == 'message':
        handle_message(data['payload'])
        handle_postback(data['payload'])

    return '', 204  # Responder con un status 204 No Content

def set_cita_state(state):
    global cita
    cita = state

def handle_message(payload):
    if payload.get('type') == 'text' and 'payload' in payload:
        inner_payload = payload['payload']
        if 'text' in inner_payload:
            from_number = payload['source']
            message = inner_payload['text'].lower()
            
            if not cita:
                match = re.match(r'(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2})', message)
                if match:
                    date_str = match.group(1)
                    print(f"Fecha detectada: {date_str}")  # Mensaje de depuración
                    cita_a_eliminar = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    delete_cita(from_number, cita_a_eliminar)
                else:
                    send_welcome_message(from_number)
            elif cita: 
                match = re.match(r'(\d{4}-\d{1,2}-\d{1,2})', message)
                if match:
                    date_str = match.group(1)
                    print(f"Fecha detectada: {date_str}")  # Mensaje de depuración
                    fecha = datetime.strptime(date_str, '%Y-%m-%d').date()
                    select_add_cita(from_number, fecha)
                else:
                    save_name(from_number, message)

def handle_postback(payload):
    if 'payload' in payload:
        inner_payload = payload['payload']
        if 'postbackText' in inner_payload:
            postback_text = inner_payload['postbackText']
            from_number = payload['source']
            if postback_text == 'cita':
                send_response_cita(from_number)
            elif postback_text == 'agendar_cita':
                add_cita(from_number)
            elif postback_text == 'add_cita':
                if from_number in usuario_info and 'time' in usuario_info[from_number]:
                    select_name(from_number, usuario_info[from_number]['time'])
            elif postback_text == 'otra_fecha':
                another_date(from_number)
            elif postback_text == 'hour':
                check_hours(from_number, inner_payload['title'])
            elif postback_text == 'seleccionar_fecha':
                select_date(from_number)
            elif postback_text == 'hour_select':
                select_name(from_number, inner_payload['title'])
            elif postback_text == 'cancelar_cita':
                cancel_cita(from_number)
            elif postback_text == 'mostrar_citas':
                mostrar_citas_reservadas(from_number)
            elif postback_text == 'contacto':
                contact_menu(from_number)
            elif postback_text == 'ubicacion':
                send_location_message(from_number)
            elif postback_text == 'kevin':
                send_contact(from_number)
            elif postback_text == 'salir':
                send_welcome_message(from_number)

def send_welcome_message(to_number):
    welcome_text = "¡Bienvenido! ¿Qué deseas hacer?"
    options = [
        {"title": "Agendar Cita", "postbackText": "cita"},
        {"title": "Consultar", "postbackText": "mostrar_citas"},
        {"title": "Contacto", "postbackText": "contacto"}
    ]
    set_cita_state(False)
    send_quick_reply_message(to_number, options, welcome_text)

def send_response_cita(to_number):
    options = [
        {"title": "Seleccionar fecha", "postbackText": "seleccionar_fecha"},
        {"title": "Cita rápida", "postbackText": "agendar_cita"},
        {"title": "Salir", "postbackText": "salir"}
    ]
    send_quick_reply_message(to_number, options)

def add_cita(to_number):
    set_cita_state(True)
    next_appointment = get_next_available_appointment()

    if to_number not in usuario_info:
        usuario_info[to_number] = {}
    
    usuario_info[to_number]["next_appointment"] = next_appointment
    usuario_info[to_number]["date"] = next_appointment.date()
    usuario_info[to_number]["time"] = next_appointment.strftime('%I:%M %p')

    response_text = f"La cita más próxima es el {next_appointment.strftime('%d de %B a las %I:%M %p')}. ¿Deseas agendarla?"
    options = [
        {"title": "Sí", "postbackText": "add_cita"},
        {"title": "Deseo otra fecha", "postbackText": "otra_fecha"},
        {"title": "Salir", "postbackText": "salir"}
    ]

    send_quick_reply_message(to_number, options, response_text)

def another_date(to_number):
    response_text = "Indica la hora a la que deseas agendar la cita."
    morning = [
        {"id": 11, "title": "11:00 AM", "postbackText": "hour"},
        {"id": 12, "title": "12:00 AM", "postbackText": "hour"},
        {"id": 1, "title": "01:00 PM", "postbackText": "hour"},
    ]

    evening = [
        {"id": 2, "title": "02:00 PM", "postbackText": "hour"},
        {"id": 3, "title": "03:00 PM", "postbackText": "hour"},
        {"id": 4, "title": "04:00 PM", "postbackText": "hour"},
    ]

    night = [
        {"id": 5, "title": "05:00 PM", "postbackText": "hour"},
        {"id": 6, "title": "06:00 PM", "postbackText": "hour"},
        {"id": 7, "title": "07:00 PM", "postbackText": "hour"},
    ]

    sections = [
        {"title": "Morning", "subtitle": "Choose a morning time", "options": morning},
        {"title": "Evening", "subtitle": "Choose an evening time", "options": evening},
        {"title": "Night", "subtitle": "Choose a night time", "options": night},
    ]

    send_list_message(to_number, sections, response_text)

def extract_hour(title):
    # Asumiendo que el título siempre está en el formato "HH:MM AM/PM"
    hour, minute_period = title.split(':')
    minute, period = minute_period.split(' ')
    hour = int(hour)
    
    if period == 'PM' and hour != 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    
    return hour

def check_hours(to_number, title):
    set_cita_state(True)
    hour_selected = extract_hour(title)
    end_hour = hour_selected + 1
    next_appointment = get_next_available_appointment(hour_selected, end_hour)

    if to_number not in usuario_info:
        usuario_info[to_number] = {}

    usuario_info[to_number]["next_appointment"] = next_appointment
    usuario_info[to_number]["date"] = next_appointment.date()
    usuario_info[to_number]["time"] = next_appointment.strftime('%I:%M %p')

    response_text = f"La cita más próxima es el {next_appointment.strftime('%d de %B a las %I:%M %p')}. ¿Deseas agendarla?"

    options = [
        {"title": "Sí", "postbackText": "add_cita"},
        {"title": "Deseo otra fecha", "postbackText": "otra_fecha"},
        {"title": "Salir", "postbackText": "salir"}
    ]

    send_quick_reply_message(to_number, options, response_text)

def get_booked_hours(date):
    return [cita["date"].strftime('%I:%M %p') for cita in citas_reservadas if cita["date"].date() == date]

def get_next_available_days(start_date, num_days=3):
    available_days = []
    current_date = start_date + timedelta(days=1)

    while len(available_days) < num_days:
        booked_hours = get_booked_hours(current_date)
        if len(booked_hours) < 6:  # Suponiendo que hay 6 slots por día
            available_days.append(current_date)
        current_date += timedelta(days=1)
    
    return available_days

def select_date(to_number):
    set_cita_state(True)
    send_response(to_number, "Indica la fecha de la cita que deseas agendar en el formato 'YYYY-MM-DD'.")

def select_add_cita(to_number, date):
    response_text = "El día {} está disponible, por favor selecciona la hora"
    booked_hours = get_booked_hours(date)

    # Opciones de horarios disponibles
    all_hours = [
        {"id": 11, "title": "11:00 AM", "postbackText": "hour_select"},
        {"id": 12, "title": "12:00 PM", "postbackText": "hour_select"},
        {"id": 13, "title": "01:00 PM", "postbackText": "hour_select"},
        {"id": 14, "title": "02:00 PM", "postbackText": "hour_select"},
        {"id": 15, "title": "03:00 PM", "postbackText": "hour_select"},
        {"id": 16, "title": "04:00 PM", "postbackText": "hour_select"},
        {"id": 17, "title": "05:00 PM", "postbackText": "hour_select"},
        {"id": 18, "title": "06:00 PM", "postbackText": "hour_select"},
        {"id": 19, "title": "07:00 PM", "postbackText": "hour_select"},
    ]

    # Filtrar las horas que ya están reservadas
    available_hours = [slot for slot in all_hours if slot["title"] not in booked_hours]

    # Dividir los horarios en secciones: mañana, tarde y noche
    morning = [slot for slot in available_hours if 11 <= slot["id"] < 14]
    evening = [slot for slot in available_hours if 14 <= slot["id"] < 17]
    night = [slot for slot in available_hours if 17 <= slot["id"] < 20]

    sections = [
        {"title": "Morning", "subtitle": "Choose a morning time", "options": morning},
        {"title": "Evening", "subtitle": "Choose an evening time", "options": evening},
        {"title": "Night", "subtitle": "Choose a night time", "options": night},
    ]

    if morning or evening or night:
        usuario_info[to_number] = {"date": date}  # Guardar la fecha temporalmente
        send_list_message(to_number, sections, response_text.format(date))
    else:
        next_days = get_next_available_days(date)
        if next_days:
            for day in next_days:
                booked_hours = get_booked_hours(day)
                available_hours = [slot for slot in all_hours if slot["title"] not in booked_hours]

                morning = [slot for slot in available_hours if 11 <= slot["id"] < 14]
                evening = [slot for slot in available_hours if 14 <= slot["id"] < 17]
                night = [slot for slot in available_hours if 17 <= slot["id"] < 20]

                sections = [
                    {"title": "Morning", "subtitle": "Choose a morning time", "options": morning},
                    {"title": "Evening", "subtitle": "Choose an evening time", "options": evening},
                    {"title": "Night", "subtitle": "Choose a night time", "options": night},
                ]

                if morning or evening or night:
                    send_list_message(to_number, sections, f"El día {day} está disponible, por favor selecciona la hora")
                    return  # Termina la función después de enviar el mensaje
        else:
            send_response(to_number, f"No hay horarios disponibles para el {date} ni en los próximos 3 días.")

def select_name(to_number, time):
    if to_number in usuario_info:
        usuario_info[to_number]["time"] = time  # Guardar la hora temporalmente
        send_response(to_number, "Por favor, indica tu nombre completo.")
    else:
        send_response(to_number, "Hubo un error en la selección de la hora. Por favor, empieza de nuevo.")

def save_name(to_number, name):
    if to_number in usuario_info:
        usuario_info[to_number]["name"] = name
        date = usuario_info[to_number]["date"]
        time = usuario_info[to_number]["time"]
        select_save_cita(to_number, date, time)
    else:
        send_response(to_number, "Hubo un error en la selección del nombre.")

def enviar_cita_a_api(cita):
    try:
        response = requests.post(API_URL, json=cita, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print("Cita enviada exitosamente a la API")
        else:
            print(f"Error al enviar la cita a la API: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Excepción al enviar la cita a la API: {e}")

def select_save_cita(to_number, date, time):
    name = usuario_info[to_number]["name"]
    cita_datetime = datetime.combine(date, datetime.strptime(time, "%I:%M %p").time())
    citas_reservadas.append({"date": cita_datetime, "time": time, "name": name})
    enviar_cita_a_api({"telephone": to_number ,"date": cita_datetime.isoformat(), "time": time, "name": name})
    send_response(to_number, f"¡Gracias {name}! Tu cita para el {date} a las {time} ha sido agendada.")
    send_welcome_message(to_number)
    usuario_info.pop(to_number, None)

def cancel_cita(to_number):
    send_response(to_number, "Indica la fecha y hora de la cita que deseas cancelar.")

def delete_cita(to_number, cita):
    # Verifica si la cita está en la lista y la elimina
    response_text = f"Cita para el {cita.strftime('%d de %B a las %H:%M')} eliminada."

    for r_cita in citas_reservadas:
        if r_cita["date"] == cita:
            citas_reservadas.remove(r_cita)
            send_response(to_number, response_text) 
            return
    
    send_response(to_number, "La cita no se encuentra en la lista.") 

def get_next_available_appointment(start_hour=11, end_hour=20):
    now = datetime.now()
    appointment_date = now

    appointment_duration = timedelta(hours=1)

    # Encuentra la próxima hora de cita disponible
    while True:
        if appointment_date.hour >= end_hour:
            # Si es después del horario de citas, pasa al siguiente día
            appointment_date += timedelta(days=1)
            appointment_date = appointment_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        elif appointment_date.hour < start_hour:
            # Si es antes del horario de citas, establece la hora de inicio
            appointment_date = appointment_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        else:
            # Incrementa una hora hasta encontrar una cita disponible
            appointment_date = appointment_date.replace(minute=0, second=0, microsecond=0)
            if all(r_cita["date"] != appointment_date for r_cita in citas_reservadas) and appointment_date > now:
                break
            appointment_date += appointment_duration

    return appointment_date

def mostrar_citas_reservadas(to_number):
    if citas_reservadas:
        response_text = "Citas reservadas:\n"
        for cita in citas_reservadas:
            date_str = cita["date"].strftime('%Y-%m-%d %I:%M %p')
            response_text += f"- {date_str} para {cita['name']}\n"
    else:
        response_text = "No hay citas reservadas."
    
    send_response(to_number, response_text)

def contact_menu(to_number):
    options = [
        {"title": "Contacto", "postbackText": "kevin"},
        {"title": "Ubicacion", "postbackText": "ubicacion"},
        {"title": "Salir", "postbackText": "salir"}
    ]
    send_quick_reply_message(to_number, options)

def send_response(to_number, text):
    url = "https://api.gupshup.io/sm/api/v1/msg"

    payload = {
        "channel": "whatsapp",
        "source": SOURCE_NUMBER,
        "destination": to_number,
        "message": json.dumps({"type": "text", "text": text}),
        "src.name": "myapp",
        "disablePreview": False,
        "encode": False
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": API_KEY
    }

    response = requests.post(url, data=payload, headers=headers)
    print(f"Response for {to_number}: {response.text}")

def send_quick_reply_message(to_number, options, text="¿Qué deseas hacer?"):
    url = "https://api.gupshup.io/sm/api/v1/msg"

    quick_reply_message = {
        "type": "quick_reply",
        "msgid": "qr1",
        "content": {
            "type": "text",
            "header": "KevinStyle",
            "text": text,
            "caption": "Elige una de las siguientes opciones:"
        },
        "options": [
            {
                "type": "text",
                "title": option["title"],
                "postbackText": option["postbackText"]
                
            } for option in options
        ]
    }

    payload = {
        "channel": "whatsapp",
        "source": SOURCE_NUMBER,
        "destination": to_number,
        "message": json.dumps(quick_reply_message),
        "src.name": "myapp",
        "disablePreview": False,
        "encode": False
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": API_KEY
    }

    response = requests.post(url, data=payload, headers=headers)
    print(f"Quick reply message response for {to_number}: {response.text}")

def send_list_message(to_number, sections, text="¿Qué deseas hacer?"):
    url = "https://api.gupshup.io/sm/api/v1/msg"

    list_message = {
        "type":"list",
        "title":"KevinStyle",
        "body":text,
        "footer":"Elige una de las siguientes opciones:",
        "msgid":"list1",
        "globalButtons":[
        {
            "type":"text",
            "title":"Global button"
        }
    ],
    "items": [
                {
                    "title": section["title"],
                    "subtitle": section["subtitle"],
                    "options": [
                        {
                            "type": "text",
                            "title": option["title"],
                            "postbackText": option["postbackText"]
                        } for option in section["options"]
                    ]
                } for section in sections
            ]
    }
    
    payload = {
        "channel": "whatsapp",
        "source": SOURCE_NUMBER,
        "destination": to_number,
        "message": json.dumps(list_message),
        "src.name": "myapp",
        "disablePreview": False,
        "encode": False
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": API_KEY
    }

    response = requests.post(url, data=payload, headers=headers)
    print(f"Quick reply message response for {to_number}: {response.text}")

def send_contact(to_number):
    url = "https://api.gupshup.io/sm/api/v1/msg"

    contact = {
        "type":"contact",
        "contact":{
            "addresses":[
            {
            "city":"Menlo Park",
            "country":"United States",
            "countryCode":"us",
            "state":"CA",
            "street":"1 Hacker Way",
            "type":"HOME",
            "zip":"94025"
            },
            {
            "city":"Menlo Park",
            "country":"United States",
            "countryCode":"us",
            "state":"CA",
            "street":"200 Jefferson Dr",
            "type":"WORK",
            "zip":"94025"
            }
            ],
            "birthday":"1995-08-18",
            "emails":
            [
            {
            "email":"personal.mail@gupshup.io",
            "type":"Personal"
            },
            {
            "email":"devsupport@gupshup.io",
            "type":"Work"
            }
        ],
        "name":{
            "firstName":"Kevin",
            "formattedName":"Style",
            "lastName":"Style"
        },
        "org":{
            "company":"Guspshup",
            "department":"Product",
            "title":"Manager"
        },
        "phones":[
            {
            "phone":"+1 (940) 555-1234",
            "type":"HOME"
            },
            {
            "phone":"+1 (650) 555-1234",
            "type":"WORK",
            "wa_id":"16505551234"
            }
        ],
        "urls":[
            {
            "url":"https://www.gupshup.io",
            "type":"WORK"
            }
        ]
    }
    }


    payload = {
        "channel": "whatsapp",
        "source": SOURCE_NUMBER,
        "destination": to_number,
        "message": json.dumps(contact),
        "src.name": "myapp",
        "disablePreview": False,
        "encode": False
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": API_KEY
    }

    response = requests.post(url, data=payload, headers=headers)
    print(f"Quick reply message response for {to_number}: {response.text}")

def send_location_message(to_number):
    url = "https://api.gupshup.io/sm/api/v1/msg"

    location_message = {
   "type":"location",
   "longitude":72.877655,
   "latitude":19.075983,
   "name":"Mumbai",
   "address":"Mumbai, Maharashtra"
}
    
    payload = {
        "channel": "whatsapp",
        "source": SOURCE_NUMBER,
        "destination": to_number,
        "message": json.dumps(location_message),
        "src.name": "myapp",
        "disablePreview": False,
        "encode": False
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": API_KEY
    }

    response = requests.post(url, data=payload, headers=headers)
    print(f"Quick reply message response for {to_number}: {response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    print("Servidor iniciado")