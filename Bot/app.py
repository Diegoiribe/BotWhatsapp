from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def receive_message():
    return 'Servidor Listo'

if __name__ == '__main__':
    app.run(port=5000)