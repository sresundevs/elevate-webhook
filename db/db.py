
import os
import sys

from dotenv import dotenv_values
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

def connect_db(debug):
    #The mongo client is created
    client = MongoClient(config['DB_URI'], server_api=ServerApi('1')) 

    #It checks that there is a connection with the client
    try:
        client.admin.command('ping')
        if debug: 
            print("DB Connected")
    except Exception as e:
        print(e)
        sys.exit(1)
    
    #The db is called elevate
    db = client[config['DB_NAME']]
    
    #The collection is called customers
    customers = db[config['DB_COLLECTION_C']]
    customers.create_index("Telefono",unique=True)

    leads = db[config['DB_COLLECTION_L']]
    leads.create_index("Telefono",unique=True)

    purchases = db[config['DB_COLLECTION_P']]
    purchases.create_index("Telefono",unique=True)

    return db