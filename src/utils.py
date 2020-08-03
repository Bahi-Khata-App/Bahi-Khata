from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64

def authenticate():
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('../data/token.pickle'):
        with open('../data/token.pickle', 'rb') as token:
            creds = pickle.load(token)


    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '../data/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../data/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def parse_mail(data_dump):
    # subject, from, date, snippet, email_html
    data_arr = []
    for message in data_dump:
        if 'multipart' in message['payload']['mimeType']:
            for j in range(len(message['payload']['parts'])):
                if message['payload']['parts'][j]['mimeType'] == 'text/html':
                    if "data" in message['payload']['parts'][j]['body']:
                        this_str = base64.urlsafe_b64decode(message['payload']['parts'][j]['body']['data'])
                else:
                    this_str = b"[attachment here]"
                this_str = (this_str.decode("utf-8") + "\n\n\n")
        else:
            this_str = base64.urlsafe_b64decode(message['payload']['body']['data'])
            this_str = (this_str.decode("utf-8") + "\n\n\n")
        this_snippet = message['snippet']
        this_subject = -1
        this_from = -1
        this_date = -1
        for i in range(len(message['payload']['headers'])):
            # print (message['payload']['headers'][i]['name'])
            # print (message['payload']['headers'][i]['value'], "\n\n\n")
            if message['payload']['headers'][i]['name'] == 'Subject':
                this_subject = message['payload']['headers'][i]['value']
            elif message['payload']['headers'][i]['name'] == 'From':
                this_from = message['payload']['headers'][i]['value']
            elif message['payload']['headers'][i]['name'] == 'Date':
                this_date = message['payload']['headers'][i]['value']
        this_dict= {}
        this_dict['subject'] = this_subject
        this_dict['from'] = this_from
        this_dict['date'] = this_date
        this_dict['snippet'] = this_snippet
        this_dict['str'] = this_str
        data_arr.append(this_dict)
    return data_arr


