import json
import os
from datetime import datetime as dt

from dotenv import dotenv_values
from flask import Blueprint, request
from lolapy import LolaMessageSender
import pytz
import stripe

from db.db import connect_db, timestamps

webhooks_bp = Blueprint('webhooks_bp',__name__)

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

tz = pytz.timezone(config['TIMEZONE'])

db = connect_db()
leads = db[config['DB_COLLECTION_L']]
customers = db[config['DB_COLLECTION_C']]
purchases = db[config['DB_COLLECTION_P']]

def messageToSend(customer, purchaseData):
    messages = {
        'APPROVED':f'me complace informarte que tu pago fue aprobado. Por favor verifica tu email {purchaseData["data"]["buyer"]["email"]}, dado que te estaremos enviando un email con la factura y otro con un acceso para que definas la contraseña de tu usuario y puedas acceder al curso. Felicitaciones.',
        'EXPIRED':'lamentablemente la tarjeta con la que ha intentado realizar el pago esta expirada, por favor intente con otra.',
        'BLOCKED':'lamentablemente la tarjeta con la que ha intentado pagar esta bloqueada, por favor intente con otra.',
        'NO_FUNDS':'lamentablemente la tarjeta con la que ha intentado pagar no tiene fondos suficientes, por favor intente con otra.',
        'CANCELED':'lamentablemente el pago fue cancelado debido a un problema del procesador de pagos, por favor intente con otra tarjeta. En caso de querer saber más sobre pagos cancelados acceda a: https://help.hotmart.com/pt-BR/article/Como-funciona-o-processo-de-compra-na-Hotmart-Por-que-minha-compra-foi-cancelada-/203456160'
    }
    try:
        return f'Estimado {customer["Nombre"]}, {messages[purchaseData["data"]["purchase"]["status"]]}'
    except Exception as e:
        print(">>> Error", e)
        return None

#Route to listen event in hotmart
@webhooks_bp.route('/event_hotmart', methods=['POST'])
def handle_event_hotmart():
    
    try:
        purchaseData = request.json
        telefono = purchaseData["data"]["buyer"]["checkout_phone"]
        email = purchaseData["data"]["buyer"]["email"]

        customer = customers.find_one({'$or':[{'Telefono':"+"+telefono},{'Email':email}]})
    
        leadData = leads.find_one({'Telefono':customer["Telefono"]})
        
        message = messageToSend(customer, purchaseData)

        print(">>> MESSAGE", message)
        
        data = {
            "Telefono": customer["Telefono"],
            "IdCompra": purchaseData["data"]["purchase"]["transaction"],
            "FechaCompra": dt.utcfromtimestamp(int(purchaseData["data"]["purchase"]["order_date"])/1000).replace(tzinfo=pytz.utc).astimezone(tz),
            "CompraVerificable": "Yes",
            "MetodoPago": f'Hotmart - {purchaseData["data"]["purchase"]["payment"]["type"]}',
            "PagoAprobado": "Yes" if purchaseData["data"]["purchase"]["status"] == "APPROVED" else "Not",
            "Status": purchaseData["data"]["purchase"]["status"],
            }
        
        purchase = purchases.find_one({"IdCompra":data["IdCompra"]})

        print(">>> PURCHASE", purchase)

        sendMessage = False
        if purchase:
            purchases.update_one({'IdCompra':data["IdCompra"]},{'$set': timestamps(data,True)})
            if purchase["PagoAprobado"] == "Not" and data["PagoAprobado"] == "Yes":
                sendMessage = True
        else:
            purchases.insert_one(timestamps(data))
            sendMessage = True

        print(">>> SEND MESSAGE", sendMessage)

        if message and sendMessage:
            lead = leadData["lead"]
            print(">>> LEAD", lead)
            print(">>> CONFIG", config["ASSISTANT_TOKEN"], config['PROMPTER_URL'])
            lola = LolaMessageSender(lead, config["ASSISTANT_TOKEN"], config['PROMPTER_URL'])    
            lola.send_text_message(message)
            print("Mensaje enviado")
        else:
            print('Mensaje no enviado')
        
    except Exception as e:
        print(e)
        

    return json.dumps(None), 200 , {'Content-Type': 'application/json'}

#Route to listen event in stripe    
@webhooks_bp.route('/event_stripe', methods=['POST'])
def handle_event_stripe():
    try:
        stripe.api_key = config['STRIPE_API_KEY']
        endpoint_secret = config['ENDPOINT_SECRET']
        sig_header = request.headers['STRIPE_SIGNATURE']
        payload = request.data
        print('sig_header',sig_header)
        event = stripe.Webhook.construct_event(payload,sig_header,endpoint_secret)
        print(event['type'])
        # if event['type'] == 'payment_intent.succeeded':
        #     payment_intent = event['data']['object']
        #     print(event)
        # else:
        #     print('Unhandled event type {}'.format(event['type']))
    except Exception as e:
        print('ERROR',e)
    return json.dumps(None), 200 , {'Content-Type': 'application/json'}