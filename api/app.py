from werkzeug.datastructures import FileStorage
from flask_restx import Resource, Api, fields
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import isoparse
from flask_migrate import Migrate
from flask import Flask, request
from dotenv import load_dotenv
from pathlib import Path
import logging
import pymysql
import json

import os
# configure root logger
logging.basicConfig(level=logging.INFO)

# Change mysql connector to MySQLdb
pymysql.install_as_MySQLdb()


dotenv_path = Path('../.env')
load_dotenv(dotenv_path=dotenv_path)

# get env variables
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
# URL containes port
MYSQL_URL = os.getenv('MYSQL_URL')

# PATHS
PROVIDER_FILE_PATH = Path('../data/providers.json')
SPOTPRICES_FILE_PATH = Path('../data/spotpriser.json')

# create the app
app = Flask(__name__)
# create the extension
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_URL}/{MYSQL_DATABASE}"
logging.info(f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_URL}/{MYSQL_DATABASE}")
db = SQLAlchemy()

# initialize the app with the extension
db.init_app(app)

# DB MODELS


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    consumptions = db.relationship(
        'Consumption', backref='customer', lazy=True)


class Consumption(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_datetime = db.Column(db.DateTime, nullable=False)
    to_datetime = db.Column(db.DateTime, nullable=False)
    consumption = db.Column(db.Float, nullable=False)
    consumption_unit = db.Column(db.String(10), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey(
        'customer.id'), nullable=False)


class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    pricing_model = db.Column(db.String(100), nullable=False)
    monthly_fee = db.Column(db.Float, nullable=False)
    fixed_price = db.Column(db.Float)
    fixed_price_period = db.Column(db.Integer)
    variable_price = db.Column(db.Float)
    variable_price_period = db.Column(db.Integer)
    spot_price = db.Column(db.Float)

# Handler functions


class CustomerHandler:
    def __init__(self, db):
        self.db = db

    def get_customer_by_username(self, username):
        return self.db.session.query(Customer).filter_by(username=username).first()

    def create_customer(self, username):
        customer = Customer(username=username)
        self.db.session.add(customer)
        self.db.session.commit()
        return customer

    def update_customer_username(self, customer_id, new_username):
        customer = self.db.session.query(Customer).get(customer_id)
        customer.username = new_username
        self.db.session.commit()
        return customer

    def delete_customer(self, customer_id):
        customer = self.db.session.query(Customer).get(customer_id)
        self.db.session.delete(customer)
        self.db.session.commit()
        return customer

    def get_or_create_customer(self, username):
        customer = self.get_customer_by_username(username)
        if customer is None:
            customer = self.create_customer(username)
        return customer

    def get_customer_consumptions(self, customer_id):
        customer = self.db.session.query(Customer).get(customer_id)
        return customer.consumptions


class ConsumptionHandler:
    def __init__(self, db):
        self.db = db

    def create_consumption(self, from_datetime, to_datetime, consumption, consumption_unit, customer_id):
        consumption = Consumption(
            from_datetime=isoparse(from_datetime),
            to_datetime=isoparse(to_datetime),
            consumption=consumption,
            consumption_unit=consumption_unit,
            customer_id=customer_id
        )
        self.db.session.add(consumption)
        self.db.session.commit()
        return consumption

    def create_bulk_consumption(self, data, customer_id, remove_old=True):
        # We want to remove old consumption when uploading in bulk.
        if remove_old:
            self.delete_all_consumptions_for_user(customer_id)

        consumptions = []
        for item in data:
            consumptions.append(Consumption(
                from_datetime=isoparse(item['from']),
                to_datetime=isoparse(item['to']),
                consumption=item['consumption'],
                consumption_unit=item['consumptionUnit'],
                customer_id=customer_id
            ))

        self.db.session.bulk_save_objects(consumptions)
        self.db.session.commit()
        return consumptions

    def get_consumption_by_id(self, consumption_id):
        return self.db.session.query(Consumption).get(consumption_id)

    def update_consumption(self, consumption_id, from_datetime, to_datetime, consumption, consumption_unit):
        consumption = self.db.session.query(Consumption).get(consumption_id)
        consumption.from_datetime = isoparse(from_datetime)
        consumption.to_datetime = isoparse(to_datetime)
        consumption.consumption = consumption
        consumption.consumption_unit = consumption_unit
        self.db.session.commit()
        return consumption

    def delete_consumption(self, consumption_id):
        consumption = self.db.session.query(Consumption).get(consumption_id)
        self.db.session.delete(consumption)
        self.db.session.commit()
        return consumption

    # We take abit of a different approach since we are bulk deleting,
    # credit to https://stackoverflow.com/questions/39773560/sqlalchemy-how-do-you-delete-multiple-rows-without-querying
    def delete_all_consumptions_for_user(self, customer_id):
        delete_q = Consumption.__table__.delete().where(
            Consumption.customer_id == customer_id)
        self.db.session.execute(delete_q)
        self.db.session.commit()

    def get_customer_consumptions(self, customer_id):
        return self.db.session.query(Consumption).filter_by(customer_id=customer_id).all()


class ProviderHandler:
    def __init__(self, db):
        self.db = db

    def create_provider(self, name, pricing_model, monthly_fee, fixed_price=None,
                        fixed_price_period=None, variable_price=None,
                        variable_price_period=None, spot_price=None):
        provider = Provider(
            name=name,
            pricing_model=pricing_model,
            monthly_fee=monthly_fee,
            fixed_price=fixed_price,
            fixed_price_period=fixed_price_period,
            variable_price=variable_price,
            variable_price_period=variable_price_period,
            spot_price=spot_price
        )
        self.db.session.add(provider)
        self.db.session.commit()
        return provider

    def get_provider_by_id(self, provider_id):
        return self.db.session.query(Provider).get(provider_id)

    def get_or_create_provider(self, name, pricing_model, monthly_fee, fixed_price=None,
                               fixed_price_period=None, variable_price=None,
                               variable_price_period=None, spot_price=None):
        provider = self.get_provider_by_name(name)
        if provider is None:
            provider = self.create_provider(name, pricing_model, monthly_fee,
                                            fixed_price, fixed_price_period,
                                            variable_price, variable_price_period,
                                            spot_price)
        return provider

    def update_provider(self, provider_id, name=None, pricing_model=None, monthly_fee=None,
                        fixed_price=None, fixed_price_period=None, variable_price=None,
                        variable_price_period=None, spot_price=None):
        provider = self.db.session.query(Provider).get(provider_id)
        if name:
            provider.name = name
        if pricing_model:
            provider.pricing_model = pricing_model
        if monthly_fee:
            provider.monthly_fee = monthly_fee
        if fixed_price is not None:
            provider.fixed_price = fixed_price
        if fixed_price_period is not None:
            provider.fixed_price_period = fixed_price_period
        if variable_price is not None:
            provider.variable_price = variable_price
        if variable_price_period is not None:
            provider.variable_price_period = variable_price_period
        if spot_price is not None:
            provider.spot_price = spot_price
        self.db.session.commit()
        return provider

    def delete_provider(self, provider_id):
        provider = self.db.session.query(Provider).get(provider_id)
        self.db.session.delete(provider)
        self.db.session.commit()
        return provider

    def delete_all_providers(self):
        providers = self.db.session.query(Provider).all()
        for provider in providers:
            self.db.session.delete(provider)
        self.db.session.commit()
        return providers

    def get_all_providers(self):
        return self.db.session.query(Provider).all()


# Migrations
migrate = Migrate(app, db)

# Initualize Handlers
CH = CustomerHandler(db)
CSH = ConsumptionHandler(db)
PH = ProviderHandler(db)

api = Api(app, version='1.0', title='Sample API',
          description='A sample API',
          )

# prepare file uploads parser
upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)
upload_parser.add_argument('name', type=str, location='form')

