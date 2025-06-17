import streamlit as st
import datetime
import pandas as pd
from manajer_anggaran import AnggaranHarian  # Import backend AnggaranHarian
from konfigurasi import KATEGORI_PENGELUARAN  # Ambil list kategori
from model import Transaksi
import locale

# Set page configuration
st.set_page_config(page_title="Catatan Pengeluaran", layout="wide", initial_sidebar_state="expanded")

def format_rp(angka):
    """Formats a number into Indonesian Rupiah currency format."""
    try: 
        # Attempt to use locale for formatting, which is more robust
        locale.setlocale(locale.LC_ALL, 'id_ID')
        return locale.currency(angka or 0, grouping=True, symbol='Rp ')[:-3]
    except (locale.Error, TypeError): 
        # Fallback for environments where the locale is not available
        return f"Rp {angka or 0:,.0f}".replace(",", ".")
    
# Initialize budget manager with caching to prevent re-initialization on each rerun
@st.cache_resource
def get_anggaran_manager():
    """Initializes the AnggaranHarian manager and caches the resource."""
    print(">>> STREAMLIT: (Cache Resource) Menginisialisasi AnggaranHarian...")
    return AnggaranHarian()  # This will trigger DB/Table check in __init__
anggaran = get_anggaran_manager()

# --- UI Pages ---

