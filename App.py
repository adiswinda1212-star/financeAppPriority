import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Fungsi untuk mengkategorikan transaksi secara sederhana
def simple_classifier(deskripsi):
    deskripsi = deskripsi.lower()
    if any(keyword in deskripsi for keyword in ["makan", "resto", "kfc", "cafe", "kopi"]):
        return "Keinginan"
    elif any(keyword in deskripsi for keyword in ["listrik", "air", "transport", "bbm", "pulsa", "sewa"]):
        return "Kebutuhan"
    elif any(keyword in deskripsi for keyword in ["tabung", "invest", "deposito"]):
        return "Tabungan/Investasi"
    else:
        return "Lainnya"

# Fungsi untuk merangkum data
def ringkasan_pengeluaran(df):
    df['Kategori'] = df['Deskripsi'].apply(simple_classifier)
    summary = df.groupby('Kategori')['Jumlah'].sum().reset_index()
    return summary

# Fungsi untuk membuat laporan HTML sederhana
def generate_report(df, summary):
    total = summary['Jumlah'].sum()
    report_html = f"""
    <h2>Laporan Keuangan Pribadi</h2>
    <p>Total Pengeluaran: <strong>Rp{total:,.0f}</strong></p>
    <h3>Rincian:</h3>
    <ul>
    {''.join([f'<li>{row.Kategori}: Rp{row.Jumlah:,.0f}</li>' for _, row in summary.iterrows()])}
    </ul>
    <br><br>
    <p><em>Generated with FinanceAppPriority</em></p>
    """
    return report_html

# UI Streamlit
st.title("📊 FinanceApp Priority")

uploaded_file = st.file_uploader("Unggah file transaksi (CSV dengan kolom: Deskripsi, Jumlah)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if 'Deskripsi' not in df.columns or 'Jumlah' not in df.columns:
        st.error("File harus memiliki kolom 'Deskripsi' dan 'Jumlah'")
    else:
        st.success("✅ File berhasil diunggah dan dibaca.")
        df['Kategori'] = df['Deskripsi'].apply(simple_classifier)
        summary = ringkasan_pengeluaran(df)

        st.markdown("### 📌 Ringkasan Pengeluaran")
        st.dataframe(summary)

        # Donut chart
        fig, ax = plt.subplots()
        labels = summary['Kategori']
        sizes = summary['Jumlah']
        colors = sns.color_palette('pastel')[0:len(labels)]
        ax.pie(sizes, labels=labels, colors=colors, startangle=90, wedgeprops=dict(width=0.4))
        ax.axis('equal')
        st.pyplot(fig)

        # Insight otomatis
        st.markdown("### 💡 Insight Otomatis dari AI")
        if 'Keinginan' in summary['Kategori'].values:
            kebutuhan = summary[summary['Kategori'] == 'Kebutuhan']['Jumlah'].values[0] if 'Kebutuhan' in summary['Kategori'].values else 0
            keinginan = summary[summary['Kategori'] == 'Keinginan']['Jumlah'].values[0]
            tabungan = summary[summary['Kategori'] == 'Tabungan/Investasi']['Jumlah'].values[0] if 'Tabungan/Investasi' in summary['Kategori'].values else 0

            total = kebutuhan + keinginan + tabungan
            p_keinginan = keinginan / total * 100 if total != 0 else 0

            if p_keinginan > 40:
                st.warning("⚠️ Pengeluaran untuk *Keinginan* terlalu tinggi. Pertimbangkan untuk menurunkannya agar keuangan lebih sehat.")
            elif tabungan / total < 20:
                st.info("💰 Coba alokasikan lebih banyak ke tabungan untuk mencapai tujuan keuangan jangka panjang.")
            else:
                st.success("✅ Struktur keuangan kamu sudah ideal. Pertahankan!")

        # Tombol laporan
        if st.button("📥 Download Laporan"):
            html_report = generate_report(df, summary)
            st.download_button("📄 Download HTML", html_report, file_name="laporan_keuangan.html")

        # Simulasi tujuan keuangan
        st.markdown("## 🎯 Simulasi Tujuan Keuangan")
        target_uang = st.number_input("Masukkan jumlah target tabungan (Rp):", min_value=100000, step=100000)
        jumlah_per_bulan = st.number_input("Masukkan kemampuan menabung per bulan (Rp):", min_value=100000, step=100000)

        if target_uang and jumlah_per_bulan:
            bulan = target_uang // jumlah_per_bulan
            st.info(f"🗓️ Dengan menabung Rp{jumlah_per_bulan:,.0f}/bulan, kamu akan mencapai target Rp{target_uang:,.0f} dalam {bulan} bulan.")

            bulan_arr = list(range(1, bulan + 1))
            simpanan_arr = [jumlah_per_bulan * b for b in bulan_arr]

            fig2, ax2 = plt.subplots()
            ax2.plot(bulan_arr, simpanan_arr, marker='o')
            ax2.set_title("Proyeksi Pencapaian Target")
            ax2.set_xlabel("Bulan")
            ax2.set_ylabel("Total Tabungan (Rp)")
            st.pyplot(fig2)

else:
    st.info("Silakan unggah file transaksi terlebih dahulu.")
