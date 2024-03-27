import mailbox
import string


import bs4
import email

from populateFlatByJson import cleanText

def get_html_text(html):
    try:
        return bs4.BeautifulSoup(html, 'html5lib').body.get_text(' ', strip=True)
    except AttributeError: # message contents empty
        return None
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
class GmailMboxMessage():
    def __init__(self, email_data):
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError('Variable must be type mailbox.mboxMessage')
        self.email_data = email_data
    def parse_email(self)->EmailMaloi:
        
        
        def cleanHeader(textTransform):
            return cleanText(textTransform) \
                    if isinstance(textTransform,str) \
                    else "".join([x for x in email.header.decode_header(textTransform)[0][0].decode('utf8','ignore') if x in string.printable]).strip() \
                        if isinstance(textTransform,email.header.Header) else "NO CONTENT"
        
        self.emailMaloi = EmailMaloi()
        self.emailMaloi._id = self.email_data['X-GM-THRID']
        self.emailMaloi.labels = self.email_data['X-Gmail-Labels'].split(",") if self.email_data['X-Gmail-Labels'] else None
        self.emailMaloi.date = self.email_data['Date']
        self.emailMaloi.frommail = cleanHeader(self.email_data['From'])
        self.emailMaloi.to = cleanHeader(self.email_data['To'])
        self.emailMaloi.subject = cleanHeader(self.email_data['Subject'])
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


import pymongo
from pymongo import UpdateOne
import os
myclient = pymongo.MongoClient("mongodb://root:secret@localhost:27027/admin")["extractData"]
mycol = myclient["gmail"]

for root,folders,files in os.walk(os.environ["GMAIL_DATA"]):
    for file in  files:

        mbox =  mailbox.mbox(os.path.join(root,file))
        print(f"The file [{file}] has {len(mbox)} messages")
        for idx,message in enumerate(mbox):
            try:
                gmail = GmailMboxMessage(message)
                gmail = gmail.parse_email()
                gmail.file=file
                try:
                    mycol.update_one({"_id":gmail._id},{"$set":gmail.__dict__},upsert=True)
                except Exception as e:
                    msg=f"Error save message from {gmail.frommail} with subject {gmail.subject} =={str(e)}=="
                    print(msg)
                    print(msg,gmail.__dict__,file=open(f"{gmail._id}.txt","w"))
            except Exception as e:
                print("Error read message ",idx,str(e))
            
            # # Process or print the extracted information
            # print(f"From: {gmail.frommail}, Subject: {gmail.to}")
            # print(f"Body: {gmail.text}")