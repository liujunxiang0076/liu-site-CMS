from fastapi import File, UploadFile
from core.image_uploader import TelegramUploader

uploader = TelegramUploader()

@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    img_url = await uploader.upload_image(file)
    if img_url:
        # Vditor 要求返回固定的 JSON 格式才能正确插入图片
        return {
            "msg": "Success",
            "code": 0,
            "data": {
                "errFiles": [],
                "succMap": {
                    file.filename: img_url
                }
            }
        }
    return {"msg": "Upload failed", "code": 1}
