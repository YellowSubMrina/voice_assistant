import asyncio
import config
import re
import datetime
import threading
import os
import sys
import random
import pygame

from micro import Microfon
from rapidfuzz import fuzz

print(f"{config.VA_NAME} начал свою работу ...")

mc = Microfon(model_path="vosk-model-small-ru-0.22")

# Инициализация pygame микшера
pygame.mixer.init()

def filter_cmd(raw_voice: str):
    cmd = raw_voice.lower()
    pattern = r'\b(' + '|'.join(config.VA_ALIAS + config.VA_TBR) + r')\b'
    cmd = re.sub(pattern, '', cmd).strip()
    return cmd

def recognize_cmd(cmd: str):
    rc = {'cmd': '', 'percent': 0}
    for c, v in config.VA_CMD_LIST.items():
        for x in v:
            vrt = fuzz.ratio(cmd, x)
            if vrt > rc['percent'] and vrt > 70:
                rc['cmd'] = c
                rc['percent'] = vrt
    return rc

def find_music_files():
    """Ищет все .wav и .mp3 файлы в директории скрипта"""
    current_dir = os.path.dirname(__file__)
    music_files = [
        os.path.join(current_dir, file)
        for file in os.listdir(current_dir)
        if file.lower().endswith((".mp3", ".wav"))
    ]
    return music_files

def play_music_in_background(file_path):
    """Проигрывает музыку в фоновом потоке"""
    def _play():
        try:
            print(f"Воспроизвожу: {os.path.basename(file_path)}")
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Ошибка воспроизведения: {e}", file=sys.stderr)

    threading.Thread(target=_play).start()

def execute_cmd(cmd: str, microfon: Microfon):
    def run_cmd():
        if cmd == 'help':
            print("Доступные команды:")
            print("- 'время' — узнать текущее время")
            print("- 'проиграй песню' — воспроизведение музыки")
            print("- 'пауза' — поставить музыку на паузу или продолжить")
            print("- 'сделай заметку' — добавить заметку в файл")
            print("- 'напомни' — показать последнюю заметку")
            print("- 'стоп' — завершить работу")

        elif cmd == 'ctime':
            now = datetime.datetime.now()
            print(f"Сейчас {now.strftime('%H:%M:%S')}")

        elif cmd == 'play_music':
            music_files = find_music_files()
            if music_files:
                file_to_play = random.choice(music_files)
                play_music_in_background(file_to_play)
            else:
                print("Файлы музыки не найдены (.mp3 или .wav)")

        elif cmd == 'pause_music':
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                print("Музыка поставлена на паузу.")
            else:
                pygame.mixer.music.unpause()
                print("Музыка продолжена.")

        elif cmd == 'note_add':
            note_text = input("Что записать? ")
            notes_path = os.path.join(os.path.dirname(__file__), "notes.txt")
            try:
                with open(notes_path, "a", encoding="utf-8") as f:
                    f.write(note_text.strip() + "\n")
                print("Заметка добавлена.")
            except Exception as e:
                print(f"Ошибка при записи заметки: {e}", file=sys.stderr)

        elif cmd == 'note_last':
            notes_path = os.path.join(os.path.dirname(__file__), "notes.txt")
            try:
                if os.path.exists(notes_path):
                    with open(notes_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            print("Последняя заметка:")
                            print(lines[-1].strip())
                        else:
                            print("Заметок пока нет.")
                else:
                    print("Файл заметок не найден.")
            except Exception as e:
                print(f"Ошибка при чтении заметки: {e}", file=sys.stderr)

        elif cmd == 'stop':
            print("Завершаю работу...")
            pygame.mixer.music.stop()
            microfon._cleanup()
            os._exit(0)

    threading.Thread(target=run_cmd).start()

async def va_respond(voice: str):
    print(f"Распознано: {voice}")
    if any(alias in voice.lower() for alias in config.VA_ALIAS):
        cmd = recognize_cmd(filter_cmd(voice))
        if cmd['cmd'] in config.VA_CMD_LIST:
            print(f"Команда: {cmd['cmd']} ({cmd['percent']}%)")
            execute_cmd(cmd['cmd'], mc)

async def main():
    try:
        await mc.va_listen(va_respond)
    except Exception as e:
        print(f"Ошибка в главном цикле: {e}", file=sys.stderr)
        mc._cleanup()

if __name__ == "__main__":
    asyncio.run(main())
