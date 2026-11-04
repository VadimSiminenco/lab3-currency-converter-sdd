"""Selenium WebDriver end-to-end browser tests for Currency Converter Streamlit UI."""
from datetime import date
from decimal import Decimal
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


def get_free_port() -> int:
    """Find and return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: float = 25.0) -> bool:
    """Poll the Streamlit health endpoint until responsive."""
    health_url = f"{url}/_stcore/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def streamlit_server():
    """Launch Streamlit server configured with deterministic XML fixture data."""
    port = get_free_port()
    fixture_xml = FIXTURES_DIR / "valid_rate_feed.xml"

    env = os.environ.copy()
    env["CONVERTER_TEST_FIXTURE"] = str(fixture_xml)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"
    if not wait_for_server(base_url, timeout=25.0):
        proc.terminate()
        raise RuntimeError(f"Streamlit server failed to start within timeout on {base_url}")

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def driver():
    """Create a headless Chrome WebDriver instance with explicit window size."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1024")

    chrome_driver = webdriver.Chrome(options=options)
    chrome_driver.implicitly_wait(2.0)

    yield chrome_driver

    chrome_driver.quit()


def get_convert_button(driver):
    return driver.find_element(By.XPATH, '//button[contains(., "Convert Currency")]')


def set_amount_and_commit(driver, text: str):
    """Set input amount and commit change via Enter key to notify Streamlit."""
    inp = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="stTextInput"] input'))
    )
    inp.send_keys(Keys.CONTROL + "a")
    inp.send_keys(Keys.BACKSPACE)
    if text:
        inp.send_keys(text)
    inp.send_keys(Keys.ENTER)
    time.sleep(0.6)


class TestStreamlitConverterBrowser:
    """Selenium E2E tests for user journeys in the currency converter web application."""

    def test_convert_button_disabled_on_invalid_amount(self, driver, streamlit_server):
        driver.get(streamlit_server)
        wait = WebDriverWait(driver, 10)

        # Wait for page to be ready
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="stTextInput"] input')))

        # 1. Test empty amount
        set_amount_and_commit(driver, "")
        wait.until(lambda d: not get_convert_button(d).is_enabled())
        val_error = wait.until(EC.presence_of_element_located((By.ID, "validation-error")))
        assert "required" in val_error.text.lower()

        # 2. Test zero amount
        set_amount_and_commit(driver, "0")
        wait.until(lambda d: not get_convert_button(d).is_enabled())
        val_error = driver.find_element(By.ID, "validation-error")
        assert "greater than zero" in val_error.text.lower()

        # 3. Test negative amount
        set_amount_and_commit(driver, "-25")
        wait.until(lambda d: not get_convert_button(d).is_enabled())
        val_error = driver.find_element(By.ID, "validation-error")
        assert "greater than zero" in val_error.text.lower()

        # 4. Test alphabetic amount
        set_amount_and_commit(driver, "abc")
        wait.until(lambda d: not get_convert_button(d).is_enabled())
        val_error = driver.find_element(By.ID, "validation-error")
        assert "invalid amount format" in val_error.text.lower()

        # 5. Test NaN amount
        set_amount_and_commit(driver, "NaN")
        wait.until(lambda d: not get_convert_button(d).is_enabled())
        val_error = driver.find_element(By.ID, "validation-error")
        assert "finite" in val_error.text.lower() or "invalid" in val_error.text.lower()

    def test_valid_conversion_displays_result_and_metadata(self, driver, streamlit_server):
        driver.get(streamlit_server)
        wait = WebDriverWait(driver, 10)

        # Enter valid amount: 100 USD (default source is USD, default target is MDL)
        set_amount_and_commit(driver, "100")
        wait.until(lambda d: get_convert_button(d).is_enabled())

        convert_btn = get_convert_button(driver)
        convert_btn.click()

        # Wait for conversion result card to appear
        result_card = wait.until(EC.visibility_of_element_located((By.ID, "conversion-result")))
        assert result_card.is_displayed()

        # Check result amount (100 * 18.1250 = 1,812.50 MDL)
        result_amount = driver.find_element(By.ID, "result-amount")
        assert "1,812.50" in result_amount.text
        assert "MDL" in result_amount.text

        # Check effective rate date (04.11.2026 from fixture)
        effective_date = driver.find_element(By.ID, "effective-date")
        assert "04.11.2026" in effective_date.text

        # Check data source name
        source_name = driver.find_element(By.ID, "source-name")
        assert "National Bank of Moldova" in source_name.text

    def test_stale_result_cleared_on_input_change(self, driver, streamlit_server):
        driver.get(streamlit_server)
        wait = WebDriverWait(driver, 10)

        set_amount_and_commit(driver, "100")
        wait.until(lambda d: get_convert_button(d).is_enabled())
        get_convert_button(driver).click()

        # Result is displayed
        wait.until(EC.visibility_of_element_located((By.ID, "conversion-result")))

        # Change input amount
        set_amount_and_commit(driver, "200")

        # Stale result must be cleared!
        wait.until(lambda d: len(d.find_elements(By.ID, "conversion-result")) == 0)

    def test_swap_currencies_action(self, driver, streamlit_server):
        driver.get(streamlit_server)
        wait = WebDriverWait(driver, 10)

        swap_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Swap currencies")]'))
        )
        swap_btn.click()
        time.sleep(0.8)

        # Perform conversion with swapped currencies (MDL -> USD)
        set_amount_and_commit(driver, "1812.50")
        wait.until(lambda d: get_convert_button(d).is_enabled())

        convert_btn = get_convert_button(driver)
        convert_btn.click()

        wait.until(EC.visibility_of_element_located((By.ID, "conversion-result")))
        result_amount = driver.find_element(By.ID, "result-amount")
        # 1812.50 MDL / 18.1250 = 100.00 USD
        assert "100.00" in result_amount.text
        assert "USD" in result_amount.text
