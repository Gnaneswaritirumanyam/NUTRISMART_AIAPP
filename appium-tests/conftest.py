import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options

@pytest.fixture(scope="session")
def driver():
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = 'emulator-5554' # Default Android Emulator
    # Specify the path to your APK or app package/activity if already installed
    # options.app = '/path/to/your/app.apk'
    options.app_package = 'com.nutrismart.aiapp' # Replace with actual if different
    options.app_activity = '.MainActivity'
    options.automation_name = 'UiAutomator2'
    
    # Initialize the driver
    driver = webdriver.Remote('http://127.0.0.1:4723', options=options)
    
    # Wait for webview context since it's a Capacitor app
    # In real tests, you'd switch context to WEBVIEW
    # contexts = driver.contexts
    # for context in contexts:
    #     if 'WEBVIEW' in context:
    #         driver.switch_to.context(context)
    #         break
            
    yield driver
    
    # Teardown
    driver.quit()