# Helper functinos, Initualized in this document as HelperMethods
class HelperMethods:
    def __init__(self):
        pass

    def get_spot_prices(self, file_path):
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            file.close()
        return json_data

    def ingest_json_to_customer(self, username, uploaded_file):
        # get or create customer
        customer = CH.get_or_create_customer(username)
        data = json.load(uploaded_file.stream)
        CSH.create_bulk_consumption(data=data, customer_id=customer.id)
        return "Accepted"

    def calculate_best_options_for_user(self, username):
        # Get neccesary data
        customer = CH.get_customer_by_username(username=username)
        providers = PH.get_all_providers()
        spotprices = self.get_spot_prices(SPOTPRICES_FILE_PATH)
        consumption_data = CSH.get_customer_consumptions(
            customer_id=customer.id)

        # first we locate the independent monthly averages
        # this could have been done through datetime manipulation, but for
        # the sace of simplicity i will simply do so using dicts and string
        # manipulations, since we know the format is iso. In a perfect world
        # this information will be stored somewhere else, e.g. a in a database
        # or grabbed through an api.

        # '12': {'NO1': 2495.197829999998, 'NO2': 2495.162239999998, 'NO3': 1684.75557, 'NO4': 732.3229399999994, 'NO5': 2503.085129999998, 'n': 743}
        monthly_average_spot_price = {}

        for price in spotprices.keys():
            # If established month, add together data
            if price[5:7] in monthly_average_spot_price.keys():
                monthly_average_spot_price[price[5:7]
                                           ]["NO1"] += spotprices[price]["NO1"]
                monthly_average_spot_price[price[5:7]
                                           ]["NO2"] += spotprices[price]["NO2"]
                monthly_average_spot_price[price[5:7]
                                           ]["NO3"] += spotprices[price]["NO3"]
                monthly_average_spot_price[price[5:7]
                                           ]["NO4"] += spotprices[price]["NO4"]
                monthly_average_spot_price[price[5:7]
                                           ]["NO5"] += spotprices[price]["NO5"]
                monthly_average_spot_price[price[5:7]]["n"] += 1
                pass
            # If new month, add base prices
            else:
                monthly_average_spot_price[price[5:7]] = {
                    "NO1": spotprices[price]["NO1"],
                    "NO2": spotprices[price]["NO2"],
                    "NO3": spotprices[price]["NO3"],
                    "NO4": spotprices[price]["NO4"],
                    "NO5": spotprices[price]["NO5"],
                    "n": 1
                }

        # Return payload:
        payload = []
        # Calculate cost
        for provider in providers:
            if provider.pricing_model == 'variable':
                # when variable, we persume the spot price is already accounted in,
                # and only look to take the consumed kwh times the price.
                use = 0.00
                for consumption in consumption_data:
                    use += consumption.consumption * provider.variable_price

                payload.append({
                    "name": provider.name,
                    "pricingModel": "variable",
                    "variablePrice": provider.variable_price,
                    "cost_based_on_user_history": {
                        "NO1": use,
                        "NO2": use,
                        "NO3": use,
                        "NO4": use,
                        "NO5": use
                    },
                })

            elif provider.pricing_model == 'fixed':
                # when fixed, we persume the spot price is already accounted in,
                # and only look to take the comsued kwh times the price.
                use = 0.00
                for consumption in consumption_data:
                    use += consumption.consumption * provider.fixed_price

                payload.append({
                    "name": provider.name,
                    "pricingModel": "fixed",
                    "fixedPrice": provider.fixed_price,
                    "cost_based_on_user_history": {
                        "NO1": use,
                        "NO2": use,
                        "NO3": use,
                        "NO4": use,
                        "NO5": use
                    },
                })

            elif provider.pricing_model == 'spot-hourly':
                # when spot-hourly, we calculate each hour as independent.
                use_no1 = 0.00
                use_no2 = 0.00
                use_no3 = 0.00
                use_no4 = 0.00
                use_no5 = 0.00
                for consumption in consumption_data:

                    time_key = (consumption.from_datetime).isoformat()

                    use_no1 += consumption.consumption * \
                        (provider.spot_price + spotprices[time_key]["NO1"])
                    use_no2 += consumption.consumption * \
                        (provider.spot_price + spotprices[time_key]["NO2"])
                    use_no3 += consumption.consumption * \
                        (provider.spot_price + spotprices[time_key]["NO3"])
                    use_no4 += consumption.consumption * \
                        (provider.spot_price + spotprices[time_key]["NO4"])
                    use_no5 += consumption.consumption * \
                        (provider.spot_price + spotprices[time_key]["NO5"])

                payload.append({
                    "name": provider.name,
                    "pricingModel": "spot-hourly",
                    "fixedPrice": provider.spot_price,
                    "cost_based_on_user_history": {
                        "NO1": use_no1,
                        "NO2": use_no2,
                        "NO3": use_no3,
                        "NO4": use_no4,
                        "NO5": use_no5
                    },
                })

            elif provider.pricing_model == 'spot-monthly':
                # when spot-monthly, we persume average monthly spot price
                use_no1 = 0.00
                use_no2 = 0.00
                use_no3 = 0.00
                use_no4 = 0.00
                use_no5 = 0.00
                for consumption in consumption_data:

                    relevant_month = monthly_average_spot_price.get(
                        consumption.from_datetime.strftime('%m'), 0)

                    relevant_month_n = relevant_month['n']

                    use_no1 += consumption.consumption * \
                        (provider.spot_price +
                         (relevant_month['NO1']/relevant_month_n))
                    use_no2 += consumption.consumption * \
                        (provider.spot_price +
                         (relevant_month['NO2']/relevant_month_n))
                    use_no3 += consumption.consumption * \
                        (provider.spot_price +
                         (relevant_month['NO3']/relevant_month_n))
                    use_no4 += consumption.consumption * \
                        (provider.spot_price +
                         (relevant_month['NO4']/relevant_month_n))
                    use_no5 += consumption.consumption * \
                        (provider.spot_price +
                         (relevant_month['NO5']/relevant_month_n))

                payload.append({
                    "name": provider.name,
                    "pricingModel": "spot-monthly",
                    "fixedPrice": provider.spot_price,
                    "cost_based_on_user_history": {
                        "NO1": use_no1,
                        "NO2": use_no2,
                        "NO3": use_no3,
                        "NO4": use_no4,
                        "NO5": use_no5
                    },
                })

        # Find the entry with the lowest NO1 value - Curtesy of ChatGPT
        lowest_no1_entry = min(
            payload, key=lambda x: x["cost_based_on_user_history"]["NO1"])

        payload.remove(lowest_no1_entry)

        return {"best_option": lowest_no1_entry, "other_options": payload}

    def ingest_providers_from_json(self, file_path):
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            file.close()

        # We persume we want a clean slate.
        PH.delete_all_providers()
        for provider in json_data:
            new_provider = PH.create_provider(
                name=provider['name'],
                pricing_model=provider['pricingModel'],
                monthly_fee=provider['monthlyFee'],
                fixed_price=provider.get('fixedPrice', None),
                fixed_price_period=provider.get('fixedPricePeriod', None),
                variable_price=provider.get('variablePrice', None),
                variable_price_period=provider.get(
                    'variablePricePeriod', None),
                spot_price=provider.get('spotPrice', None),
            )



