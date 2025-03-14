import os
import re
import random
import logging


logger = logging.getLogger(__name__)


def get_random_txt_file(folder):
    """Выбирает случайный .txt файл из папки."""
    txt_files = [f for f in os.listdir(folder) if f.endswith('.txt')]
    if not txt_files:
        raise FileNotFoundError('Нет текстовых файлов в папке.')
    random_file = random.choice(txt_files)
    logger.info(f'Случайно выбран файл с вопросами: {random_file}')
    return os.path.join(folder, random_file)


def format_text(text: str) -> str:
    """Сохраняет переносы строк, если текст полностью прописными буквами (стихи), иначе убирает переносы."""
    lines = text.splitlines()
    if all(line.isupper() or line.strip() == "" for line in lines):
        return text
    else:
        return " ".join(line.strip() for line in lines)


def prepare_questions(filename) -> dict:
    """Читает вопросы и ответы из указанного текстового файла и возвращает их в виде словаря."""
    with open(filename, "r", encoding="KOI8-R") as file:
        content = file.read()

    question_pattern = r"Вопрос\s\d+:\s*(.*?)(?=\nОтвет:)"
    answer_pattern = r"Ответ:\s*(.*?)(?=\n\n|$)"

    questions = [format_text(q.group(1).strip()) for q in re.finditer(question_pattern, content, re.DOTALL)]
    answers = [format_text(a.group(1).strip()) for a in re.finditer(answer_pattern, content, re.DOTALL)]

    if not questions or not answers:
        raise ValueError('Не удалось извлечь вопросы или ответы из файла.')

    return dict(zip(questions, answers))


def load_new_qa_file(redis_connect):
    """Загружает новый файл с вопросами и обновляет их в Redis."""
    file_with_qa = get_random_txt_file(os.path.join(os.path.dirname(__file__), 'data', "QA_FOLDER"))
    questions_dict = prepare_questions(file_with_qa)

    redis_connect.delete("questions")
    redis_connect.hset("questions", mapping=questions_dict)

    logger.info(f"Загружено {len(questions_dict)} вопросов.\nФайл: {file_with_qa}")


def get_random_question(redis_connect, user_id):
    """Выдает случайный вопрос пользователю и записывает его в Redis."""
    questions = redis_connect.hgetall("questions")

    if not questions:
        logger.warning("Все вопросы использованы. Загружаю новый файл...")
        load_new_qa_file(redis_connect)
        questions = redis_connect.hgetall("questions")

    if not questions:
        return None, None

    question = random.choice(list(questions.keys()))

    redis_connect.set(f"user:{user_id}:question", question)

    return question, questions[question]


def normalize_answer(text: str) -> str:
    """
    Нормализует ответ:
    - Удаляет содержимое в квадратных и круглых скобках.
    - Обрезает текст по первой точке.
    - Удаляет кавычки.
    - Убирает лишние знаки препинания (оставляя запятые, если несколько ответов).
    - Приводит к нижнему регистру и убирает лишние пробелы.
    """

    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = text.split('.')[0]
    text = text.replace('"', '').replace("'", '')
    text = re.sub(r'[^\w\s,]', '', text)
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def check_answer(user_answer: str, correct_answer: str) -> bool:
    """
    Проверяет ответ пользователя.

    Если правильный ответ содержит несколько вариантов, разделённых запятыми,
    то сравнивает множества вариантов.

    Сравнение нечувствительно к регистру, кавычкам и содержимому в скобках.
    """
    norm_user = normalize_answer(user_answer)
    norm_correct = normalize_answer(correct_answer)

    if ',' in norm_correct:
        correct_set = {item.strip() for item in norm_correct.split(',') if item.strip()}
        user_set = {item.strip() for item in norm_user.split(',') if item.strip()}
        return correct_set == user_set
    else:
        return norm_user == norm_correct
