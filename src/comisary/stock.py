import datetime
import logging
import sqlite3
from dbHandle import create_db
import sys
from time_manager import addEvent, compose_mail, confirmation
from services import get_google_creds, send_mail_gmail_api
import os
import sys
from dotenv import load_dotenv
load_dotenv()

sender = os.environ.get("FROM")
to = os.environ.get("TO")
dbname = os.environ.get("STOCKDB")
log_name = os.environ.get("STOCKLOG")


class ItemContainer:
    def __init__(self):
        self.items = {}


class Item:
    def __init__(
        self, name, stock, daily_usage_weight, box_quant, box_price, unit_weight
    ):
        self.name = name
        self.stock = stock
        self.daily_usage_weight = daily_usage_weight
        self.box = {
            "quantity": box_quant,
            "price": box_price,
            "unit_weight": unit_weight,
        }
        logging.basicConfig(filename=log_name, level=logging.DEBUG)
        logging.debug(
            f"Instantiated {self.name} with stock {self.stock}, with {self.daily_units()} units of {daily_usage_weight} kg per day"
        )
        logging.debug(f"Box has {box_quant} units")
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS item
                     (nombre text, stock integer, uso_diario_kg real, uso_diario_u real, hasta text, precio_x_mes)"""
        )
        self.days_left

    def add_stock(self, value):
        self.stock += value
        days = self.days_left()
        till = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime(
            "%d-%m-%Y"
        )
        self.commit_to_table(till)

        logging.debug(
            f"Added {value} to stock of {self.name}. New stock: {self.stock}. Logged to database"
        )
        print(f"Se actualizó el stock a {self.stock}. Base de datos actualizada")

    def add_box(self, boxes=1):
        self.add_stock(boxes * self.box["quantity"])

    def check_stock(self):
        days = self.days_left()
        till = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime(
            "%d-%m-%Y"
        )
        print(
            f"Quedan {self.stock} items de {self.name}, aproximadamente hasta el {till} ({days} días)"
        )
        logging.debug(
            f"{self.stock} {self.name} units left, until {till} ({days} days left)"
        )
        logging.debug(f"Committing stock to db")

        self.commit_to_table(till)

        if days <= 7:
            prompt = f"Queda poco stock! ¿Generar pedido y evento?"
            
            if not confirmation(prompt):
                print(f"No se creará la orden, recordá checkear o agregar stock antes del {till}")
            else:
                logging.debug(f"Accessing credentials to create event for {self.name}")
                print("Obteniendo credenciales")
                creds = get_google_creds()

                event_date = (
                    datetime.datetime.now() + datetime.timedelta(days=days - 2)
                ).strftime("%d-%m-%Y")

                event_date = event_date.split("-")
                event_time = "14:00".split(":")
                addEvent(creds, event_date, event_time, 1, f"comprar {self.name}")
                logging.debug(f"Event created for {event_date}")

                subject = f"Poco stock de {self.name}"
                body = f"Queda poco stock de {self.name}. Solo para {days} días. Pedir a proveedor  "

                message = compose_mail(to, subject, body)
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


    def monthly_price(self):
        daily_units = float(self.daily_units())
        monthly_units = daily_units * 30
        box_price = self.box["price"]
        unit_price = box_price / self.box["quantity"]
        monthly_price = monthly_units * unit_price
        return monthly_price

    def commit_to_table(self, till):
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute(
            "INSERT INTO item (nombre, stock, uso_diario_u, hasta, precio_x_mes) VALUES (?,?,?,?,?)",
            (
                self.name,
                self.stock,
                self.daily_units(),
                till,
                self.monthly_price(),
            ),
        )
        conn.commit()
        conn.close()
        logging.debug(f"{self.name} stock committed to db: {self.stock}")

    def commit_to_table(self, till):
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute("SELECT * FROM item WHERE nombre = ?", (self.name,))
        item = c.fetchone()
        if item:
            # Update existing item
            c.execute("UPDATE item SET stock = ?, hasta = ? WHERE nombre = ?", (self.stock, till, self.name))
        else:
            # Insert new item
            c.execute("INSERT INTO item (nombre, stock, uso_diario_kg, uso_diario_u, hasta, precio_x_mes) VALUES (?,?,?,?,?,?)", (self. name, self.stock, self.daily_usage_weight, self.daily_units(), till, self.monthly_price()))
        conn.commit()
        conn.close()