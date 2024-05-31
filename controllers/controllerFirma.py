import logging, json, requests, os, base64
from flask import Flask,jsonify,request, Response
from models.firma import firmar
from models.firma_electronica import ElectronicSign

def postFirmaElectronica(data):
    response_array=[]
    try:
        for i in range(len(data)):
            IdDocumento = data[i]['IdTipoDocumento']
            res = requests.get(str(os.environ['DOCUMENTOS_CRUD_URL'])+'/tipo_documento/'+str(IdDocumento))
            
            if res.status_code != 200:
                return Response(json.dumps({'Status':'404','Error': str("the id "+str(data[i]['IdTipoDocumento'])+" does not exist in documents_crud")}), status=404, mimetype='application/json')

            res_json = json.loads(res.content.decode('utf8').replace("'", '"'))
            blob = base64.b64decode(data[i]['file'])
            with open(os.path.expanduser('./documents/documentToSign.pdf'), 'wb') as fout:
                fout.write(blob)
            jsonFirmantes = {
                    "firmantes": data[i]["firmantes"],
                    "representantes": data[i]["representantes"],
            }
            all_metadata = str({** data[i]['metadatos']}).replace("{'", '{\\"').replace("': '", '\\":\\"').replace("': ", '\\":').replace(", '", ',\\"').replace("',", '",').replace('",' , '\\",').replace("'}", '\\"}').replace('\\"', '\"')
            DicPostDoc = {
                'Metadatos': all_metadata,
                'Nombre': data[i]['nombre'],
                "Descripcion": data[i]['descripcion'],
                'TipoDocumento':  res_json,
                'Activo': True
            }
            resPost = requests.post(str(os.environ['DOCUMENTOS_CRUD_URL'])+'/documento', json=DicPostDoc).content
            responsePostDoc = json.loads(resPost.decode('utf8').replace("'", '"'))
            firma_electronica = firmar(str(data[i]['file']))
            electronicSign = ElectronicSign()
            firma_completa = electronicSign.firmaCompleta(firma_electronica["llaves"]["firma"], responsePostDoc["Id"])
            objFirmaElectronica = {
                "Activo": True,
                "CodigoAutenticidad": firma_electronica["codigo_autenticidad"],
                "FirmaEncriptada": firma_completa,
                "Firmantes": json.dumps(jsonFirmantes),
                "Llaves": json.dumps(firma_electronica["llaves"]),
                "DocumentoId": {"Id": responsePostDoc["Id"]},
            }
            reqPostFirma = requests.post(str(os.environ['DOCUMENTOS_CRUD_URL'])+'firma_electronica', json=objFirmaElectronica).content
            responsePostFirma = json.loads(reqPostFirma.decode('utf8').replace("'", '"'))
            datos = {
                "firma": responsePostFirma["Id"],
                "firmantes": data[i]["firmantes"],
                "representantes": data[i]["representantes"],
                "tipo_documento": res_json["Nombre"],
            }
            electronicSign.estamparFirmaElectronica(datos)
            jsonStringFirmantes = {
                "firmantes": json.dumps(data[i]["firmantes"]),
                "representantes": json.dumps(data[i]["representantes"])
            }

            all_metadata = str({** firma_electronica, ** data[i]['metadatos'],  ** jsonStringFirmantes}).replace("{'", '{\\"').replace("': '", '\\":\\"').replace("': ", '\\":').replace(", '", ',\\"').replace("',", '",').replace('",' , '\\",').replace("'}", '\\"}').replace('\\"', '\"').replace("[", "").replace("]", "").replace('"{', '{').replace('}"', '}').replace(": ", ":").replace(", ", ",").replace("[", "").replace("]", "").replace("},{", ",")
            DicPostDoc = {
                'Metadatos': all_metadata,
                "firmantes": data[i]["firmantes"],
                "representantes": data[i]["representantes"],
                'Nombre': data[i]['nombre'],
                "Descripcion": data[i]['descripcion'],
                'TipoDocumento' :  res_json,
                'Activo': True
            }

            putUpdateJson = [{
                "IdTipoDocumento": data[i]['IdTipoDocumento'],
                "nombre": data[i]['nombre'],
                "metadatos": all_metadata,
                "descripcion": data[i]['descripcion'],
                "file": str(electronicSign.docFirmadoBase64()),
                "idDocumento": responsePostDoc["Id"]
            }]
            reqPutFirma = requests.put(str(os.environ['GESTOR_DOCUMENTAL_URL'])+'document/putUpdate', json=putUpdateJson).content
            responsePutUpdate = json.loads(reqPutFirma.decode('utf8').replace("'", '"'))
            response_array.append(responsePutUpdate)
        responsePutUpdate = response_array if len(response_array) > 1 else responsePutUpdate
        return Response(json.dumps({'Status':'200', 'res':responsePutUpdate}), status=200, mimetype='application/json')
    except Exception as e:
        logging.error("type error: " + str(e))

        if str(e) == "'IdTipoDocumento'":
            error_dict = {'Status':'the field IdTipoDocumento is required','Code':'400'}
            return Response(json.dumps(error_dict), status=400, mimetype='application/json')
        elif str(e) == "'nombre'":
            error_dict = {'Status':'the field nombre is required','Code':'400'}
            return Response(json.dumps(error_dict), status=400, mimetype='application/json')
        elif str(e) == "'file'":
            error_dict = {'Status':'the field file is required','Code':'400'}
            return Response(json.dumps(error_dict), status=400, mimetype='application/json')
        elif str(e) == "'metadatos'":
            error_dict = {'Status':'the field metadatos is required','Code':'400'}
            return Response(json.dumps(error_dict), status=400, mimetype='application/json')
        elif '400' in str(e):
            DicStatus = {'Status':'invalid request body', 'Code':'400'}
            return Response(json.dumps(DicStatus), status=400, mimetype='application/json')
        return Response(json.dumps({'Status':'500','Error':str(e)}), status=500, mimetype='application/json')
