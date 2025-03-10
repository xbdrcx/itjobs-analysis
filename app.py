# pip install --force-reinstall torch --index-url https://download.pytorch.org/whl/cu118
# pip install --upgrade typing_extensions
# spacy download en_core_web_sm
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from dotenv import load_dotenv
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import requests, os, torch, spacy
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# TODO
# - Verificar uso legal de dados do ITJOBS (Adicionar disclaimer)
# - Adicionar traduções
# - Pesquisar descrições por detalhes
# - Corrigir URL de ofertas (atualmente comentado da tabela)
# - Adicionar à tabela caso seja "Contrato", "Estágio", etc
# - Corrigir distribuiçoes de Tech/Roles (estao misturados)
# - Treinar modelo NER para reconhecimento de TECNOLOGIAS e ROLES
# - 

st.set_page_config(page_icon="💻", page_title="ITJobs Analyzer", layout="wide")
st.title("ITJobs Analyzer 🕵️‍♂️💻")
st.caption("Use AI and Data Visualization techniques to search, analyze, and extract insight from Portugal's IT job market.")
st.markdown(
    """
    Powered by 
    <a href="https://www.itjobs.pt/" target="_blank">
        <img src="https://static.itjobs.pt/images/logo.png" alt="ITJobs" width="100">
    </a>
    """,
    unsafe_allow_html=True,
)

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Define known technologies and roles for better classification
TECH_KEYWORDS = {"Python", "JavaScript", "React", "Node.js", "Java", "C++", "Docker", "AWS", "Azure", "SQL", "Kubernetes", "TensorFlow", "PyTorch"}
ROLE_KEYWORDS = {"Frontend Developer", "Backend Developer", "Data Scientist", "DevOps Engineer", "Software Engineer", "AI Engineer", "Cloud Architect"}

def extract_entities(text):
    """Extract technologies and roles from job titles."""
    doc = nlp(text)
    extracted_roles = set()
    extracted_techs = set()

    # Named Entity Recognition (NER)
    for ent in doc.ents:
        # Classify as technology if it's an org, product, or tech-related entity
        if ent.label_ in ["ORG", "PRODUCT", "TECHNOLOGY"]:
            extracted_techs.add(ent.text)
        elif ent.label_ in ["PERSON", "JOB_TITLE", "WORK_OF_ART"]:
            extracted_roles.add(ent.text)

    # Manual keyword matching (NER may miss some)
    for tech in TECH_KEYWORDS:
        if tech.lower() in text.lower():
            extracted_techs.add(tech)
    for role in ROLE_KEYWORDS:
        if role.lower() in text.lower():
            extracted_roles.add(role)

    # Additional checks for ambiguity (e.g., "React" could be both a tech and a role in some cases)
    for tech in TECH_KEYWORDS:
        if tech.lower() in text.lower():
            extracted_techs.add(tech)
    
    return extracted_roles, extracted_techs

# Load environment variables (for API_KEY)
load_dotenv()
api_key = os.getenv("API_KEY")

# Function to format the date
def format_date(date_str):
    if date_str != "N/A":
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return date_obj.strftime("%d-%m-%Y")
        except ValueError:
            return "N/A"
    return "N/A"

