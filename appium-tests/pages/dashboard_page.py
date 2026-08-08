from appium.webdriver.common.appiumby import AppiumBy
from .base_page import BasePage

class DashboardPage(BasePage):
    DASHBOARD_TITLE = (AppiumBy.ID, "dashboardTitle")
    NAV_MENU = (AppiumBy.ID, "navMenu")
    AI_CHAT_BTN = (AppiumBy.ID, "aiChatNav")
    FITNESS_BTN = (AppiumBy.ID, "fitnessNav")

    def __init__(self, driver):
        super().__init__(driver)

    def is_dashboard_loaded(self):
        return self.is_visible(self.DASHBOARD_TITLE)

    def navigate_to_ai_chat(self):
        self.click(self.AI_CHAT_BTN)

    def navigate_to_fitness(self):
        self.click(self.FITNESS_BTN)
