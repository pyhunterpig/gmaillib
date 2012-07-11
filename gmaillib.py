#coding=utf-8
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
#from email.message import Message
from email.header import Header
from email.MIMEBase import MIMEBase
from email import Encoders
import mimetypes

import os
import imaplib
import smtplib
import email


class message:

    def __init__(self, fetched_email):
        accepted_types = ['text/plain']
        parsed = email.message_from_string(fetched_email)
        self.reciever_addr = parsed['to']
        self.sender_addr = parsed['from']
        self.date = parsed['date']
        self.subject = parsed['subject']
        self.body = ''
        if parsed.is_multipart():
            for part in parsed.walk():
                if part.get_content_type() in accepted_types:
                    self.body = part.get_payload()
        else:
            if parsed.get_content_type() in accepted_types:
                self.body = parsed.get_payload()

    def __repr__(self):
        return "<Msg from: {0}>".format(self.sender_addr)

    def __str__(self):
        return "To: {0}\nFrom: {1}\nDate: {2}\nSubject: {3}\n\n{4}".format(
               self.reciever_addr,
               self.sender_addr,
               self.date,
               self.subject,
               self.body)


class account:

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.sendserver = smtplib.SMTP('smtp.gmail.com:587')
        self.sendserver.starttls()
        self.sendserver.login(username, password)

        self.recieveserver = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        self.recieveserver.login(username, password)

    def send(self, toaddr, subject='', content=''):
        fromaddr = self.username
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Content-Type'] = 'text/plain; charset="utf-8"'
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        self.sendserver.sendmail(fromaddr, toaddr.split(','), msg.as_string())

    def sendwithatt(self, toaddr, subject, content, attfiles):
        fromaddr = self.username
        msg = MIMEMultipart()
        body = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg.attach(body)

        for attfile in list(attfiles):
            msg.attach(self.attachment(attfile))
        self.sendserver.sendmail(fromaddr, toaddr.split(','), msg.as_string())

    def sendHTMLwithatt(self, toaddr, subject, html, attfiles):
        fromaddr = self.username
        msg = MIMEMultipart()
        body = MIMEText(html, 'html', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg.attach(body)

        for attfile in list(attfiles):
            msg.attach(self.attachment(attfile))
        self.sendserver.sendmail(fromaddr, toaddr.split(','), msg.as_string())

    def attachment(self, filename):
        fd = file(filename, "rb")
        mimetype, mimeencoding = mimetypes.guess_type(filename)
        if mimeencoding or (mimetype is None):
            mimetype = "application/octet-stream"
        maintype, subtype = mimetype.split("/")

        if maintype == "text":
            retval = MIMEText(fd.read(), _subtype = subtype)
        else:
            retval = MIMEBase(maintype, subtype)
            retval.set_payload(fd.read())
            Encoders.encode_base64(retval)
        retval.add_header("Content-Disposition",
                          "attachment",
                          filename=os.path.basename(filename))
        fd.close()
        return retval

    def recieve(self):
        return

    def get_all_messages(self):
        self.recieveserver.select('Inbox')
        fetch_list = self.recieveserver.search(None, '(UNDELETED)')[1][0]
        fetch_list = fetch_list.split(' ')
        inbox_emails = []
        for each_email in fetch_list:
            inbox_emails.append(self.get_email(each_email))
        return inbox_emails

    def unread(self):
        self.recieveserver.select('Inbox')
        fetch_list = self.recieveserver.search(None, 'UnSeen')[1][0]
        fetch_list = fetch_list.split(' ')
        if fetch_list == ['']:
            return []
        unread_emails = []
        for each_email in fetch_list:
            unread_emails.append(self.get_email(each_email))
        return unread_emails

    def get_email(self, email_id):
        self.recieveserver.select('Inbox')
        #This nasty syntax fetches the email as a string
        fetched_email = self.recieveserver.fetch(email_id, "(RFC822)")[1][0][1]
        parsed_email = message(fetched_email)
        return parsed_email

    def inbox(self, start=0, amount=10):
        self.recieveserver.select('Inbox')
        inbox_emails = []
        messages_to_fetch = ','.join(self._get_uids()[start:start+amount])
        fetch_list = self.recieveserver.uid('fetch',
                                            messages_to_fetch,
                                            '(RFC822)')
        for each_email in fetch_list[1]:
            if(len(each_email) == 1):
                continue
            inbox_emails.append(message(each_email[1]))
        return inbox_emails

    def get_inbox_count(self):
        return int(self.recieveserver.select('Inbox')[1][0])

    def _get_uids(self):
        self.recieveserver.select('Inbox')
        result, data = self.recieveserver.uid('search', None, 'ALL')
        data = data[0].split(' ')
        data.reverse()
        return data
