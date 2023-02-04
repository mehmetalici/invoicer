# invoicer
A Gmail bot that generates invoices from order confirmation emails and sends it to seller in real-time.

For example, given the incoming order confirmation email:

```
Hallo!

Du hast eine Bestellung (123) über deinen Online-Shop www.muster-shop.de erhalten:


==========

1 x "Englische Rose 'Munstead Wood'" : 30,00 €
1 x "Epimedium grandiflorum 'Yubae'" : 5,50 €
Summe für alle Artikel: 35,50 €

==========


Versandkosten (inkl. MwSt.): 12,00 €
----------------------------------------
----------------------------------------
Gesamtpreis (inkl. MwSt.): 47,50 €


Bezahlmethode: Kreditkarte

*Rechnungs- und Versandadresse*
Max Mustermann
Musterweg 123
12345 Berlin
Deutschland
+491761234567
maxmustermann@email.de

--
Diese Bestelldaten findest du auch in der Bestellübersicht auf deiner Webseite: https://www.muster-shop.de/ Einfach einloggen und über das Menü (auf der linken Seite) den Punkt "Shop" aufrufen.


Für Shops mit Sitz in einem EU-Land: Aufgrund neuer EU-Regelungen zur Mehrwertsteuer gibt es Änderungen an deinem Onlineshop. Bitte stelle sicher, dass du bei all deinen Preisen bereits die MwSt. einkalkuliert hast.

Befindet sich der Sitz deines Shops nicht in einem EU-Land, ändert sich nichts daran, wie die Mehrwertsteuer in deinem Shop angezeigt wird.
```

The bot parses and converts it to the following print-ready invoice seconds after arrival to its inbox:

![](docs/template_customer-1.png)

After generating above invoice, the bot sends it to the seller with email as attachment.

## Running a Demo
A step-by-step instructions on how to run the application on your machine.

### Prerequisites
1. Poetry package manager
    
    Install it from https://python-poetry.org/docs/.

2. Python ^3.10.7

    You can use Pyenv https://github.com/pyenv/pyenv.

3. Microsoft Office Word 2016+

### Installation
1. Clone repository:
    ```
    git clone git@github.com:mehmetalici/invoicer.git
    ```

2. Install dependencies:
    ```
    cd invoicer
    poetry install
    ```
3. Open `docs/template_sample.docx` with Word 2016+:
    ![](docs/template_ex-1.png)


    Customize the template according to your wishes. You can add extra text, images etc.
    
    Note that you should treat the text within '{{}}' as special and not replace the characters inside of it. You can, however, move them freely throughout the document. Do not change the column number in the table as well.   

4. Create a `config.json` similar to the following sample and edit it according to your specs. You can refer to the explanation section for clarifications.
    ```json
    {
        "orderMail": {
            "sender": "no-reply@hoster.de",
            "subjectHas": "Neue Bestellung"
        },
        "invoiceMail": {
            "to": "info@mustershop.de",
            "saluteName": "Maximiliane"
        },
        "invoiceCountStart": 0,
        "pollInterval": 10,
        "invoiceTemplatePath": "./docs/template_sample.docx",
        "OAuth2AppCredentialsPath": "/path/to/your/credentials.json"
    }
    ```
    **Explanation for the fields**:
    - orderMail.sender: Email account sending order confirmations
    - orderMail.subjectHas: A substring in subject line for order confirmation emails
    - invoiceMail.to: Email address to send the generated invoice
    - invoiceMail.saluteName: Salutation name for the email address holder
    - invoiceCountStart: Last invoice number before the start of Gmail bot
    - pollInterval: Period of polls in seconds for checking any incoming order confirmation emails 
    - invoiceTemplatePath: Path to your invoice template 
    - OAuth2CredentialsPath: Path to your credentials file obtained from Google Cloud console.

5. For Google OAuth Servers to identify the app, create a OAuth2 Client ID for the app following the instructions on below link:

     https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application 

    Afterwards, save `credentials.json` to a secure directory. Take steps to protect and secure the file.  
### Running
1. Start the application with the following command:
    ```
    poetry run python app.py -c config.json
    ```
2. If you run for the first time, a web page will prompt you to authenticate your Gmail account and authorize the bot to manage the account.
3. After the authentication flow has completed, the app will start to its normal operation and output the following information:
    ```
    2023-01-24 21:55:05 INFO     Searching for orders...
    2023-01-24 21:55:05 INFO     No new orders are found.
    2023-01-24 21:55:05 INFO     Sleeping for 10s
    2023-01-24 21:55:15 INFO     Searching for orders...
    ```
4. If a new order confirmation mail appears, it will output the following: