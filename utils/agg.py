def aggPurchases(range):
    return [
        {
            "$addFields": {
                "FechaCompra": {
                    "$toDate": {
                        "$dateToString": {
                            "date": "$FechaCompra",
                            "timezone": "America/Bogota",
                        }
                    }
                }
            }
        },
        {"$match": {"FechaCompra": {"$gte": range[0], "$lte": range[1]}}},
        {
            "$group": {
                "_id": {
                    "Fecha": {
                        "$dateFromParts": {
                            "year": {"$year": "$FechaCompra"},
                            "month": {"$month": "$FechaCompra"},
                            "day": {"$dayOfMonth": "$FechaCompra"},
                            "timezone": "America/Bogota",
                        }
                    },
                    "CompraVerificable": "$CompraVerificable",
                },
                "Total": {"$sum": 1},
            }
        },
        {
            "$group": {
                "_id": "$_id.Fecha",
                "Compras": {
                    "$push": {
                        "k": "$_id.CompraVerificable",
                        "v": "$Total",
                    }
                },
            }
        },
        {"$addFields": {"Compras": {"$arrayToObject": "$Compras"}}},
        {"$sort": {"_id": 1}},
    ]


def aggCustomers(range):
    return [
        {
            "$addFields": {
                "created_at": {
                    "$toDate": {
                        "$dateToString": {
                            "date": "$created_at",
                            "timezone": "America/Bogota",
                        }
                    }
                }
            }
        },
        {"$match": {"created_at": {"$gte": range[0], "$lte": range[1]}}},
        {
            "$lookup": {
                "from": "purchases",
                "localField": "Telefono",
                "foreignField": "Telefono",
                "as": "purchases",
            }
        },
        {
            "$project": {
                "_id": 0,
                "created_at": {
                    "$dateFromParts": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"},
                        "timezone": "America/Bogota",
                    }
                },
                "Compras": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$purchases"}, 0]},
                        "then": 1,
                        "else": 0,
                    }
                },
            }
        },
        {
            "$group": {
                "_id": "$created_at",
                "Clientes": {"$sum": 1},
                "Compras": {"$sum": "$Compras"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
