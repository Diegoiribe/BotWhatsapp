from twilio.rest import Client



client = Client(account_sid, auth_token)



client.messages.create(body="Ahoy Woeld!",
                        from_=from_whatsapp_number,
                        to=to_whatsapp_number)