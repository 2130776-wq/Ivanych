# app.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# === Настройки ===
# Если у тебя файл называется 1.json — оставь так.
DATA_FILE = os.getenv("DATA_FILE", "1.json")  # или поменяй на "price.json"

# Ключ храним в переменной окружения OPENAI_API_KEY на Render
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Загрузка прайса ===
def _norm(s: str) -> str:
    # нормализуем артикулы: убираем пробелы и дефисы, приводим к верхнему регистру
    return "".join(ch for ch in s.upper() if ch.isalnum())

with open(DATA_FILE, "r", encoding="utf-8") as f:
    price_data = json.load(f)

# построим быстрый индекс по артикулам
index = {}
for item in price_data:
    art = item.get("Артикул", "")
    if art:
        index[_norm(art)] = item

# === Flask ===
app = Flask(__name__)
# Разрешаем CORS для /chat (можно оставить "*" или ограничить доменом)
CORS(app, resources={r"/chat": {"origins": "*"}})

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        payload = request.get_json(force=True) or {}
        user_message = (payload.get("message") or "").strip()

        if not user_message:
            return jsonify({"reply": "Пустой запрос."}), 200

        # 1) пробуем точное совпадение по артикулу
        key = _norm(user_message)
        item = index.get(key)

        # 2) если точного нет — поищем подстрокой по всем артикулам
        if not item:
            for row in price_data:
                art = _norm(str(row.get("Артикул", "")))
                if key and key in art:
                    item = row
                    break

        if item:
            name = str(item.get("Наименование", "")).strip()
            art = str(item.get("Артикул", "")).strip()
            reply_text = f"Наименование: {name}\nАртикул: {art}"
            return jsonify({"reply": reply_text}), 200

        # 3) если в прайсе нет — спрашиваем модель (дешёвая и быстрая)
        # при необходимости поменяй на gpt-4o
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты технический консультант по смазочному оборудованию. "
                        "Отвечай кратко и по делу. Если вопрос не про тему, вежливо скажи, что "
                        "отвечаешь только по смазочному оборудованию."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
        )
        reply_text = completion.choices[0].message.content.strip()
        return jsonify({"reply": reply_text}), 200

    except Exception as e:
        # чтобы в логи всё попадало
        print("ERROR /chat:", repr(e))
        return jsonify({"reply": "Ошибка на сервере. Попробуйте ещё раз."}), 200


if __name__ == "__main__":
    # на Render host/port управляются процессом, но так локально удобнее
    app.run(host="0.0.0.0", port=5000, debug=False)
