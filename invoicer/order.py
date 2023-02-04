from dataclasses import dataclass, field
from typing import List, Optional


from invoicer.mail import Mail


@dataclass
class Customer:
    name: str
    email: str
    phone: str


@dataclass
class Address:
    full_name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Invoice:
    address: Address
    number: Optional[str] = None
    date: Optional[str] = None
    docx: Optional[bytes] = None
    pdf: Optional[bytes] = None


@dataclass
class Item:
    count: int
    description: str
    price: float
    tax_rate: float = 0.07
    unit: str = "Stck."

    unit_price_net: float = field(init=False)
    unit_price_gross: float = field(init=False)
    total_price_net: float = field(init=False)
    total_price_gross: float = field(init=False)
    tax: float = field(init=False)

    def __post_init__(self):
        self.total_price_net = self.price / (1 + self.tax_rate)
        self.total_price_gross = self.price
        self.tax = self.total_price_gross - self.total_price_net
        self.unit_price_gross = self.total_price_gross / self.count
        self.unit_price_net = self.total_price_net / self.count


@dataclass
class Customer:
    name: str
    surname: str

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"


@dataclass
class Order:
    source_mail: Optional[Mail] = None
    number: Optional[str] = None
    date: Optional[str] = None
    invoice: Optional[Invoice] = None
    delivery_address: Optional[Address] = None
    items: Optional[List[Item]] = None
    shipping_cost: Optional[float] = None
    payment_method: Optional[str] = None 
    customer: Optional[Customer] = None





