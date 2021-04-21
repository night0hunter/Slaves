import logging
import os
import random
import sys
from data import db_session
from telegram.ext import Updater, CommandHandler, CallbackContext
from data.users import User
import sqlite3
from sqlalchemy import desc, select

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
    update.message.reply_text("Пользователь успешно зарегистрирован!")
def random_handler(update, context):
    # Creating a handler-function for /random command
    number = random.randint(0, 10)
    logger.info("User {} randomed number {}".format(
        update.effective_user["id"], number))
    update.message.reply_text("Random number: {}".format(number))

def print_money(update, context):
    cur_id = update.effective_user["id"]
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == cur_id).first()
    db_sess.commit()
    logger.info("User {} printed money {}".format(
        cur_id, user.money))
    update.message.reply_text("Your money: {}".format(user.money))

def rating(update, context):
    # result = cur.execute("""SELECT * FROM users ORDER BY money DESC""").fetchall()
    logger.info("User {} viewed rating".format(update.effective_user["id"]))
    db_sess = db_session.create_session()
    users = db_sess.query(User).order_by(User.money.desc())
    db_sess.commit()
    text = "\n".join([f"{user.name}:    {user.money}" for user in users])
    update.message.reply_text(text)

def slaves_purchasing(update, context):
    def slaves_purchasing(update, context):
    cur_id = update.effective_user["id"]
    db_sess = db_session.create_session()

    slave = update.message.text.split()
    cur_user = db_sess.query(User).filter(User.id == cur_id).first()  
    users = db_sess.query(User)
    usersNames = "\n".join([user.name for user in users])
    if slave[1] not in usersNames:
        update.message.reply_text("Такого пользователя не существует!")
        logger.info("User {} tried to buy non-existent person".format(cur_id))
        
    elif cur_user.name == slave[1]:
        update.message.reply_text("Нельзя купить самого себя!")
        logger.info("User {} tried to buy himself".format(cur_id))

    else:
        slaveObj = db_sess.query(User).filter(User.name == slave[1]).first()
        slaveObj.parent_id = cur_id
        update.message.reply_text("Успешно!")
        logger.info("User {} bought user {}".format(cur_id, cur_user))


    db_sess.commit()

def profile(update, context):
    logger.info("User {} viewed profile".format(update.effective_user["id"]))
    cur_id = update.effective_user["id"]
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == cur_id).first()
    db_sess.commit()
    update.message.reply_text(f"Name: {user.name}\nMoney: {user.money}\nYour owner: {user.parent_id}")

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN)
    
    
    db_session.global_init("db/slaves.db")

    

    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler("random", random_handler))
    updater.dispatcher.add_handler(CommandHandler("money", print_money))
    updater.dispatcher.add_handler(CommandHandler("rating", rating))
    updater.dispatcher.add_handler(CommandHandler("profile", profile))

    run(updater)
