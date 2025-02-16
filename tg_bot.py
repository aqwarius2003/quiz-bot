import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from telegram.ext import ConversationHandler
from quiz_logic import get_random_question, load_new_qa_file, QUESTIONS

logger = logging.getLogger(__name__)

ANSWERING = 1


def build_menu():
    """Создает клавиатуру с кнопками."""
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def start(update: Update, context: CallbackContext):
    """Приветственное сообщение при старте."""
    update.message.reply_text(
        'Здравствуйте! Я бот, который проведет для вас викторину.\n'
        'Нажмите "Новый вопрос", чтобы начать.',
        reply_markup=build_menu()
    )
    context.user_data["last_question"] = None  # Сбрасываем текущий вопрос
    return ANSWERING


def handle_new_question_request(update: Update, context: CallbackContext):
    """Выдает новый случайный вопрос и запоминает его."""
    question, answer = get_random_question()

    if not question:
        update.message.reply_text("Вопросы закончились или не загружены.")
        return ANSWERING

    context.user_data["last_question"] = question  # Сохраняем текущий вопрос
    context.user_data["last_answer"] = answer  # Сохраняем текущий ответ

    update.message.reply_text(question)
    return ANSWERING


def give_up(update: Update, context: CallbackContext):
    """Показывает правильный ответ, если пользователь сдается."""
    last_question = context.user_data.get("last_question")
    last_answer = context.user_data.get("last_answer")

    if last_question and last_answer:
        update.message.reply_text(last_answer)
        context.user_data["last_question"] = None  # Сбрасываем текущий вопрос
        context.user_data["last_answer"] = None  # Сбрасываем текущий ответ
    else:
        update.message.reply_text("Сначала получите вопрос! Нажмите 'Новый вопрос'.")


def handle_solution_attempt(update: Update, context: CallbackContext):
    """Пока просто заглушка – в будущем здесь будет проверка ответа."""
    update.message.reply_text("Ваш ответ принят!")
    return ANSWERING


def setup_handlers(dispatcher):
    """Настроить обработку команд и сообщений."""
    conversation = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^Новый вопрос$'), handle_new_question_request)],
        states={
            ANSWERING: [
                MessageHandler(Filters.regex(r'^Новый вопрос$'), handle_new_question_request),
                MessageHandler(Filters.regex(r'^Сдаться$'), give_up),
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
    except KeyError as error:
        logger.error(f'Переменные окружения не найдены. Ошибка: {error}')
        return

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    logger.info("Бот запущен")

    # Изначальная загрузка вопросов
    load_new_qa_file()

    try:
        updater = Updater(tg_bot_token, use_context=True)
        dispatcher = updater.dispatcher

        setup_handlers(dispatcher)

        updater.start_polling(timeout=20)
        updater.idle()
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
