from datetime import datetime as dt, timedelta

from bson import ObjectId
from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError
import requests

from db.db import connect_db, timestamps
from utils.agg import aggPurchases, aggCustomers
from utils.auth import verify_token
from utils.s3 import upload_from_file, upload_from_url


class PurchaseInfoException(Exception):
    "Raised when the purchase hasn't required info"
    pass


class PurchaseNotFoundException(Exception):
    "Raised when the purchase not found"
    pass


customers = connect_db().customers
purchases = connect_db().purchases

purchases_bp = Blueprint("purchases_bp", __name__)


# Routes to purchases collection
@purchases_bp.route("/purchases", methods=["POST"])
@verify_token
def handle_list_purchases():
    filter = request.json

    if len(filter["range"]) == 0:
        list_purchase = [
            {
                **purchase,
                "_id": str(purchase["_id"]),
                **(
                    customers.find_one({"Telefono": purchase["Telefono"]}, {"_id": 0})
                    if customers.find_one({"Telefono": purchase["Telefono"]})
                    else {"Nombre": "Customer not found"}
                ),
            }
            for purchase in purchases.find().sort("created_at", -1)
        ]
    else:
        dates = [dt.fromisoformat(date) for date in filter["range"]]
        list_purchase = [
            {
                **purchase,
                "_id": str(purchase["_id"]),
                **(
                    customers.find_one({"Telefono": purchase["Telefono"]}, {"_id": 0})
                    if customers.find_one({"Telefono": purchase["Telefono"]})
                    else {"Nombre": "Customer not found"}
                ),
            }
            for purchase in purchases.find(
                {"FechaCompra": {"$gte": dates[0], "$lte": dates[1]}}
            ).sort("created_at", -1)
        ]

    return list_purchase


@purchases_bp.route("/purchase", methods=["GET"])
@verify_token
def handle_consult_purchase():
    try:
        id = str(request.args.get("id"))
        purchase = purchases.find_one({"_id": ObjectId(id)})
        if not purchase:
            raise PurchaseNotFoundException
        resp = {
            **purchase,
            "_id": str(purchase["_id"]),
            **customers.find_one({"Telefono": purchase["Telefono"]}, {"_id": 0}),
        }, 200
    except PurchaseNotFoundException:
        resp = {"message": "Purchase not found"}, 400
    except Exception as e:
        print(e)
        resp = {"message": "Something went wrong"}, 400

    return resp


@purchases_bp.route("/purchase", methods=["POST"])
@verify_token
def handle_create_purchase():
    try:
        purchase = request.json
        if not purchase["Telefono"]:
            raise PurchaseInfoException
        purchases.insert_one(timestamps(purchase))
        resp = {"message": "Purchase created"}, 200
    except PurchaseInfoException:
        resp = {"message": "Purchase hasn't required info"}, 400
    except DuplicateKeyError:
        resp = {"message": "Purchase is already created"}, 400
    except Exception as e:
        print(e)
        resp = {"message": "Something went wrong"}, 400

    return resp


@purchases_bp.route("/purchase", methods=["PUT"])
@verify_token
def handle_update_purchase():
    try:
        if not "_id" in request.form or not "PagoAprobado" in request.form:
            raise PurchaseInfoException
        id = request.form["_id"]
        if not purchases.find_one({"_id": ObjectId(id)}):
            raise PurchaseNotFoundException

        if "Evidencia" in request.files:
            data = request.form.to_dict()
            purchase = purchases.find_one({"_id": ObjectId(id)})
            file = request.files["Evidencia"]
            filename = f"{file.filename.split('.')[0]}_{purchase['FechaCompra'].strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[1]}"
            url = upload_from_file(file, filename)
            print("data", data)
            print("url", url)
        elif "Evidencia" in request.form:
            data = request.form.to_dict()
            purchases.find_one_and_update(
                {"_id": ObjectId(id)}, {"$set": timestamps(data, True)}
            )
        resp = {"message": "Purchase updated"}, 200
    except PurchaseInfoException:
        resp = {"message": "Purchase hasn't required info"}, 400
    except PurchaseNotFoundException:
        resp = {"message": "Purchase not found"}, 400
    except Exception as e:
        print("error", e)
        resp = {"message": "Something went wrong"}, 400

    return resp


@purchases_bp.route("/purchase", methods=["DELETE"])
@verify_token
def handle_delete_purchase():
    return "OK"


@purchases_bp.route("/purchase/upload", methods=["POST"])
@verify_token
def handle_upload_purchase():
    data = request.json
    purchase = purchases.find_one({"_id": ObjectId(data["_id"])})
    namelist = (
        purchase["Evidencia"]
        .split("/")[len(purchase["Evidencia"].split("/")) - 1]
        .split(".")
    )
    filename = f"{namelist[0]}_{purchase['FechaCompra'].strftime('%Y%m%d%H%M%S')}.{namelist[1]}"
    file = requests.get(purchase["Evidencia"]).content
    url = upload_from_url(file, filename)
    if url:
        print("success", url)
        purchases.find_one_and_update(
            {"_id": ObjectId(data["_id"])}, {"$set": {"Evidencia": url}}
        )
    else:
        print("error")

    return "OK"


@purchases_bp.route("/purchasesStats", methods=["POST"])
@verify_token
def handle_get_purchasesStats():
    filter = request.json
    dates = [dt.now() - timedelta(days=60), dt.now()]

    if len(filter["range"]) > 0:
        #dates = [dt.fromisoformat(date) for date in filter["range"]]
        dates = [dt.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ") for date in filter["range"]]        

    pipeline = aggPurchases(dates)
    list_purchase = list(purchases.aggregate(pipeline))

    return list_purchase
