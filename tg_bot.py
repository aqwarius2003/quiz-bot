import os
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

logger = logging.getLogger(__name__)


def send_message(bot, chat_id, message):
    bot.send_message(chat_id=chat_id, text=message)


def respond_to_message(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает текстовые сообщения от пользователей и отправляет обратно как эхо.

    Параметры:

    update (Update): Объект, содержащий информацию о входящем обновлении от Telegram.

    context (CallbackContext): Контекст, предоставляющий доступ к боту и другим данным.
    """
    user_text = update.message.text
    send_message(context.bot, update.message.chat_id, user_text)


def start(update, context):
    update.message.reply_text('Здравствуйте! Я бот, который проведет для вас викторину.')


def main():
    load_dotenv()
    try:
        tg_bot_token = os.environ['TG_BOT_TOKEN']
    except KeyError as error:
        logger.error(f'Переменные окружения не найдены. Ошибка: {error}')

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    logger.info("The bot has started")

    try:
        updater = Updater(tg_bot_token)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, respond_to_message))

        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
