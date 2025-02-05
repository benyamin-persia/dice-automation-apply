import os                          # Provides functions for file and directory operations.
import getpass                     # Provides a secure way to prompt for a password without echoing.
import time                        # Provides time-related functions (e.g., sleep).
import pandas as pd                # Used for data manipulation and exporting data to Excel.
from selenium import webdriver     # Allows control of a web browser via Selenium.
from selenium.webdriver.common.by import By        # Provides strategies to locate elements (e.g., by name, xpath).
from selenium.webdriver.common.keys import Keys    # Enables sending keyboard keys (like ENTER) to elements.
from selenium.webdriver.support.ui import WebDriverWait  # Enables explicit waits until a condition is met.
from selenium.webdriver.support import expected_conditions as EC  # Provides conditions to use with explicit waits.

# =============================================================================
# Step 1: Credential Handling
# =============================================================================
# Determine the directory in which the current script resides.
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define the path for a credentials file to store/retrieve the username and password.
creds_file = os.path.join(script_directory, "credentials.txt")

# Check if the credentials file exists.
if os.path.exists(creds_file):
    # Open and read the credentials file.
    with open(creds_file, "r") as f:
        lines = f.read().splitlines()
        # Expect the first two lines to be the saved username and password.
        if len(lines) >= 2:
            saved_username = lines[0]
            saved_password = lines[1]
        else:
            saved_username = None
            saved_password = None
    # Ask the user if they want to use the saved credentials.
    use_saved = input("Found saved credentials. Use them? (Y/n): ").strip().lower() or "y"
    if use_saved.startswith("y") and saved_username and saved_password:
        username = saved_username
        password = saved_password
    else:
        # Prompt for new credentials if the user chooses not to use the saved ones.
        username = input("Enter your username (email): ")
        password = getpass.getpass("Enter your password: ")
        # Save these new credentials to the file for future use.
        with open(creds_file, "w") as f:
            f.write(username + "\n")
            f.write(password + "\n")
else:
    # If no credentials file exists, prompt the user and save the credentials.
    username = input("Enter your username (email): ")
    password = getpass.getpass("Enter your password: ")
    with open(creds_file, "w") as f:
        f.write(username + "\n")
        f.write(password + "\n")

# =============================================================================
# Step 2: Prompt for Job Title
# =============================================================================
# Ask the user for the job title they want to search for.
# If the user enters nothing, default to "QA tester".
job_title = input("Enter the job title, if left blank, default to QA tester: ").strip()
if not job_title:
    job_title = "QA tester"

# =============================================================================
# Step 3: Prompt for Filter Options
# =============================================================================
# --- Posted Date Filter ---
# Display options for the posted date filter.
print("Select posted date filter:")
print(" 0. 0 Any date")
print(" 1. 1 Today")
print(" 3. 3 Last days")
print(" 7. 7 Last days")
# Prompt the user to choose a filter by entering a number.
posted_date_input = input("Enter choice number (0, 1, 3 or 7): ").strip()

# Map the user's numeric input to the corresponding value used in the URL query.
posted_date_map = {
    "0": "zero",   # No date restriction.
    "1": "ONE",    # Jobs posted in the last 1 day.
    "3": "THREE",  # Jobs posted in the last 3 days.
    "7": "SEVEN"   # Jobs posted in the last 7 days.
}
# Validate the user input; if invalid, default to "ONE".
if posted_date_input in posted_date_map:
    posted_date_value = posted_date_map[posted_date_input]
else:
    print("Invalid choice; defaulting to 1 day (ONE).")
    posted_date_value = "ONE"

# --- Employment Type Filter ---
# Define available employment types with numeric keys.
employment_map = {
    "1": "FULLTIME",
    "2": "PARTTIME",
    "3": "CONTRACTS",
    "4": "THIRD_PARTY"
}
print("\nSelect employment type(s) (enter comma-separated numbers).")
print("If you do not select any, all types will be selected by default:")
# Display each employment type option.
for key, value in employment_map.items():
    print(f" {key}. {value}")
# Prompt the user for input.
employment_input = input("Your choice (leave blank for all): ").strip()
if employment_input:
    # Process the input: split by commas and remove extra spaces.
    selected_keys = [x.strip() for x in employment_input.split(",")]
    # Map the selected keys to their corresponding employment type values.
    emp_types_list = [employment_map[k] for k in selected_keys if k in employment_map]
    # If no valid keys were selected, default to all.
    if not emp_types_list:
        print("No valid employment types selected; defaulting to all.")
        emp_types_list = list(employment_map.values())
else:
    # If input is blank, select all employment types.
    emp_types_list = list(employment_map.values())
# Join the employment type values with URL-encoded vertical bars (%7C) for use in the query string.
employment_type_value = "%7C".join(emp_types_list)

# ---------------- EasyApply Filter ----------------
# This filter is appended to the URL to show jobs that have an "easy apply" option.
easy_apply_filter = "&filters.easyApply=true"

