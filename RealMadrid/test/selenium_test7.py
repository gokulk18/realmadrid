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
        print("Navigated to home page successfully!")
        time.sleep(5)
        
        # Click on the 'Madridstas' link in the navbar
        madridstas_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Madridstas"))
        )
        madridstas_link.click()
        print("Clicked on the 'Madridstas' link successfully!")
        time.sleep(5)
        
        # Wait for player cards to load and find a player card to click
        player_card = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".player-card a"))
        )
        
        # Get player info for verification
        player_name = player_card.find_element(By.CSS_SELECTOR, "span[style*='font-size: 24px']").text
        jersey_num = player_card.find_element(By.CSS_SELECTOR, "span[style*='font-size: 29px']").text
        print(f"Selecting player: {player_name} (#{jersey_num})")
        
        # Click on the player card
        player_card.click()
        print("Clicked on player card successfully!")
        
        # Wait for player detail page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print(f"Successfully navigated to the player detail page for {player_name}")
        time.sleep(5)
        
        try:
            # Take a screenshot of the player detail page
            driver.save_screenshot("player_detail.png")
            print("Screenshot saved successfully")
        except Exception as e:
            print(f"Error taking screenshot: {e}")
        
        print("Test completed successfully - player detail page loaded")

    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Close the browser
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_login()
