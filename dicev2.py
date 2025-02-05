import os                          # For file and directory operations.
import getpass                     # For secure password input.
import time                        # For sleep/delays.
import pandas as pd                # For creating and saving the Excel file.
from selenium import webdriver     # To control the browser.
from selenium.webdriver.common.by import By        # To locate elements.
from selenium.webdriver.common.keys import Keys    # To simulate key presses (like ENTER).
from selenium.webdriver.support.ui import WebDriverWait  # For explicit waiting.
from selenium.webdriver.support import expected_conditions as EC  # For expected conditions in waits.

# -------------------- Credential Handling --------------------
# Determine the directory where this script is located.
script_directory = os.path.dirname(os.path.abspath(__file__))
# Define the credentials file path.
creds_file = os.path.join(script_directory, "credentials.txt")

# Check if a credentials file exists and read credentials if it does.
if os.path.exists(creds_file):
    with open(creds_file, "r") as f:
        lines = f.read().splitlines()
        if len(lines) >= 2:
            saved_username = lines[0]
            saved_password = lines[1]
        else:
            saved_username = None
            saved_password = None
    # Ask the user whether to use the saved credentials.
    use_saved = input("Found saved credentials. Use them? (Y/n): ").strip().lower() or "y"
    if use_saved.startswith("y") and saved_username and saved_password:
        username = saved_username
        password = saved_password
    else:
        username = input("Enter your username (email): ")
        password = getpass.getpass("Enter your password: ")
        # Save the new credentials.
        with open(creds_file, "w") as f:
            f.write(username + "\n")
            f.write(password + "\n")
else:
    # If no credentials file exists, prompt the user and save credentials.
    username = input("Enter your username (email): ")
    password = getpass.getpass("Enter your password: ")
    with open(creds_file, "w") as f:
        f.write(username + "\n")
        f.write(password + "\n")

# -------------------- Step 0: Prompt for Job Title --------------------
# Ask the user for the job title; if left blank, default to "QA tester".
job_title = input("Enter the job title, if left blank, default to QA tester: ").strip()
if not job_title:
    job_title = "QA tester"  # Default value.

# -------------------- Step 1: Prompt for Filter Options --------------------
# --- Posted Date Filter ---
print("Select posted date filter:")
print(" 0. 0 Any date")
print(" 1. 1 Today")
print(" 3. 3 Last days")
print(" 7. 7 Last days")
posted_date_input = input("Enter choice number (0, 1, 3 or 7): ").strip()
# Map the choice to the value used by Dice.
posted_date_map = {
    "0": "zero",   # 0 days.
    "1": "ONE",    # 1 day.
    "3": "THREE",  # 3 days.
    "7": "SEVEN"   # 7 days.
}
if posted_date_input in posted_date_map:
    posted_date_value = posted_date_map[posted_date_input]
else:
    print("Invalid choice; defaulting to 1 day (ONE).")
    posted_date_value = "ONE"

# --- Employment Type Filter ---
employment_map = {
    "1": "FULLTIME",
    "2": "PARTTIME",
    "3": "CONTRACTS",
    "4": "THIRD_PARTY"
}
print("\nSelect employment type(s) (enter comma-separated numbers).")
print("If you do not select any, all types will be selected by default:")
for key, value in employment_map.items():
    print(f" {key}. {value}")
employment_input = input("Your choice (leave blank for all): ").strip()
if employment_input:
    selected_keys = [x.strip() for x in employment_input.split(",")]
    emp_types_list = [employment_map[k] for k in selected_keys if k in employment_map]
    if not emp_types_list:
        print("No valid employment types selected; defaulting to all.")
        emp_types_list = list(employment_map.values())
else:
    emp_types_list = list(employment_map.values())
# Join the employment types with URL-encoded vertical bar (%7C).
employment_type_value = "%7C".join(emp_types_list)

# ---------------- Add the easyApply filter after employment type ----------------
easy_apply_filter = "&filters.easyApply=true"

