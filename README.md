# Selenium Login Test

Script test automation sederhana untuk menguji fitur **login** pada website
[Indonesia Limbus Translation](https://oresfall.vercel.app/limbus-id-tl/login)
menggunakan **Python + Selenium WebDriver + pytest**.

## Tujuan

Menguji fungsi login secara otomatis tanpa mengisi form secara manual:
membuka halaman, mengisi form, menekan tombol, lalu memeriksa respon website.

## Library yang digunakan

| Library  | Fungsi                                                         |
|----------|----------------------------------------------------------------|
| selenium | Mengendalikan browser Google Chrome (WebDriver)                |
| pytest   | Menjalankan test dan menampilkan hasil PASS / FAIL / SKIPPED   |

Selenium versi 4.6 ke atas sudah memiliki **Selenium Manager** yang otomatis
mengunduh ChromeDriver sesuai versi Chrome, jadi tidak perlu instal driver manual.

## Struktur project

```text
Selenium-login-test/
├── test_login.py      # seluruh test case login
├── requirements.txt   # daftar dependency
├── .gitignore         # mencegah .venv / file rahasia ter-upload
└── README.md
```

## Hasil inspeksi halaman login

Selector diambil dari HTML asli halaman login (form tidak memiliki `id`/`name`):

| Elemen         | Selector                                   |
|----------------|--------------------------------------------|
| Input email    | `form input[type='email']`                 |
| Input password | `form input[type='password']`              |
| Tombol login   | `form button[type='submit']` (teks "Masuk")|

Perilaku website (dari kode JavaScript halaman):

- Login memakai **Supabase** (`signInWithPassword`).
- Jika login gagal, muncul pesan **"Email atau kata sandi salah."**
- Jika berhasil, diarahkan ke `/limbus-id-tl` dan header menampilkan tombol **"Keluar"**.
- Kedua input memiliki atribut `required`, dan input email bertipe `type="email"`,
  sehingga input kosong dan format email salah **ditolak browser (validasi HTML5)**
  sebelum data dikirim ke server.

## Instalasi (Windows, terminal Cursor / PowerShell)

Pastikan Python 3 dan Google Chrome sudah terpasang.

```powershell
cd D:\Selenium-login-test
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Menjalankan test

```powershell
.venv\Scripts\python -m pytest -v
```

Opsi tambahan:

```powershell
# Menampilkan alasan test yang di-skip
.venv\Scripts\python -m pytest -v -rs

# Menjalankan tanpa membuka jendela Chrome (headless)
$env:HEADLESS = "1"
.venv\Scripts\python -m pytest -v
Remove-Item Env:HEADLESS   # kembali menampilkan jendela browser

# Menjalankan satu test saja
.venv\Scripts\python -m pytest -v -k test_login_wrong_password
```

### Mengatur akun pengujian (untuk test login valid)

Password **tidak disimpan di kode**. Kredensial dibaca dari environment variable
yang hanya berlaku di sesi terminal saat ini:

```powershell
$env:TEST_EMAIL = "email-akun-test@contoh.com"
$env:TEST_PASSWORD = "password-akun-test"
.venv\Scripts\python -m pytest -v
```

Jika variabel ini belum diatur, `test_login_valid` akan berstatus **SKIPPED**
(bukan FAIL), karena memang tidak bisa diuji tanpa akun yang benar.
Akun dapat dibuat melalui halaman *Buat Akun* pada website.

## Penjelasan test case

| No | Fungsi test                       | Skenario                                   | Hasil yang diharapkan |
|----|-----------------------------------|--------------------------------------------|-----------------------|
| 1  | `test_open_login_page`            | Membuka halaman login                      | Judul "Login Manajer", input email, input password, dan tombol "Masuk" tampil |
| 2  | `test_login_valid`                | Login dengan email & password benar        | Diarahkan ke `/limbus-id-tl`, tombol "Keluar" muncul, teks "Belum Login" hilang |
| 3  | `test_login_wrong_password`       | Login dengan password salah                | Pesan "Email atau kata sandi salah." tampil, tetap di halaman login |
| 4  | `test_login_empty_fields`         | Klik "Masuk" dengan form kosong            | Browser menandai email & password `valueMissing`, form tidak terkirim |
| 5  | `test_login_invalid_email_format` | Email `email-tidak-valid`, `user@`, `@example.com` | Browser menandai email `typeMismatch`, form tidak terkirim |

Catatan:

- **Fixture `driver`** membuka Chrome sebelum setiap test dan memanggil
  `driver.quit()` setelah test selesai, termasuk ketika test gagal.
- **Test 3**: jika `TEST_EMAIL` belum diatur, dipakai email contoh
  `selenium.test@example.com`. Website menampilkan pesan error yang sama untuk
  email tidak terdaftar maupun password salah.
- **Test 4 & 5**: validasi dicek melalui properti `validity` milik input
  (bukan teks pop-up), karena teks pesan validasi browser berbeda-beda
  tergantung bahasa Chrome.
- **Test 5** memakai `@pytest.mark.parametrize`, jadi satu fungsi dijalankan
  3 kali dengan contoh email berbeda.

## Contoh membaca hasil pengujian

```text
test_login.py::test_open_login_page PASSED                               [ 14%]
test_login.py::test_login_valid SKIPPED (Kredensial belum diatur. Se...) [ 28%]
test_login.py::test_login_wrong_password PASSED                          [ 42%]
test_login.py::test_login_empty_fields PASSED                            [ 57%]
test_login.py::test_login_invalid_email_format[email-tidak-valid] PASSED [ 71%]
test_login.py::test_login_invalid_email_format[user@] PASSED             [ 85%]
test_login.py::test_login_invalid_email_format[@example.com] PASSED      [100%]

======================== 6 passed, 1 skipped in 44.87s ========================
```

- **PASSED**: kondisi website sesuai harapan.
- **FAILED**: ada assertion yang tidak terpenuhi. pytest akan menampilkan pesan
  penyebabnya, misalnya
  `Failed: Pesan error 'Email atau kata sandi salah.' tidak muncul dalam 15 detik`
  atau `AssertionError: Halaman berpindah padahal form kosong`.
- **SKIPPED**: test dilewati, misalnya karena kredensial akun belum diatur.
