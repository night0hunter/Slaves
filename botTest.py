import logging
import os
import random
import sys
from data import db_session
from telegram.ext import Updater, CommandHandler, CallbackContext
from data.users import User
import sqlite3


# Enabling logging  
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

con = sqlite3.connect("db\slaves.db")
cur = con.cursor()
# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")

if mode == "dev":
    def run(updater):
        updater.start_polling()
        updater.idle()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "500"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook(
            "https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)


def start_handler(update, context):
    logger.info("User {} started bot".format(update.effective_user))

    user = User()
    user.id = update.effective_user["id"]
    user.name = update.effective_user["username"]
    user.money = 0
    user.parent_id = None
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()

def random_handler(update, context):
    # Creating a handler-function for /random command
    number = random.randint(0, 10)
    logger.info("User {} randomed number {}".format(
        update.effective_user["id"], number))
    update.message.reply_text("Random number: {}".format(number))

def print_money(update, context):
    global cur
    global con
    cur_id = update.effective_user["id"]
    # user_money = cur.execute(f"""SELECT money FROM users WHERE id = '{cur_id}'""").fetchone()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == cur_id).first()
    db_sess.commit()
    logger.info("User {} printed money {}".format(
        cur_id, user.money))
    update.message.reply_text("Your money: {}".format(user.money))

def rating(update, context):
    result = cur.execute("""SELECT * FROM users ORDER BY money DESC""").fetchall()
    print(result)

def slaves_purchasing(update, context):
    pass

def profile(update, context):
    pass
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN)
    
    
    db_session.global_init("db/slaves.db")

    

    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler("random", random_handler))
    updater.dispatcher.add_handler(CommandHandler("money", print_money))
    updater.dispatcher.add_handler(CommandHandler("rating", rating))

    run(updater)
