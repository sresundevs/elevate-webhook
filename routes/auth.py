
import os

from dotenv import dotenv_values
from flask import Blueprint, request
from werkzeug.security import check_password_hash

from db.db import connect_db
from utils.auth import generate_token

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

users = connect_db().users

auth_bp = Blueprint('auth_bp',__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users.find_one({'Email': data['Email']})
    if user and check_password_hash(user['Password'], data["Password"]):
        user['_id'] = str(user['_id'])
        user.pop('Password')
        user['created_at'] = str(user['created_at'])
        user['updated_at'] = str(user['updated_at'])
        token = generate_token(user)
        return {'token': token}, 200
    else:
        return {'message': 'Invalid credentials'}, 401 