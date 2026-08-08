from appium.webdriver.common.appiumby import AppiumBy
from .base_page import BasePage

class LoginPage(BasePage):
    # Selectors for the webview content (assuming HTML IDs)
    EMAIL_INPUT = (AppiumBy.ID, "email")
    PASSWORD_INPUT = (AppiumBy.ID, "password")
    LOGIN_BUTTON = (AppiumBy.ID, "loginBtn")
    ERROR_MESSAGE = (AppiumBy.ID, "errorMessage")

    def __init__(self, driver):
        super().__init__(driver)

    def login(self, email, password):
        self.type_text(self.EMAIL_INPUT, email)
        self.type_text(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)

    def is_error_message_visible(self):
        return self.is_visible(self.ERROR_MESSAGE)
