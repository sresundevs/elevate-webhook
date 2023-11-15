from datetime import datetime as dt

from bson import ObjectId
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash

from db.db import connect_db, timestamps
from utils.auth import verify_token


class UserInfoException(Exception):
    "Raised when the user hasn't required info"
    pass

class UserNotFoundException(Exception):
    "Raised when the user not found"
    pass

users = connect_db().users

users_bp = Blueprint('users_bp',__name__)

#Routes to users collection
@users_bp.route('/users', methods=['POST'])
@verify_token
def handle_list_users():
    filter = request.json
    if len(filter['range']) == 0:
        list_user = [{**user, '_id': str(user['_id'])} for user in users.find().sort('created_at', -1)]
    else:
        dates = [dt.fromisoformat(date) for date in filter['range']]
        list_user = [{**user, '_id': str(user['_id'])} for user in users.find({'created_at': {'$gte': dates[0], '$lte': dates[1]}}).sort('created_at', -1)]
    return list_user

@users_bp.route('/user', methods=['GET'])
@verify_token
def handle_consult_user():
    try:
        id = str(request.args.get('id'))
        user = users.find_one({'_id': ObjectId(id)})
        if not user:
            raise UserNotFoundException
        resp = {**user, '_id': str(user['_id'])}, 500
    except UserNotFoundException:
        resp = {'message':'User not found'}, 400
    except Exception as e:
        print(e)
        resp = {'message':'Something went wrong'}, 400

    return resp
    
@users_bp.route('/user', methods=['POST'])
@verify_token
def handle_create_user():
    try:
        user = request.json
        if not user['Name'] or not user['LastName'] or not user['Email'] or not user['Password']:
            raise UserInfoException

        user['Active'] = True
        user['Password'] = generate_password_hash(user['Password'])
        users.insert_one(timestamps(user))
        resp = {'message': 'User created'}, 200

    except UserInfoException:
        resp = {'message': "User hasn't required info"}, 400

    except DuplicateKeyError:
        resp = {'message': 'User is already created'}, 400

    except Exception as e: 
        print(e)
        resp = {'message': 'Something went wrong'}, 400
    
    return resp

@users_bp.route('/user', methods=['PUT'])
@verify_token
def handle_update_user():
    try:
        userInfo = request.json
        if not userInfo['_id'] or not userInfo['Name'] or not userInfo['LastName'] or not userInfo['Email']:
            raise UserInfoException
        
        id = userInfo['_id']
        userInfo.pop('_id')
        user = users.find_one_and_update({'_id': ObjectId(id)}, {'$set': timestamps(userInfo,True)})
        
        if not user:
            raise UserNotFoundException
        resp = {'message': 'User updated'}, 200
    except UserInfoException:
        resp = {'message': "User hasn't required info"}, 400
    except UserNotFoundException:
        resp = {'message': "User not found"}, 400
    except Exception as e:
        print(e)
        resp = {'message': "Something went wrong"}, 400
    
    return resp

@users_bp.route('/set_password', methods=['POST'])
@verify_token
def handle_set_password():
    try:
        userInfo = request.json
        if not userInfo['_id'] or not userInfo['Password']:
            raise UserInfoException
        user = users.find_one_and_update({'_id': ObjectId(userInfo['_id'])}, {'$set': timestamps(userInfo,True)})
        if not user:
            raise UserNotFoundException
        resp = {'message': 'User updated'}, 200
    except UserInfoException:
        resp = {'message': "User hasn't required info"}, 400
    except UserNotFoundException:
        resp = {'message': "User not found"}, 400
    except Exception as e:
        print(e)
        resp = {'message': "Something went wrong"}, 400
    return resp



    

@users_bp.route('/user', methods=['DELETE'])
@verify_token
def handle_delete_user():
    return 'delete user'