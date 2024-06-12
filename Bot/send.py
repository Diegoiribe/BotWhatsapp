import requests
import json

url = "https://api.gupshup.io/sm/api/v1/msg"

payload = {
   "channel": "whatsapp",
   "source": 5216675014303,  # Reemplaza con tu número registrado en Gupshup, en formato internacional
   "destination": 5216674507062,  # Reemplaza con el número de destino, en formato internacional
   "message": json.dumps({
   "type":"list",
   "title":"title text",
   "body":"body text",
   "footer":"footer text",
   "msgid":"list1",
   "globalButtons":[
      {
         "type":"text",
         "title":"Global button"
      }
   ],
   "items":[
      {
         "title":"first Section",
         "subtitle":"first Subtitle",
         "options":[
            {
               "type":"text",
               "title":"section 1 row 1",
               "description":"first row of first section description",
               "postbackText":"section 1 row 1 postback payload"
            },
            {
               "type":"text",
               "title":"section 1 row 2",
               "description":"second row of first section description",
               "postbackText":"section 1 row 2 postback payload"
            },
            {
               "type":"text",
               "title":"section 1 row 3",
               "description":"third row of first section description",
               "postbackText":"section 1 row 3 postback payload"
            }
         ]
      },
      {
         "title":"second section",
         "subtitle":"second Subtitle",
         "options":[
            {
               "type":"text",
               "title":"section 2 row 1",
               "description":"first row of second section description",
               "postbackText":"section 1 row 3 postback payload"
            }
         ]
      }
   ]
}),
    "src.name": "myapp",
    "disablePreview": False,
    "encode": False
}

headers = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "apikey": "o6botgtule9omsamb70z42udlyzp3cql"  # Reemplaza con tu clave API de Gupshup
}

response = requests.post(url, data=payload, headers=headers)

print(response.text)