def halaman_input(anggaran: AnggaranHarian):
    """Page for adding a new expense transaction."""
    st.header("Tambah Pengeluaran Baru")
    with st.form("form_transaksi_baru", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1: 
            deskripsi = st.text_input("Deskripsi*", placeholder="Contoh: Makan siang")
        with col2: 
            kategori = st.selectbox("Kategori*:", KATEGORI_PENGELUARAN, index=0)
        
        col3, col4 = st.columns([1, 1])
        with col3: 
            jumlah = st.number_input("Jumlah (Rp)*:", min_value=0.01, step=1000.0, format="%.0f", value=None, placeholder="Contoh: 25000")
        with col4: 
            tanggal = st.date_input("Tanggal*:", value=datetime.date.today())
            
        submitted = st.form_submit_button(" Simpan Transaksi")
        
        if submitted:
            # Validate input fields
            if not deskripsi: 
                st.warning("Deskripsi wajib diisi!", icon="⚠")
            elif jumlah is None or jumlah <= 0: 
                st.warning("Jumlah wajib diisi dan harus lebih dari nol!", icon="⚠")
            else:
                with st.spinner("Menyimpan..."):
                    tx = Transaksi(deskripsi, float(jumlah), kategori, tanggal)
                    if anggaran.tambah_transaksi(tx): 
                        st.success("Transaksi berhasil disimpan!", icon="✅")
                        st.cache_data.clear()  # Clear cache to reflect new data
                        st.rerun()
                    else: 
                        st.error("Gagal menyimpan transaksi.", icon="❌")

def halaman_riwayat(anggaran: AnggaranHarian):
    """Page to display and delete transaction history."""
    st.subheader("Detail Semua Transaksi")
    if st.button("Refresh Riwayat"): 
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Memuat riwayat..."): 
        df_transaksi = anggaran.get_dataframe_transaksi()
    
    if df_transaksi is None: 
        st.error("Gagal mengambil data riwayat.")
    elif df_transaksi.empty: 
        st.info("Belum ada transaksi yang tercatat.")
    else:
        # --- MODIFICATION START: Display transaction ID ---
        # Copy the dataframe to avoid modifying the cached version
        df_display = df_transaksi.copy()
        
        # Reset the index to turn the transaction ID (assumed to be the index) into a column
        df_display.reset_index(inplace=True)
        df_display = df_display.rename(columns={'index': 'ID'})
        
        # Ensure the ID column is present before trying to reorder
        if 'ID' in df_display.columns:
            # Reorder columns to make 'ID' the first column
            all_columns = list(df_display.columns)
            all_columns.remove('ID')
            new_order = ['ID'] + all_columns
            df_display = df_display[new_order]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        # --- MODIFICATION END ---

    # --- Section for deleting a transaction by ID ---
    st.subheader("Hapus Transaksi")
    id_transaksi = st.number_input(
        "ID Transaksi yang ingin dihapus:", 
        min_value=1, 
        step=1, 
        value=None, 
        placeholder="Ketik ID dari tabel di atas..."
    )
    confirm_button = st.button("Konfirmasi Hapus")

    if confirm_button:
        if id_transaksi is not None:
            with st.spinner("Menghapus..."):
                # FIX: Corrected the method name based on the AttributeError.
                # It's likely a typo in the original method call.
                if anggaran.hapus_transaksi(int(id_transaksi)):
                    st.success(f"Transaksi dengan ID {id_transaksi} berhasil dihapus.", icon="✅")
                    st.cache_data.clear()  # Clear cache to reflect the deletion
                    st.rerun()
                else:
                    st.error(f"Gagal menghapus transaksi dengan ID {id_transaksi}. Pastikan ID valid.", icon="❌")
        else:
            st.warning("Mohon masukkan ID transaksi yang valid untuk dihapus.")


def halaman_ringkasan(anggaran: AnggaranHarian):
    """Page for displaying summary and charts of expenses."""
    st.subheader("Ringkasan Pengeluaran")
    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        # Note: on_change clears cache to ensure summary is recalculated
        pilihan_periode = st.selectbox(
            "Filter Periode:", 
            ["Semua Waktu", "Hari Ini", "Pilih Tanggal"], 
            key="filter_periode", 
            on_change=lambda: st.cache_data.clear()
        )
    
    tanggal_filter = None
    label_periode = "(Semua Waktu)"
    if pilihan_periode == "Hari Ini":
        tanggal_filter = datetime.date.today()
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"
    # FIX: Corrected condition from "Pilih Tanggal Tertentu" to "Pilih Tanggal"
    elif pilihan_periode == "Pilih Tanggal":
        if 'tanggal_pilihan_state' not in st.session_state:
            st.session_state.tanggal_pilihan_state = datetime.date.today()
        
        tanggal_filter = st.date_input(
            "Pilih Tanggal:", 
            value=st.session_state.tanggal_pilihan_state, 
            key="tanggal_pilihan", 
            on_change=lambda: setattr(st.session_state, 'tanggal_pilihan_state', st.session_state.tanggal_pilihan) or st.cache_data.clear()
        )
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"
    
    with col_filter2:
        @st.cache_data(ttl=300)
        def hitung_total_cached(tgl_filter): 
            return anggaran.hitung_total_pengeluaran(tanggal=tgl_filter)
        
        total_pengeluaran = hitung_total_cached(tanggal_filter)
        st.metric(label=f"Total Pengeluaran {label_periode}", value=format_rp(total_pengeluaran))

    st.divider()
    st.subheader(f"Pengeluaran per Kategori {label_periode}")
    
    @st.cache_data(ttl=300)
    def get_kategori_cached(tgl_filter): 
        return anggaran.get_pengeluaran_per_kategori(tanggal=tgl_filter)

    with st.spinner("Memuat ringkasan kategori..."): 
        dict_per_kategori = get_kategori_cached(tanggal_filter)

    if not dict_per_kategori: 
        st.info("Tidak ada data pengeluaran untuk periode ini.")
    else:
        try:
            data_kategori = [{"Kategori": kat, "Total": jml} for kat, jml in dict_per_kategori.items()]
            df_kategori = pd.DataFrame(data_kategori).sort_values(by="Total", ascending=False).reset_index(drop=True)
            df_kategori['Total (Rp)'] = df_kategori['Total'].apply(format_rp)
            
            col_kat1, col_kat2 = st.columns(2)
            with col_kat1: 
                st.write("Tabel Ringkasan:")
                st.dataframe(df_kategori[['Kategori', 'Total (Rp)']], hide_index=True, use_container_width=True)
            with col_kat2: 
                st.write("Grafik:")
                st.bar_chart(df_kategori.set_index('Kategori')['Total'], use_container_width=True)
        except Exception as e: 
            st.error(f"Gagal menampilkan ringkasan: {e}")

# --- Main App Logic ---

def main():
    """Main function to run the Streamlit app."""
    st.sidebar.title("Catatan Pengeluaran")
    menu_pilihan = st.sidebar.radio("Pilih Menu:", ["Tambah", "Riwayat", "Ringkasan"], key="menu_utama")
    st.sidebar.markdown("---")
    st.sidebar.info("Jobsheet - Aplikasi Keuangan")
    
    manajer_anggaran = get_anggaran_manager()
    
    if menu_pilihan == "Tambah": 
        halaman_input(manajer_anggaran)
    elif menu_pilihan == "Riwayat": 
        halaman_riwayat(manajer_anggaran)
    elif menu_pilihan == "Ringkasan":
        halaman_ringkasan(manajer_anggaran)
    
    st.markdown("---")
    st.caption("Pengembangan Aplikasi Berbasis OOP")

if __name__ == "__main__":
    main()
