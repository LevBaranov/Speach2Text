import speech_recognition as sr
import subprocess
import os
import logging
# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()


class Converter:

    def __init__(self, path_to_file: str, language: str = "ru-RU"):
        self.language = language
        subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path_to_file, path_to_file.replace(".ogg", ".wav")])
        self.wav_file = path_to_file.replace(".ogg", ".wav")

    def audio_to_text(self) -> str:
        r = sr.Recognizer()

        with sr.AudioFile(self.wav_file) as source:
            audio = r.record(source)
            r.adjust_for_ambient_noise(source)

        try:
            return r.recognize_google(audio, language=self.language, key=os.getenv("API_KEY"))
        except sr.UnknownValueError:
            logger.info("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            logger.info(f"Could not request results from Google Speech Recognition service; {e}")

    def __del__(self):
        os.remove(self.wav_file)