# --- Work Settings Filter ---
work_settings_map = {
    "1": "On-Site",
    "2": "Hybrid",
    "3": "Remote"
}
print("\nSelect work setting(s) (enter comma-separated numbers):")
for key, value in work_settings_map.items():
    print(f" {key}. {value}")
work_settings_input = input("Your choice (leave blank for none): ").strip()
if work_settings_input:
    selected_ws_keys = [x.strip() for x in work_settings_input.split(",")]
    work_settings_list = [work_settings_map[k] for k in selected_ws_keys if k in work_settings_map]
    if work_settings_list:
        work_settings_value = "%7C".join(work_settings_list)
    else:
        work_settings_value = ""
else:
    work_settings_value = ""

# -------------------- Step 2: Set Up Selenium and Log In --------------------
driver = webdriver.Chrome()  # Ensure chromedriver is in your PATH.
driver.get("https://www.dice.com/dashboard/login")
wait = WebDriverWait(driver, 20)

# Login process: enter username then password.
email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
email_field.send_keys(username)
email_field.send_keys(Keys.ENTER)

password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
password_field.send_keys(password)
password_field.send_keys(Keys.ENTER)

# Confirm login by waiting for a known dashboard element.
try:
    dashboard = wait.until(EC.presence_of_element_located((By.ID, "dashboard-container")))
    print("Login successful!")
except Exception as e:
    print("Login may have failed or the dashboard did not load as expected.", e)

# -------------------- Step 3: Build the Base Filtered Jobs URL --------------------
base_url = "https://www.dice.com/jobs"
q_value = job_title.replace(" ", "%20")  # URL-encode spaces.
url_params = (
    f"?q={q_value}"
    "&countryCode=US"
    "&radius=30"
    "&radiusUnit=mi"
    "&pageSize=1000"  # Retrieve many jobs per page.
    f"&filters.postedDate={posted_date_value}"
    f"&filters.employmentType={employment_type_value}"
    f"{easy_apply_filter}"
    "&language=en"
)
if work_settings_value:
    url_params += f"&filters.workplaceTypes={work_settings_value}"

print("\nBase URL with filters (without page number):")
print(base_url + url_params)

# -------------------- Step 4: Traverse Pages, Filter by Keywords, and Build Job Detail Links --------------------
# Define keywords (in lowercase) for filtering job titles.
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

job_detail_links = []   # To store the URLs of matching job postings.
page = 1                # Start from page 1.

while True:
    # Construct URL for the current page.
    current_url = f"{base_url}{url_params}&page={page}"
    print(f"\nNavigating to page {page}:")
    print(current_url)
    try:
        driver.get(current_url)
    except Exception as e:
        print(f"Error navigating to page {page}: {e}")
        break
    time.sleep(3)  # Wait for the page to load.
    
    # Find all job cards using the CSS selector.
    job_cards = driver.find_elements(By.CSS_SELECTOR, 'a[data-cy="card-title-link"]')
    
    # If no job cards are found, assume there are no more pages.
    if not job_cards:
        print("No job cards found on this page. Ending pagination.")
        break
    
    print(f"Found {len(job_cards)} job card(s) on page {page}.")
    
    # Iterate over each job card.
    for card in job_cards:
        # Extract the job title text and convert to lowercase.
        job_text = card.text.lower()
        # Check if any keyword exists in the job title.
        if any(keyword in job_text for keyword in keywords):
            # If matched, extract the job card's id.
            job_id = card.get_attribute("id")
            if job_id:
                job_detail_url = f"https://www.dice.com/job-detail/{job_id}"
                job_detail_links.append(job_detail_url)
    
    page += 1  # Go to the next page.

print(f"\nTotal job detail links extracted (matching keywords): {len(job_detail_links)}")

# -------------------- Step 5: Ask Application Mode --------------------
# Prompt the user to select application mode.
print("\nSelect application mode:")
print(" 1. Auto Apply")
print(" 2. Supervised")
apply_mode = input("Enter 1 for Auto Apply or 2 for Supervised: ").strip()

