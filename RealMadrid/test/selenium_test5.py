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
            EC.element_to_be_clickable((By.LINK_TEXT, "Game Zone"))
        )
        store_link.click()
        print("Clicked on the 'Game Zone' link successfully!")
        time.sleep(5)
        
        # Find and click the "Play Now" button for Quiz
        play_now_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Play Now')]"))
        )
        play_now_button.click()
        print("Clicked on the 'Play Now' button successfully!")
        time.sleep(5)
        
        # Verify we're on the Quiz page
        quiz_title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h2"))
        )
        print(f"Navigated to Quiz page: {quiz_title.text}")
        
        # Continue answering questions until the quiz is complete
        quiz_complete = False
        question_count = 1
        
        while not quiz_complete:
            try:
                # Wait for quiz options to be present
                options = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "quiz-option"))
                )
                
                # Get the current question text
                question_text = driver.find_element(By.ID, "question").text
                print(f"Question {question_count}: {question_text}")
                
                # Select a random option
                import random
                random_option = random.choice(options)
                print(f"Selected option: {random_option.text}")
                random_option.click()
                
                # Wait for 5 seconds after selecting an option (as per the quiz's behavior)
                time.sleep(5)
                
                # Check if the quiz is complete by looking for the score modal
                try:
                    score_modal = WebDriverWait(driver, 2).until(
                        EC.visibility_of_element_located((By.ID, "score-modal"))
                    )
                    final_score = driver.find_element(By.ID, "final-score").text
                    print(f"Quiz completed! {final_score}")
                    
                    # Click the OK button to return to the Game Zone
                    ok_button = driver.find_element(By.XPATH, "//button[contains(text(), 'OK')]")
                    ok_button.click()
                    print("Clicked OK to return to Game Zone")
                    quiz_complete = True
                    
                except TimeoutException:
                    # Quiz is not complete yet, continue to the next question
                    question_count += 1
                    print(f"Moving to question {question_count}")
                    
            except TimeoutException:
                print("Could not find quiz options or quiz has ended")
                quiz_complete = True

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    test_login()
