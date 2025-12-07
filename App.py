import streamlit as st
import pandas as pd
import openai
import plotly.express as px
from jinja2 import Template
import os

# === SETUP API ===
openai.api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
openai.api_base = "https://api.groq.com/openai/v1"

def classify_transaction_groq(text):
    prompt = f"""
Tugas kamu adalah mengklasifikasikan transaksi berikut ke dalam salah satu dari 4 kategori:
- Kewajiban
- Kebutuhan
- Tujuan
- Keinginan

Berikan hanya 1 kata jawaban, tanpa penjelasan.

Transaksi: "{text}"
Kategori:
"""
    try:
        response = openai.ChatCompletion.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
        )
        kategori = response.choices[0].message.content.strip().capitalize()
        if kategori in ['Kewajiban', 'Kebutuhan', 'Tujuan', 'Keinginan']:
            return kategori
        else:
            return "Tidak Terkategori"
    except Exception as e:
        print("❌ Error Groq:", e)
        return "Tidak Terkategori"


# === ANALISA EXCEL ===
def analyze_transactions(df):
    df = df.rename(columns=str.lower)
    if 'jumlah' in df.columns:
        df['jumlah'] = df['jumlah'].astype(float)
    elif 'debit' in df.columns and 'kredit' in df.columns:
        df['jumlah'] = df['debit'].fillna(0) - df['kredit'].fillna(0)
    transaksi_col = 'transaksi' if 'transaksi' in df.columns else 'deskripsi'
    df['kategori'] = df[transaksi_col].apply(classify_transaction_groq)
    return df[[transaksi_col, 'jumlah', 'kategori']]

# === DONUT CHART ===
def generate_donut_chart(df):
    summary = df.groupby('kategori')['jumlah'].sum().abs().reset_index()
    fig = px.pie(summary, names='kategori', values='jumlah', hole=0.4, title="Distribusi T-K-K-K")
    return fig

# === RASIO KEUANGAN ===
def generate_ratios(df):
    total = df['jumlah'].abs().sum()
    ratios = {}
    for kategori in ['Kewajiban', 'Kebutuhan', 'Tujuan', 'Keinginan']:
        amount = df[df['kategori'] == kategori]['jumlah'].abs().sum()
        ratios[f"{kategori}/Total"] = f"{(amount/total*100):.2f}%" if total else "0%"
    return ratios

# === EXPORT HTML ===
def export_report_as_html(df, ratios):
    html_template = """
    <html>
    <head>
        <style>
            body { font-family: Arial; padding: 20px; }
            h1 { color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f4f4f4; }
            ul { line-height: 1.6; }
        </style>
    </head>
    <body>
        <h1>Laporan Keuangan - PRIORITAS</h1>
        <h2>📊 Rasio T-K-K-K</h2>
        <ul>
            {% for key, value in ratios.items() %}
                <li><strong>{{ key }}</strong>: {{ value }}</li>
            {% endfor %}
        </ul>
        <h2>📄 Transaksi Terklasifikasi</h2>
        <table>
            <thead>
                <tr>
                    {% for col in df.columns %}
                        <th>{{ col }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in df.itertuples(index=False) %}
                    <tr>
                        {% for cell in row %}
                            <td>{{ cell }}</td>
                        {% endfor %}
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    return Template(html_template).render(df=df, ratios=ratios)

# === UI STREAMLIT ===
st.set_page_config(page_title="Prioritas Keuangan", layout="wide")
st.title("📊 Aplikasi Prioritas Keuangan - T-K-K-K")

uploaded_file = st.file_uploader("📤 Unggah File Excel Laporan Bank", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("🧾 Data Mentah")
    st.dataframe(df.head())

    st.info("🔍 Menganalisis dan mengklasifikasikan transaksi dengan AI...")
    df_analyzed = analyze_transactions(df)

    st.subheader("📌 Hasil Klasifikasi T-K-K-K")
    st.dataframe(df_analyzed)

    st.subheader("📈 Alokasi Pengeluaran (Donut Chart)")
    st.plotly_chart(generate_donut_chart(df_analyzed), use_container_width=True)

    st.subheader("📊 Rasio Keuangan")
    ratios = generate_ratios(df_analyzed)
    st.json(ratios)

    st.subheader("📄 Ekspor Laporan")
    if st.button("🔽 Generate Laporan HTML"):
        html_report = export_report_as_html(df_analyzed, ratios)
        st.download_button("📥 Unduh Laporan HTML", data=html_report, file_name="laporan_keuangan.html", mime="text/html")
