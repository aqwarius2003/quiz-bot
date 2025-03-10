import logging
import os

import redis
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

from quiz_logic import get_random_question, check_answer


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

ANSWERING = 1


def build_menu():
    """Создает клавиатуру с кнопками."""
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def start(update: Update, context: CallbackContext):
    """Приветственное сообщение при старте."""
    update.message.reply_text(
        'Здравствуйте!\nЯ бот, который проведет для вас викторину.\n'
        'Нажмите "Новый вопрос", чтобы начать.',
        reply_markup=build_menu()
    )
    context.user_data["last_question"] = None
    return ANSWERING


def handle_new_question_request(update: Update, context: CallbackContext):
    """Выдает новый случайный вопрос пользователю и сохраняет его в Redis."""
    db_connection = context.bot_data['redis_connection']
    user_id = f'tg-{update.message.chat_id}'

    question, answer = get_random_question(db_connection, user_id)

    if not question:
        update.message.reply_text("Не удалось загрузить вопрос.")
        return ANSWERING

    update.message.reply_text(question)
    return ANSWERING


def give_up(update: Update, context: CallbackContext):
    """Показывает правильный ответ, если пользователь сдается, и дает новый вопрос."""
    db_connection = context.bot_data['redis_connection']
    user_id = f'tg-{update.message.chat_id}'

    # question = get_stored_question(db_connection, user_id)
    question = db_connection.get(f"user:{user_id}:question")
    answer = db_connection.hget("questions", question) if question else None

    if question and answer:
        update.message.reply_text(f'Правильный ответ:\n "{answer}"')
    else:
        update.message.reply_text("Вы не получали вопрос. Нажмите 'Новый вопрос'")

    return handle_new_question_request(update, context)


def show_score(update: Update, context: CallbackContext):
    update.message.reply_text("Вы лидируете")
    return ANSWERING


def handle_solution_attempt(update: Update, context: CallbackContext):
    user_answer = update.message.text
    db_connection = context.bot_data['redis_connection']
    user_id = f'tg-{update.message.chat_id}'

    question = db_connection.get(f"user:{user_id}:question")
    correct_answer = db_connection.hget("questions", question) if question else None

    if not question or not correct_answer:
        update.message.reply_text("Вы не получали вопрос. Нажмите 'Новый вопрос'.")
        return ANSWERING

    if check_answer(user_answer, correct_answer):
        update.message.reply_text(f'Правильно! Поздравляем.\n'
                                  f'Правильный ответ:\n{correct_answer}', reply_markup=build_menu())
    else:
        update.message.reply_text("Неправильно. Попробуйте ещё раз или нажмите 'Сдаться'.")

    return ANSWERING


def setup_handlers(dispatcher):
    """Обработка команд и сообщений."""
    conversation = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^Новый вопрос$'), handle_new_question_request)],
        states={
            ANSWERING: [
                MessageHandler(Filters.regex(r'^Новый вопрос$'), handle_new_question_request),
                MessageHandler(Filters.regex(r'^Сдаться$'), give_up),
                MessageHandler(Filters.regex(r'^Мой счет$'), show_score),
                MessageHandler(Filters.text & ~Filters.command, handle_solution_attempt),
            ]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conversation)


def main():
    """Запуск бота."""
    load_dotenv()

    try:
        tg_bot_token = os.environ['TG_BOT_TOKEN']
        redis_address = os.environ["REDIS_ADDRESS"]
        redis_port = os.environ["REDIS_PORT"]
        redis_password = os.environ['REDIS_PASSWORD']
    except KeyError as error:
        logger.error(f'Переменные окружения не найдены. Ошибка: {error}')
        return

    try:
        redis_connect = redis.Redis(
            host=redis_address,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )
        redis_connect.flushall()
        questions_and_answers = redis_connect.hgetall("questions")

        updater = Updater(tg_bot_token, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.bot_data['redis_connection'] = redis_connect
        dispatcher.bot_data['questions_and_answers'] = questions_and_answers

        setup_handlers(dispatcher)
        logger.info("Бот запущен")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
