import os
from flask import Flask, jsonify, request, send_from_directory
from conf import conf
from controllers import error
from routers import router

app = Flask(__name__) #Creo la app de servidor
error.add_error_handler(app)
router.addRutas(app)
if __name__=='__main__':
    app.run(debug=True,port=int(os.environ['API_PORT']))