from openai import OpenAI

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

def classify_transaction_groq(text):
    prompt = f"""
Tugas kamu adalah mengklasifikasikan transaksi berikut ke salah satu dari 4 kategori:
- Kewajiban
- Kebutuhan
- Tujuan
- Keinginan

Jawaban hanya satu kata saja.

Transaksi: "{text}"
Jawaban:
"""
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip().capitalize()
        if result in ['Kewajiban', 'Kebutuhan', 'Tujuan', 'Keinginan']:
            return result
        else:
            return "Tidak Terkategori"
    except Exception as e:
        print("❌ ERROR Groq:", e)
        return "Tidak Terkategori"
