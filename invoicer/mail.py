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
            # raise Exception("html and plain_text fields cannot be both None.") 
            logging.warn("html and plain_text fields are both None.")

@dataclass
class ParsedMail:
    errors: List[str]
    mail: Mail


@dataclass
class GmailAttachment:
    filename: str
    ident: Optional[str] = None
    data: Optional[str] = None


class EmailPartExtractError(Exception):
    def __init__(self, mime_type, msg=None) -> None:
        super().__init__(msg)
        self.mime_type = mime_type


def payload_to_mail(payload: dict, ident: str) -> ParsedMail:
    headers = payload["headers"]
    subject = get_header(headers, "Subject")
    sender = get_header(headers, "From")
    to = get_header(headers, "To")
    date = get_header(headers, "Date")

    mime_type = payload["mimeType"]
    plain_text_encoded = None
    html_encoded = None
    gmail_attachments = []
    errors = []
    if "multipart/" in mime_type:
        parts_to_visit = list(payload["parts"])
        while parts_to_visit:
            part = parts_to_visit.pop(0)
            part_mime_type = part["mimeType"]
            if "parts" in part:
                parts_to_visit.extend(part["parts"])
            elif part_mime_type == "text/plain" and "data" in part["body"]:
                plain_text_encoded = part["body"]["data"]
            elif part_mime_type == "text/html" and "data" in part["body"]:
                html_encoded = part["body"]["data"]
            elif ("image" in part_mime_type or "pdf" in part_mime_type) and part.get(
                "filename"
            ):
                body = part["body"]
                if "attachmentId" in body or "data" in body:
                    att = GmailAttachment(
                        ident=body.get("attachmentId"),
                        data=body.get("data"),
                        filename=part["filename"],
                    )
                    gmail_attachments.append(att)
                else:
                    errors.append(f"Attachment without data: {part['filename']}")
            else:
                errors.append(f"Unexpected mimeType: {part_mime_type}")

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
    return Mail(sender=parseaddr(sender)[1], 
                to=parseaddr(to)[1], 
                date=date, 
                subject=subject, 
                plain_text=plain_text, 
                html=html, 
                ident=ident), gmail_attachments, errors


def get_header(headers: dict, name: str) -> str:
    return next((header["value"] for header in headers if header["name"] == name))


def from_gmail(gmail: dict) -> Tuple[Mail, List[GmailAttachment]]:
    payload = gmail["payload"]
    mail, gmail_attachment, errors = payload_to_mail(payload=payload, ident=gmail["id"])
    return mail, gmail_attachment, errors
