import os

from dotenv import dotenv_values
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from db.db import connect_db, timestamps

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

class CustomerInfoException(Exception):
    "Raised when the customer hasn't required info"
    pass

class CustomerNotFoundException(Exception):
    "Raised when the customer not found"
    pass

db = connect_db(debug=False)
customers = db[config['DB_COLLECTION_C']]

customer_bp=Blueprint('customers_bp',__name__)

#Routes to customers collection
@customer_bp.route('/customers', methods=['POST'])
def handle_list_customers():
    filter = request.json
    
    list_customer = [{**customer, '_id': str(customer['_id'])} for customer in customers.find().sort('created_at', -1)]

    return list_customer

@customer_bp.route('/customer', methods=['GET'])
def handle_consult_customer():
    try:
        tel = str(request.args.get('tel'))
        customer = customers.find_one({'Telefono': "+"+tel})
        if not customer:
            raise CustomerNotFoundException
        resp = {**customer, '_id': str(customer['_id'])}, 500
    except CustomerNotFoundException:
        resp = {'message':'Customer not found'}, 400
    except Exception as e:
        print(e)
        resp = {'message':'Something went wrong'}, 400

    return resp
    
@customer_bp.route('/customer', methods=['POST'])
def handle_create_customer():
    try:
        customer = request.json
        if not customer['Nombre'] or not customer['Telefono']:
            raise CustomerInfoException
                    
        customers.insert_one(timestamps(customer))
        resp = {'message': 'Customer created'}, 200

    except CustomerInfoException:
        resp = {'message': "Customer hasn't required info"}, 400

    except DuplicateKeyError:
        resp = {'message': 'Customer is already created'}, 400

    except Exception as e: 
        print(e)
        resp = {'message': 'Something went wrong'}, 400
    

    return resp

@customer_bp.route('/customer', methods=['PUT'])
def handle_update_customer():
    try:
        customerInfo = request.json
        if not customerInfo['Telefono'] or not customerInfo['Nombre']:
            raise CustomerInfoException
        customer = customers.find_one_and_update({'Telefono':customerInfo['Telefono']}, {'$set':timestamps(customerInfo,True)})
        if not customer:
            raise CustomerNotFoundException
        resp = {'message': 'Customer updated'}, 200
    except CustomerInfoException:
        resp = {'message': "Customer hasn't required info"}, 400
    except CustomerNotFoundException:
        resp = {'message': "Customer not found"}, 400
    except Exception as e:
        print(e)
        resp = {'message': "Something went wrong"}, 400
    
    return resp

@customer_bp.route('/customer', methods=['DELETE'])
def handle_delete_customer():
    return 'delete customer'