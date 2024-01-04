import os
import sys
from datetime import datetime as dt

from dotenv import dotenv_values
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

config = {
    **dotenv_values(".env"),  # load development variables
    **os.environ,  # override loaded values with environment variables
}


def connect_db(debug=False):
    # The mongo client is created
    client = MongoClient(config["DB_URI"], server_api=ServerApi("1"))

    # It checks that there is a connection with the client
    try:
        client.admin.command("ping")
        if debug:
            print("DB Connected")
    except Exception as e:
        print(e)
        sys.exit(1)

    # The db is called
    db = client[config["DB_NAME"]]

    # The collections are called
    customers = db[config["DB_COLLECTION_C"]]
    customers.create_index("Telefono", unique=True)

    leads = db[config["DB_COLLECTION_L"]]
    leads.create_index("Telefono", unique=True)

    return db


def timestamps(document, isUpdate=False):
    if isUpdate:
        document["updated_at"] = dt.utcnow()
    else:
        current_time = dt.utcnow()
        document["created_at"] = current_time
        document["updated_at"] = current_time

    return document
