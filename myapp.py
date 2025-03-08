from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import requests, os

# Load environment variables (for API_KEY)
load_dotenv()
api_key = os.getenv("API_KEY")

# Function to fetch data with limit and pagination
def fetch_jobs():
    url = "https://api.itjobs.pt/job/list.json"
    data = {
        "api_key": api_key,
        "limit": 100,  # Set the limit to a higher number (maximum supported value)
        "page": 1      # You can change the page number to get results from different pages
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['results'], response.json()['total'], response.json()['page'], response.json()['limit']
    else:
        print(f"Error: {response.status_code}")
        return [], None, None, None

# Fetch job listings
jobs, total, page, limit = fetch_jobs()  # Unpack correctly

if jobs:
    # Prepare data for the job offers table
    job_offers = []
    company_counts = {}
    tech_distribution = {}
    role_distribution = {}

    for job in jobs:
        # Prepare job offer data
        job_offers.append({
            "Job Title": job["title"],
            "Company": job["company"]["name"],
            "Offer": job["company"]["url"]
        })

        # Count the companies
        company_name = job["company"]["name"]
        company_counts[company_name] = company_counts.get(company_name, 0) + 1

        # Technology and Role Distribution (Assuming 'types' and 'locations' contain relevant data)
        for tech in job.get("types", []):
            tech_name = tech["name"]
            tech_distribution[tech_name] = tech_distribution.get(tech_name, 0) + 1
        
        for role in job.get("locations", []):
            role_name = role["name"]
            role_distribution[role_name] = role_distribution.get(role_name, 0) + 1

    # Display Job Offers Table (without index)
    st.write("### Job Offers")
    offers_df = pd.DataFrame(job_offers)
    st.dataframe(offers_df, use_container_width=True)  # Hide index

    # Display Company Offer Counts (without index)
    st.write("### Offers per Company")
    company_counts_df = pd.DataFrame(list(company_counts.items()), columns=["Company", "Number of Offers"])
    st.dataframe(company_counts_df, use_container_width=True)  # Hide index

    # Technology Distribution Bar Chart
    st.write("### Technology Distribution")
    tech_df = pd.DataFrame(list(tech_distribution.items()), columns=["Technology", "Count"])
    tech_df = tech_df.sort_values(by="Count", ascending=False)

    st.bar_chart(tech_df.set_index("Technology"))

    # City Distribution Bar Chart
    st.write("### City Distribution")
    role_df = pd.DataFrame(list(role_distribution.items()), columns=["City", "Count"])
    role_df = role_df.sort_values(by="Count", ascending=False)

    st.bar_chart(role_df.set_index("City"))

else:
    st.warning("No jobs found.")
