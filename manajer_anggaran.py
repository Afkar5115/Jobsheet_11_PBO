# manajer_anggaran.py

import sqlite3
import pandas as pd
from model import Transaksi
from typing import List, Dict, Any, Optional
import datetime

class DatabaseManager:
    """Manages all database connections and operations."""
    def __init__(self, db_name="anggaran.db"):
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        """Opens the database connection."""
        self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the database connection."""
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def execute_query(self, sql: str, params: tuple = (), is_insert: bool = False, fetch: str = None):
        """
        Executes a given SQL query.
        
        Args:
            sql (str): The SQL query to execute.
            params (tuple): The parameters to substitute in the query.
            is_insert (bool): True if it's an INSERT statement to return the last row ID.
            fetch (str): 'one' for a single record, 'all' for multiple records.

        Returns:
            The result of the query (last row ID, one record, all records, or None).
        """
        try:
            with self as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                
                if is_insert:
                    return cursor.lastrowid  # FIX: Correctly get the last inserted ID
                if fetch == 'one':
                    return cursor.fetchone()
                if fetch == 'all':
                    return cursor.fetchall()
                
                # For UPDATE, DELETE, or statements where no return is needed
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None if is_insert or fetch else False


class AnggaranHarian:
    """Handles the business logic for the expense tracking app."""
    def __init__(self, db_name="anggaran.db"):
        self.db_manager = DatabaseManager(db_name)
        self._buat_tabel_jika_tidak_ada()

    def _buat_tabel_jika_tidak_ada(self):
        """Creates the 'transaksi' table if it doesn't already exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deskripsi TEXT NOT NULL,
            jumlah REAL NOT NULL,
            kategori TEXT NOT NULL,
            tanggal DATE NOT NULL
        );
        """
        self.db_manager.execute_query(sql)

    def tambah_transaksi(self, tx: Transaksi) -> bool:
        """Adds a new transaction to the database."""
        sql = """
        INSERT INTO transaksi (deskripsi, jumlah, kategori, tanggal) 
        VALUES (?, ?, ?, ?);
        """
        params = (tx.deskripsi, tx.jumlah, tx.kategori, tx.tanggal.strftime('%Y-%m-%d'))
        # FIX: The execute_query now correctly handles INSERTs and returns the ID
        last_id = self.db_manager.execute_query(sql, params, is_insert=True)
        return last_id is not None

    def get_dataframe_transaksi(self) -> Optional[pd.DataFrame]:
        """Retrieves all transactions and returns them as a DataFrame."""
        sql = "SELECT id, tanggal, deskripsi, kategori, jumlah FROM transaksi ORDER BY tanggal DESC, id DESC;"
        try:
            records = self.db_manager.execute_query(sql, fetch='all')
            if records is None: return None
            
            df = pd.DataFrame(records, columns=['ID', 'Tanggal', 'Deskripsi', 'Kategori', 'Jumlah'])
            df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.strftime('%d-%m-%Y')
            df['Jumlah'] = df['Jumlah'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            return df.set_index('ID')
        except Exception:
            return None

    def hapus_transaksi(self, id_transaksi: int) -> bool:
        """Deletes a transaction by its ID."""
        sql = "DELETE FROM transaksi WHERE id = ?;"
        return self.db_manager.execute_query(sql, (id_transaksi,))

    def hitung_total_pengeluaran(self, tanggal: Optional[datetime.date] = None) -> float:
        """Calculates total expenses, optionally filtered by date."""
        if tanggal:
            sql = "SELECT SUM(jumlah) FROM transaksi WHERE tanggal = ?;"
            params = (tanggal.strftime('%Y-%m-%d'),)
        else:
            sql = "SELECT SUM(jumlah) FROM transaksi;"
            params = ()
        
        result = self.db_manager.execute_query(sql, params, fetch='one')
        return result[0] if result and result[0] is not None else 0.0

    def get_pengeluaran_per_kategori(self, tanggal: Optional[datetime.date] = None) -> Dict[str, float]:
        """Gets total expenses per category, optionally filtered by date."""
        if tanggal:
            sql = "SELECT kategori, SUM(jumlah) FROM transaksi WHERE tanggal = ? GROUP BY kategori;"
            params = (tanggal.strftime('%Y-%m-%d'),)
        else:
            sql = "SELECT kategori, SUM(jumlah) FROM transaksi GROUP BY kategori;"
            params = ()
            
        records = self.db_manager.execute_query(sql, params, fetch='all')
        return {row[0]: row[1] for row in records} if records else {}