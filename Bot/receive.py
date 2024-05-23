from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import re

app = Flask(__name__)


# Estructura para almacenar las citas
appointments = []

# Horarios disponibles
available_hours = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

@app.route('/receive', methods=['GET', 'POST'])
def receive_message():
    incoming_msg = request.values.get('Body', '').lower()
    response = MessagingResponse()
    message = response.message()

    # Verificar si hay un estado guardado en la sesión, si no, establecer estado inicial
    if 'estado' not in session:
        session['estado'] = 'inicio'
        # Mensaje introductorio
        message.body(
            "👋 ¡Hola! Bienvenido a nuestro sistema de citas de corte de cabello. "
            "Puedes agendar una cita diciendo algo como 'cita de corte de cabello'. "
            "También puedes ver tus reservas actuales diciendo 'reservas' o "
            "consultar horarios disponibles diciendo 'horarios disponibles'. "
            "Si en algún momento deseas salir del proceso, simplemente escribe 'salir'.\n\n"
            "¿Cómo puedo ayudarte hoy? 😊\n\n"
            "Opciones:\n1. Cita de Corte de Cabello\n2. Ver Reservas\n3. Horarios Disponibles\n4. Salir"
        )
        return str(response)

    # Estado inicial de la conversación
    if session['estado'] == 'inicio':
        # Verificar si el usuario quiere salir del proceso
        if 'salir' in incoming_msg or incoming_msg == '4':
            message.body("👋 ¡Hasta luego! Si necesitas algo más, no dudes en contactarnos.")
            session.clear()  # Limpiar la sesión
        # Si el mensaje contiene palabras clave como 'cita', 'corte' o 'cabello'
        elif re.search(r'\bcita\b|\bcorte\b|\bcabello\b', incoming_msg) or incoming_msg == '1':
            response_text = get_closest_available_slot()
            session['estado'] = 'esperando_confirmacion'  # Cambiar estado a 'esperando_confirmacion'
            message.body(f"{response_text}\n\n¿Te parece bien esta hora? Responde con 'sí' o 'no'.")
        # Si el mensaje contiene la palabra 'reservas'
        elif 'reservas' in incoming_msg or incoming_msg == '2':
            today = datetime.now().date()
            todays_appointments = [appt for appt in appointments if appt.date() == today]
            if todays_appointments:
                response_text = "📅 **Citas para hoy:**\n" + "\n".join(appt.strftime('%I:%M %p') for appt in todays_appointments)
            else:
                response_text = "📅 **No hay citas para hoy.**"
            message.body(response_text)
        # Si el mensaje contiene 'horarios disponibles'
        elif 'horarios' in incoming_msg or incoming_msg == '3':
            response_text = get_available_slots()
            message.body(response_text)
        # Si el mensaje no coincide con ninguna de las opciones anteriores
        else:
            message.body(
                "❓ **Lo siento, no entendí eso.** Intenta decir 'cita de corte de cabello', 'reservas', 'horarios disponibles' o proporciona una hora en el formato 'HH:MM AM/PM'.\n\n"
                "Opciones:\n1. Cita de Corte de Cabello\n2. Ver Reservas\n3. Horarios Disponibles\n4. Salir\n\n"
                "**Ejemplos válidos:**\n- 10:30 AM\n- 2:00 PM\n\n💡 **Nota:** Asegúrate de usar el formato de 12 horas con AM/PM."
            )
    
    # Estado esperando confirmación del usuario
    elif session['estado'] == 'esperando_confirmacion':
        # Verificar si el usuario quiere salir del proceso
        if 'salir' in incoming_msg or incoming_msg == '4':
            message.body("👋 ¡Hasta luego! Si necesitas algo más, no dudes en contactarnos.")
            session.clear()  # Limpiar la sesión
        # Si el usuario responde 'no' o 'no gracias'
        elif 'no' in incoming_msg:
            message.body("🕒 **¿A qué hora te gustaría?** Por favor, proporciona la hora en el formato 'HH:MM AM/PM'.\n\n**Ejemplos válidos:**\n- 10:30 AM\n- 2:00 PM")
            session['estado'] = 'esperando_hora'  # Cambiar estado a 'esperando_hora'
        # Si el usuario responde 'sí', 'si', 'claro' o 'ok'
        elif 'si' in incoming_msg or 'sí' in incoming_msg or 'claro' in incoming_msg or 'ok' in incoming_msg:
            appointment_datetime_str = session.get('ultima_cita_sugerida', None)
            if appointment_datetime_str:
                appointment_datetime = datetime.strptime(appointment_datetime_str, '%d-%m-%Y a las %I:%M %p')
                if appointment_datetime >= datetime.now():
                    appointments.append(appointment_datetime)
                    message.body(f"✅ **Tu cita para el {appointment_datetime_str} ha sido registrada.**")
                    session['estado'] = 'inicio'  # Volver al estado inicial
                    session.pop('ultima_cita_sugerida', None)
                else:
                    message.body("❌ **No se puede agendar una cita en el pasado.** Por favor, proporciona una nueva fecha y hora.")
                    session['estado'] = 'esperando_hora'
            else:
                message.body("⚠️ **Hubo un error al registrar tu cita. Por favor, intenta nuevamente.**")
                session['estado'] = 'inicio'
        # Si la respuesta del usuario no es clara
        else:
            message.body("❓ **Lo siento, no entendí eso.** ¿Te parece bien la hora sugerida? Por favor responde con 'sí' o 'no'.")
    
    # Estado esperando que el usuario proporcione una hora específica
    elif session['estado'] == 'esperando_hora':
        # Verificar si el usuario quiere salir del proceso
        if 'salir' in incoming_msg or incoming_msg == '4':
            message.body("👋 ¡Hasta luego! Si necesitas algo más, no dudes en contactarnos.")
            session.clear()  # Limpiar la sesión
        else:
            try:
                preferred_time = datetime.strptime(incoming_msg, '%I:%M %p').time()
                now = datetime.now()
                if datetime.combine(now.date(), preferred_time) > now:
                    response_text, new_appointment_datetime_str = get_first_available_day(preferred_time)
                else:
                    response_text, new_appointment_datetime_str = get_first_available_day(preferred_time, check_today=False)
                message.body(f"{response_text}\n\n¿Te parece bien esta hora? Responde con 'sí' o 'no'.")
                session['estado'] = 'esperando_confirmacion'  # Volver a esperar confirmación
                session['ultima_cita_sugerida'] = new_appointment_datetime_str
            except ValueError:
                message.body("⚠️ **Formato de hora incorrecto.** Por favor, usa 'HH:MM AM/PM'.\n\n**Ejemplos válidos:**\n- 10:30 AM\n- 2:00 PM")
                session['estado'] = 'esperando_hora'

    return str(response)

