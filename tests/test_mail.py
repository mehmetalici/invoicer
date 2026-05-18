import base64
import unittest

from invoicer.mail import payload_to_mail


def encode_text(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode()


class TestMail(unittest.TestCase):
    def test_payload_to_mail_finds_nested_text_and_attachments(self):
        payload = {
            "headers": [
                {"name": "Subject", "value": "Hello"},
                {"name": "From", "value": "Customer <customer@example.com>"},
                {"name": "To", "value": "Seller <seller@example.com>"},
                {"name": "Date", "value": "Mon, 18 May 2026 19:38:47 +0200"},
            ],
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "body": {},
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": encode_text("Plain body")},
                        },
                        {
                            "mimeType": "text/html",
                            "body": {"data": encode_text("<p>HTML body</p>")},
                        },
                    ],
                },
                {
                    "mimeType": "image/jpeg",
                    "filename": "20260504_115223.jpg",
                    "body": {"attachmentId": "attachment-id"},
                },
            ],
        }

        mail, attachments, errors = payload_to_mail(payload=payload, ident="message-id")

        self.assertEqual(mail.plain_text, "Plain body")
        self.assertEqual(mail.html, "<p>HTML body</p>")
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].filename, "20260504_115223.jpg")
        self.assertEqual(attachments[0].ident, "attachment-id")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
