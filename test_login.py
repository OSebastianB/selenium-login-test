"""
Test Automation Sederhana - Fitur Login
Website : https://oresfall.vercel.app/limbus-id-tl/login
Tools   : Python + Selenium WebDriver + pytest + Google Chrome

Cara menjalankan (lihat README.md untuk detail):
    pytest -v
"""

import os

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------
BASE_URL = "https://oresfall.vercel.app/limbus-id-tl"
LOGIN_URL = BASE_URL + "/login"
WAIT_TIMEOUT = 15  # detik maksimal menunggu elemen / respon server

# Kredensial akun pengujian diambil dari environment variable,
# BUKAN ditulis langsung di kode (agar tidak ikut ter-upload ke GitHub).
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")

# ---------------------------------------------------------------------------
# Selector elemen (hasil inspeksi HTML halaman login)
# Form login tidak memiliki atribut id/name, sehingga elemen dicari
# berdasarkan tipe input dan tipe tombol di dalam <form>.
# ---------------------------------------------------------------------------
LOGIN_HEADING = (By.XPATH, "//h1[normalize-space()='Login Manajer']")
EMAIL_INPUT = (By.CSS_SELECTOR, "form input[type='email']")
PASSWORD_INPUT = (By.CSS_SELECTOR, "form input[type='password']")
LOGIN_BUTTON = (By.CSS_SELECTOR, "form button[type='submit']")

# Pesan yang ditampilkan website ketika Supabase menolak login
ERROR_TEXT = "Email atau kata sandi salah."
ERROR_MESSAGE = (By.XPATH, f"//span[normalize-space()='{ERROR_TEXT}']")

# Indikator sudah login: tombol "Keluar" muncul di header
LOGOUT_BUTTON = (By.XPATH, "//header//button[normalize-space()='Keluar']")


# ---------------------------------------------------------------------------
# Fixture: menyiapkan dan menutup browser untuk setiap test
# ---------------------------------------------------------------------------
@pytest.fixture
def driver():
    """
    Membuka Chrome sebelum test dijalankan, lalu menutupnya setelah test
    selesai. Kode setelah `yield` tetap dijalankan walaupun test FAIL/error,
    sehingga driver.quit() selalu terpanggil.
    """
    options = Options()
    options.add_argument("--window-size=1280,900")
    if os.getenv("HEADLESS") == "1":
        options.add_argument("--headless=new")  # jalan tanpa jendela browser

    browser = webdriver.Chrome(options=options)
    yield browser
    browser.quit()


# ---------------------------------------------------------------------------
# Fungsi bantu (dipakai oleh beberapa test agar tidak duplikasi kode)
# ---------------------------------------------------------------------------
def open_login_page(driver):
    """Membuka halaman login dan menunggu sampai form siap dipakai."""
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    wait.until(EC.visibility_of_element_located(EMAIL_INPUT))
    wait.until(EC.element_to_be_clickable(LOGIN_BUTTON))


def submit_login(driver, email, password):
    """Mengisi email dan password, lalu menekan tombol Masuk."""
    driver.find_element(*EMAIL_INPUT).send_keys(email)
    driver.find_element(*PASSWORD_INPUT).send_keys(password)
    driver.find_element(*LOGIN_BUTTON).click()


def get_validity(driver, element):
    """
    Mengambil status validasi HTML5 dari sebuah input.
    Browser mengisi properti ini ketika form punya atribut `required`
    atau `type="email"`.
    """
    return driver.execute_script(
        "const el = arguments[0];"
        "return {"
        "  valid: el.validity.valid,"
        "  valueMissing: el.validity.valueMissing,"
        "  typeMismatch: el.validity.typeMismatch,"
        "  message: el.validationMessage"
        "};",
        element,
    )


# ---------------------------------------------------------------------------
# Test Case 1: Membuka halaman login
# ---------------------------------------------------------------------------
def test_open_login_page(driver):
    open_login_page(driver)

    assert "/limbus-id-tl/login" in driver.current_url, (
        f"URL tidak sesuai, didapat: {driver.current_url}"
    )
    assert driver.find_element(*LOGIN_HEADING).is_displayed(), (
        "Judul 'Login Manajer' tidak tampil"
    )
    assert driver.find_element(*EMAIL_INPUT).is_displayed(), "Input email tidak tampil"
    assert driver.find_element(*PASSWORD_INPUT).is_displayed(), "Input password tidak tampil"

    button = driver.find_element(*LOGIN_BUTTON)
    assert button.is_enabled(), "Tombol login tidak bisa ditekan"
    assert button.text.strip().lower() == "masuk", (
        f"Teks tombol login tidak sesuai, didapat: '{button.text}'"
    )


