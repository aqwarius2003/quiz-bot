import os
import zipfile
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)


def download_archive(url, save_path):
    """Загружает ZIP-архив по указанному URL и сохраняет его на диск."""
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=10) as response:
        if response.status != 200:
            raise URLError(f"HTTP Error {response.status}")

        with open(save_path, 'wb') as f:
            f.write(response.read())


def unzip_archive(zip_file_path, output_folder):
    """Распаковывает ZIP-архив в указанную папку."""
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(output_folder)


def main():
    url_archive = 'https://dvmn.org/media/modules_dist/quiz-questions.zip'
    current_directory = os.path.dirname(os.path.abspath(__file__))
    zip_file_path = os.path.join(current_directory, 'data', 'quiz-questions.zip')
    output_folder = os.path.join(current_directory, 'data', 'QA_FOLDER')

    try:
        os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        logging.info("Начало загрузки архива...")
        download_archive(url_archive, zip_file_path)

        logger.info("Начало распаковки архива...")
        unzip_archive(zip_file_path, output_folder)

        logger.info("Архив {zip_file_path} успешно распакован в {output_folder}")

    except Exception as e:
        logger.error(f"Ошибка при скачивании или распаковке архива: {type(e).__name__} - {str(e)}")
    finally:
        logger.info(f'Архив {zip_file_path} успешно распакован в {output_folder}')

        logger.exception(f"Ошибка выполнения: {type(e).__name__} - {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.DEBUG)
    main()
