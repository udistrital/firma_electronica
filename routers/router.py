from flask import Flask, jsonify, Blueprint, request, send_from_directory
from controllers import controllerFirma
from flask_restx import Resource, Api
from models.model_params import define_parameters
from conf.conf import api_cors_config
from flask_cors import cross_origin, CORS
#Creo función para capturar la app de server y poder hacer routing
def addRutas(app_main):
    app_main.register_blueprint(docControl, url_prefix='/v1')
#Uso Blueprint para poder utilizar la función route
docControl=Blueprint('docControl', __name__)
CORS(docControl)
#----------INICIO SWAGGER --------------
docDocumentacion = Api(docControl, version='1.0',title="firma_electronica", description='API para la firma electrónica de documentos',doc='/swagger')
docFirmacontroller = docDocumentacion.namespace("firma_electronica", description="methods for electronic signature process")
model_params=define_parameters(docDocumentacion)
#----------FIN SWAGGER ----------------

#Ruta de Home
@docControl.route('/home')
def home():
    return jsonify({'message':'Todo ok'})

#Firma electrónica
@docFirmacontroller.route('/firma_electronica')
class docFirmaElectronica(Resource):
    @docDocumentacion.doc(responses={
        200: 'Success',
        500: 'Nuxeo Error',
        400: 'Bad request'
    }, body=model_params['upload_model'])
    @docFirmacontroller.expect(model_params['request_parser'])
    @cross_origin(**api_cors_config)
    def post(self):
        body=request.get_json()
        return controllerFirma.postFirmaElectronica(body)
#Verificación Firma electrónica
