import json
import os

from dotenv import dotenv_values
from flask import Flask, request
from lolapy import LolaMessageSender
from db import connect_db

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

db = connect_db()

leads = db[config['DB_COLLECTION_L']]
#customers = db[config['DB_COLLECTION_C']]

#Flask app to listen Webhook from Hotmart
app = Flask(__name__)

@app.route('/purchase_event', methods=['POST'])
def handle_purchase_event():
    purchaseData = request.json
    #print(purchaseData)
    phone = purchaseData["data"]["buyer"]["checkout_phone"]
    email = purchaseData["data"]["buyer"]["email"]
    leadData = leads.find_one({'$or':[{'Telefono':phone},{'Email':email}]})
    #print(leadData)
    if leadData: 
        lead = leadData["lead"]
        lola = LolaMessageSender(lead, config["ASSISTANT_TOKEN"], config['PROMPTER_URL'])    
        lola.send_text_message("Compra confirmada")
        message="Compra con asistente"
    else:
        print("Telefono no registrado en base de datos")
        message="Compra sin asistente"

    return json.dumps({message:"Hola mundo"}), 200 , {'Content-Type': 'application/json'}
    

app.run(host=config['HOST'],port=config['PORT_PURCHASE'])