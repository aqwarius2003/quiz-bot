import os
import zipfile
import logging

logging.basicConfig(level=logging.INFO)

def unzip_archive(zip_file_path, output_folder):
    """Распаковывает ZIP-архив в указанную папку."""
    os.makedirs(output_folder, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(output_folder)
    logging.info(f'Архив {zip_file_path} распакован в {output_folder}')

def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    zip_file_path = os.path.join(current_directory, 'data', 'quiz-questions.zip')
    output_folder = os.path.join(current_directory, 'data', 'QA_FOLDER')

    try:
        unzip_archive(zip_file_path, output_folder)
    except FileNotFoundError:
        logging.error(f'Файл {zip_file_path} не найден.')
    except zipfile.BadZipFile:
        logging.error('Ошибка: Неверный ZIP-архив.')
    except Exception as e:
        logging.error(f'Произошла ошибка: {e}')

if __name__ == "__main__":
    main()
