from __future__ import print_function
import base64

from flask import *
import pickle
import os.path
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import datetime
import sys
import importlib
from threading import Thread
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)

import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import altair as alt
from altair_saver import save

LOCAL_DEV = False
PARAMS_FILE = 'params_central.json'
IGNORE_LIST = ['curefit']

with open(PARAMS_FILE) as params_file:
    params = json.load(params_file)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/userinfo.email', 'openid', 'https://www.googleapis.com/auth/userinfo.profile']

if LOCAL_DEV:
    credentials_filename = 'data/credentials.json.bak'
    REDIRECT_URL = "http://localhost:5000/push"
else:
    credentials_filename = 'data/credentials.json'
    REDIRECT_URL = "https://bahi-khata-app.herokuapp.com/push"


flow = InstalledAppFlow.from_client_secrets_file(
            credentials_filename, SCOPES)
flow.redirect_uri = REDIRECT_URL
authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
credentials = None

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app


app = create_app()

# Use this for getting form authenticating with GMail
@app.route('/auth', methods=['GET', 'POST'])
def start_auth():
    global authorization_url
    return redirect(authorization_url)

@app.route('/push')
def build_service():
    print ("Done")
    print (request)
    print (request.args.get("code"))
    flow.fetch_token(code=request.args.get("code"))
    credentials = flow.credentials   # write it to file
    service = build('gmail', 'v1', credentials=credentials)
    thread = Thread(target=push_report, args=(service,))
    thread.daemon = True
    thread.start()
    return redirect(url_for('display_thankyou'))

@app.route('/thankyou', methods=['GET'])
def display_thankyou():
    return render_template('thankyou.html')

def push_report(service):
    user_email = service.users().getProfile(userId='me').execute()['emailAddress']
    print(user_email)
    global params
    y_bottom = np.zeros(12)
    charts = []
    df1 = pd.DataFrame()
    for company_name in params:
        company = params[company_name]
        if company_name in IGNORE_LIST or not create_dump(service, company):
            continue
        # if company_name in IGNORE_LIST:
        #     continue
        try:
            x, y = getData(company_name, company['fname'])
            x, y = coerceData(x, y)
        except Exception as e:
            print(e)
            continue
        print(company_name, y)
        y_bottom = np.add(y_bottom, y)
        source = pd.DataFrame({
            'month': x,
            'spent': y,
            'company': [company_name] * 12
        })
        chart = alt.Chart(source).mark_bar(size=15).encode(
            x=alt.X('month', title=''),
            y=alt.Y('spent', title='Amount spent (₹)')
        ).properties(
            title=company_name,
        )
        charts.append(chart)
        source.set_index('month')
        if not df1.size:
            df1 = source
        else:
            df1 = df1.append(source)
    if not df1.size:
        print('No data found for ' + user_email)
        return
    stackedchart = alt.Chart(df1).mark_bar(size=15).encode(
        alt.X('month', title=''),
        y=alt.Y('sum(spent)', title='Amount spent (₹)'),
        color='company'
    ).properties(
        title='Aggregate Monthly Spending'
    )
    charts.insert(0, stackedchart)
    repchart = alt.VConcatChart(vconcat=charts)
    save(repchart, os.path.dirname(os.path.abspath(__file__)) + '/data/report.png', scale_factor=1.5)
    with app.app_context():
        context = {'amount': np.sum(y_bottom)}
        email_content = render_template('report.html', **context)
    push_email(email_content, user_email)

def create_dump(service, company):
    query = company['query']
    after_time = company['after']
    filename_to_dump = company['fname']
    message_ids = []

    returned_request = service.users().messages().list(userId='me', q=query).execute()
    if 'messages' not in returned_request:
        return False

    message_ids += returned_request['messages']

    while 'nextPageToken' in returned_request:
        next_page_token = returned_request['nextPageToken']
        returned_request = service.users().messages().list(userId='me', q=query, pageToken = next_page_token).execute()
        message_ids += returned_request['messages']

    list_all_messages = []
    for i in range(len(message_ids)):
        msg_id = message_ids[i]['id']
        message = service.users().messages().get(userId='me', id=msg_id, format = 'full').execute()
        try:
            if (datetime.datetime.fromtimestamp(int(message['internalDate'])/1000).strftime('%Y-%m-%d %H:%M:%S') > after_time):
                list_all_messages.append(message)
                print ('Message snippet: %s' % message['snippet'])
            else:
                break
        except Exception as e:
            print (e)
            print ("Index", i, message['snippet'])

    with open(filename_to_dump, 'wb') as handle:
        pickle.dump(list_all_messages, handle)    
    return True


def push_email(email_content, user_email):
    message = Mail(
        from_email='admin@bahikhata.com',
        to_emails=user_email,
        subject='Bahi Khata Report',
        html_content= email_content)
    file_path = './static/images/bahi_khata.png'
    with open(file_path, 'rb') as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType('image/png')
    attachment.file_name = FileName('bahi_khata.png')
    attachment.disposition = Disposition('inline')
    attachment.content_id = ContentId('bahikhatalogo')
    message.attachment = attachment
    file_path = './data/report.png'
    with open(file_path, 'rb') as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType('image/png')
    attachment.file_name = FileName('report.png')
    attachment.disposition = Disposition('inline')
    attachment.content_id = ContentId('report')
    message.attachment = attachment
    with open('data/sendgrid.json') as f:
        SG_API_KEY = f.readline()
    try:
        sg = SendGridAPIClient(SG_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.to_dict)
    return "sent email"


def getData(company_name, filename_to_dump):
    sys.path.append('src')
    return importlib.import_module('src.analysis_' + company_name).getData(filename_to_dump)


def coerceData(x, y):
    df = pd.DataFrame({'Amount': y}, index=x)
    df.index = pd.to_datetime(df.index.strftime('%Y-%m-%d'))
    df = df['Amount'].resample('M').sum()
    df = df.reindex(pd.date_range('2019-07-01', periods=12, freq='M')).fillna(0.0)
    # print(df.index)
    # print(df)
    x = df.index.tolist()
    y = df.values
    return x, y
