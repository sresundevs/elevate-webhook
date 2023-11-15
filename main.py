import os

from dotenv import dotenv_values
from flask import Flask
from flask_cors import CORS


from db.db import connect_db
from routes.customers import customer_bp
from routes.purchases import purchases_bp
from routes.webhooks import webhooks_bp
from routes.escalations import escalations_bp
from routes.users import users_bp
from routes.auth import auth_bp

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

db = connect_db(True)

#Flask app to listen Webhook from Hotmart
app = Flask(__name__)

#config secret key to use jwt
app.config['SECRET_KEY'] = config['SECRET_KEY']


CORS(app)


app.register_blueprint(webhooks_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(purchases_bp)
app.register_blueprint(escalations_bp)
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)

@app.route('/health', methods=['GET'])
def handle_check():
    return 'OK'

if __name__ == '__main__':
    app.run(host=config['HOST'],port=config['PORT'])  #To run in local
    #app.run(port=os.getenv("PORT", default=5000)) #To run in PROD


