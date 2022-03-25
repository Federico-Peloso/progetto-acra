import certifi
import pymongo
from flask import Flask, jsonify, render_template, request
from flask_cors import cross_origin, CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from werkzeug.routing import BaseConverter

app = Flask(__name__, template_folder='./templates')

client = pymongo.MongoClient(
    'mongodb+srv://mongo_loide:jpnqAQ5Jq4k98wai@cluster0.7ftto.mongodb.net/sfizi?retryWrites=true&w=majority',
    tlsCAFile=certifi.where())

dizionario_italiano = client['sfizi']['dizionario_italiano']
tecnologie = client['tecnologie']
cors = CORS(app)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'federicosuper898@gmail.com'
app.config['MAIL_PASSWORD'] = '****'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# limiter = Limiter(app, key_func=get_remote_address, default_limits=['1000/minute', '3000/hour'])
limiter = Limiter(app, key_func=get_remote_address)


@cross_origin()
@app.route("/vocabolario/<string:lettere>/<regex('[0-9]+'):limit>")
def vocabolario(lettere, limit):
    limit = int(limit)
    query = dizionario_italiano.aggregate(
        [
            {'$match': {'vocabolo': {'$regex': f'{str.lower(lettere)}'}}},
            {'$group': {
                '_id': '$vocabolo'
            }},
            {'$project': {
                "_id": 1,
                "field_length": {'$strLenCP': "$_id"}
            }},
            {'$sort': {"field_length": 1}},
            {'$project': {"field_length": 0}},
            {'$limit': limit}
        ]
    )

    return jsonify(list(query))


def get_spearated_data_query(country_code, data_type):
    if country_code.lower() == 'all':
        query = [
            {'$unwind': '$years'},
            {'$project': {
                '_id': 0,
                'country_name': 1,
                'country_code': 1,
                'years.year': 1,
                f'years.{data_type}': 1
            }},
            {'$group': {
                '_id': '$country_code',
                'country_name': {'$first': '$country_name'},
                'country_code': {'$first': '$country_code'},
                'years': {'$push': '$years'}
            }},
            {'$sort':
                 {'country_name': 1}
             }
        ]
    else:
        query = [
            {'$match': {'country_code': str.upper(country_code)}},
            {'$unwind': '$years'},
            {'$match': {'years.year': {'$gt': 1969 if data_type != 'female_intake' else 2004,
                                       '$lt': 2019 if data_type != 'female_intake' else 2019}}},
            {'$project': {
                '_id': 0,
                'years.year': 1,
                f'years.{data_type}': 1
            }},
            {'$sort':
                 {'years.year': 1}
             },
            {"$replaceRoot": {
                "newRoot": "$years"
            }
            }
        ]

    return query


@app.route('/')
def hello_world():
    return render_template('Vesperr/index.html')


@app.route('/send-contact-form', methods=['POST'])
def send_contact_email():
    if request.method == 'POST' and all(
            elem in ['name', 'email', 'subject', 'message'] for elem in request.form.keys()):

        mailto = request.form.get('email')
        name = request.form.get('name')
        subject = request.form.get('subject')
        message = request.form.get('message')
        msg = Message(f"messaggio da: {name} - email: {mailto}", sender='federicosuper898@gmail.com',
                      recipients=['peloso.federico@iisgalvanimi.edu.it'])
        msg.body = f"subject: {subject}, messaggio: {message}"
        mail.send(msg)

        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


@app.route('/api/countries')
def get_countries():
    return jsonify(list(tecnologie['quality_education2'].find({}, {'_id': 0})))


@app.route('/api/education/all-average')
def get_all_average():
    query = tecnologie['quality_education2'].aggregate([
        {'$unwind': '$years'},
        {'$group': {
            '_id': '$country_code',
            'country_name': {'$first': '$country_name'},
            'avg_sc_enr_primary': {'$avg': '$years.sc_enr_primary'},
            'avg_female_intake': {'$avg': '$years.female_intake'},
            'avg_trained_ratio': {'$avg': '$years.trained_ratio'}
        }},
        {'$match': {
            'avg_sc_enr_primary': {'$ne': None},
            'avg_female_intake': {'$ne': None},
            'avg_trained_ratio': {'$ne': None}
        }},
        {'$project': {
            '_id': 0
        }},
        {'$limit': 10}
    ])

    return jsonify(list(query))


@app.route('/api/education/all')
def get_all_countries_data():
    return jsonify(list(tecnologie['quality_education2'].find({}, {'_id': 0})))


@app.route('/api/education/school-enrollment-primary-by-income-group/<string:income_group_code>')
def get_shool_enrollment_income_groups(income_group_code):
    if income_group_code != str.lower('all'):
        query = tecnologie['income_groups'].find({'income_group_code': str.upper(income_group_code)}, {'_id': 0})
        return jsonify(list(query))
    else:
        query = tecnologie['income_groups'].find({}, {'_id': 0})
        return jsonify(list(query))


@app.route('/api/education/school-enrollment-primary-by-income-group/average')
def get_average_income_groups():
    query = tecnologie['income_groups'].aggregate([
        {'$unwind': '$years'},
        {'$group': {
            '_id': '$income_group_code',
            'income_group': {'$first': '$income_group'},
            'income_group_code': {'$first': '$income_group_code'},
            'avg_income_group': {'$avg': '$years.sc_enr_primary'}
        }},
        {'$match': {
            'avg_income_group': {'$ne': None}
        }},
        {'$project': {
            '_id': 0
        }},
        {'$limit': 10}
    ])

    return jsonify(list(query))


@app.route('/api/education/<string:data_type>/country-by-code/<string:country_code>')
def get_school_enrollment(country_code, data_type):
    parameter = None

    if data_type == "school-enrollment-primary":
        parameter = 'sc_enr_primary'
    elif data_type == "female-intake":
        parameter = 'female_intake'
    elif data_type == "trained-ratio":
        parameter = 'trained_ratio'

    if parameter is not None:
        query = tecnologie['quality_education2'].aggregate(get_spearated_data_query(country_code, parameter))
        return jsonify(list(query))
    else:
        return jsonify(list())


@app.route('/api/education/country-by-name/<string:country_name>')
def get_country_data_by_name(country_name):
    return jsonify(
        list(tecnologie['quality_education2'].find({'country_name': str.capitalize(country_name)}, {'_id': 0})))


@app.route('/api/education/country-by-code/<string:country_code>')
def get_country_data_by_code(country_code):
    return jsonify(
        list(tecnologie['quality_education2'].find({'country_code': str.upper(country_code)}, {'_id': 0})))


if __name__ == '__main__':
    app.run()
