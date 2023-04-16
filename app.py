import logging
from pathlib import Path
from time import sleep

from invoicer.config import load_config
from invoicer.invoice import InvoiceGenerator
from invoicer.log_config import init_root_logger
import argparse
from googleapiclient.errors import HttpError

from invoicer.mail_account import InvoicerAccount


def main(config_file: Path, credentials_file: Path):
    config = load_config(path=config_file)
    init_root_logger()
    invoicer_account = InvoicerAccount(cfg=config, creds=credentials_file)
    invoice_generator = InvoiceGenerator(cfg=config)

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
        logging.info(f"Sleeping for {config.pollInterval}s")
        sleep(config.pollInterval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to configuration json file", type=str, required=True)
    parser.add_argument("-d", "--credentials", help="Path to credentials json file", type=str, required=True)
    args = parser.parse_args()
    config = Path(args.config)
    credentials = Path(args.credentials)

    while True:
        try:
            main(config_file=config, credentials_file=credentials)
        except Exception:
            logging.exception("An error occured. Restarting the app after 60 seconds...")
            sleep(60)
