import requests
import os
from fastapi import UploadFile

class TelegramUploader:
    def __init__(self):
        # 这里的 URL 换成你自己的 TG 图床 API 地址
        self.api_url = os.getenv("TG_IMG_API")

    async def upload_image(self, file: UploadFile):
        """将前端传来的文件转发给 TG 图床 API"""
        try:
            # 读取文件内容
            file_content = await file.read()
            
            # 构造发送给 TG 接口的数据
            files = {
                'file': (file.filename, file_content, file.content_type)
            }
            
            # 调用你的第三方图床接口
            response = requests.post(self.api_url, files=files)
            res_data = response.json()
            
            # 假设你的接口返回格式是 {"src": "https://..."} 
            # 请根据你实际的 API 返回结构修改下面这行
            return res_data.get("src") or res_data.get("url")
        except Exception as e:
            print(f"上传失败: {e}")
            return None
