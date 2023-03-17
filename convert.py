import os
import logging
import requests
from time import sleep

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()


class Converter:

    def __init__(self):
        self.url_converter = os.getenv("CONVERTER_URL")
        self.auth_token = os.getenv("CONVERTER_TOKEN")

    def audio_to_text(self, file_name: str) -> str | None:
        url = f"{self.url_converter}/transcription"

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        r = requests.post(url, headers=headers, files={'file': open(file_name, 'rb')})
        if r.status_code == 200:
            resp_json = r.json()
            logger.info(f"Response: {r.status_code} {r.text}")
            return resp_json["response_text"]
        elif r.status_code == 500:
            logger.info(f"Response: {r.status_code} {r.text}")
            sleep(2)
            self.audio_to_text(file_name)
        else:
            return None


