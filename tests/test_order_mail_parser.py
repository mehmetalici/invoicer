from invoicer.config import load_config
import unittest

from invoicer.order import Address, Customer
from invoicer.order_mail_parsers import OrderMailParser


MAIL_BODY = 'Hallo!\r\n\r\nDu hast eine Bestellung (1357) über deinen Online-Shop\r\nwww.mustershop.de erhalten:\r\n\r\n\r\n==========\r\n\r\n2 x "Salvia uliginosa - Pfeffersalbei, Hummelschaukel" (Einzelpreis 7,50\r\n€): 15,00 €\r\n1 x "Tricyrtis macranthopsis" : 14,50 €\r\n2 x "Salvia greggii \'Blue Note\' - Pfirsich-Salbei" (Einzelpreis 7,00 €):\r\n14,00 €\r\n1 x "Corydalis calycosa" : 12,50 €\r\n1 x "Dicentra x hybr. \'Love Hearts\' - Tränendes Herz" : 10,00 €\r\n1 x "Corydalis nobilis - Edler Lerchensporn, Sibirischer Lerchensporn" :\r\n10,00 €\r\n1 x "Acanthus x hybr. \'Tasmanian Angel\'" : 10,00 €\r\n1 x "Dicentra cucullaria \'Pittsburg\'" : 9,50 €\r\n1 x "Acanthus x hybr. \'Whitewater\'" : 9,50 €\r\n1 x "Salvia argentea - Silber-Salbei" : 8,50 €\r\n1 x "Corydalis flexuosa \'Rainier Blue\' DJHC 0615" : 8,50 €\r\n1 x "Tricyrtis setouchiensis BSWJ4701" : 8,00 €\r\n1 x "Salvia forskaohlei - Bulgarischer Salbei, Balkan-Salbei" : 7,50 €\r\n1 x "Brunnera macrophylla \'Langtrees\'" : 7,50 €\r\n1 x "Corydalis flexuosa \'Blue Panda\' (Klon 2 - Typ Luckhardt)" : 7,50 €\r\n1 x "Tricyrtis formosana \'Small Wonder\' BSWJ306" : 7,50 €\r\n1 x "Corydalis linstowiana" : 7,50 €\r\n1 x "Penstemon mensarum - Tiger-Bartfaden" : 7,50 €\r\n1 x "Tricyrtis latifolia BSWJ10996" : 7,00 €\r\n1 x "Tricyrtis ravenii RWJ10012" : 7,00 €\r\n1 x "Primula japonica \'Carminea\' - Japanische Etagen-Schlüsselblume" : 7,00\r\n€\r\n1 x "Tricyrtis affinis BSWJ11063" : 7,00 €\r\n1 x "Polemonium reptans \'Blue Pearl\'" : 6,50 €\r\n1 x "Catananche caerulea \'Major\' - Blaue Rasselblume" : 6,50 €\r\n1 x "Lamium orvala \'Silva\' - Nesselkönig, Riesen-Taubnessel" : 6,50 €\r\n1 x "Corydalis flexuosa x omeiana \'Craigton Blue\'" : 6,50 €\r\n1 x "Tricyrtis formosana \'Dark Beauty\'" : 6,50 €\r\n1 x "Nepeta nervosa \'Neptune\' - Geaderte Katzenminze" : 5,50 €\r\n1 x "Tricyrtis hirta \'Taiwan Adbane\'" : 5,50 €\r\n1 x "Polemonium yezoense \'Purple Rain\' - Purpur-Jakobsleiter" : 5,50 €\r\n1 x "Tricyrtis hirta \'Sinonome\'" : 5,50 €\r\nSumme für alle Artikel: 257,50 €\r\n\r\n==========\r\n\r\n\r\nVersandkosten (inkl. MwSt.): 29,50 €\r\n----------------------------------------\r\n----------------------------------------\r\nGesamtpreis (inkl. MwSt.): 287,00 €\r\n\r\n\r\nBezahlmethode: Gegen Vorkasse\r\n\r\n*Rechnungs- und Versandadresse*\r\nMax Mustermann\r\nMusterweg 1\r\n01234 Berlin\r\nMusterland\r\nDeutschland\r\n004917612345678\r\ninfo@max.mustermann.com\r\n--\r\nDiese Bestelldaten findest du auch in der Bestellübersicht auf deiner\r\nWebseite: https://www.gaertnerei-bluetenreich.de/ Einfach einloggen und\r\nüber das Menü (auf der linken Seite) den Punkt "Shop" aufrufen.\r\n\r\n\r\n\r\n\r\n*Für Shops mit Sitz in einem EU-Land: Aufgrund neuer EU-Regelungen zur\r\nMehrwertsteuer gibt es Änderungen an deinem Onlineshop. Bitte stelle\r\nsicher, dass du bei all deinen Preisen bereits die MwSt. einkalkuliert\r\nhast.Befindet sich der Sitz deines Shops nicht in einem EU-Land, ändert\r\nsich nichts daran, wie die Mehrwertsteuer in deinem Shop angezeigt wird.*\r\n'    
MAIL_SUBJECT = 'Fwd: Neue Bestellung (1340) bei www.mustershop.de von Mustermann, Max'


class TestOrderAccount(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = OrderMailParser(
            subject=MAIL_SUBJECT,
            body=MAIL_BODY
        )

    def test_find_invoice_address(self):
        result = self.parser.find_invoice_address()
        correct = Address(
            full_name="Max Mustermann",
            address="Musterweg 1\n01234 Berlin\nMusterland\nDeutschland"
        )
        self.assertEqual(result, correct)

        self.parser.body.replace("info@max.mustermann.com", "not-an-email")
        result = self.parser.find_invoice_address()
        self.assertEqual(result, correct)


if __name__ == "__main__":
    unittest.main()