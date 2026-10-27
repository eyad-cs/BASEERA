from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse
import requests
import base64
import uvicorn

app = FastAPI()

API_URL = "https://baseerah.duckdns.org/webhook/parts-search"
API_KEY = 'X9p#vL2$mPq7!kR4'
CHAT_API_URL = "https://dilute-uncheck-eastward.ngrok-free.dev/extract"
ANALYSIS_API_URL = "http://84.13.140.2:8001/upload-damage"

cars = {
    "Toyota": {"Camry": "كامري", "Corolla": "كورولا", "Yaris": "يارس"},
    "Hyundai": {"Elantra": "إلنترا", "Sonata": "سوناتا", "Accent": "أكسنت"},
    "Kia": {"Pegas": "بيجاس", "Sportage": "سبورتاج", "K5": "كي 5"},
    "Nissan": {"Sunny": "صني", "Patrol": "باترول", "X-Trail": "إكس تريل"},
    "Ford": {"Taurus": "توروس", "Territory": "تيريتوري", "Explorer": "إكسبلورر"},
    "GMC": {"Yukon": "يوكن", "Sierra": "سييرا", "Acadia": "أكاديا"}
}

# نرسل JSON ونستقبل JSON، ونوضح سبب تعذّر الطلب.
def send(url, data, headers=None):
    try:
        response = requests.post(url, json=data, headers=headers, timeout=90)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return {"error": "انتهت مهلة انتظار الخدمة. انتظر قليلًا ثم جرّب مرة ثانية."}
    except requests.HTTPError as error:
        return {"error": f"الخدمة أعادت خطأ HTTP {error.response.status_code}. تحقق من رابط الخدمة وسجلّها."}
    except ValueError:
        return {"error": "الخدمة أرسلت ردًا غير صالح بدل JSON."}
    except requests.RequestException:
        return {"error": "تعذّر الاتصال بالخدمة. جرّب مرة ثانية."}

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/models")
def models(make: str = ""):
    return cars.get(make, {})

# إرسال الصورة إلى نموذج الضرر، ثم عرض رده.
@app.post("/analyze")
def analyze(image: UploadFile = File()):
    photo = image.file.read(5 * 1024 * 1024 + 1)
    if not photo or len(photo) > 5 * 1024 * 1024:
        return {"error": "اختر صورة بحجم لا يتجاوز 5 MB."}
    encoded = base64.b64encode(photo).decode("utf-8")
    data = {"image": f"data:{image.content_type};base64,{encoded}"}
    return send(ANALYSIS_API_URL, data)

# كل طلب يبحث عن قطعة واحدة. الصفحة ترسل القطع المحددة بالترتيب.
@app.post("/search")
def search(make: str = Form(), model: str = Form(), year: int = Form(),
           vin: str = Form(""), partName: str = Form(), partType: str = Form("any")):
    data = {"make": make, "model": model, "year": year, "vin": vin,
            "partName": partName, "partType": partType}
    return send(API_URL, data, {"x-api-key": API_KEY})

# نظهر رسالة المستخدم أولًا، ثم نرسل المحادثة ونعرض رد الخدمة.
@app.post("/chat")
def chat(history: list[str] = Form()):
    message = "هذه المحادثة بالترتيب. أكمل معلومات السيارة والقطع من الرسائل السابقة، واعتمد أحدث تصحيح للمستخدم. أجب عن آخر رسالة فقط.\n\n" + "\n".join(history)
    answer = send(CHAT_API_URL, {"message": message})
    result = answer.get("result_from_backend") or {}
    reply = answer.get("reply") or answer.get("message") or result.get("message")
    error = answer.get("error")
    if answer.get("status") == "error" or reply == "Error in workflow":
        error = "تعذّر إكمال الطلب من خدمة الشات. جرّب مرة ثانية."
    notice = ""
    if not result.get("items") and (result or answer.get("status") == "success"):
        notice = result.get("message") or "لم تصل منتجات لهذا الطلب من خدمة البحث."
        reply = notice
    if not reply and not result.get("items"):
        error = error or "لم ترسل خدمة الشات ردًا."
    reply = error or reply or "لقيت لك قطعًا. تقدر تشوفها أسفل التحليل."
    return {"reply": reply, "result": result, "error": error, "notice": notice}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