# --- Work Settings Filter ---
# Define available work settings.
work_settings_map = {
    "1": "On-Site",
    "2": "Hybrid",
    "3": "Remote"
}
print("\nSelect work setting(s) (enter comma-separated numbers):")
# Display each work setting option.
for key, value in work_settings_map.items():
    print(f" {key}. {value}")
# Prompt the user for work setting choices.
work_settings_input = input("Your choice (leave blank for none): ").strip()
if work_settings_input:
    # Process the input similarly to employment types.
    selected_ws_keys = [x.strip() for x in work_settings_input.split(",")]
    work_settings_list = [work_settings_map[k] for k in selected_ws_keys if k in work_settings_map]
    if work_settings_list:
        work_settings_value = "%7C".join(work_settings_list)
    else:
        work_settings_value = ""
else:
    work_settings_value = ""

# =============================================================================
# Step 4: Set Up Selenium and Log In
# =============================================================================
# Initialize the Chrome WebDriver (ensure that chromedriver is accessible in PATH).
driver = webdriver.Chrome()
# Navigate to the Dice login page.
driver.get("https://www.dice.com/dashboard/login")
# Create an explicit wait object with a 20-second timeout.
wait = WebDriverWait(driver, 20)

# Log in by waiting for and interacting with the email input.
email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
email_field.send_keys(username)
email_field.send_keys(Keys.ENTER)

# Wait for the password input, then enter the password.
password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
password_field.send_keys(password)
password_field.send_keys(Keys.ENTER)

# Confirm successful login by waiting for a known element on the dashboard.
try:
    dashboard = wait.until(EC.presence_of_element_located((By.ID, "dashboard-container")))
    print("Login successful!")
except Exception as e:
    print("Login may have failed or the dashboard did not load as expected.", e)

# =============================================================================
# Step 5: Build the Base Filtered Jobs URL
# =============================================================================
# Define the base URL for job searches on Dice.
base_url = "https://www.dice.com/jobs"
# URL-encode the job title (replace spaces with %20).
q_value = job_title.replace(" ", "%20")
# Construct the URL parameters by concatenating query strings for each filter.
url_params = (
    f"?q={q_value}" +
    "&countryCode=US" +
    "&radius=30" +
    "&radiusUnit=mi" +
    "&pageSize=1000" +  # Retrieve a large number of jobs per page.
    f"&filters.postedDate={posted_date_value}" +
    f"&filters.employmentType={employment_type_value}" +
    f"{easy_apply_filter}" +
    "&language=en"
)
# Append work settings filter if the user provided any.
if work_settings_value:
    url_params += f"&filters.workplaceTypes={work_settings_value}"

# Print the complete base URL (without the page parameter) for debugging purposes.
print("\nBase URL with filters (without page number):")
print(base_url + url_params)

# =============================================================================
# Step 6: Traverse Pages and Build Job Detail Links
# =============================================================================
# Define keywords for filtering job titles (all in lowercase).
keywords = [
    "quality assurance",
    "software testing",
    "test automation",
    "manual testing",
    "agile methodologies",
    "scrum",
    "regression testing",
    "functional testing",
    "performance testing",
    "user acceptance testing",
    "test cases",
    "defect tracking",
    "bug reporting",
    "selenium",
    "continuous integration",
    "exploratory testing",
    "test documentation",
    "test strategy",
    "web automation"
]

job_detail_links = []   # List to store job detail URLs that match the keywords.
page = 1                # Initialize pagination at page 1.

# Loop through pages until no job cards are found.
while True:
    # Construct the current page URL by adding the page number parameter.
    current_url = f"{base_url}{url_params}&page={page}"
    print(f"\nNavigating to page {page}:")
    print(current_url)
    try:
        driver.get(current_url)
    except Exception as e:
        print(f"Error navigating to page {page}: {e}")
        break
    time.sleep(3)  # Allow time for the page to load.
    
    # Locate job card elements using the CSS selector that identifies them.
    job_cards = driver.find_elements(By.CSS_SELECTOR, 'a[data-cy="card-title-link"]')
    
    # If no job cards are found, exit the loop (assume no more pages).
    if not job_cards:
        print("No job cards found on this page. Ending pagination.")
        break
    
    print(f"Found {len(job_cards)} job card(s) on page {page}.")
    
    # Process each job card on the current page.
    for card in job_cards:
        # Extract the visible text (job title) and convert it to lowercase for comparison.
        job_text = card.text.lower()
        # Check if any of the keywords exist in the job title.
        if any(keyword in job_text for keyword in keywords):
            # If a match is found, get the job card's id attribute.
            job_id = card.get_attribute("id")
            if job_id:
                # Construct the full job detail URL using the job id.
                job_detail_url = f"https://www.dice.com/job-detail/{job_id}"
                job_detail_links.append(job_detail_url)
    
    page += 1  # Increment the page number to navigate to the next page.

