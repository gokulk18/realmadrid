from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


def test_login():
    # Initialize the WebDriver with options to ignore SSL errors and suppress logs
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--silent')  # Suppress logging
    options.add_argument('--disable-logging')  # Disable logging
    options.add_argument('--log-level=3')  # Set log level to fatal
    driver = webdriver.Chrome(options=options)  # Ensure you have the ChromeDriver installed and in your PATH
    driver.get("http://127.0.0.1:8000/login")  # Replace with your actual login URL

    try:
        # Wait for the email input field to be present and enter the email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys("dinsjacobvarghese2025@mca.ajce.in")  # Replace with a test email

        # Locate the password input field and enter the password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("Dins@123")  # Replace with a test password

        # Click the sign-in button
        sign_in_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        sign_in_button.click()

        # Navigate to the home page after successful login
        driver.get("http://127.0.0.1:8000/")  # Load the home page
        
        print(f"Successfully logged in with email: dinsjacobvarghese2025@mca.ajce.in")  # Display the logged-in email

        print("Navigated to home page successfully!")
        time.sleep(5)

        # Step 5: Click on the news item div after logging in
        news_div = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.rounded-lg.h-64.overflow-hidden a"))  # Adjust selector to match the news div
        )
        news_div.click() 
        print("Clicked on latest news available")

    

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Wait for a few seconds to observe the result, then close the browser
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_login()
