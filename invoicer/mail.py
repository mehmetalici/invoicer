import base64
from dataclasses import dataclass
import email
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Optional


@dataclass
class Mail:
    sender: str
    to: str
    subject: str
    date: Optional[str] = None
    html: Optional[str] = None
    plain_text: Optional[str] = None
    ident: Optional[str] = None
    attachments: Optional[Path] = None

    def __post_init__(self):
        if [self.html, self.plain_text] == [None, None]:
            raise Exception("html and plain_text fields cannot be both None.") 


def payload_to_mail(payload: dict, ident: str) -> Mail:
    headers = payload["headers"]
    subject = get_header(headers, "Subject")
    sender = get_header(headers, "From")
    to = get_header(headers, "To")
    date = get_header(headers, "Date")

    mime_type = payload["mimeType"]
    plain_text_encoded = None
    html_encoded = None
    if mime_type == "multipart/*":
        plain_text_encoded = payload["parts"][0]["body"]["data"]
        html_encoded = payload["parts"][1]["body"]["data"]
    elif mime_type == "text/plain":
        plain_text_encoded = payload["body"]["data"]
    elif mime_type == "text/html":
        html_encoded = payload["body"]["data"]
    else:
        raise RuntimeError(f"mime_type {mime_type} is unknown.")
    
    plain_text = None
    if plain_text_encoded:
        plain_text = base64.urlsafe_b64decode(plain_text_encoded).decode()

    html = None
    if html_encoded:
        html = base64.urlsafe_b64decode(html_encoded).decode()

    return Mail(sender=parseaddr(sender)[1], to=parseaddr(to)[1], date=date, subject=subject, plain_text=plain_text, html=html, ident=ident)




def get_header(headers: dict, name: str) -> str:
    return next((header["value"] for header in headers if header["name"] == name))


def from_gmail(gmail: dict) -> Mail:
    payload = gmail["payload"]
    mail = payload_to_mail(payload=payload, ident=gmail["id"])
    return mail