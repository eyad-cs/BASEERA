import base64
import requests
import uvicorn
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse

app = FastAPI()

API_URL = "https://baseerah.duckdns.org/webhook/parts-search"
API_KEY = 'X9p#vL2$mPq7!kR4'
CHAT_API_URL = "https://dilute-uncheck-eastward.ngrok-free.dev/extract"
ANALYSIS_API_URL = "https://yolo-api.duckdns.org/analyze-damage"

cars = {
    "Toyota": {"Camry": "كامري", "Corolla": "كورولا", "Yaris": "يارس"},
    "Hyundai": {"Elantra": "إلنترا", "Sonata": "سوناتا", "Accent": "أكسنت"},
    "Kia": {"Pegas": "بيجاس", "Sportage": "سبورتاج", "K5": "كي 5"},
    "Nissan": {"Sunny": "صني", "Patrol": "باترول", "X-Trail": "إكس تريل"},
    "Ford": {"Taurus": "توروس", "Territory": "تيريتوري", "Explorer": "إكسبلورر"},
    "GMC": {"Yukon": "يوكن", "Sierra": "سييرا", "Acadia": "أكاديا"}
}

# جميع الخدمات تستقبل JSON وتعيد JSON.
def send(url, data, headers=None):
    try:
        response = requests.post(url, json=data, headers=headers, timeout=90)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {"error": "تعذّر الاتصال بالخدمة. جرّب مرة ثانية."}

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/models")
def models(make: str = ""):
    return cars.get(make, {})

@app.post("/analyze")
def analyze(image: UploadFile = File()):
    limit = 5 * 1024 * 1024
    photo = image.file.read(limit + 1)
    if not photo or len(photo) > limit:
        return {"error": "اختر صورة بحجم لا يتجاوز 5 MB."}
    data = {"image": base64.b64encode(photo).decode("utf-8")}
    return send(ANALYSIS_API_URL, data)

@app.post("/search")
def search(make: str = Form(), model: str = Form(), year: int = Form(),
           vin: str = Form(""), partName: str = Form(), partType: str = Form("any")):
    data = {"make": make, "model": model, "year": year, "vin": vin,
            "partName": partName, "partType": partType}
    return send(API_URL, data, {"x-api-key": API_KEY})

@app.post("/chat")
def chat(history: list[str] = Form()):
    message = "هذه المحادثة بالترتيب. أكمل معلومات السيارة والقطع من الرسائل السابقة، واعتمد أحدث تصحيح للمستخدم. أجب عن آخر رسالة فقط.\n\n"
    message += "\n".join(history)
    answer = send(CHAT_API_URL, {"message": message})
    result = answer.get("result_from_backend") or {}
    items = result.get("items")
    reply = answer.get("reply") or answer.get("message") or result.get("message")
    error = answer.get("error")
    if answer.get("status") == "error" or reply == "Error in workflow":
        error = "تعذّر إكمال الطلب من خدمة الشات. جرّب مرة ثانية."
    notice = ""
    if not items and (result or answer.get("status") == "success"):
        notice = result.get("message") or "لم تصل منتجات لهذا الطلب من خدمة البحث."
        reply = notice
    if not reply and not items:
        error = error or "لم ترسل خدمة الشات ردًا."
    reply = error or reply or "لقيت لك قطعًا. تقدر تشوفها أسفل التحليل."
    return {"reply": reply, "result": result, "error": error, "notice": notice}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
