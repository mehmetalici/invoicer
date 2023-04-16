import json
from dataclasses import dataclass
from pathlib import Path

from dacite import from_dict


@dataclass
class OrderMailCfg:
    subjectHas: str
    sender: str


@dataclass
class InvoiceMailCfg:
    to: str
    saluteName: str


@dataclass
class Config:
    orderMail: OrderMailCfg
    invoiceMail: InvoiceMailCfg
    invoiceCountStart: int
    pollInterval: int
    invoiceTemplatePath: str


def load_config(path: Path):
    with open(path) as json_file:
        data = json.load(json_file)
    return from_dict(data_class=Config, data=data)
