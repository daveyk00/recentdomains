import smtplib
import argparse
import sys
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


def send_mail(send_from, send_to, subject, message, files=[],
              server="", port=587, username='', password='',
              use_tls=True):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        print("in files")
        print("attachemnt is "+path)
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    if username != "" and username != "":
        print("try login")
        smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()



parser=argparse.ArgumentParser()
parser.add_argument('--fromemail', help="Require --from address")
parser.add_argument('--toemail', help="Require --to address")
parser.add_argument('--subject', help="Require --subject")
parser.add_argument('--body', help="Require --body")
parser.add_argument('--attachment', help="Require --attachment name")
parser.add_argument('--server', help="Require --server address")

args=parser.parse_args()

print("Sending email...")
print("from email: ",args.fromemail)
print("to email: ",args.toemail)
print("subject: ",args.subject)
print("body: ",args.body)
print("attachment: ",args.attachment)
print("server: ",args.server)

attachment=args.attachment.split(',')
print(attachment)
send_mail(args.fromemail,args.toemail,args.subject,args.body,attachment,args.server)