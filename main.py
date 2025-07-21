import speech_recognition as sr
import os
from datetime import datetime
from vosk import Model, KaldiRecognizer
import wave
import io
import json
import re
import glob
import micro

class Recognizer:
    def __init__(self, model_path=os.path.join(os.path.dirname(__file__), "vosk-model-small-ru-0.22")):
        self.recognizer = sr.Recognizer()
        # Инициализация Vosk
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель Vosk не найдена по пути: {model_path}")
        self.vosk_model = Model(model_path)
        self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)  # Частота дискретизации 16 кГц

    def recognize_speech(self, audio):
        """Оффлайн-распознавание речи с помощью Vosk."""
        if audio is None:
            return None

        try:
            # Конвертация аудио из speech_recognition в WAV
            audio_data = audio.get_wav_data(convert_rate=16000, convert_width=2)  # 16 кГц, 16 бит
            # Создаем временный WAV-файл в памяти
            wav_io = io.BytesIO(audio_data)
            with wave.open(wav_io, 'rb') as wav_file:
                # Проверка параметров аудио
                if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2 or wav_file.getframerate() != 16000:
                    print("Неподходящий формат аудио для Vosk.")
                    return None
                
                # Чтение аудиоданных
                while True:
                    data = wav_file.readframes(4000)
                    if len(data) == 0:
                        break
                    self.vosk_recognizer.AcceptWaveform(data)

                # Получение результата
                result = self.vosk_recognizer.FinalResult()
                result_dict = json.loads(result)
                text = result_dict.get("text", "")
                
                if text:
                    print(f"Распознанный текст: {text}")
                    return text
                else:
                    print("Не удалось распознать речь.")
                    return None

        except Exception as e:
            print(f"Ошибка распознавания: {e}")
            return None

def process_command(text):
    """Обработка голосовых команд."""
    if text is None:
        return False

    text = text.lower()

    # Команда для создания заметки с определенным названием
    if "создай заметку с названием" in text:
        # Извлекаем название и текст заметки
        match = re.match(r"создай заметку с названием\s+([^\s]+)\s*(.*)", text)
        if match:
            note_title, note_text = match.groups()
            # Очищаем название от недопустимых символов для имени файла
            note_title = re.sub(r'[<>:"/\\|?*]', '', note_title).strip()
            if not note_title:
                note_title = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            note_filename = os.path.join(os.path.dirname(__file__), f"{note_title}.txt")

            # Создаем файл (даже если текст пустой)
            with open(note_filename, "a", encoding="utf-8") as f:
                if note_text.strip():
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {note_text}\n")
                    print(f"Заметка сохранена в файл '{note_filename}': {note_text}")
                else:
                    print(f"Файл '{note_filename}' создан, но текст заметки пуст.")
        else:
            print("Не удалось распознать название заметки.")
    
    # Команда для записи заметки в указанный файл
    elif "запиши заметку в файл" in text:
        # Извлекаем название файла и текст заметки
        match = re.match(r"запиши заметку в файл\s+([^\s]+)\s*(.*)", text)
        if match:
            note_title, note_text = match.groups()
            # Очищаем название от недопустимых символов
            note_title = re.sub(r'[<>:"/\\|?*]', '', note_title).strip()
            if not note_title:
                print("Не указано название файла для заметки.")
                return False
            note_filename = os.path.join(os.path.dirname(__file__), f"{note_title}.txt")

            if note_text.strip():
                with open(note_filename, "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {note_text}\n")
                print(f"Заметка сохранена в файл '{note_filename}': {note_text}")
            else:
                print("Текст заметки пуст.")
        else:
            print("Не указано название файла для заметки.")
    
    # Команда для чтения заметок
    elif "покажи заметки" in text:
        # Проверяем, указано ли название файла
        match = re.match(r"покажи заметки из файла\s+([^\s]+)", text)
        if match:
            note_title = match.group(1)
            # Очищаем название от недопустимых символов
            note_title = re.sub(r'[<>:"/\\|?*]', '', note_title).strip()
            note_filename = os.path.join(os.path.dirname(__file__), f"{note_title}.txt")
            
            if os.path.exists(note_filename):
                with open(note_filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content:
                        print(f"Содержимое файла '{note_filename}':\n{content}")
                    else:
                        print(f"Файл '{note_filename}' пуст.")
            else:
                print(f"Файл '{note_filename}' не найден.")
        else:
            # Если название не указано, ищем последний измененный файл .txt
            notes_dir = os.path.dirname(__file__)
            txt_files = glob.glob(os.path.join(notes_dir, "*.txt"))
            
            if not txt_files:
                print("В директории нет файлов заметок (.txt).")
                return False
            
            # Находим файл с самой поздней датой изменения
            latest_file = max(txt_files, key=os.path.getmtime)
            
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    print(f"Содержимое последнего измененного файла '{latest_file}':\n{content}")
                else:
                    print(f"Последний измененный файл '{latest_file}' пуст.")
    
    # Команда для завершения
    elif "стоп" in text:
        print("Программа завершена.")
        return True
    
    return False

def main():
    # Для отладки: вывести текущую рабочую директорию и путь к модели
    print("Текущая рабочая директория:", os.getcwd())
    print("Путь к модели:", os.path.join(os.path.dirname(__file__), "vosk-model-small-ru-0.22"))

    mic = Microfon()
    recognizer = Recognizer()
    
    print("Голосовой помощник запущен. Доступные команды:")
    print("- 'Создай заметку с названием [название] [текст]' - для создания файла (может быть пустым)")
    print("- 'Запиши заметку в файл [название] [текст]' - для записи в указанный файл")
    print("- 'Покажи заметки' - для отображения последней измененной заметки")
    print("- 'Покажи заметки из файла [название]' - для отображения заметок из указанного файла")
    print("- 'Стоп' - для завершения программы")
    
    while True:
        audio = mic.capture_audio()
        text = recognizer.recognize_speech(audio)
        stop = process_command(text)
        if stop:
            break

if __name__ == "__main__":
    main()