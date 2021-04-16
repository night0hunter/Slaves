import logging
import os
import random
import sys
from data import db_session
from telegram.ext import Updater, CommandHandler, CallbackContext
from data.users import User

# Enabling logging  
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")

# REQUEST_KWARGS = {
#     'proxy_url': 'socks5://tginfo.themarfa.online',  # Адрес прокси сервера
#     # Опционально, если требуется аутентификация:
#     'urllib3_proxy_kwargs': {
#         'assert_hostname': 'False',
#         'cert_reqs': 'CERT_NONE'
#         # 'username': 'user',
#         # 'password': 'password'
#     }
# }

if mode == "dev":
    def run(updater):
        updater.start_polling()
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
    # Creating a handler-function for /start command
    logger.info("User {} started bot".format(update.effective_user["id"]))
    update.message.reply_text(
        "Hello from Python!\nPress /random to get random number")

def random_handler(update, context):
    # Creating a handler-function for /random command
    number = random.randint(0, 10)
    logger.info("User {} randomed number {}".format(
        update.effective_user["id"], number))
    update.message.reply_text("Random number: {}".format(number))

def print_money(update, context):
    user = db_sess.query(User).first()
    logger.info("User {} printed money {}".format(
        update.effective_user["id"], user.money))
    update.message.reply_text("Your money: {}".format(user.money))

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN)
    
    
    db_session.global_init("db/slaves.db")

    user = User()
    user.name = "guest"
    user.money = 0
    user.parent_id = None
    user.hashed_password = ""
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()

    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler("random", random_handler))
    updater.dispatcher.add_handler(CommandHandler("money", print_money))

    run(updater)
