# app.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# === настройки ===
DATA_FILE = os.getenv("DATA_FILE", "1.json")  # поменяй на "price.json", если нужно
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def _norm(s: str) -> str:
    # нормализуем артикулы: убираем пробелы, дефисы и приводим к верхнему регистру
    return "".join(ch for ch in str(s).upper() if ch.isalnum())

# загрузка прайса
with open(DATA_FILE, "r", encoding="utf-8") as f:
    price_data = json.load(f)

# быстрый индекс по артикулам
index = {}
for row in price_data:
    art = row.get("Артикул")
    if art:
        index[_norm(art)] = row

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        payload = request.get_json(force=True) or {}
        user_text = (payload.get("message") or "").strip()

        if not user_text:
            return jsonify({"reply": "Пустой запрос."}), 200

        # 1) точное совпадение
        key = _norm(user_text)
        item = index.get(key)

        # 2) если точного нет — поиск подстрокой по артикулам
        if not item:
            for row in price_data:
                if key and key in _norm(row.get("Артикул", "")):
                    item = row
                    break

        if item:
            name = (row if not item else item).get("Наименование", "").strip()
            art = (row if not item else item).get("Артикул", "").strip()
            return jsonify({"reply": f"Наименование: {name}\nАртикул: {art}"}), 200

        # 3) GPT-ответ (кратко по теме)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # можно заменить на gpt-3.5-turbo, если нужно
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты технический консультант по смазочному оборудованию. "
                        "Отвечай кратко и по делу. Если вопрос не по теме — вежливо сообщи, "
                        "что консультируешь только по смазочному оборудованию."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
        )
        reply = completion.choices[0].message.content.strip()
        return jsonify({"reply": reply}), 200

    except Exception as e:
        print("ERROR /chat:", repr(e))
        return jsonify({"reply": "Ошибка на сервере. Попробуйте ещё раз."}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
