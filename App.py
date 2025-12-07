import streamlit as st
import pandas as pd
import plotly.express as px
from jinja2 import Template
from groq import Groq
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# SETUP GROQ CLIENT
# =========================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = "llama-3.3-70b-versatile"

# =========================
# AI CLASSIFIER (GROQ)
# =========================
def classify_transaction_groq(text: str) -> str:
    text = str(text).strip()
    if not text:
        return "Tidak Terkategori"

    prompt = f"""
Kamu adalah mesin klasifikasi transaksi keuangan.
Klasifikasikan transaksi berikut ke SALAH SATU kategori:
1) Kewajiban
2) Kebutuhan
3) Tujuan
4) Keinginan

Aturan:
- Jawab hanya dengan 1 kata kategori di atas.
- Tanpa titik, tanpa penjelasan, tanpa tambahan kata lain.

Transaksi: "{text}"
Kategori:
"""

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
        )
        raw = resp.choices[0].message.content.strip()
        cleaned = re.sub(r"[^a-zA-Z]", "", raw).capitalize()
        valid = {"Kewajiban", "Kebutuhan", "Tujuan", "Keinginan"}
        return cleaned if cleaned in valid else "Tidak Terkategori"
    except Exception as e:
        print("❌ ERROR Groq:", e)
        return "Tidak Terkategori"

# =========================
# ANALYZE EXCEL
# =========================
def analyze_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)

    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    else:
        df['tanggal'] = pd.NaT

    if "jumlah" in df.columns:
        df["jumlah"] = pd.to_numeric(df["jumlah"], errors="coerce").fillna(0)
    elif "debit" in df.columns and "kredit" in df.columns:
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)
        df["kredit"] = pd.to_numeric(df["kredit"], errors="coerce").fillna(0)
        df["jumlah"] = df["debit"] - df["kredit"]
    else:
        df["jumlah"] = 0

    transaksi_col = "transaksi" if "transaksi" in df.columns else "deskripsi"
    if transaksi_col not in df.columns:
        df[transaksi_col] = ""

    df["kategori"] = df[transaksi_col].apply(classify_transaction_groq)
    return df[["tanggal", transaksi_col, "jumlah", "kategori"]]

# =========================
# VISUALIZATION
# =========================
def generate_donut_chart(df: pd.DataFrame):
    summary = df.groupby("kategori")["jumlah"].sum().abs().reset_index()
    fig = px.pie(
        summary,
        names="kategori",
        values="jumlah",
        hole=0.4,
        title="Distribusi T-K-K-K"
    )
    return fig

def generate_ratios(df: pd.DataFrame):
    total = df["jumlah"].abs().sum()
    ratios = {}
    for k in ["Kewajiban", "Kebutuhan", "Tujuan", "Keinginan"]:
        amount = df[df["kategori"] == k]["jumlah"].abs().sum()
        ratios[f"{k}/Total"] = f"{(amount/total*100):.2f}%" if total else "0%"
    return ratios

# =========================
# EXPORT HTML REPORT
# =========================
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

# =========================
# STREAMLIT UI
# =========================
st.set_page_config(page_title="Prioritas Keuangan", layout="wide")
st.title("📊 Aplikasi Prioritas Keuangan - T-K-K-K")

uploaded_file = st.file_uploader("📤 Unggah File Excel Laporan Bank", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("🧾 Data Mentah")
    st.dataframe(df.head())

    st.info("🔍 Menganalisis & mengklasifikasikan transaksi dengan Groq AI...")
    df_analyzed = analyze_transactions(df)

    st.subheader("📌 Hasil Klasifikasi T-K-K-K")
    st.dataframe(df_analyzed)

    st.subheader("📈 Alokasi Pengeluaran (Donut Chart)")
    st.plotly_chart(generate_donut_chart(df_analyzed), use_container_width=True)

    st.markdown("### 📊 Rasio Keuangan Interaktif")
    total = df_analyzed["jumlah"].abs().sum()
    for kategori in ["Kewajiban", "Kebutuhan", "Tujuan", "Keinginan"]:
        jumlah = df_analyzed[df_analyzed["kategori"] == kategori]["jumlah"].abs().sum()
        st.metric(label=f"{kategori}", value=f"Rp{jumlah:,.0f}")

    # === SARAN AI OTOMATIS BERDASARKAN RASIO ===
    st.markdown("### 💡 Saran AI Berdasarkan Rasio")
    nilai = {
        "Kewajiban": df_analyzed[df_analyzed["kategori"] == "Kewajiban"]["jumlah"].abs().sum(),
        "Kebutuhan": df_analyzed[df_analyzed["kategori"] == "Kebutuhan"]["jumlah"].abs().sum(),
        "Tujuan": df_analyzed[df_analyzed["kategori"] == "Tujuan"]["jumlah"].abs().sum(),
        "Keinginan": df_analyzed[df_analyzed["kategori"] == "Keinginan"]["jumlah"].abs().sum(),
    }

    if nilai["Keinginan"] / total > 0.4:
        st.warning("⚠️ Pengeluaran untuk *Keinginan* lebih dari 40%. Pertimbangkan untuk menurunkannya agar tidak mengganggu kebutuhan utama.")
    if nilai["Tujuan"] / total < 0.1:
        st.info("💰 Alokasi ke *Tujuan* (seperti menabung/investasi) masih kecil. Coba tingkatkan untuk jangka panjang.")
    if nilai["Kebutuhan"] / total > 0.5:
        st.warning("📌 *Kebutuhan* mendominasi lebih dari 50%. Pastikan tetap ada ruang untuk Tujuan dan Keinginan.")
    if nilai["Kewajiban"] / total > 0.3:
        st.error("🚨 *Kewajiban* lebih dari 30%. Cek apakah utang atau cicilan terlalu membebani keuangan.")

    if all(0.1 < (v / total) < 0.4 for v in nilai.values()):
        st.success("✅ Rasio keuangan kamu cukup seimbang. Pertahankan dan tetap disiplin!")

    st.subheader("📄 Ekspor Laporan")
    if st.button("🔽 Generate Laporan HTML"):
        ratios = generate_ratios(df_analyzed)
        html_report = export_report_as_html(df_analyzed, ratios)
        st.download_button(
            "📥 Unduh Laporan HTML",
            data=html_report,
            file_name="laporan_keuangan.html",
            mime="text/html"
        )

    st.subheader("📊 Grafik Tren Pengeluaran Bulanan")
    if 'tanggal' in df_analyzed.columns and not df_analyzed['tanggal'].isna().all():
        df_analyzed['bulan'] = df_analyzed['tanggal'].dt.to_period('M').astype(str)
        monthly = df_analyzed.groupby(['bulan', 'kategori'])['jumlah'].sum().reset_index()
        pivot_df = monthly.pivot(index='bulan', columns='kategori', values='jumlah').fillna(0)
        st.line_chart(pivot_df)
    else:
        st.warning("📅 Kolom 'Tanggal' tidak tersedia atau tidak valid, grafik tren tidak ditampilkan.")
else:
    st.info("Silakan unggah file Excel terlebih dahulu.")
