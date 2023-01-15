import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from stock import ItemContainer,Item
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("TOKEN")
sender = os.environ.get("FROM")
calendarId = os.environ.get("CALID")
dbname = os.environ.get("COMMITDB")


class ItemContainer:
    def __init__(self):
        self.items = {}

    def add_item(self, name, stock, daily_usage_weight, box_quant, box_price, unit_weight):
        self.items[name] = Item(name, stock, daily_usage_weight, box_quant, box_price, unit_weight)
    
    def check_all_stock(self):
        for name, item in self.items.items():
            item.check_stock()


class TelegramBot:
    def __init__(self, token, item_container):
        self.bot = telegram.Bot(token=token)
        self.updater = Updater(self.bot,None)
        self.item_container = item_container

        start_handler = CommandHandler("start", self.start)
        self.dispatcher.add_handler(start_handler)
        
        add_item_handler = CommandHandler("add_item", self.add_item)
        self.dispatcher.add_handler(add_item_handler)

        check_stock_handler = CommandHandler("check_all_stock", self.check_all_stock)
        self.dispatcher.add_handler(check_stock_handler)

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Item Tracker Bot! Please select an option from the menu below.")
        self.show_main_menu(update, context)

    def add_item(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the item information in the following format: name, stock, daily_usage_weight, box_quant, box_price, unit_weight")
        item_info_handler = MessageHandler(Filters.text, self.process_item_info)
        self.dispatcher.add_handler(item_info_handler)

    def process_item_info(self, update, context):
        item_info = update.message.text.split(", ")
        name, stock, daily_usage_weight, box_quant, box_price, unit_weight = item_info
        self.item_container.add_item(name, int(stock), float(daily_usage_weight), int(box_quant), float(box_price), float(unit_weight))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Item added successfully.")
        self.show_main_menu(update, context)

    def check_all_stock(self, update, context):
        self.item_container.check_all_stock()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Checked all item stocks.")

    def show_main_menu(self, update, context):
        main_menu = "Please select an option:\n"
        main_menu += "/add_item - Add a new item\n"
        main_menu += "/check_all_stock - Check the stock of all items\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=main_menu)

    def start_polling(self):
        self.updater.start_polling()

if __name__ == "__main__":
    item_container = ItemContainer()
    bot = TelegramBot(token, item_container)
    bot.start_polling()


