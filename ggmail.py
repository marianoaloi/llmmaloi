# %% [markdown]
# # Extract , transform and load the gmail data
# From the takeout gmail data this script will read the messages file, with your body , subject , labels and other informations and load the data to Mongodb Collection.
# 
# 1. Befour execute enable the mongodb by the docker-compose script, if you dont have a mongodb.
# 1. Set up the URL Connection ("mongodb://root:secret@localhost:27027/admin") to the environment variable MONGO_STRING
# 1. Set up the folder location of the Takeout/Mail/ extracted data to the environment variable GMAIL_DATA

# %%
import mailbox
import re
import string
from typing import List


from tqdm import tqdm

import bs4
import email

from populateFlatByJson import cleanText

# %% [markdown]
# Create a simple method that transform the html body content in the flat text

# %%
def get_html_text(html):
    try:
        return bs4.BeautifulSoup(html, 'html5lib').body.get_text(' ', strip=True)
    except AttributeError: # message contents empty
        return None

# %% [markdown]
# Create the main python DTO object to represent the email message data

# %%
class EmailMaloi:
    labels=None
    date=None
    frommail=None
    to=None
    subject=None
    text    =None
    headers=None
    _id=None
    file=None
    def __init__(self) -> None:
        pass

# %% [markdown]
# Create the transform message class. All the transformation is defined in this class.

# %%
class GmailMboxMessage():
    def __init__(self, email_data):
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError('Variable must be type mailbox.mboxMessage')
        self.email_data = email_data
    def parse_email(self)->EmailMaloi:
        
        def extractEmail(addressText:str) -> List[str]:
            def extract(text:str):
                m = re.findall("\<([^\>]+)\>",text)
                if(m):
                    return m[0].strip()
                else:
                    return text.strip()
            results = [extract(y) for x in addressText for y in x.split(",") ]
            return results
            
            
        
        def cleanHeader(textTransform):
            return [cleanText(textTransform)] \
                    if isinstance(textTransform,str) \
                    else [x for x in email.header.decode_header(textTransform)[0][0].decode('utf8','ignore') if x in string.printable] \
                        if isinstance(textTransform,email.header.Header) else ["NO CONTENT"]
        
        self.emailMaloi = EmailMaloi()
        self.emailMaloi._id = self.email_data['X-GM-THRID']
        self.emailMaloi.labels = self.email_data['X-Gmail-Labels'].split(",") if self.email_data['X-Gmail-Labels'] else None
        self.emailMaloi.date = self.email_data['Date']
        self.emailMaloi.frommail = extractEmail(cleanHeader(self.email_data['From']))
        self.emailMaloi.to = extractEmail(cleanHeader(self.email_data['To']))
        self.emailMaloi.subject = "".join(cleanHeader(self.email_data['Subject']))
        self.emailMaloi.text = self.read_email_payload() 
        def cleanDolar(x):
            lit=list(x)
            lit[0]=x[0].replace("$","DLR_")
            lit[1]="".join([m for m in x[1] if m in string.printable])
            return tuple(lit)
        self.emailMaloi.headers = dict([cleanDolar(x) for x in self.email_data._headers])
        return self.emailMaloi;

    def read_email_payload(self):
        email_payload = self.email_data.get_payload()
        if self.email_data.is_multipart():
            email_messages = list(self._get_email_messages(email_payload))
        else:
            email_messages = [email_payload]
        return [self._read_email_text(msg) for msg in email_messages]

    def _get_email_messages(self, email_payload):
        for msg in email_payload:
            if isinstance(msg, (list,tuple)):
                for submsg in self._get_email_messages(msg):
                    yield submsg
            elif msg.is_multipart():
                for submsg in self._get_email_messages(msg.get_payload()):
                    yield submsg
            else:
                yield msg

    def _read_email_text(self, msg):
        content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
        encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
        if 'text/plain' in content_type and 'base64' not in encoding:
            msg_text = msg.get_payload()
        elif 'text/html' in content_type and 'base64' not in encoding:
            msg_text = get_html_text(msg.get_payload())
        elif content_type == 'NA':
            msg_text = get_html_text(msg)
        else:
            msg_text = None
        return (content_type, encoding, cleanText(msg_text))

# %% [markdown]
# #### Enable Mongo 
# Remenber the configure the official Mongo. Or run the Docker-Compose to enable the mongo with the set up bellow. 

# %%
import pymongo
from pymongo import UpdateOne
import os
myclient = pymongo.MongoClient(os.environ["MONGO_STRING"])["extractData"]
mycol_all_gmail = myclient["gmail_all"]

# %% [markdown]
# #### Read and load
# Read the big message file and save the transformed message to Mongodb. After we will filter the message we can use.

# %%
for root,folders,files in os.walk(os.environ["GMAIL_DATA"]):
    for file in  files:

        mbox =  mailbox.mbox(os.path.join(root,file))
        print(f"The file [{file}] has {len(mbox)} messages")
        for message in tqdm(mbox):
            try:
                gmail = GmailMboxMessage(message)
                gmail = gmail.parse_email()
                gmail.file=file
                try:
                    mycol_all_gmail.update_one({"_id":gmail._id},{"$set":gmail.__dict__},upsert=True)
                except Exception as e:
                    msg=f"Error save message from {gmail.frommail} with subject {gmail.subject} =={str(e)}=="
                    print(msg)
                    print(msg,gmail.__dict__,file=open(f"{gmail._id}.txt","w"))
            except Exception as e:
                print("Error read message ",str(e))

# %% [markdown]
# #### Filter and save data

# %%

mycol_gmail = myclient["gmail"]
sentEmails=[UpdateOne({"_id":msg["_id"]},{"$set":msg},upsert=True) for msg in mycol_all_gmail.find({"labels":"Sent"})]
if(sentEmails):
    mycol_gmail.bulk_write(sentEmails)


