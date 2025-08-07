from flask import Flask, request, jsonify
import openai
import json

app = Flask(__name__)

openai.api_key = "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"

# Загружаем товары из price.json
with open("price.json", "r", encoding="utf-8") as f:
    products = json.load(f)

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Пустой запрос."})

    matches = [item for item in products if user_input in item["code"]]

    if matches:
        context = "\n".join(f'{m["code"]}: {m["name"]}' for m in matches)
    else:
        context = "Совпадений не найдено в базе артикулов."

    prompt = f"""Ты — консультант Иваныч, специалист по смазочному оборудованию.
Вот данные из прайса:

{context}

Запрос клиента: {user_input}
Ответ: """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты технический консультант по смазке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Ошибка: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)