import vosk
from vosk import Model, KaldiRecognizer, SetLogLevel
import pyaudio
import json
import sys
import asyncio
import os

# Настройка логирования
# logging.basicConfig(filename='assistant.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')

SetLogLevel(-1)

class Microfon:
    def __init__(self, model_path="model_small", samplerate=16000, chunk=1024):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель Vosk не найдена: {model_path}")
        self.model = vosk.Model(model_path)
        self.samplerate = samplerate
        self.chunk = chunk
        self.recognizer = KaldiRecognizer(self.model, self.samplerate)
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None

    async def va_listen(self, callback):
        try:
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.samplerate,
                input=True,
                frames_per_buffer=self.chunk
            )
            print("Микрофон активен, говорите...")
            # logging.debug("Микрофон инициализирован")

            while True:
                try:
                    data = await asyncio.to_thread(self.stream.read, self.chunk, exception_on_overflow=False)
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())["text"]
                        if result:
                            await callback(result)
                except Exception as e:
                    # print(f"Ошибка микрофона: {e}", file=sys.stderr)
                    # logging.error(f"Ошибка микрофона: {e}")
                    await asyncio.sleep(1)  # Задержка перед повторной попыткой
        except Exception as e:
            print(f"Ошибка инициализации микрофона: {e}", file=sys.stderr)
            # logging.error(f"Ошибка инициализации микрофона: {e}")
            raise
        finally:
            self._cleanup()

    def _cleanup(self):
        # logging.debug("Очистка ресурсов микрофона")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio.terminate()