# Fetch all available cities and their respective location codes
def fetch_cities():
    url = "https://api.itjobs.pt/location/list.json"
    params = {
        "api_key": api_key
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for any HTTP errors

        if response.status_code == 200:
            data = response.json()
            locations = data.get("results", [])
            # Create a dictionary with location names and their codes
            locations = {location["name"]: location["id"] for location in locations}
            return locations
        else:
            st.error(f"Failed to fetch locations. HTTP Status Code: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return {}

# Fetch job listings and classify as full-time or part-time
def fetch_all_jobs(location_code=None):
    url = "https://api.itjobs.pt/job/list.json"
    all_jobs = []
    page = 1
    limit = 100  # Maximum allowed per request

    while True:
        params = {
            "api_key": api_key,
            "limit": limit,
            "page": page,
            "state": 1,
        }

        if location_code:
            params["location"] = location_code  # Use the location code for the request

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()
        jobs = data.get('results', [])

        if not jobs:
            break  # No more jobs to fetch

        all_jobs.extend(jobs)
        page += 1

    return all_jobs

# Fetch and select locations
locations = fetch_cities()
selected_location_name = st.selectbox("Select a location", ["All"] + list(locations.keys()))
selected_location_code = locations.get(selected_location_name)

# Fetch job listings
jobs = fetch_all_jobs(location_code=selected_location_code if selected_location_name != "All" else None)

if jobs:
    # Add the classification of Full-Time vs Part-Time to the job offers table
    job_offers, company_counts, location_distribution = [], {}, {}
    tech_distribution, role_distribution = {}, {}
    full_time_count, part_time_count = 0, 0  # New counters

    for job in jobs:
        roles, techs = extract_entities(job["title"])

        for role in roles:
            role_distribution[role] = role_distribution.get(role, 0) + 1
        for tech in techs:
            tech_distribution[tech] = tech_distribution.get(tech, 0) + 1
        for location in job.get("locations", []):
            location_name = location["name"]
            location_distribution[location_name] = location_distribution.get(location_name, 0) + 1

        allow_remote = "✅" if job["allowRemote"] else "❌"
        job_type = "Part-Time"  # Default to Part-Time
        if "types" in job and job["types"]:
            job_type = "Full-Time" if job["types"][0]["id"] == "1" else "Part-Time"  # Access job type

        full_time_count = sum(1 for job in jobs if "types" in job and job["types"] and job["types"][0]["id"] == "1")
        part_time_count = len(jobs) - full_time_count

        wage = job.get("wage", "Not disclosed")

        job_offers.append({
            "Job Title": job["title"],
            "Company": job["company"]["name"],
            # "Offer": f'<a href="https://www.itjobs.pt/oferta/{job["id"]}" target="_blank">🔗 Link</a>',
            "Date Posted": format_date(job.get("updatedAt", "N/A")),
            "Job Type": job_type,
            "Wage": wage if wage != "null" else "Not disclosed",
            "Allow Remote": allow_remote,
        })

        # Count companies
        company_counts[job["company"]["name"]] = company_counts.get(job["company"]["name"], 0) + 1

    # Display job offers
    offers_df = pd.DataFrame(job_offers)
    st.write("###", len(jobs), "offer(s) found")
    st.dataframe(offers_df, use_container_width=True)

    # Display company counts
    company_counts_df = pd.DataFrame(list(company_counts.items()), columns=["Company", "Number of Offers"])
    st.write("###", len(company_counts_df), "unique companies")
    st.dataframe(company_counts_df.sort_values(by="Number of Offers", ascending=False), use_container_width=True)

    # Location Distribution
    if selected_location_name == "All":
        st.write("### Location Distribution")
        location_df = pd.DataFrame(list(location_distribution.items()), columns=["Location", "Count"])
        st.bar_chart(location_df.set_index("Location"))

    # Remote vs Non-Remote job count
    remote_count = sum(1 for job in jobs if job["allowRemote"])
    non_remote_count = len(jobs) - remote_count

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Allow-Remote vs. In-Person")
        remote_vs_non_remote_df = pd.DataFrame({"Type": ["Allow Remote", "In-Person"], "Count": [remote_count, non_remote_count]})
        fig, ax = plt.subplots()
        ax.pie(remote_vs_non_remote_df['Count'], labels=remote_vs_non_remote_df['Type'], autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel2.colors)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig)

    with col2:
        st.write("### Full-Time vs. Part-Time")
        full_time_part_time_df = pd.DataFrame({"Type": ["Full-Time", "Part-Time"], "Count": [full_time_count, part_time_count]})
        fig, ax = plt.subplots()
        ax.pie(full_time_part_time_df['Count'], labels=full_time_part_time_df['Type'], autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel2.colors)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig)

    # Display technology distribution
    st.write("### Technology Distribution")
    st.bar_chart(pd.DataFrame.from_dict(tech_distribution, orient='index', columns=['Count']))

    # Display role distribution
    st.write("### Role Distribution")
    st.bar_chart(pd.DataFrame.from_dict(role_distribution, orient='index', columns=['Count']))

else:
    st.warning("No jobs found.")