# ---------------------------------------------------------------------------
# Test Case 2: Login dengan data valid
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not (TEST_EMAIL and TEST_PASSWORD),
    reason="Kredensial belum diatur. Set environment variable TEST_EMAIL dan TEST_PASSWORD.",
)
def test_login_valid(driver):
    open_login_page(driver)
    submit_login(driver, TEST_EMAIL, TEST_PASSWORD)

    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    try:
        # Setelah login berhasil, website mengarahkan ke halaman utama
        wait.until(EC.url_matches(r"/limbus-id-tl/?$"))
        # dan tombol "Keluar" muncul di header
        wait.until(EC.visibility_of_element_located(LOGOUT_BUTTON))
    except TimeoutException:
        error_shown = len(driver.find_elements(*ERROR_MESSAGE)) > 0
        pytest.fail(
            "Login dengan kredensial valid tidak berhasil. "
            f"URL sekarang: {driver.current_url}. "
            f"Pesan error tampil: {error_shown}"
        )

    assert "Belum Login" not in driver.page_source, (
        "Sidebar masih menampilkan 'Belum Login' setelah login"
    )


# ---------------------------------------------------------------------------
# Test Case 3: Login dengan password salah
# ---------------------------------------------------------------------------
def test_login_wrong_password(driver):
    # Jika akun pengujian belum diatur, dipakai email contoh yang tidak terdaftar.
    # Website menampilkan pesan yang sama untuk kedua kondisi tersebut.
    email = TEST_EMAIL or "selenium.test@example.com"

    open_login_page(driver)
    submit_login(driver, email, "PasswordSalah123!")

    try:
        error = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.visibility_of_element_located(ERROR_MESSAGE)
        )
    except TimeoutException:
        pytest.fail(
            f"Pesan error '{ERROR_TEXT}' tidak muncul dalam {WAIT_TIMEOUT} detik. "
            f"URL sekarang: {driver.current_url}"
        )

    assert error.text.strip() == ERROR_TEXT
    assert "/login" in driver.current_url, "Halaman berpindah padahal login seharusnya ditolak"
    assert not driver.find_elements(*LOGOUT_BUTTON), "Tombol 'Keluar' muncul, berarti user ter-login"


# ---------------------------------------------------------------------------
# Test Case 4: Login dengan input kosong
# ---------------------------------------------------------------------------
def test_login_empty_fields(driver):
    open_login_page(driver)
    driver.find_element(*LOGIN_BUTTON).click()

    email_status = get_validity(driver, driver.find_element(*EMAIL_INPUT))
    password_status = get_validity(driver, driver.find_element(*PASSWORD_INPUT))

    # Browser harus menandai kedua field sebagai "wajib diisi"
    assert email_status["valueMissing"], f"Email kosong tidak divalidasi: {email_status}"
    assert password_status["valueMissing"], f"Password kosong tidak divalidasi: {password_status}"
    assert email_status["message"], "Browser tidak menampilkan pesan validasi untuk email"

    # Form tidak terkirim, jadi tetap di halaman login dan tidak ada respon server
    assert "/login" in driver.current_url, "Halaman berpindah padahal form kosong"
    assert not driver.find_elements(*ERROR_MESSAGE), "Form kosong ternyata terkirim ke server"


# ---------------------------------------------------------------------------
# Test Case 5: Login dengan format email tidak valid
# Dijalankan beberapa kali dengan contoh email yang berbeda.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("invalid_email", ["email-tidak-valid", "user@", "@example.com"])
def test_login_invalid_email_format(driver, invalid_email):
    open_login_page(driver)
    submit_login(driver, invalid_email, "Password123!")

    email_status = get_validity(driver, driver.find_element(*EMAIL_INPUT))

    assert not email_status["valid"], f"Email '{invalid_email}' dianggap valid oleh form"
    assert email_status["typeMismatch"], (
        f"Email '{invalid_email}' tidak ditolak sebagai format salah: {email_status}"
    )
    assert email_status["message"], "Browser tidak menampilkan pesan validasi format email"

    assert "/login" in driver.current_url, "Halaman berpindah padahal format email salah"
    assert not driver.find_elements(*ERROR_MESSAGE), "Form dengan email salah format terkirim ke server"
