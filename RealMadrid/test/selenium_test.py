from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def test_login():
    # Initialize the WebDriver
    driver = webdriver.Chrome()  # Ensure you have the ChromeDriver installed and in your PATH
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
        # Click on the 'Store' link in the navbar
        store_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Store"))
        )
        store_link.click()
        print("Clicked on the 'Store' link successfully!")
        time.sleep(5)

        # Wait for the product page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "p-4"))  # Adjust the class name as needed
        )

        # Click on the first product card in the store
        product_card = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".grid > div:first-child a"))  # Adjust the selector as needed
        )
        product_card.click()
        print("Clicked on the product card successfully!")
        time.sleep(5)

        # Wait for the 'Add to Wishlist' button to be clickable and click it
        add_to_wishlist_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'bg-yellow-400')]"))
        )
        add_to_wishlist_button.click()
        print("Clicked on the 'Add to Wishlist' button successfully!")
        time.sleep(5)




        

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    test_login()
