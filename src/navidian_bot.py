# ================================================================
#  NavidianBot - Navidian CloudTime automation
# ================================================================

import os
import sys
import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ------------------------------------------------------------
#  Global Constants
# ------------------------------------------------------------
SELENIUM_GRID_URL = os.getenv("SELENIUM_GRID_URL", "http://selenoid:4444/wd/hub")
SECONDS_OFFSET_FROM_8HOURS = 60  # seconds subtracted from 8 hours

# ------------------------------------------------------------
#  Helpers
# ------------------------------------------------------------
def format_seconds(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_hms_to_seconds(text):
    h, m, s = map(int, text.split(':'))
    return h * 3600 + m * 60 + s

# ================================================================
#  Main Bot Class
# ================================================================
class NavidianBot:
    def __init__(self, user, password, telework, compensation=0, pause="y"):
        self.user = user
        self.password = password
        self.telework = telework
        self.timeToAdd = int(compensation) * 60
        self.pause_enabled = pause.lower() not in ["n", "no"]
        self.driver = self.init_driver()
        self.driver.implicitly_wait(20)

    # ------------------------------------------------------------
    #  WebDriver initialization
    # ------------------------------------------------------------
    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Remote(command_executor=SELENIUM_GRID_URL, options=options)
        driver.set_page_load_timeout(60)
        return driver

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    # ------------------------------------------------------------
    #  Safe action wrapper
    # ------------------------------------------------------------
    def safe_action(self, action_fn, description, retries=3, wait_between=10):
        for attempt in range(1, retries + 1):
            try:
                action_fn()
                return True
            except Exception:
                if attempt < retries:
                    time.sleep(wait_between)
                    self.close_driver()
                    self.driver = self.init_driver()
                    self.safe_action(self.login, "Re-login before retry")
        return False

    # ------------------------------------------------------------
    #  Wait helper
    # ------------------------------------------------------------
    def wait_for_element(self, by, value, timeout=15):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    # ------------------------------------------------------------
    #  Login
    # ------------------------------------------------------------
    def login(self):
        def _login():
            self.driver.get("https://cloudtime.navidian.net/NavidianCloudTime/xsysm0001.aspx?ReturnUrl=%2fNavidianCloudTime%2fdefault.aspx")
            self.driver.set_window_size(1920, 1040)
            WebDriverWait(self.driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            self.wait_for_element(By.ID, "UserName_TextBox").clear()
            self.wait_for_element(By.ID, "UserPass_TextBox").clear()
            self.wait_for_element(By.ID, "UserName_TextBox").send_keys(self.user)
            self.wait_for_element(By.ID, "UserPass_TextBox").send_keys(self.password)
            self.wait_for_element(By.ID, "LogonButton").click()
            WebDriverWait(self.driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
            WebDriverWait(self.driver, 20).until(EC.presence_of_all_elements_located((By.TAG_NAME, "frame")))
        self.safe_action(_login, "Login")

    # ------------------------------------------------------------
    #  Get worked / pause / remaining seconds
    # ------------------------------------------------------------
    def get_worked_seconds(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(1)
        self.wait_for_element(By.ID, "UltraWebListbar1_0_Item_2").click()
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(2)
        text = self.wait_for_element(By.ID, "lbHT").get_attribute('innerText')
        hours, minutes, seconds = map(int, text.split(':'))
        return hours * 3600 + minutes * 60 + seconds

    def get_pause_seconds(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(1)
        self.wait_for_element(By.ID, "UltraWebListbar1_0_Item_2").click()
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(2)
        text = self.wait_for_element(By.ID, "lbHP").get_attribute('innerText')
        return parse_hms_to_seconds(text)

    def get_remaining_seconds(self):
        worked_seconds = self.get_worked_seconds()
        pause_seconds = self.get_pause_seconds()
        base = max(28800 - SECONDS_OFFSET_FROM_8HOURS + self.timeToAdd - worked_seconds, 0)
        variation = random.randint(-5, 5)
        return max(base + variation, 0)

    # ------------------------------------------------------------
    #  Action buttons
    # ------------------------------------------------------------
    def mark_entry(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(1)
        self.wait_for_element(By.ID, "UltraWebListbar1_0_Item_0").click()
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(2)
        if self.telework.lower() == "y":
            self.wait_for_element(By.CSS_SELECTOR, "#teleabrir > img").click()
        self.wait_for_element(By.ID, "ndbEntrada").click()

    def mark_exit(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(2)
        exit_button = self.wait_for_element(By.ID, "ndbSalida")
        if exit_button.is_enabled():
            exit_button.click()

    def mark_pause(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(2)
        self.wait_for_element(By.ID, "ndbPausa").click()

    def mark_resume(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(2)
        self.wait_for_element(By.ID, "ndbReanudar").click()

    # ------------------------------------------------------------
    #  Main workflow
    # ------------------------------------------------------------
    def run(self):
        self.login()
        worked_seconds = self.get_worked_seconds()
        pause_seconds = self.get_pause_seconds()
        remaining_seconds = self.get_remaining_seconds()

        # Schedule pause after ~4h of work
        if self.pause_enabled:
            pause_after_seconds = max(4*3600 - worked_seconds, 0)
            time.sleep(pause_after_seconds)
            self.mark_pause()
            remaining_pause = max(random.randint(58*60, 62*60) - pause_seconds, 0)
            time.sleep(remaining_pause)
            self.mark_resume()

        # Sleep remaining effective work time
        time.sleep(remaining_seconds)
        self.mark_exit()
        self.close_driver()

# ================================================================
#  Main Execution
# ================================================================
if __name__ == "__main__":
    user = os.getenv("NAVIDIAN_USER")
    password = os.getenv("NAVIDIAN_PASSWORD")
    telework = os.getenv("NAVIDIAN_TELEWORK", "y")
    compensation = os.getenv("NAVIDIAN_COMPENSATION", 0)
    pause_opt = os.getenv("NAVIDIAN_PAUSE", "y")

    if not user or not password:
        print("NAVIDIAN_USER and NAVIDIAN_PASSWORD must be defined")
        sys.exit(1)

    bot = NavidianBot(user, password, telework, compensation, pause_opt)
    bot.run()