import os

from dotenv import dotenv_values
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from db.db import connect_db

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

class EscalationInfoException(Exception):
    "Raised when the escalation hasn't required info"
    pass

class EscalationNotFoundException(Exception):
    "Raised when the escalation not found"
    pass

db = connect_db(debug=False)
customers = db[config['DB_COLLECTION_C']]
escalations = db[config['DB_COLLECTION_E']]

escalations_bp = Blueprint('escalations_bp',__name__)

#Routes to escalations collection
@escalations_bp.route('/escalations', methods=['GET'])
def handle_list_escalations():
    agg = [{'$group':{'_id': "$Telefono", 'FechasEscalamiento': {"$push":{"FechaEscalamiento":"$FechaEscalamiento", "_id":"$_id"}}}}]
    list_escalation = [{**escalation,  **customers.find_one({'Telefono':escalation['_id']},{'_id':0})} for escalation in escalations.aggregate(agg)]
    return list_escalation

@escalations_bp.route('/escalation', methods=['GET'])
def handle_consult_escalation():
    try:
        tel = str(request.args.get('tel'))
        agg = [{'$match':{'Telefono': "+"+tel}},{'$group':{'_id': "$Telefono", 'FechasEscalamiento': {"$push":{"FechaEscalamiento":"$FechaEscalamiento", "_id":"$_id"}}}}]
        escalation_list = list(escalations.aggregate(agg))
        if not escalation_list:
            raise EscalationNotFoundException
        escalation = escalation_list[0]
        resp = {**escalation, **customers.find_one({'Telefono':escalation['_id']}, {'_id': 0})}, 200
    except EscalationNotFoundException:
        resp = {'message':'Escalation not found'}, 400
    except Exception as e:
        print(e)
        resp = {'message':'Something went wrong'}, 400

    return resp

@escalations_bp.route('/escalation', methods=['POST'])
def handle_create_escalation():
    try:
        escalation = request.json
        if not escalation['Telefono'] or not escalation['FechaEscalamiento']:
            raise EscalationInfoException
                    
        escalations.insert_one(escalation)
        resp = {'message': 'Escalation created'}, 200

    except EscalationInfoException:
        resp = {'message': "Escalation hasn't required info"}, 400

    except DuplicateKeyError:
        resp = {'message': 'Escalation is already created'}, 400

    except Exception as e: 
        print(e)
        resp = {'message': 'Something went wrong'}, 400
    

    return resp

@escalations_bp.route('/escalation', methods=['PUT'])
def handle_update_escalation():
    try:
        escalationInfo = request.json
        if not escalationInfo['Telefono'] or not escalationInfo['FechaEscalamiento'] or not escalationInfo['_id']:
            raise EscalationInfoException
        escalation = escalations.find_one_and_update({'_id':escalationInfo['_id']}, {'$set':escalationInfo})
        if not escalation:
            raise EscalationNotFoundException
        resp = {'message': 'Escalation updated'}, 200
    except EscalationInfoException:
        resp = {'message': "Escalation hasn't required info"}, 400
    except EscalationNotFoundException:
        resp = {'message': "Escalation not found"}, 400
    except Exception as e:
        print('error', )
        resp = {'message': "Something went wrong"}, 400
    
    return resp

@escalations_bp.route('/escalation', methods=['DELETE'])
def handle_delete_escalation():
    return 'OK' 