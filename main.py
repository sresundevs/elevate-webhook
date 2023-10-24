from datetime import datetime as dt
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
customers = db[config['DB_COLLECTION_C']]
purchases = db[config['DB_COLLECTION_P']]


def messageToSend(customer, purchaseData):
    messages = {
        'APPROVED':f'me complace informarte que tu pago fue aprobado. Por favor verifica tu email {purchaseData["data"]["buyer"]["email"]}, dado que te estaremos enviando un email con la factura y otro con un acceso para que definas la contraseña de tu usuario y puedas acceder al curso. Felicitaciones.',
        'EXPIRED':'lamentablemente la tarjeta con la que ha intentado realizar el pago esta expirada, por favor intente con otra.',
        'BLOCKED':'lamentablemente la tarjeta con la que ha intentado pagar esta bloqueada, por favor intente con otra.',
        'NO_FUNDS':'lamentablemente la tarjeta con la que ha intentado pagar no tiene fondos suficientes, por favor intente con otra.',
        'CANCELLED':'lamentablemente el pago fue cancelado debido a un problema del procesador de pagos, por favor intente con otra tarjeta. En caso de querer saber más sobre pagos cancelados acceda a: https://help.hotmart.com/pt-BR/article/Como-funciona-o-processo-de-compra-na-Hotmart-Por-que-minha-compra-foi-cancelada-/203456160'
    }
    try:
        return f'Estimado {customer["Nombre"]}, {messages[purchaseData["data"]["purchase"]["status"]]}'
    except:
        return None

#Flask app to listen Webhook from Hotmart
app = Flask(__name__)

@app.route('/purchase_event', methods=['POST'])
def handle_purchase_event():
    
    try:
        purchaseData = request.json
        #print(purchaseData)
        telefono = purchaseData["data"]["buyer"]["checkout_phone"]
        email = purchaseData["data"]["buyer"]["email"]

        customer = customers.find_one({'$or':[{'Telefono':"+"+telefono},{'Email':email}]})
    
        leadData = leads.find_one({'Telefono':customer["Telefono"]})
        #print(leadData)
        #print(customer)
        message = messageToSend(customer, purchaseData)
        #print(message)
        data = {
            "IdCompra": purchaseData["data"]["purchase"]["transaction"],
            "FechaCompra": dt.utcfromtimestamp(int(purchaseData["data"]["purchase"]["order_date"])/1000),
            "CompraVerificable": "Yes",
            "MetodoPago": f'Hotmart - {purchaseData["data"]["purchase"]["payment"]["type"]}',
            "PagoAprobado": "Yes" if purchaseData["data"]["purchase"]["status"] == "APPROVED" else "Not"
            }
        
        #print(data)
        purchasesInfo = purchases.find_one({'Telefono':customer["Telefono"]})
        sendMessage = False
        if purchasesInfo:
            existingPurchase = None
            for info in purchasesInfo["InfoCompras"]:    
                if info["IdCompra"] == data["IdCompra"]:
                    existingPurchase = info
                    break
            if existingPurchase:
                indexPurchase = purchasesInfo["InfoCompras"].index(existingPurchase)
                purchasesInfo["InfoCompras"][indexPurchase] = data
                purchases.update_one({'Telefono':purchasesInfo["Telefono"]},{'$set':purchasesInfo})

                if existingPurchase["PagoAprobado"] == "Not" and data["PagoAprobado"]=="Yes" : 
                    sendMessage = True
            else:
                purchases.update_one({'Telefono':purchasesInfo["Telefono"]},{'$push':{"InfoCompras":data}})
                sendMessage = True

        else:
            purchases.insert_one({'Telefono':customer["Telefono"],'InfoCompras':[data]})
            sendMessage = True

        if message and sendMessage:
            lead = leadData["lead"]
            lola = LolaMessageSender(lead, config["ASSISTANT_TOKEN"], config['PROMPTER_URL'])    
            lola.send_text_message(message)
            print("Mensaje enviado")
        else:
            print('Mensaje no enviado')
        
        
        
        
    except Exception as e:
        print(e)
        

    return json.dumps(None), 200 , {'Content-Type': 'application/json'}
    

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))