HelperMethods = HelperMethods()

# MODELS
consumption_model = api.model('Consumption', {
    'from_datetime': fields.DateTime(),
    'to_datetime': fields.DateTime(),
    'consumption': fields.Float,
    'consumption_unit': fields.String,
})


consumption_model_list = api.model('ConsumptionList', {
    'consumptions': fields.List(fields.Nested(consumption_model)),
})

# ROUTES
# @app.route("/api/customer/create", methods=["GET", "POST"])
# def user_create():
#     if request.method == "POST":
#         customer = Customer(
#             username=request.form['username']
#         )
#         db.session.add(customer)
#         db.session.commit()
#         return {"user": request.form['username']}


# @api.route('/api/customer_consumption/<string:username>')
# class GetCustomerConsumptions(Resource):
#     @api.doc(description='Shows consumption for a customer')
#     @api.marshal_with(consumption_model_list, envelope='resource')
#     def get(self, username):

#         customer = CH.get_customer_by_username(username=username)
#         consumptions = CH.get_customer_consumptions(customer_id=customer.id)

#         return {"consumptions": consumptions}


# @api.route('/api/init')
# class InitualizeDatabase(Resource):
#     def get(self):
#         HelperMethods.ingest_providers_from_json(PROVIDER_FILE_PATH)
#         return {'Status': 'Success'}


@api.route('/api/calculate/<string:username>')
class CalculateBestOptions(Resource):
    def get(self, username):
        best_options = HelperMethods.calculate_best_options_for_user(
            username=username)
        print(best_options)
        return best_options, 200


@api.route('/api/uploadfile/')
@api.expect(upload_parser)
class Upload(Resource):
    @api.doc(description='Upload a file')
    @api.response(201, 'Success', model={'url': fields.String})
    def post(self):
        """
        Upload a file.
        """
        args = upload_parser.parse_args()
        uploaded_file = args['file']  # This is FileStorage instance

        username = args['name']
        url = HelperMethods.ingest_json_to_customer(
            username=username, uploaded_file=uploaded_file)
        return {'url': url}, 201


if __name__ == '__main__':
    HelperMethods.ingest_providers_from_json(PROVIDER_FILE_PATH)
    app.run(debug=True)
