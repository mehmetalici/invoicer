import logging
from pathlib import Path
from time import sleep

from invoicer.config import load_config
from invoicer.invoice import InvoiceGenerator
from invoicer.log_config import init_root_logger
import argparse
from googleapiclient.errors import HttpError

from invoicer.mail_account import InvoicerAccount


def main(config_file: Path, credentials_file: Path, token_file: Path, template_file: Path):
    config = load_config(path=config_file)
    init_root_logger()

    # TODO: Create Invoicer that composes orderAccount and invoice generator. 
    # TODO: Under loop, we have two flows: invoicer.process_new_orders(), order_account.forward_new_replies_to_seller() 
    
    invoicer_account = InvoicerAccount(cfg=config, creds=credentials_file, token=token_file)
    invoice_generator = InvoiceGenerator(cfg=config, template_path=template_file)

    while True:
        logging.info(f"Searching for orders...")
        orders = invoicer_account.search_new_orders()
        if len(orders) > 0:
            logging.info(f"{len(orders)} new orders are found, creating invoices...")
            for order in orders:
                invoice_path, errors = invoice_generator.generate(order=order)
                logging.info(f"Invoice is created at {invoice_path}")
                invoicer_account.send_invoice(order=order, errors=errors, invoice=invoice_path, delete_invoice=True)
        else:
            logging.info(f"No new orders are found.")
        
        logging.info("Searching for customer emails...")
        customer_mails = invoicer_account.search_new_customer_mails()
        if len(customer_mails) > 0:
            logging.info(f"{len(customer_mails)} customer mails are found")
            for customer_mail in customer_mails:
                invoicer_account.forward_customer_mail(customer_mail=customer_mail)
                logging.info(f"Customer mail was forwarded to seller.")
                # invoicer_account.inform_customer_forwarded(customer_mail=customer_mail)
                # logging.info(f"Customer was informed with forwarding.")
        else:
            logging.info("No new customer emails are found.")

        logging.info(f"Waiting for {config.pollInterval}s")
        sleep(config.pollInterval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to configuration json file", type=str, required=True)
    parser.add_argument("-d", "--credentials", help="Path to credentials json file", type=str, required=True)
    parser.add_argument("-t", "--token", help="Path to token json file. If unspecified, app will create one with web-auth flow.", type=str, required=False)
    parser.add_argument("-p", "--template", help="Path to template docx file.", type=str, required=True)
    args = parser.parse_args()
    config = Path(args.config)
    credentials = Path(args.credentials)
    template = Path(args.template)
    if args.token is None:
        token = ".token.json"
    else:
        token = Path(args.token)

    while True:
        try:
            main(config_file=config, credentials_file=credentials, token_file=token, template_file=template)
        except Exception:
            logging.exception("An error occured. Restarting the app after 60 seconds...")
            sleep(60)
