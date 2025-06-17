# model.py
import datetime
import locale

class Transaksi:
    """
    Merepresentasikan satu entitas transaksi pengeluaran (Data Class).
    """
    def __init__(self, deskripsi: str, jumlah: float, kategori: str,
                 tanggal: datetime.date | str, id_transaksi: int | None = None):
        """
        Inisialisasi objek Transaksi dengan validasi input.
        """
        self.id = id_transaksi
        self.deskripsi = str(deskripsi) if deskripsi else "Tanpa Deskripsi"
        self.kategori = str(kategori) if kategori else "Lainnya"

        # Validasi dan konversi jumlah
        try:
            jumlah_float = float(jumlah)
            if jumlah_float <= 0:
                print(f"Peringatan: Jumlah '{jumlah}' harus positif.")
                self.jumlah = 0.0
            else:
                self.jumlah = jumlah_float
        except (ValueError, TypeError):
            print(f"Peringatan: Jumlah '{jumlah}' tidak valid.")
            self.jumlah = 0.0

        # Validasi dan konversi tanggal
        if isinstance(tanggal, datetime.date):
            self.tanggal = tanggal
        elif isinstance(tanggal, str):
            try:
                self.tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except ValueError:
                self.tanggal = datetime.date.today()
                print(f"Peringatan: Format tanggal '{tanggal}' salah, menggunakan tanggal hari ini.")
        else:
            self.tanggal = datetime.date.today()
            print(f"Peringatan: Tipe tanggal '{type(tanggal).__name__}' tidak valid, menggunakan tanggal hari ini.")

    def __repr__(self) -> str:
        """
        Representasi string dari objek Transaksi untuk debugging.
        """
        try:
            # Mengatur locale ke Indonesia untuk format ribuan
            locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
            jml_str = locale.format_string("Rp %'d", self.jumlah, grouping=True)
        except locale.Error:
            # Fallback jika locale tidak tersedia
            jml_str = f"Rp {self.jumlah:,.0f}"

        tgl_str = self.tanggal.strftime('%d-%m-%Y')
        return (f"Transaksi(ID: {self.id}, Tgl: {tgl_str}, Jml: {jml_str}, "
                f"Kat: '{self.kategori}', Desc: '{self.deskripsi}')")

    def to_dict(self) -> dict:
        """
        Mengubah objek Transaksi menjadi dictionary.
        """
        return {
            "deskripsi": self.deskripsi,
            "jumlah": self.jumlah,
            "kategori": self.kategori,
            "tanggal": self.tanggal.strftime("%Y-%m-%d")
        }
