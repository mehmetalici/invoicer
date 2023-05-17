import base64
from dataclasses import dataclass, field
import email
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Optional, Tuple, List
import logging

@dataclass
class Mail:
    sender: str
    to: str
    subject: str
    date: Optional[str] = None
    html: Optional[str] = None
    plain_text: Optional[str] = None
    ident: Optional[str] = None
    attachments: List[Path] = field(default_factory=list)

    def __post_init__(self):
        if [self.html, self.plain_text] == [None, None]:
            # TODO: Why?
            raise Exception("html and plain_text fields cannot be both None.") 

@dataclass
class GmailAttachment:
    ident: str
    filename: str
    

def payload_to_mail(payload: dict, ident: str) -> Mail:
    headers = payload["headers"]
    subject = get_header(headers, "Subject")
    sender = get_header(headers, "From")
    to = get_header(headers, "To")
    date = get_header(headers, "Date")

    mime_type = payload["mimeType"]
    plain_text_encoded = None
    html_encoded = None
    gmail_attachments = []
    # TODO: Should be done recursively
    if "multipart/" in mime_type:
        # TODO: Looks ugly 
        for part in payload["parts"]:
            mime_type = part["mimeType"]
            if mime_type == "text/plain":
                plain_text_encoded = part["body"]["data"]
            elif mime_type == "text/html":
                html_encoded = part["body"]["data"]
            elif "image" or "pdf" in part["mimeType"]:
                att = GmailAttachment(ident=part["body"]["attachmentId"], filename=part["filename"])
                gmail_attachments.append(att)
            else:
                logging.warning(f"Unexpected mimeType: {mime_type}")
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

    return Mail(sender=parseaddr(sender)[1], to=parseaddr(to)[1], date=date, subject=subject, plain_text=plain_text, html=html, ident=ident), gmail_attachments


def get_header(headers: dict, name: str) -> str:
    return next((header["value"] for header in headers if header["name"] == name))


def from_gmail(gmail: dict) -> Tuple[Mail, List[GmailAttachment]]:
    payload = gmail["payload"]
    mail, gmail_attachment = payload_to_mail(payload=payload, ident=gmail["id"])
    return mail, gmail_attachment