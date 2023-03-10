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
```

The bot parses and converts it to the following print-ready invoice seconds after arrival to its inbox:

![](docs/template_customer-1.png)

After generating the invoice above, the bot sends it to the seller with email as attachment.

## Running a Demo
Follow the instructions below to run a demo on your machine: 

### Prerequisites
1. Poetry package manager
    
    Install it from https://python-poetry.org/docs/.

2. Python ^3.10.7

    You can use Pyenv https://github.com/pyenv/pyenv.

3. Microsoft Office Word 2016+

### Installation
1. Clone repository and install dependencies:
    ```
    git clone git@github.com:mehmetalici/invoicer.git
    cd invoicer
    poetry install
    ```

2. Edit the invoice template:

    To do this, Open `docs/template_sample.docx` with Word 2016+:
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
    - **orderMail.sender**: Email account sending order confirmations
    - **orderMail.subjectHas**: A substring in subject line for order confirmation emails
    - **invoiceMail.to**: Email address to send the generated invoice
    - **invoiceMail.saluteName**: Salutation name for the email address holder
    - **invoiceCountStart**: Last invoice number before the start of Gmail bot
    - **pollInterval**: Period of polls in seconds for checking any incoming order confirmation emails 
    - **invoiceTemplatePath**: Path to your invoice template 
    - **OAuth2CredentialsPath**: Path to your credentials file obtained from Google Cloud console. Refer to the following step to create one.

5. For Google OAuth Servers to identify the app, create a OAuth2 Client ID for the app following the instructions on below link:

     https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application 

    Afterwards, save `credentials.json` to a secure directory and provide its path with `OAuth2AppCredentialsPath=/path/to/your/credentials.json` in `config.json` . Take steps to protect and secure the file.  
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
    ```
    2023-02-05 13:48:39 INFO     Searching for orders...
    2023-02-05 13:48:40 INFO     1 new orders are found, creating invoices...
    2023-02-05 13:48:43 INFO     Invoice is created at docs/Invoice-2023001.docx
    2023-02-05 13:48:45 INFO     Mail has been sent. Message Id: 186219f2db25b235
    2023-02-05 13:48:45 INFO     Sleeping for 10s
    ```