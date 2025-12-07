import streamlit as st
import pandas as pd
import plotly.express as px
from jinja2 import Template
from groq import Groq
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns
import io
from weasyprint import HTML

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
# PDF EXPORT
# =========================
def export_pdf_report(df: pd.DataFrame, donut_fig, line_fig, rasio_html: str):
    donut_path = "/tmp/donut.png"
    line_path = "/tmp/trend.png"
    donut_fig.write_image(donut_path)
    line_fig.write_image(line_path)

    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; padding: 30px; }}
            h1 {{ color: #2c3e50; }}
            img {{ max-width: 100%; }}
        </style>
    </head>
    <body>
        <h1>Laporan Keuangan</h1>
        <h2>📊 Rasio Keuangan</h2>
        {rasio_html}
        <h2>📈 Donut Chart</h2>
        <img src="{donut_path}" />
        <h2>📉 Grafik Tren Bulanan</h2>
        <img src="{line_path}" />
    </body>
    </html>
    """
    pdf_bytes = HTML(string=html_template).write_pdf()
    return pdf_bytes

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

    donut_fig = generate_donut_chart(df_analyzed)
    st.subheader("📈 Alokasi Pengeluaran (Donut Chart)")
    st.plotly_chart(donut_fig, use_container_width=True)

    st.subheader("📊 Grafik Tren Pengeluaran Bulanan")
    if 'tanggal' in df_analyzed.columns and not df_analyzed['tanggal'].isna().all():
        df_analyzed['bulan'] = df_analyzed['tanggal'].dt.to_period('M').astype(str)
        monthly = df_analyzed.groupby(['bulan', 'kategori'])['jumlah'].sum().reset_index()
        pivot_df = monthly.pivot(index='bulan', columns='kategori', values='jumlah').fillna(0)
        trend_fig = px.line(pivot_df, title="Tren Pengeluaran per Kategori")
        st.plotly_chart(trend_fig, use_container_width=True)
    else:
        trend_fig = px.line(title="(Data tidak tersedia)")
        st.warning("📅 Kolom 'Tanggal' tidak tersedia atau tidak valid, grafik tren tidak ditampilkan.")

    # Rasio ringkas untuk HTML
    rasio_dict = generate_ratios(df_analyzed)
    rasio_html = "<ul>" + "".join([f"<li><strong>{k}</strong>: {v}</li>" for k, v in rasio_dict.items()]) + "</ul>"

    st.subheader("📤 Ekspor Laporan PDF")
    if st.button("📥 Unduh PDF"):
        pdf_data = export_pdf_report(df_analyzed, donut_fig, trend_fig, rasio_html)
        st.download_button("📄 Download Laporan PDF", pdf_data, file_name="laporan_keuangan.pdf", mime="application/pdf")
else:
    st.info("Silakan unggah file Excel terlebih dahulu.")
