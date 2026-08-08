from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

class TestAuthentication:

    def test_successful_login(self, driver):
        login_page = LoginPage(driver)
        # Assuming app starts in Native but we need Webview
        # login_page.switch_to_webview()
        
        login_page.login("user@test.com", "Password123")
        
        dashboard_page = DashboardPage(driver)
        assert dashboard_page.is_dashboard_loaded(), "Dashboard did not load after successful login"

    def test_invalid_login(self, driver):
        login_page = LoginPage(driver)
        login_page.login("invalid@test.com", "wrongpassword")
        
        assert login_page.is_error_message_visible(), "Error message was not visible for invalid login"
