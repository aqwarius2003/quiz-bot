import logging
import os
import re
import zipfile
import random

logger = logging.getLogger(__name__)


def unzip_archive(zip_file_path, output_folder):
    """Распаковывает ZIP-архив в указанную папку."""
    # Создаем папку, если она не существует
    os.makedirs(output_folder, exist_ok=True)

    # Распаковываем ZIP-архив
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(output_folder)


def preparing_questions(filename, code='KOI8-R') -> dict:
    """Читает вопросы и ответы из указанного текстового файла и возвращает их в виде словаря."""
    with open(filename, "r", encoding=code) as file:
        questions_and_answers = file.read()

    # Регулярные выражения для поиска вопросов и ответов
    question_pattern = r"(Вопрос\s\d+:.*?)(?=Ответ:)"
    answer_pattern = r"(Ответ:.*?)(?=\n\n|$)"

    # Используем finditer для более эффективного извлечения
    questions = [match.group(0).replace("\n", " ").strip() for match in
                 re.finditer(question_pattern, questions_and_answers, re.DOTALL)]
    answers = [match.group(0).replace("\n", " ").strip() for match in
               re.finditer(answer_pattern, questions_and_answers, re.DOTALL)]

    # Создаем словарь вопросов и ответов
    qa_pairs = dict(zip(questions, answers))
    return qa_pairs


def main():
    # Получаем путь к текущему каталогу
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # Путь к ZIP-архиву
    zip_file_path = os.path.join(current_directory, 'quiz-questions.zip')
    # Папка, в которую вы хотите распаковать архив
    output_folder = 'QA_FOLDER'

    try:
        # Распаковываем ZIP-архив
        unzip_archive(zip_file_path, output_folder)
        print(f'Архив {zip_file_path} распакован в папку: {output_folder}')

        # Получаем список всех .txt файлов в распакованной папке
        txt_files = [f for f in os.listdir(output_folder) if f.endswith('.txt')]

        if not txt_files:
            print("В распакованной папке нет текстовых файлов.")
            return

        # Выбираем случайный .txt файл
        random_txt_file = random.choice(txt_files)
        random_txt_file_path = os.path.join(output_folder, random_txt_file)

        print(f"Выбран случайный файл: {random_txt_file}")

        # Обрабатываем выбранный файл
        qa_pairs = preparing_questions(random_txt_file_path)
        # Проверочный принт вопросов ответов
        print("Содержимое файла:")
        for question, answer in qa_pairs.items():
            print(f"{question}\n{answer}\n")

    except FileNotFoundError:
        print(f'Ошибка: Файл {zip_file_path} не найден.')
    except zipfile.BadZipFile:
        print('Ошибка: Неверный ZIP-архив.')
    except Exception as e:
        print(f'Произошла ошибка: {e}')



if __name__ == "__main__":
    main()
