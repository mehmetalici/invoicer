from __future__ import print_function

import base64
import logging
import mimetypes
import os
import os.path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from invoicer.config import Config
from invoicer.mail import Mail, from_gmail
from invoicer.order import Order
from invoicer.order_mail_parsers import order_from_mail


class GmailAccount:
    def __init__(self, oauth2_app_credentials_file: Path, token_file: Path) -> None:
        # If modifying these scopes, delete the file token.json.
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.settings.basic",
        ]
        creds = self._authorize(oauth2_app_credentials_file, token_file=token_file)
        self.service = build("gmail", "v1", credentials=creds)

    def create_label(self, name: str):
        labels = self.get_labels()
        for label in labels:
            if name == label["name"]:
                logging.info(
                    f"Label '{name}' could not be created. It is already present."
                )
                return label["id"]

        label = {
            "labelListVisibility": "labelShow",
            "msgListVisibility": "labelHide",
            "name": f"{name}",
        }
        created_label = (
            self.service.users().labels().create(userId="me", body=label).execute()
        )
        return created_label["id"]

    def get_labels(self):
        result = self.service.users().labels().list(userId="me").execute()
        labels = result["labels"]
        return labels

    def _authorize(self, oauth2_app_credentials_file: Path, token_file: Path):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    oauth2_app_credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=1025)
            # Save the credentials for the next run
            with open(token_file, "w") as token:
                token.write(creds.to_json())
        return creds

    def search_mails(self, query: str) -> Tuple[Mail]:
        msg_ids = self._list_mail_ids(query=query)
        gmails = self._get_mails(msg_ids=msg_ids)
        mails = tuple(map(from_gmail, gmails))
        return mails

    def _list_mail_ids(self, query: str) -> List[str]:
        maxResults = 100
        result = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=maxResults)
            .execute()
        )
        if result["resultSizeEstimate"] > maxResults:
            # TODO: Convert to logging
            logging.warning(
                f"result['resultSizeEstimate']{result['resultSizeEstimate']} > maxResults{maxResults}"
            )
        elif result["resultSizeEstimate"] == 0:
            return []

        msg_ids = list(map(lambda m: m["id"], result["messages"]))
        return msg_ids

    def _get_mails(self, msg_ids: List[str]):
        mails = []
        for msg_id in msg_ids:
            result = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            mails.append(result)
        return mails

    def add_label(self, mail_id: str, label_id: str):
        body = {"addLabelIds": [label_id]}
        self.service.users().messages().modify(
            userId="me", id=mail_id, body=body
        ).execute()

    def send_mail(self, mail: Mail):
        """Create and insert a draft email with attachment.
        Print the returned draft's message and id.
        Returns: Draft object, including draft id and message meta data.

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            # create a multipart message
            mime_message = MIMEMultipart("related")

            # headers
            mime_message["To"] = mail.to
            mime_message["From"] = mail.sender
            mime_message["Subject"] = mail.subject
            # mime_message["Content-Type"] = "text/html"

            if mail.html:
                # Add the HTML message body
                html = mail.html
                text = MIMEText(html, "html")
                mime_message.attach(text)
            elif mail.plain_text:
                text = MIMEText(mail.plain_text, "plain")
                mime_message.attach(text)
            if mail.attachments:
                for path in mail.attachments:
                    attach_file(mime_message, path)

            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            created_message = {"raw": encoded_message}
            # pylint: disable=E1101
            send_message = (
                self.service.users()
                .messages()
                .send(userId="me", body=created_message)
                .execute()
            )
            # logging.info(f'Mail has been sent. Message Id: {send_message["id"]}')
            ident = send_message["id"]

        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            ident = None
        return ident

# TODO: Change InvoicerAccount -> OrderAccount
class InvoicerAccount:
    def __init__(self, cfg: Config, creds: Path, token: Path) -> None:
        super().__init__()
        self.cfg = cfg
        self._mailing = GmailAccount(oauth2_app_credentials_file=creds, token_file=token)
        self.invoiced_label_id = self._mailing.create_label("Invoiced")
        # TODO: Create MailLabel dataclass
        self.forwarded_label_id = self._mailing.create_label("Forwarded")

    def search_new_orders(self) -> Tuple[Order]:
        mails = self._mailing.search_mails(
            query=f'from:{self.cfg.orderMail.sender} subject:"{self.cfg.orderMail.subjectHas}" -label:Invoiced'
        )
        orders = tuple(map(order_from_mail, mails))
        return orders

    def search_new_customer_mails(self) -> Tuple[Mail]:
        senders_to_exclude = f"from:{self.cfg.orderMail.sender} from:amazon.com from:amazonaws.com from:signup.aws from:google.com"
        # TODO: After date fix to release date
        mails = self._mailing.search_mails(
            query=f"-{{{senders_to_exclude}}} in:inbox -label:Forwarded after:2023/05/07"
        )
        return mails

    def forward_customer_mail(self, customer_mail: Mail) -> None:
        html = create_forward_mail_body(customer_mail=customer_mail, salute_name=self.cfg.invoiceMail.saluteName)
        # body = MailBodyGenerator.get_forward_reply_body(reply=reply, cfg=self.cfg)
        mail = Mail(
            sender="me",
            to=self.cfg.invoiceMail.to,
            subject="Neue Kunden-E-Mail",
            html=html
        )
        self._mailing.send_mail(mail=mail)
        self._mailing.add_label(
            mail_id=customer_mail.ident,
            label_id=self.forwarded_label_id
        )

    def inform_customer_forwarded(self, customer_mail: Mail):
        # body = MailBodyGenerator.get_inform_forwarded_body(reply=reply, cfg=self.cfg)
        html = create_inform_forwarded_mail_body(forward_address=self.cfg.invoiceMail.to)
        mail = Mail(
            sender="me",
            to=customer_mail.sender,
            subject=f"AW: {customer_mail.subject}",
            html=html
        )
        self._mailing.send_mail(mail=mail)

    # def forward_new_replies_to_seller(inform_customer=True):
        # replies = self.search_new_replies()
        # for reply in replies:
            # self.forward_reply(reply)
            # self.inform_customer_forwarded(reply)
            # self.gmail.label_mail(id=reply.id, label="Forwarded")

    def send_invoice(self, order: Order, invoice: Path, delete_invoice=True, errors: Optional[List[str]] = None):
        html = create_invoice_mail_body(salute_name=self.cfg.invoiceMail.saluteName, order=order, errors=errors)
        mail = Mail(
            sender="me",
            to=self.cfg.invoiceMail.to,
            subject=f"Neue Rechnung #{order.invoice.number}",
            html=html,
            attachments=[invoice]
        )
        self._mailing.send_mail(mail=mail)

        if delete_invoice:
            os.remove(invoice)

        self._mailing.add_label(mail_id=order.source_mail.ident, label_id=self.invoiced_label_id)
    

def get_image(image_path, inline_reference):
    # Open the image file in binary mode
    with open(image_path, "rb") as f:
        # Set the image as the payload for the MIME message
        image = MIMEImage(f.read(), name=Path(image_path).stem)
    # Set the content id of the image
    image.add_header("Content-ID", inline_reference)
    return image


def attach_file(mime_message, attachment_path):
    # attachment
    # guessing the MIME type
    type_subtype, _ = mimetypes.guess_type(attachment_path.name)
    maintype, subtype = type_subtype.split("/")

    with open(attachment_path, "rb") as fp:
        attachment_data = fp.read()
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload((attachment_data))
    # encode the attachment
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition", "attachment", filename=attachment_path.name
    )
    mime_message.attach(attachment)


def create_invoice_mail_body(salute_name: str, order: Order, errors: Optional[List[str]] = None):
    html = f"""
        Hallo {salute_name},
        <p>
            Ich habe die Bestellung #{order.number} erhalten &#x2705;
    """
    if errors and len(errors) > 0:
        html += f"""
            <b>aber leider konnte ich die Rechnung#{order.invoice.number} nicht erfolgreich erstellen.</b>
            Ich hatte Probleme mit den folgenden Feldern:{'<br/>'.join(errors)}.<br/>
            <b>Bitte fülle die Felder manuell aus.</b>
        """
    else:
        html +=   f"; und die Rechnung #{order.invoice.number} erstellt &#129299;"       

    html += f"""
        </p>
        <p>
                Du kannst die Rechnung im Anhang sehen &#128521;
        </p>
        <p>
            Außerdem füge ich die Mail mit den Bestelldaten, die ich erhalten habe, unten an, damit du <b>meine Fehler überprüfen</b> kannst.
        </p>
        <p/>
        <p>
            Sonnige Grüße &#9728;&#65039;,<br>
            Dein Bot<br>
        </p>
        <p/>
        <p> ---- Original Email ---- </p>
        <p>
            From: {order.source_mail.sender}<br>
            To: {order.source_mail.to}<br>
            Subject: {order.source_mail.subject}<br>
            Date: {order.source_mail.date}<br>
        </p>
        <pre>{order.source_mail.html}</pre>
    """
    return html


def create_forward_mail_body(customer_mail: Mail, salute_name: str):
    html = f"""
        Hallo {salute_name},

        <p>
        ich habe eine neue E-Mail in meinem Posteingang erhalten und möchte sie mit dieser E-Mail mit dir teilen.
        </p>

        <p>
        Wenn du darauf antworten möchtest, antworte bitte <b>nicht<b> auf diese E-Mail und erstelle stattdessen eine neue E-Mail für den Absender. 
        </p>
        <p>
            Sonnige Grüße &#9728;&#65039;,<br>
            Dein Bot<br>
        </p> 
        <p/>
        <p> ---- Original Email ---- </p>
        <p>
            From: {customer_mail.sender}<br>
            To: {customer_mail.to}<br>
            Subject: {customer_mail.subject}<br>
            Date: {customer_mail.date}<br>
        </p>
        <pre>{customer_mail.html}</pre>
    """
    return html


def create_inform_forwarded_mail_body(forward_address: str):
    html = f"""
        Sehr geehrte(r) Absender(in),
        <p>
        vielen Dank für Ihre Kontaktaufnahme. Ihre E-Mail wurde an {forward_address} weitergeleitet und wird so schnell wie möglich bearbeitet.
        </p>
        <p>
        Dies ist eine automatische Antwort, bitte antworten Sie nicht darauf.
        </p>
        <p>
            Viele Grüße,<br>
            Ihr Laden <br>
        </p> 
    """
    return html


# def search_and_forward():
    # search_customer_replies()
    # 