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
        # Click on the 'Store' link in the navbar
        store_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Tickets"))
        )
        store_link.click()
        print("Clicked on the 'Tickets' link successfully!")
        time.sleep(5)
        
        # Find and click the "Book Ticket" button for the first upcoming match
        book_ticket_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "book-ticket-btn"))
        )
        print("Found 'Book Ticket' button for the first upcoming match")
        
        # Get match details for verification
        fixture_element = book_ticket_button.find_element(By.XPATH, "./ancestor::div[contains(@class, 'fixture')]")
        match_details = fixture_element.find_element(By.XPATH, ".//p[contains(@class, 'text-2xl')]").text
        print(f"Booking ticket for match: {match_details}")
        
        # Click the Book Ticket button
        book_ticket_button.click()
        print("Clicked on 'Book Ticket' button successfully!")
        
        # Wait for the dynamic_stadium page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print(f"Successfully navigated to the dynamic stadium page")
        time.sleep(5)

         # Select up to 4 available seats
        print("Selecting available seats...")
        seats_selected = 0
        max_seats = 4
        
        # Find all available seats (not booked)
        available_seats = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".seat:not(.booked)"))
        )
        
        # Select up to 4 seats
        for seat in available_seats[:max_seats]:
            seat.click()
            seats_selected += 1
            print(f"Selected seat {seats_selected}")
            time.sleep(1)  # Brief pause between selections
        
        print(f"Successfully selected {seats_selected} seats")
        
        # Verify seats were selected by checking the total amount
        total_amount = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "total-amount"))
        )
        print(f"Total amount: ₹{total_amount.text}")
        
        # Take a screenshot of the final state with selected seats
        driver.save_screenshot("seats_selected.png")
        print("Test completed successfully - seats have been selected")
        
        # Optional: Get details of the selected seats from the UI
        selected_seats_elements = driver.find_elements(By.CSS_SELECTOR, "#selected-seats li")
        if selected_seats_elements:
            print("Selected seat details:")
            for seat_element in selected_seats_elements:
                print(f"  - {seat_element.text}")

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    test_login()