def get_closest_available_slot():
    today = datetime.now().date()
    for days_ahead in range(7):  # Revisa los próximos 7 días
        current_date = today + timedelta(days=days_ahead)
        daily_appointments = [appt for appt in appointments if appt.date() == current_date]

        for hour in available_hours:
            slot_datetime = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour)
            if slot_datetime not in daily_appointments and slot_datetime > datetime.now():
                slot_datetime_str = slot_datetime.strftime('%d-%m-%Y a las %I:%M %p')
                return f"📅 **La próxima cita disponible es el {slot_datetime_str}.**\n\n**¿Te parece bien esta hora?** Responde con 'sí' o 'no'."

    return "❌ **No hay horarios disponibles en los próximos 7 días.**"

def get_available_slots():
    today = datetime.now().date()
    available_slots = []

    for days_ahead in range(7):  # Revisa los próximos 7 días
        current_date = today + timedelta(days=days_ahead)
        daily_appointments = [appt for appt in appointments if appt.date() == current_date]

        for hour in available_hours:
            slot_datetime = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour)
            if slot_datetime not in daily_appointments and slot_datetime > datetime.now():
                available_slots.append(slot_datetime)

        if available_slots:
            break

    if available_slots:
        response_text = "📅 **Horarios disponibles:**\n" + "\n".join(slot.strftime('%d-%m-%Y %I:%M %p') for slot in available_slots)
    else:
        response_text = "❌ **No hay horarios disponibles en los próximos 7 días.**"

    return response_text

def get_first_available_day(preferred_time, check_today=True):
    today = datetime.now().date()
    now = datetime.now()
    for days_ahead in range(30):  # Revisa los próximos 30 días
        current_date = today + timedelta(days=days_ahead)
        daily_appointments = [appt for appt in appointments if appt.date() == current_date]

        if check_today and current_date == today:
            if preferred_time <= now.time():
                continue

        slot_datetime = datetime.combine(current_date, preferred_time)
        if slot_datetime not in daily_appointments and slot_datetime > now:
            slot_datetime_str = slot_datetime.strftime('%d-%m-%Y a las %I:%M %p')
            return f"📅 **El primer día disponible para las {preferred_time.strftime('%I:%M %p')} es el {current_date.strftime('%d-%m-%Y')}.**\n\n**¿Te parece bien esta hora?**", slot_datetime_str

    return "❌ **No hay horarios disponibles en los próximos 30 días para la hora solicitada.**", None

if __name__ == '__main__':
    app.run(port=5000)
