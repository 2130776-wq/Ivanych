import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Инициализация клиента через переменную окружения
# На Render добавь переменную OPENAI_API_KEY в Settings → Environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Загружаем прайс (лежит в корне репо рядом с app.py)
with open("price.json", "r", encoding="utf-8") as f:
    price_data = json.load(f)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"reply": "Пустой запрос."})

    # Поиск точного артикула
    match = next((row for row in price_data if str(row.get("Артикул")).strip() == user_message), None)

    if match:
        reply_text = (
            f"Наименование: {match.get('Наименование')}\n"
            f"Артикул: {match.get('Артикул')}"
        )
        return jsonify({"reply": reply_text})

    # Если не нашли — спросим модель (ограничиваем тему смазочным оборудованием)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",   # новый быстрый и дешевый
            messages=[
                {
                    "role": "system",
                    "content": "Ты вежливый технический консультант по смазочному оборудованию. Отвечай по сути, кратко и по теме."
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
        )
        reply_text = completion.choices[0].message.content.strip()
    except Exception as e:
        reply_text = f"Ошибка при обращении к модели: {e}"

    return jsonify({"reply": reply_text})

if __name__ == "__main__":
    # Render запускает как 'python app.py', так что это ок
    app.run(host="0.0.0.0", port=5000)
