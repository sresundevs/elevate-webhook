import os

from dotenv import dotenv_values
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from db.db import connect_db

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

class PurchaseInfoException(Exception):
    "Raised when the purchase hasn't required info"
    pass

class PurchaseNotFoundException(Exception):
    "Raised when the purchase not found"
    pass

db = connect_db(debug=False)
customers = db[config['DB_COLLECTION_C']]
purchases = db[config['DB_COLLECTION_P']]

purchases_bp = Blueprint('purchases_bp',__name__)

#Routes to purchases collection
@purchases_bp.route('/purchases', methods=['GET'])
def handle_list_purchases():
    list_purchase = [
        {**purchase, '_id': str(purchase['_id']), **customers.find_one({'Telefono': purchase['Telefono']}, {'_id': 0})}
        for purchase in purchases.find()
    ]
    return list_purchase

@purchases_bp.route('/purchase', methods=['GET'])
def handle_consult_purchase():
    try:
        tel = str(request.args.get('tel'))
        purchase = purchases.find_one({'Telefono': "+"+tel})
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
def handle_create_purchase():
    try:
        purchase = request.json
        if not purchase['Telefono']:
            raise PurchaseInfoException
        purchases.insert_one(purchase)
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
def handle_update_purchase():
    try:
        purchaseInfo = request.json
        if not purchaseInfo['Telefono']:
            raise PurchaseInfoException
        purchase = purchases.find_one_and_update({'Telefono':'+'+purchaseInfo['Telefono']}, {'$set':purchaseInfo})
        if not purchase:
            raise PurchaseNotFoundException
        resp = {'message': 'Purchase updated'}, 200
    except PurchaseInfoException:
        resp = {'message': "Purchase hasn't required info"}, 400
    except PurchaseNotFoundException:
        resp = {'message': "Purchase not found"}, 400
    except Exception as e:
        print('error', )
        resp = {'message': "Something went wrong"}, 400
    
    return resp

@purchases_bp.route('/purchase', methods=['DELETE'])
def handle_delete_purchase():
    return 'OK' 