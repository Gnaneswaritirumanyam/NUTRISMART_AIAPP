from pages.dashboard_page import DashboardPage

class TestNavigation:
    
    def test_navigate_to_fitness(self, driver):
        # Assumes user is already logged in or state is managed
        dashboard_page = DashboardPage(driver)
        
        dashboard_page.navigate_to_fitness()
        # Add assertion for fitness page title/element
        
    def test_navigate_to_ai_chat(self, driver):
        dashboard_page = DashboardPage(driver)
        dashboard_page.navigate_to_ai_chat()
        # Add assertion for AI chat page title/element
