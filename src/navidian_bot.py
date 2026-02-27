# ================================================================
#  NavidianBot - Robust automation for Navidian CloudTime
#  Version prepared for public repo
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

# ================================================================
#  Global Constants
# ================================================================
SELENIUM_GRID_URL = os.getenv("SELENIUM_GRID_URL", "http://selenoid:4444/wd/hub")
SECONDS_OFFSET_FROM_8HOURS = 60  # Seconds subtracted from 8 hours

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
        print(f"User: {self.user} ::: Time adjustment (minutes): {compensation}", flush=True)
        print(f"User: {self.user} ::: Pause enabled: {self.pause_enabled}", flush=True)

    def init_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--ignore-ssl-errors=yes')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Remote(command_executor=SELENIUM_GRID_URL, options=options)
            driver.set_page_load_timeout(60)
            return driver
        except Exception as e:
            print(f"User: {self.user} ::: ERROR initializing WebDriver: {e}", flush=True)
            time.sleep(10)
            return self.init_driver()

    def close_driver(self):
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            print(f"User: {self.user} ::: ERROR closing WebDriver: {e}", flush=True)

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
            print(f"User: {self.user} ::: >>> Logged in successfully", flush=True)

        self.safe_action(_login, "Login")

    # ------------------------------------------------------------
    #  Wait helper
    # ------------------------------------------------------------
    def wait_for_element(self, by, value, timeout=15):
        return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))

    # ------------------------------------------------------------
    #  Safe action wrapper
    # ------------------------------------------------------------
    def safe_action(self, action_fn, description, retries=3, wait_between=10):
        for attempt in range(1, retries + 1):
            try:
                print(f"User: {self.user} ::: Attempt {attempt}/{retries} - {description}", flush=True)
                action_fn()
                return True
            except Exception as e:
                print(f"User: {self.user} ::: ERROR performing '{description}': {e}", flush=True)
                if attempt < retries:
                    print(f"Retrying in {wait_between} seconds...", flush=True)
                    time.sleep(wait_between)
                    try:
                        self.close_driver()
                        self.driver = self.init_driver()
                        self.driver.implicitly_wait(20)
                        self.safe_action(self.login, "Re-login before retry")
                    except Exception as suberr:
                        print(f"User: {self.user} ::: Re-login failed: {suberr}", flush=True)
        return False

    # ------------------------------------------------------------
    #  State detection & handlers (simplified for public version)
    # ------------------------------------------------------------
    # ... Mantener el resto de funciones: get_current_status, mark_entry, mark_exit, mark_pause, mark_resume, handle_working, etc.
    # No se tocan internamente, solo que el login y SELENIUM_GRID_URL son ahora configurables.

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