from flask import Flask, request, jsonify
import openai
import pandas as pd

app = Flask(__name__)

# ✅ Загружаем Excel-файл
try:
    df = pd.read_excel("price.xlsx")
except FileNotFoundError:
    df = None
    print("⚠️ Файл price.xlsx не найден на сервере!")

# ✅ API-ключ (вставлен твой)
openai.api_key = "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"

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Пустой запрос."})

    if df is None:
        return jsonify({"reply": "Файл прайса не загружен. Обратитесь к администратору."})

    # Поиск подходящих строк
    matches = df[df.apply(lambda row: row.astype(str).str.contains(user_input, case=False).any(), axis=1)]

    if not matches.empty:
        context = "\n".join(matches.astype(str).agg(" | ".join, axis=1).tolist()[:3])
    else:
        context = "Нет совпадений в прайсе. Уточните запрос."

    prompt = f"""Ты — консультант Иваныч, специалист по смазочному оборудованию.
Ответь на запрос клиента на основе прайса:

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
        return jsonify({"reply": f"Ошибка при обращении к OpenAI: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)