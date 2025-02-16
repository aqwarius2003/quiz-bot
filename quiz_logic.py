import os
import re
import random
import logging

logger = logging.getLogger(__name__)

# Глобальные переменные для хранения вопросов и использованных вопросов
QUESTIONS = {}  # Словарь вопросов и ответов
used_questions = set()  # Множество использованных вопросов


def get_random_txt_file(folder):
    """Выбирает случайный .txt файл из папки."""
    txt_files = [f for f in os.listdir(folder) if f.endswith('.txt')]
    if not txt_files:
        raise FileNotFoundError("Нет текстовых файлов в папке.")
    random_files = random.choice(txt_files)
    logger.info(f'Случайно выбран файл с фопросами: {random_files}')
    return os.path.join(folder, random_files)


def preparing_questions(filename) -> dict:
    """Читает вопросы и ответы из указанного текстового файла и возвращает их в виде словаря."""
    with open(filename, "r", encoding='KOI8-R') as file:
        content = file.read()

    question_pattern = r"(Вопрос\s\d+:.*?)(?=Ответ:)"
    answer_pattern = r"(Ответ:.*?)(?=\n\n|$)"

    questions = [q.group(0).replace("\n", " ").strip() for q in re.finditer(question_pattern, content, re.DOTALL)]
    answers = [a.group(0).replace("\n", " ").strip() for a in re.finditer(answer_pattern, content, re.DOTALL)]

    if not questions or not answers:
        raise ValueError("Не удалось извлечь вопросы или ответы из файла.")

    return dict(zip(questions, answers))


def load_new_qa_file():
    """Загружает новый файл с вопросами и обновляет глобальный словарь QUESTIONS."""
    global QUESTIONS, used_questions

    # Получаем случайный файл
    file_with_qa = get_random_txt_file(os.path.join(os.path.dirname(__file__), 'QA_FOLDER'))

    # Загружаем вопросы из этого файла
    QUESTIONS = preparing_questions(file_with_qa)

    # Очищаем множество использованных вопросов
    used_questions.clear()

    logger.info(f"Загружено вопросов: {len(QUESTIONS)}")


def get_random_question():
    """Возвращает случайный вопрос, который еще не задавался."""
    global QUESTIONS, used_questions

    if not QUESTIONS:
        logger.warning("QUESTIONS пуст! Загружаем новый файл с вопросами...")
        load_new_qa_file()

    available_questions = list(set(QUESTIONS.keys()) - used_questions)
    logger.info(f'осталось в файле {len(available_questions)}')

    if not available_questions:
        logger.info("Все вопросы использованы. Загружаю новый файл...")
        load_new_qa_file()
        available_questions = list(set(QUESTIONS.keys()) - used_questions)

    question = random.choice(available_questions)
    used_questions.add(question)
    return question, QUESTIONS[question]
