from flask import Flask,request

app= Flask(__name__)

@app.route('/')
def index():
    return "Hola mundo"

@app.route('/params')
def params():
    params=request.args.get('params1','No contiene parametros')
    return params

if __name__ == '__main__':
    app.run(debug=True,port=8000)