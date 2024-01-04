from functools import wraps
import os
from datetime import datetime as dt
from datetime import timedelta
from flask import request
import jwt
from dotenv import dotenv_values
import pytz

config = {
    **dotenv_values(".env"),  # load development variables
    **os.environ,  # override loaded values with environment variables
}


def generate_token(user: dict):
    return jwt.encode(
        {
            "data": user,
            "exp": dt.utcnow() + timedelta(hours=24),
        },
        config["SECRET_KEY"],
        algorithm="HS256",
    )


def verify_token(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if "Authorization" in request.headers.keys():
            auth = request.headers["Authorization"]
            token = auth.split(" ")[1]
        if not token:
            return {"message": "A valid token is missing!"}, 401
        try:
            jwt.decode(token, config["SECRET_KEY"], algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError, jwt.DecodeError):
            return {"message": "Invalid token!"}, 401
        return f(*args, **kwargs)

    return decorator
