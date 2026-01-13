import requests
import os
from fastapi import UploadFile

class TelegramUploader:
    def __init__(self):
        self.api_url = os.getenv("TG_IMG_API")

    async def upload_image(self, file: UploadFile):
        try:
            file_content = await file.read()
            
            # 构造 form-data
            # 注意：字段名通常是 'file'
            files = {
                'file': (file.filename, file_content, file.content_type)
            }
            
            # 发送请求
            response = requests.post(self.api_url, files=files, timeout=30)
            res_data = response.json()
            
            # 调试用：如果上传失败，可以打印 res_data 看看报错
            if response.status_code != 200:
                print(f"上传接口返回错误: {res_data}")
                return None

            # 兼容处理：根据 API 文档，通常返回在 data.url 或直接在 url 字段
            # 如果是该方案常见的返回格式：
            if isinstance(res_data, list) and len(res_data) > 0:
                return res_data[0].get("src") # 批量上传模式
            
            return res_data.get("data", {}).get("url") or res_data.get("url")
            
        except Exception as e:
            print(f"图床对接异常: {e}")
            return None
