from datetime import datetime as dt

from bson import ObjectId
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from db.db import connect_db, timestamps
from utils.auth import verify_token

class EscalationInfoException(Exception):
    "Raised when the escalation hasn't required info"
    pass

class EscalationNotFoundException(Exception):
    "Raised when the escalation not found"
    pass

customers = connect_db().customers
escalations = connect_db().escalations

escalations_bp = Blueprint('escalations_bp',__name__)

#Routes to escalations collection
@escalations_bp.route('/escalations', methods=['POST'])
@verify_token
def handle_list_escalations():
    filter = request.json
    
    if len(filter['range']) == 0:
        list_escalation = [{**escalation, '_id': str(escalation['_id']),  **customers.find_one({'Telefono':escalation['Telefono']},{'_id':0})} for escalation in escalations.find()]
    else:
        dates = [dt.fromisoformat(date) for date in filter['range']]
        list_escalation = [{**escalation, '_id': str(escalation['_id']),  **customers.find_one({'Telefono':escalation['Telefono']},{'_id':0})} for escalation in escalations.find({'FechaEscalamiento': {'$gte': dates[0], '$lte': dates[1]}})] 
        
    return list_escalation

@escalations_bp.route('/escalation', methods=['GET'])
@verify_token
def handle_consult_escalation():
    try:
        id = str(request.args.get('id'))
        escalation = escalations.find_one({'_id':ObjectId(id)})
        if not escalation:
            raise EscalationNotFoundException
        resp = {**escalation, '_id': str(escalation['_id']), **customers.find_one({'Telefono':escalation['Telefono']}, {'_id': 0})}, 200
    except EscalationNotFoundException:
        resp = {'message':'Escalation not found'}, 400
    except Exception as e:
        print(e)
        resp = {'message':'Something went wrong'}, 400

    return resp

@escalations_bp.route('/escalation', methods=['POST'])
@verify_token
def handle_create_escalation():
    try:
        escalation = request.json
        if not escalation['Telefono'] or not escalation['FechaEscalamiento']:
            raise EscalationInfoException
                    
        escalations.insert_one(timestamps(escalation))
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
@verify_token
def handle_update_escalation():
    try:
        escalationInfo = request.json
        if not escalationInfo['Telefono'] or not escalationInfo['FechaEscalamiento'] or not escalationInfo['_id']:
            raise EscalationInfoException
        escalation = escalations.find_one_and_update({'_id':ObjectId(escalationInfo['_id'])}, {'$set':timestamps(escalationInfo, True)})
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
@verify_token
def handle_delete_escalation():
    return 'OK' 