import openai

openai.api_key = "sk-xxxx"
openai.api_base = "https://api.groq.com/openai/v1"

prompt = "Klasifikasikan transaksi ini: 'Cicilan Motor'\nJawaban:"
response = openai.ChatCompletion.create(
    model="mixtral-8x7b-32768",
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    max_tokens=10
)
print(response.choices[0].message.content)
