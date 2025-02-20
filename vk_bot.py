import logging
import os
import random
import redis
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api
from quiz_logic import get_random_question, get_stored_question, get_answer, check_answer
from vk_api.keyboard import VkKeyboard


logger = logging.getLogger(__name__)


def send_message(vk, user_id, message, keyboard=None):
    """Отправляет сообщение пользователю."""
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.randint(1, 10 ** 6),
        keyboard=keyboard.get_keyboard() if keyboard else None
    )


def create_vk_keyboard():
    """Создает клавиатуру ВКонтакте."""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться')
    keyboard.add_line()
    keyboard.add_button('Мой счет')
    return keyboard


def start_message(vk, user_id):
    """Отправляет приветственное сообщение."""
    send_message(vk, user_id,
                 "Здравствуйте!\nЯ бот, который проведет для вас викторину.\nНажмите 'Новый вопрос', чтобы начать.",
                 create_vk_keyboard())


def handle_new_question_request(vk, event, redis_connect):
    """Выдает новый случайный вопрос пользователю."""
    user_id = f'vk-{event.user_id}'
    question, answer = get_random_question(redis_connect, user_id)
    if not question:
        send_message(vk, user_id, "Не удалось загрузить вопрос.", create_vk_keyboard())
        return
    send_message(vk, user_id, question, create_vk_keyboard())


def give_up(vk, event, redis_connect):
    """Показывает правильный ответ и дает новый вопрос."""
    user_id = f'vk-{event.user_id}'
    question = get_stored_question(redis_connect, user_id)
    answer = get_answer(redis_connect, question) if question else None
    if question and answer:
        send_message(vk, user_id, f'Правильный ответ:\n "{answer}"', create_vk_keyboard())
    else:
        send_message(vk, user_id, "Я бот, который проводит викторину. Нажмите 'Новый вопрос'", create_vk_keyboard())


def show_score(vk, event):
    """Показывает счет (заглушка)."""
    send_message(vk, event.user_id, "Вы лидируете", create_vk_keyboard())


def handle_solution_attempt(vk, event, redis_connect):
    """Обрабатывает ответ пользователя."""
    user_answer = event.text
    user_id = f'vk-{event.user_id}'
    question = get_stored_question(redis_connect, user_id)
    correct_answer = get_answer(redis_connect, question) if question else None
    if not question or not correct_answer:
        send_message(vk, user_id, 'Не верный ответ или команда', create_vk_keyboard())
        return
    if check_answer(user_answer, correct_answer):
        send_message(vk, user_id, f'Правильно! Поздравляем.\nПравильный ответ:\n{correct_answer}', create_vk_keyboard())
    else:
        send_message(vk, user_id, 'Неправильно. Попробуйте ещё раз или нажмите "Сдаться".', create_vk_keyboard())


def main():
    """Запуск бота."""

    load_dotenv()
    try:
        vk_token = os.environ['VK_API_KEY']
        redis_address = os.environ["REDIS_ADDRESS"]
        redis_port = os.environ["REDIS_PORT"]
        redis_password = os.environ['REDIS_PASSWORD']
    except KeyError as error:
        logger.error(f'Переменные окружения не найдены. Ошибка: {error}')
        return
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    logger.info("VK бот запущен")
    try:
        redis_connect = redis.Redis(
            host=redis_address,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )
        redis_connect.flushall()
        vk_session = vk_api.VkApi(token=vk_token)
        vk = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)

        command_handlers = {
            "Привет": start_message,
            "start": start_message,
            "Новый вопрос": handle_new_question_request,
            "Сдаться": give_up,
            "Мой счет": show_score
        }

        for event in longpoll.listen():
            if not (event.type == VkEventType.MESSAGE_NEW and event.to_me):
                continue
            handler = command_handlers.get(event.text)
            if handler:
                handler(vk, event, redis_connect)
            else:
                handle_solution_attempt(vk, event, redis_connect)

    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
