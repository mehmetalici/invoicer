import gettext
import logging
import re
from typing import Callable, List

import pycountry

from invoicer.mail import Mail
from invoicer.order import Address, Customer, Invoice, Item, Order


def handle_exception(finder: Callable):
    def inner(self, *wargs, **kwargs):
        try:
            return finder(self, *wargs, **kwargs)
        except Exception:
            # TODO: Reduce exception scope?
            logging.exception("Finder exception")
            return None

    return inner


class OrderMailParser:
    def __init__(self, subject: str, body: str) -> None:
        """
        Given subject and body of text involving order details, extract necessary information out of it.
        If extraction fails, log error and return None.
        """
        self.body = body 
        self.body = self.body.replace("<br/>", "\r\n")
        self.body = self.body.replace("\r", "\\r").replace("\n", "\\n")

        self.subject = subject

    @handle_exception
    def find_customer(self):
        p = re.compile("von (.+), (.+)")
        result = p.search(self.subject)
        surname = result.group(1)
        name = result.group(2)
        return Customer(name, surname)

    @handle_exception
    def find_items(self):
        p = re.compile(r'(\d) x "(.+?)" .*?: (\d+,\d{2}) €')
        return [
            Item(count=int(m[0]), description=m[1].replace("\\r\\n", "\r\n"), price=float(m[2].replace(",", ".")))
            for m in p.findall(self.body)
        ]

    @handle_exception
    def find_order_number(self):
        p = re.compile(r"Du hast eine Bestellung \((\d+)\) über deinen Online-Shop")
        return p.search(self.body).group(1)

    @handle_exception
    def find_shipping_cost(self):
        p = re.compile(r"Versandkosten \(inkl. MwSt.\): (\d+,\d{2}) €")
        return float(p.search(self.body).group(1).replace(",", "."))

    @handle_exception
    def find_payment_method(self, short=True):
        p = re.compile(r"Bezahlmethode: (.+)\\r\\n\\r\\n\*Rechnungs")
        payment_method = p.search(self.body).group(1).rstrip()
        if short:
            return _simplify_payment_method(payment_method)
        return payment_method

    @handle_exception
    def find_invoice_address(self):
        p = re.compile(
            r"Rechnung(?:sadresse|s- und Versandadresse)\*\\r\\n(.+\\r\\n[a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)",
            flags=re.M,
        )

        invoice_address = p.search(self.body).group(1).split("\\r\\n")
        country_index = _find_country_index(invoice_address)
        residential_address_end_index = country_index

        residential_address = "\n".join(
            invoice_address[1 : residential_address_end_index + 1]
        )

        address = Address(full_name=invoice_address[0], address=residential_address)
        return address


    @handle_exception
    def find_invoice(self):
        # TODO: Fix this
        address = self.find_invoice_address()
        return Invoice(address=address)
     


def _find_country_index(address: List[str]):
    german = gettext.translation("iso3166", pycountry.LOCALES_DIR, languages=["de"])
    german.install()
    countries = tuple(map(lambda c: _(c.name), pycountry.countries))
    for part in address:
        if part in countries:
            return address.index(part)


def _simplify_payment_method(payment_method: str):
    # TODO:Is it safe?
    if "Vorkasse" in payment_method:
        return "Vorkasse"
    if "PayPal" in payment_method:
        return "PayPal"
    if "Stripe" in payment_method:
        return "Stripe"
    return payment_method


def find_country_index(address: List[str]):
    german = gettext.translation("iso3166", pycountry.LOCALES_DIR, languages=["de"])
    german.install()
    countries = tuple(map(lambda c: _(c.name), pycountry.countries))
    for part in address:
        if part in countries:
            return address.index(part)


def order_from_mail(mail: Mail):
    """
    Find parser of provider and parse.
    """
    mail = mail.mail
    parser = OrderMailParser(subject=mail.subject, body=mail.plain_text)
    order = Order(
        source_mail=mail,
        number=parser.find_order_number(),
        invoice=parser.find_invoice(),
        items=parser.find_items(),
        shipping_cost=parser.find_shipping_cost(),
        payment_method=parser.find_payment_method(short=True),
        customer=parser.find_customer(),
        date=mail.date
    )
    return order
