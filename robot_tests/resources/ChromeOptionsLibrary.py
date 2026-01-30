"""Custom Robot Framework library for Chrome Options"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ChromeOptionsLibrary:
    """Library to create Chrome options with proper arguments"""

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def get_headless_chrome_options(self):
        """Returns Chrome options configured for headless mode"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--remote-debugging-port=9222')
        return options

    def get_visible_chrome_options(self):
        """Returns Chrome options for visible browser (non-headless) for video recording"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--force-device-scale-factor=1')
        # Disable automation flags for cleaner recording
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        return options
