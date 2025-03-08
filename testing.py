import requests, os
import pandas as pd
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
api_key = os.getenv("API_KEY")
if api_key:
    print("API KEY loaded securely :D")

url = "https://api.itjobs.pt/job/list.json"
data = {
    "api_key": api_key  # API key loaded from environment variable
}

# Adding headers to simulate a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

# Send request to API
response = requests.post(url, headers=headers, data=data)

# Check if the response is successful
if response.status_code == 200:
    result = response.json()
    
    # Extract job listings
    job_listings = result['results']
    
    # Prepare a list to store each job's data
    jobs_data = []
    
    for job in job_listings:
        # Safely get the job types if they exist, otherwise set to an empty list
        job_types = ", ".join([type["name"] for type in job.get("types", [])])
        
        # Safely get the locations if they exist, otherwise set to an empty list
        locations = ", ".join([location["name"] for location in job.get("locations", [])])
        
        # Safely get the company phone, if it exists, otherwise set to None
        company_phone = job["company"].get("phone", None)
        
        # Safely get the company email, if it exists, otherwise set to None
        company_email = job["company"].get("email", None)
        
        # Safely get the company address, if it exists, otherwise set to None
        company_address = job["company"].get("address", None)
        
        job_data = {
            "Job ID": job["id"],
            "Company ID": job["company"]["id"],
            "Company Name": job["company"]["name"],
            "Company Logo": job["company"]["logo"],
            "Company Address": company_address,  # Safely accessed
            "Company Phone": company_phone,  # Safely accessed
            "Company Email": company_email,  # Safely accessed
            "Company URL": job["company"]["url"],
            "Job Title": job["title"],
            "Job Body": job["body"],
            "Job Reference": job["ref"],
            "Wage": job["wage"],
            "Job Types": job_types,
            "Locations": locations,
            "Published At": job["publishedAt"],
            "Updated At": job["updatedAt"],
            "Slug": job["slug"]
        }
        jobs_data.append(job_data)
    
    # Create a DataFrame and save it as CSV
    df = pd.DataFrame(jobs_data)
    df.to_csv("itjobs_listings.csv", index=False)
    print("CSV file saved successfully!")
else:
    print("Error:", response.status_code, response.text)
