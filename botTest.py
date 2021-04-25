import logging
import os
import random
import sys
from data import db_session
from sqlalchemy import desc, select
from telegram.ext import Updater, CommandHandler, CallbackContext
from data.users import User
import time
from datetime import timedelta

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
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
    user.money = 100
    user.parent_id = None
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()
    update.message.reply_text("User successfully registered!")

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
    cur_id = update.effective_user["id"]
    db_sess = db_session.create_session()

    slave = update.message.text.split()
    cur_user = db_sess.query(User).filter(User.id == cur_id).first()  
    users = db_sess.query(User)
    slave2 = db_sess.query(User).filter(slave[1] == User.name).first()
    usersNames = "\n".join([user.name for user in users])
    if slave[1] not in usersNames:
        update.message.reply_text("This user doesn't exist!")
        logger.info("User {} tried to buy non-existent person".format(cur_id))
        
    elif cur_user.name == slave[1]:
        update.message.reply_text("You can't buy yourself!")
        logger.info("User {} tried to buy himself".format(cur_id))
    elif cur_user.id == slave2.id:
        update.message.reply_text("You can't buy your's slave")
        logger.info("User {} tried to buy his slave".format(cur_id))
    else:
        if cur_user.money >= 100:
            slaveObj = db_sess.query(User).filter(User.name == slave[1]).first()
            if slaveObj.parent_id != None:
                oldOwner = db_sess.query(User).filter(slaveObj.parent_id == User.id).first()
                oldOwner.count_slaves -= 1
                oldOwner.money += 50
                cur_user.money -= 100
            else:
                cur_user.money -= 100
            slaveObj.parent_id = cur_id
            cur_user.count_slaves += 1
            update.message.reply_text("Success!")
            logger.info("User {} bought user {}".format(cur_id, slave2.id))
        else:
            update.message.reply_text("Not enough money!")


    db_sess.commit()

def profile(update, context):
    mess = update.message.text.split()
    if len(mess) == 1:
        logger.info("User {} viewed profile".format(update.effective_user["id"]))
        cur_id = update.effective_user["id"]
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == cur_id).first()
        if user.parent_id != None:
            parent = db_sess.query(User).filter(User.id == user.parent_id).first()
            update.message.reply_text(f"Name: {user.name}\nMoney: {user.money}\nYour owner: {parent.name}")
        else:
            update.message.reply_text(f"Name: {user.name}\nMoney: {user.money}\nYour owner: None")
        db_sess.commit()
        
    else:
        db_sess = db_session.create_session()
        cur_id = update.effective_user["id"]
        cur_user = db_sess.query(User).filter(User.id == cur_id).first()  
        users = db_sess.query(User)
        usersNames = "\n".join([user.name for user in users])
        if mess[1] not in usersNames:
            update.message.reply_text("This user doesn't exist")
            logger.info("User {} tried to check profile of non-existent person".format(cur_id))
        else:
            slave2 = db_sess.query(User).filter(mess[1] == User.name).first()
            if slave2.parent_id != None:
                user2 = db_sess.query(User).filter(User.id == slave2.parent_id).first()
                update.message.reply_text(f"Name: {slave2.name}\nMoney: {slave2.money}\nHis owner: {user2.name}")
            else:
                update.message.reply_text(f"Name: {slave2.name}\nMoney: {slave2.money}\nHis owner: None")
        db_sess.commit()

def add_money(context: CallbackContext):
    db_sess = db_session.create_session()
    users = db_sess.query(User)
    for user in users:
        user.money += 10 * user.count_slaves 
    db_sess.commit()

def help(update, context):
    update.message.reply_text("Creating profile: /start\nProfile print: /profile\nMoney print: /money\nRating print: /rating\nBuy slaves: /buy <username>")


if __name__ == '__main__':
    db_session.global_init("db/slaves.db")
    logger.info("Starting bot")
    updater = Updater(TOKEN)
    j = updater.job_queue
    j.run_repeating(add_money, timedelta(seconds=5))


    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler("money", print_money))
    updater.dispatcher.add_handler(CommandHandler("rating", rating))
    updater.dispatcher.add_handler(CommandHandler("profile", profile))
    updater.dispatcher.add_handler(CommandHandler("buy", slaves_purchasing))
    updater.dispatcher.add_handler(CommandHandler("help", help))


    run(updater)
    