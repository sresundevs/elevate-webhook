from datetime import datetime as dt

from bson import ObjectId
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from db.db import connect_db, timestamps
from utils.auth import verify_token

class PurchaseInfoException(Exception):
    "Raised when the purchase hasn't required info"
    pass

class PurchaseNotFoundException(Exception):
    "Raised when the purchase not found"
    pass

customers = connect_db().customers
purchases = connect_db().purchases

purchases_bp = Blueprint('purchases_bp',__name__)

#Routes to purchases collection
@purchases_bp.route('/purchases', methods=['POST'])
@verify_token
def handle_list_purchases():
    filter = request.json
    
    if len(filter['range']) == 0:
        list_purchase = [
            {**purchase, '_id': str(purchase['_id']), **customers.find_one({'Telefono': purchase['Telefono']}, {'_id': 0})}
            for purchase in purchases.find().sort('created_at', -1)
        ]
    else:
        dates = [dt.fromisoformat(date) for date in filter['range']]
        list_purchase = [
            {**purchase, '_id': str(purchase['_id']), **customers.find_one({'Telefono': purchase['Telefono']}, {'_id': 0})}
            for purchase in purchases.find({'FechaCompra': {'$gte': dates[0], '$lte': dates[1]}}).sort('created_at', -1)
        ]
        
    return list_purchase

@purchases_bp.route('/purchase', methods=['GET'])
@verify_token
def handle_consult_purchase():
    try:
        id = str(request.args.get('id'))
        purchase = purchases.find_one({'_id': ObjectId(id)})
        if not purchase:
            raise PurchaseNotFoundException
        resp = {**purchase, '_id': str(purchase['_id']), **customers.find_one({'Telefono': purchase['Telefono']}, {'_id': 0})}, 200
    except PurchaseNotFoundException:
        resp = {'message':'Purchase not found'}, 400
    except Exception as e:
        print(e)
        resp = {'message':'Something went wrong'}, 400

    return resp

@purchases_bp.route('/purchase', methods=['POST'])
@verify_token
def handle_create_purchase():
    try:
        purchase = request.json
        if not purchase['Telefono']:
            raise PurchaseInfoException
        purchases.insert_one(timestamps(purchase))
        resp = {'message': 'Purchase created'}, 200
    except PurchaseInfoException:
        resp = {'message': "Purchase hasn't required info"}, 400
    except DuplicateKeyError:
        resp = {'message': 'Purchase is already created'}, 400
    except Exception as e: 
        print(e)
        resp = {'message': 'Something went wrong'}, 400

    return resp

@purchases_bp.route('/purchase', methods=['PUT'])
@verify_token
def handle_update_purchase():
    try:
        purchaseInfo = request.json
        if not purchaseInfo['_id']:
            raise PurchaseInfoException
        id = purchaseInfo['_id']
        purchaseInfo.pop('_id')
        purchase = purchases.find_one_and_update({'_id':ObjectId(id)}, {'$set':timestamps(purchaseInfo, True)})
        if not purchase:
            raise PurchaseNotFoundException
        resp = {'message': 'Purchase updated'}, 200
    except PurchaseInfoException:
        resp = {'message': "Purchase hasn't required info"}, 400
    except PurchaseNotFoundException:
        resp = {'message': "Purchase not found"}, 400
    except Exception as e:
        print('error', e)
        resp = {'message': "Something went wrong"}, 400
    
    return resp

@purchases_bp.route('/purchase', methods=['DELETE'])
@verify_token
def handle_delete_purchase():
    return 'OK' 