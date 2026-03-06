import requests
import os
import logging
from fastapi import UploadFile

logger = logging.getLogger("CMS-ImageUploader")

class TelegramUploader:
    def __init__(self):
        self.api_url = os.getenv("TG_IMG_API")

    async def upload_image(self, file: UploadFile):
        try:
            file_content = await file.read()
            files = {
                'file': (file.filename, file_content, file.content_type)
            }
            response = requests.post(self.api_url, files=files, timeout=30)
            res_data = response.json()

            if response.status_code != 200:
                logger.error(f"上传接口返回错误 [{response.status_code}]: {res_data}")
                return None

            if isinstance(res_data, list) and len(res_data) > 0:
                return res_data[0].get("src")

            return res_data.get("data", {}).get("url") or res_data.get("url")

        except Exception as e:
            logger.error(f"图床对接异常: {e}", exc_info=True)
            return None
