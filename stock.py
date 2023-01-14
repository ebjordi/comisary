from datetime import datetime, timedelta
import logging
import sqlite3
from agenda.dbHandle import create_db
from agenda.manager import get_google_creds, addEvent, send_mail_gmail_api,compose_mail, confirmation
import os
from dotenv import load_dotenv
load_dotenv()

sender = os.environ.get('FROM')
to = os.environ.get('TO')
dbname = os.environ.get('STOCKDB')
log_name = os.environ.get('STOCKLOG')

class Item:
    def __init__(self, name, stock, daily_usage_weight, box_quant, box_price, unit_weight):
        self.name = name
        self.stock = stock
        self.daily_usage_weight = daily_usage_weight
        self.box = {"quantity": box_quant, "price": box_price, "unit_weight": unit_weight}
        logging.basicConfig(filename=log_name, level=logging.DEBUG)
        logging.debug(
            f"Instantiated {self.name} with stock {self.stock}, with {self.daily_units()} units of {daily_usage_weight} kg per day"
        )
        logging.debug(f"Box has {box_quant} units")
    def add_stock(self, value):
        self.stock += value
        self.commit_to_table()
        logging.debug(f"Added {value} to stock of {self.name}. New stock: {self.stock}. Logged to database")
        print("Se actualizó el stock a {self.stock}. Base de datos actualizada")

    def add_box(self, boxes=1):
        self.add_stock(boxes * self.box["quantity"])

    def check_stock(self):
        days = self.days_left()
        till = (datetime.now() + timedelta(days=days)).strftime("%d-%m-%Y")
        print(
            f"Quedan {self.stock} items de {self.name}, aproximadamente hasta el {till} ({days} días)"
        )
        logging.debug(
            f"{self.stock} {self.name} units left, until {till} ({days} days left)"
        )
        logging.debug(f"Commiting stock to db")
        self.commit_to_table()
        if days <= 7:
            response = input(
                "Queda poco stock!  ¿Generar pedido y evento?[s/N]\n"
            ).upper()[0]

            if response == "N":
                print(
                    f"No se creará la orden, recordá checkear o agregar stock antes del {till}"
                )
            elif response == "S" or response == "Y":
                logging.debug(f"Accessing credentials to create event for {self.name}")
                print("Obteniendo credenciales")
                creds = get_google_creds()

                event_date = (
                    datetime.now() + timedelta(days=days - 2)
                ).strftime("%d-%m-%Y")

                event_date =  event_date.split("-")
                event_time = "14:00".split(":")
                addEvent(creds, event_date, event_time, 1, f"comprar {self.name}")
                logging.debug(f"Event created for {event_date}")

                subject = f"Poco stock de {self.name}"
                body = f'Queda poco stock de {self.name}. Solo para {days} días. Pedir a proovedor  '

                message = compose_mail(to,subject,body)
                prompt = f"Enviar mail a {to}?"
                if confirmation(prompt):
                    send_mail_gmail_api(creds, message)
                    logging.debug(f"Mail enviado a {to}. RE. {subject}")
                else:
                    print("Email no enviado")

    def daily_units(self):
        units = float(self.daily_usage_weight) / float(self.box["unit_weight"])
        return "{:.2f}".format(units)

    def days_left(self):
        units_needed = float(self.daily_units())
        days = self.stock // units_needed
        return int(days)



    def commit_to_table(self):
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS item
                     (nombre text, stock integer, uso_diario_kg real, uso_diario_u real, date text)"""
        )
        c.execute(
            "INSERT INTO item VALUES (?,?,?,?,?)",
            (
                self.name,
                self.stock,
                self.daily_usage_weight,
                self.daily_units(),
                datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            ),
        )
        conn.commit()
        print("Base actualizada")
        conn.close()

class Sector:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def check_stock(self):
        for item in self.items:
            item.check_stock()