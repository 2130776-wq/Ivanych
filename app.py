import json
from flask import Flask, request, jsonify
from openai import OpenAI

client = OpenAI(api_key="sk-proj-...")  # подставь свой ключ

# Загрузка price.json
with open("price.json", "r", encoding="utf-8") as f:
    price_data = json.load(f)

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    
    # Поиск по JSON
    match = next((item for item in price_data if item["Артикул"] == user_message), None)
    
    if match:
        reply_text = match["Наименование"]
    else:
        # Если не найдено — спросим у GPT
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты технический консультант по смазочному оборудованию."},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = completion.choices[0].message.content

    return jsonify({"reply": reply_text})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
