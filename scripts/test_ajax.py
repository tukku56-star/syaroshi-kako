import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_ajax():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,800")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Login
        driver.get("https://drrrkari.com/")
        time.sleep(2)
        driver.find_element(By.NAME, "name").send_keys("AjaxTester")
        driver.find_element(By.CSS_SELECTOR, "a.bb.cc").click()
        time.sleep(3)
        
        # Enter Room
        rooms = driver.find_elements(By.CSS_SELECTOR, "ul.rooms")
        entered = False
        for ul in rooms:
            if ul.is_displayed() and not ul.find_elements(By.CLASS_NAME, "full"):
                ul.find_element(By.NAME, "login").click()
                entered = True
                break
        
        if not entered:
            print("No room found")
            return

        time.sleep(5) # Wait for room load
        
        # Hook into jQuery ajax
        script = """
        var callback = arguments[arguments.length - 1];
        
        // Intercept jQuery ajax
        var originalAjax = $.ajax;
        $.ajax = function(settings) {
            if (settings.url && settings.url.indexOf('ajax.php') !== -1) {
                callback("Intercepted ajax.php request: " + JSON.stringify(settings));
                // Restore original to let the page continue (optional, but we just want one)
                $.ajax = originalAjax; 
            }
            return originalAjax.apply(this, arguments);
        };
        
        // Wait for the next poll (usually every few seconds)
        setTimeout(function() {
            // If no request intercepted after 10 seconds, return timeout
            // But we can't easily check if callback was called.
            // So we just rely on the interception calling callback.
        }, 10000);
        """
        
        print("Hooking jQuery.ajax...")
        response = driver.execute_async_script(script)
        print("Hook result:")
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_ajax()
