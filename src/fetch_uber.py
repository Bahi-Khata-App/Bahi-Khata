from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from utils import authenticate
import datetime


#### PARAMS 
### You will mostly need to change these:
query = 'uber receipts trip with uber'
# 'from:noreply@cure.fit Confirmation for ' # for cure.fit
after_time = '2019-05' # only messages after this time period gets their content
filename_to_dump = '../data/0617_one_year_dump_uber.pickle' # should be as verbose as we can so that we don't have difficulty later on
#### END of parmas


service = authenticate()

#### Firstly we will fetch message ids, then we will fetch the content of it
message_ids = []

### Fetch Message Ids
###  This is more like a do while because we need to know if the first query has a nextPageToken or not
returned_request = service.users().messages().list(userId='me', q= query).execute()
message_ids += returned_request['messages']
next_page_token = returned_request['nextPageToken']

while True:
    returned_request = service.users().messages().list(userId='me', q= query, pageToken = next_page_token).execute()
    message_ids += returned_request['messages']
    if 'nextPageToken' in returned_request:
        next_page_token = returned_request['nextPageToken']
    else:
        break
#### Fetched Message Ids

#### Fetch Message Content

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


#### Dump message content
with open(filename_to_dump, 'wb') as handle:
    pickle.dump(list_all_messages, handle)




# lists['']

# message = service.users().messages().get(userId='me', id=msg_id, format = 'full').execute()

# msg_str = ""
# for j in range(len(message['payload']['parts'])):
#     if message['payload']['parts'][j]['mimeType'] == 'text/html':
#         msg_str = base64.urlsafe_b64decode(message['payload']['parts'][j]['body']['data'])


# msg_str = msg_str.decode("utf-8")
# print ('Message snippet: %s' % message['snippet'])
# print (message)
# f = open('out.html', 'w')
# f.write(msg_str.decode("utf=8"))
# f.close()
# labels = results.get('labels', [])

# if not labels:
#     print('No labels found.')
# else:
#     print('Labels:')
#     for label in labels:
#         print(label['name'])

# i = 0
# msg_id = message_ids[i]['id']
# message = service.users().messages().get(userId='me', id=msg_id, format = 'full').execute()
# try:
#     msg_str = ""
#     for j in range(len(message['payload']['parts'])):
#         if message['payload']['parts'][j]['mimeType'] == 'text/html':
#             msg_str = base64.urlsafe_b64decode(message['payload']['parts'][j]['body']['data'])
#     all_messages += (msg_str.decode("utf-8") + "\n\n\n")
#     list_all_messages.append([msg_str.decode("utf-8"), message['snippet'], message['payload']['headers'][16]['value'], message['payload']['headers'][18]['value']])
#     print ('Message snippet: %s' % message['snippet'])
# except Exception as e:
#     print (e)
#     print ("Index", i)
