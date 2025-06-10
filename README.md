# Tokopedia Shop Scraper

Scraping informasi toko di Tokopedia dengan memanfaatkan data yang tersedia di `window.__APOLLO_STATE__`.

## Fitur

- Mengambil **informasi toko** seperti:
  - ID toko
  - Nama toko
  - Lokasi (Kota & Kecamatan)
  - Status verifikasi toko
  - Gold Merchant
  - Jam operasional
  - Waktu pemrosesan pengiriman
  - Tanggal bergabung
  - Total favorit toko

- Mengambil **daftar jasa pengiriman aktif** yang digunakan oleh toko.

- Mengambil **data rating toko**, termasuk:
  - Rata-rata rating
  - Total ulasan
  - Distribusi rating dari bintang 1 hingga 5

- Mengambil **data produk toko**, seperti:
  - Total produk yang dijual
  - Total produk yang telah terjual
  - Daftar produk (nama, stok, rating, ulasan, jumlah terjual)

## Library yang Digunakan

| Library            | Fungsi                                             |
|--------------------|----------------------------------------------------|
| `requests`         | Mengirim permintaan HTTP                           |
| `beautifulsoup4`   | Parsing HTML dan mengekstrak elemen JavaScript     |
| `fake-useragent`   | Menghasilkan User-Agent acak agar tidak terdeteksi |
| `re` & `json`      | Parsing data JS (Apollo State) dan decoding JSON   |

Instalasi:

```bash
pip install requests beautifulsoup4 fake-useragent