# -------------------- Step 5.5: Load Already Applied Jobs Record --------------------
# Define the file path to store applied job links.
applied_jobs_file = os.path.join(script_directory, "applied_jobs.txt")
# Load previously applied job links into a set.
applied_jobs = set()
if os.path.exists(applied_jobs_file):
    with open(applied_jobs_file, "r") as f:
        for line in f:
            applied_jobs.add(line.strip())

# -------------------- Step 6: Visit Each Job Link, Evaluate, and Apply --------------------
# Prepare a list to store dictionaries for each job with detailed information.
detailed_job_data = []

# Loop over each job detail link.
for index, link in enumerate(job_detail_links, start=1):
    # Check if we have already applied for this job.
    if link in applied_jobs:
        print(f"\nSkipping already applied job {index}: {link}")
        continue

    print(f"\nVisiting job detail page {index}/{len(job_detail_links)}: {link}")
    try:
        driver.get(link)
    except Exception as e:
        print(f"Error navigating to job detail page {link}: {e}")
        break
    time.sleep(2)  # Wait for the page to load.
    
    # Initialize empty fields.
    job_title_text = ""
    skills_text = ""
    
    try:
        # Extract the job title from the <h1> element with data-cy="jobTitle".
        title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-cy='jobTitle']")))
        job_title_text = title_element.text.strip()
    except Exception as e:
        print(f"Error retrieving job title for {link}: {e}")
    
    try:
        # Extract skills from the container with data-cy="skillsList".
        skills_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-cy='skillsList']")))
        # Find all <span> elements within the skills container.
        skill_spans = skills_container.find_elements(By.TAG_NAME, "span")
        skills_list = [span.text.strip() for span in skill_spans if span.text.strip()]
        skills_text = ", ".join(skills_list)
    except Exception as e:
        print(f"Error retrieving skills for {link}: {e}")
    
    # Determine whether to apply based on the chosen application mode.
    apply_job = False
    if apply_mode == "1":  # Auto Apply mode.
        apply_job = True
        print(f"Auto applying to: {job_title_text}")
    elif apply_mode == "2":  # Supervised mode.
        # Show the job title and ask the user if they want to apply.
        user_choice = input(f"Do you want to apply for '{job_title_text}'? (Y/n): ").strip().lower() or "y"
        if user_choice.startswith("y"):
            apply_job = True
        else:
            apply_job = False
            print("Skipping this job.")
    else:
        print("Invalid application mode selected; skipping application process for this job.")
    
    # If the decision is to apply, perform the click actions.
    if apply_job:
        try:
            # Click the "Apply now" button.
            apply_now_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Apply now')]")))
            apply_now_button.click()
            print("Clicked 'Apply now'.")
            time.sleep(2)  # Wait for the application page to load.
            
            # Click the "Submit" button on the application page.
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]")))
            submit_button.click()
            print("Clicked 'Submit' to finalize the application.")
            time.sleep(2)  # Wait for submission to complete.
        except Exception as e:
            print(f"Error during application process for {link}: {e}")
    
    # Record that we have processed (applied or skipped) this job.
    applied_jobs.add(link)
    
    # Append the extracted job information and the application outcome.
    detailed_job_data.append({
        "Job Detail Link": link,
        "Job Title": job_title_text,
        "Skills": skills_text,
        "Applied": "Yes" if apply_job else "No"
    })

    # Update the applied jobs file after each processed job.
    with open(applied_jobs_file, "w") as f:
        for job in applied_jobs:
            f.write(job + "\n")

# -------------------- Step 7: Save the Detailed Information to an Excel File --------------------
excel_filename = os.path.join(script_directory, "dice_job_links.xlsx")
df = pd.DataFrame(detailed_job_data, columns=["Job Detail Link", "Job Title", "Skills", "Applied"])
df.to_excel(excel_filename, index=False)
print(f"\nDetailed job information has been saved to {excel_filename}.")

# Wait for user input before closing the browser.
input("Press Enter to exit and close the browser...")
driver.quit()  # Close the Selenium browser.