print(f"\nTotal job detail links extracted (matching keywords): {len(job_detail_links)}")

# =============================================================================
# Step 7: Ask for Application Mode
# =============================================================================
# Prompt the user to select whether to Auto Apply or use Supervised mode.
print("\nSelect application mode:")
print(" 1. Auto Apply")
print(" 2. Supervised")
apply_mode = input("Enter 1 for Auto Apply or 2 for Supervised: ").strip()

# =============================================================================
# Step 7.5: Load Record of Already Applied Jobs
# =============================================================================
# Define a file to keep track of job links that have already been processed.
applied_jobs_file = os.path.join(script_directory, "applied_jobs.txt")
# Load previously applied job links into a set to avoid duplicate applications.
applied_jobs = set()
if os.path.exists(applied_jobs_file):
    with open(applied_jobs_file, "r") as f:
        for line in f:
            applied_jobs.add(line.strip())

# =============================================================================
# Step 8: Process Each Job Detail Link (Evaluate and Apply)
# =============================================================================
# Prepare a list to store detailed information for each job (for reporting and Excel export).
detailed_job_data = []

# Loop over each job detail link.
for index, link in enumerate(job_detail_links, start=1):
    # Skip the job if it has already been processed.
    if link in applied_jobs:
        print(f"\nSkipping already applied job {index}: {link}")
        continue

    print(f"\nVisiting job detail page {index}/{len(job_detail_links)}: {link}")
    try:
        driver.get(link)
    except Exception as e:
        print(f"Error navigating to job detail page {link}: {e}")
        break
    time.sleep(2)  # Allow the page to load.
    
    # Initialize variables to hold the job title and skills information.
    job_title_text = ""
    skills_text = ""
    
    # Retrieve the job title from the specified <h1> element.
    try:
        title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-cy='jobTitle']")))
        job_title_text = title_element.text.strip()
    except Exception as e:
        print(f"Error retrieving job title for {link}: {e}")
    
    # Retrieve the skills from the container element that holds them.
    try:
        skills_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-cy='skillsList']")))
        # Get all <span> elements within the skills container.
        skill_spans = skills_container.find_elements(By.TAG_NAME, "span")
        # Build a list of skill names.
        skills_list = [span.text.strip() for span in skill_spans if span.text.strip()]
        # Join the skills into a single comma-separated string.
        skills_text = ", ".join(skills_list)
    except Exception as e:
        print(f"Error retrieving skills for {link}: {e}")
    
    # Decide whether to apply for this job based on the chosen application mode.
    apply_job = False
    if apply_mode == "1":  # Auto Apply mode.
        apply_job = True
        print(f"Auto applying to: {job_title_text}")
    elif apply_mode == "2":  # Supervised mode.
        # Display the job title and ask the user for a decision.
        user_choice = input(f"Do you want to apply for '{job_title_text}'? (Y/n): ").strip().lower() or "y"
        if user_choice.startswith("y"):
            apply_job = True
        else:
            apply_job = False
            print("Skipping this job.")
    else:
        print("Invalid application mode selected; skipping application process for this job.")
    
    # If the decision is to apply, perform the necessary click actions.
    if apply_job:
        try:
            # Wait for and click the "Apply now" button.
            apply_now_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Apply now')]")))
            apply_now_button.click()
            print("Clicked 'Apply now'.")
            time.sleep(2)  # Wait for the application page to load.
            
            # Wait for and click the "Submit" button to finalize the application.
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]")))
            submit_button.click()
            print("Clicked 'Submit' to finalize the application.")
            time.sleep(2)  # Allow time for the submission to complete.
        except Exception as e:
            print(f"Error during application process for {link}: {e}")
    
    # Mark this job as processed by adding its link to the applied_jobs set.
    applied_jobs.add(link)
    
    # Append the job's detailed information and the application status.
    detailed_job_data.append({
        "Job Detail Link": link,
        "Job Title": job_title_text,
        "Skills": skills_text,
        "Applied": "Yes" if apply_job else "No"
    })
    
    # Update the applied jobs file after processing each job.
    with open(applied_jobs_file, "w") as f:
        for job in applied_jobs:
            f.write(job + "\n")

# =============================================================================
# Step 9: Save Detailed Job Information to an Excel File
# =============================================================================
# Define the path for the Excel output file (saved in the same directory as the script).
excel_filename = os.path.join(script_directory, "dice_job_links.xlsx")
# Create a pandas DataFrame from the collected detailed job data.
df = pd.DataFrame(detailed_job_data, columns=["Job Detail Link", "Job Title", "Skills", "Applied"])
# Write the DataFrame to an Excel file (using openpyxl as the engine).
df.to_excel(excel_filename, index=False)
print(f"\nDetailed job information has been saved to {excel_filename}.")

# =============================================================================
# Step 10: Cleanup
# =============================================================================
# Wait for final user input before closing the browser.
input("Press Enter to exit and close the browser...")
driver.quit()  # Close the Selenium browser and end the session.
