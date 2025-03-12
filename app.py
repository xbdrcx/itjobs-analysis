from dotenv import load_dotenv
from datetime import datetime
import plotly.express as px
import streamlit as st
import pandas as pd
import requests, os, spacy, base64, time, json, re

# Load environment variables (for API_KEY)
load_dotenv()
itjobs_key = os.getenv("ITJOBS_API_KEY")
hf_key = os.getenv("HF_API_KEY")
# itjobs_key = st.secrets["ITJOBS_API_KEY"]
# f_key = st.secrets["HF_API_KEY"]

# API Connection
API_URL = "https://itjobs-analysis.onrender.com"

# Function to track visit
def track_visit():
    response = requests.get(f"{API_URL}/track_visit")
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        st.error("Failed to track visit")
        return None

# Function to track exit
def track_exit():
    response = requests.get(f"{API_URL}/track_exit")
    if response.status_code == 200:
        return "Exit tracked"
    else:
        st.error("Failed to track exit")
        return None

# Load spaCy NLP model
nlp = spacy.load("en_core_web_lg")

# Load keywords
with open('keywords.json', 'r') as f:
    keywords = json.load(f)
    
TECH_KEYWORDS = keywords["technologies"]
ROLE_KEYWORDS = keywords["tech_roles"]

def extract_entities(text):
    """Extract technologies and roles from job titles, ensuring they aren't mixed up."""
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
    
    # Remove any roles that appear in tech and vice versa
    final_roles = {role for role in extracted_roles if not any(tech.lower() in role.lower() for tech in extracted_techs)}
    final_techs = {tech for tech in extracted_techs if not any(role.lower() in tech.lower() for role in extracted_roles)}

    return final_roles, final_techs

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
@st.cache_data
def fetch_cities():
    url = "https://api.itjobs.pt/location/list.json"
    params = {"api_key": itjobs_key}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    try:
        # Making the API request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Check if the response contains the expected data
        if response.status_code == 200:
            data = response.json()
            locations = data.get("results", [])
            
            # Check if there are any locations in the response
            if not locations:
                st.warning("No locations found in the response.")
                return {}

            # Create a dictionary with location names and their codes
            locations_dict = {location["name"]: location["id"] for location in locations}
            return locations_dict
        else:
            st.error(f"Failed to fetch locations. HTTP Status Code: {response.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        # Handle request exceptions such as network issues or invalid response
        st.error(f"An error occurred while fetching locations: {e}")
        return {}
    except ValueError as e:
        # Handle JSON decoding errors
        st.error(f"Error parsing the response data: {e}")
        return {}
    except KeyError as e:
        # Handle missing keys in the response
        st.error(f"Error processing the response data: Missing key {e}")
        return {}
    except Exception as e:
        # Catch any unexpected exceptions
        st.error(f"An unexpected error occurred: {e}")
        return {}

# Fetch job listings and classify as full-time or part-time
@st.cache_data
def fetch_all_jobs(location_code=None):
    url = "https://api.itjobs.pt/job/list.json"
    all_jobs = []
    page = 1
    limit = 100  # Maximum allowed per request
    max_retries = 3  # Retry mechanism for transient failures

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    while True:
        params = {
            "api_key": itjobs_key,
            "limit": limit,
            "page": page,
            "state": 1,
        }
        if location_code:
            params["location"] = location_code

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
                data = response.json()
                
                jobs = data.get("results", [])
                if not jobs:
                    return all_jobs  # No more jobs available

                all_jobs.extend(jobs)
                page += 1
                break  # Exit retry loop on success

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}/{max_retries}: Error fetching data - {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

        else:
            print("Max retries reached. Exiting...")
            break  # Exit the while loop if all retries fail

    return all_jobs

# Function to calculate the elapsed time
def calculate_elapsed_time(start_time):
    elapsed_time = time.time() - start_time
    return f"{elapsed_time:.2f} seconds"

def extract_job_level(job_title):
    # Define patterns for job levels in the job title
    levels = {
        "Junior": r"\bjunior\b", 
        "Mid-level": r"\bmid[-\s]*level\b", 
        "Senior": r"\bsenior\b"
    }
    
    job_level = "Unknown"  # Default value if no level is found

    for level, pattern in levels.items():
        if re.search(pattern, job_title, re.IGNORECASE):
            job_level = level
            break

    return job_level

def main():
    st.set_page_config(page_title="ITJobs Analyzer", page_icon="💻", layout="wide")

    if st.query_params.get("file") == "sitemap.xml":
        st.write('<?xml version="1.0" encoding="UTF-8"?>')
        st.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

        pages = [
            "https://itjobs.streamlit.app",
        ]

        for page in pages:
            st.write(f"""
            <url>
                <loc>{page}</loc>
                <lastmod>{datetime.today().strftime('%Y-%m-%d')}</lastmod>
                <priority>0.8</priority>
            </url>
            """)

        st.write("</urlset>")
        st.stop()

    st.markdown(
        """
        <!-- Basic SEO Meta Tags -->
        <meta name="description" content="Find the best IT jobs in Portugal with AI-powered insights. Get real-time job market analysis.">
        <meta name="keywords" content="IT jobs, Portugal, software developer, AI job analysis">
        <meta name="author" content="Your Name">
        <meta name="robots" content="index, follow">

        <!-- Open Graph (OG) for Facebook, LinkedIn -->
        <meta property="og:title" content="AI-Powered IT Job Analysis">
        <meta property="og:description" content="Analyze IT job trends, salaries, and skills in Portugal with AI.">
        <meta property="og:image" content="https://your-app-url.com/preview-image.png">
        <meta property="og:url" content="https://your-app-url.com">
        <meta property="og:type" content="website">

        <!-- Twitter Card -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="AI-Powered IT Job Analysis">
        <meta name="twitter:description" content="Find the best IT jobs and trends in Portugal with AI.">
        <meta name="twitter:image" content="https://your-app-url.com/preview-image.png">
        """,
        unsafe_allow_html=True,
    )
    st.title("ITJobs Analyzer 🕵️‍♂️💻")
    st.html("<caption>This application uses <b>data</b> from the <b>ITJobs API</b> along with <b>AI</b> and <b>Data Visualization</b> techniques to extract, analyze and present <b>meaningful insights</b> from <b>Portugal's IT job market</b>.</caption>")
    st.html("<b>Disclaimer:</b> This application is for informational purposes only and is not affiliated with ITJobs.pt.")
    st.caption("The data does not necessarily represent the entirety of Portugal's job market.")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 20px;">
            <div>
                Powered by  
                <a href="https://www.itjobs.pt/" target="_blank">
                    <img src="https://static.itjobs.pt/images/logo.png" alt="ITJobs" title="ITJobs" width="90">
                </a>
            </div>
            <div>
                Developed by  
                <a href="https://xbdrcx.github.io/" target="_blank">
                    <img src="data:image/x-icon;base64,{base64.b64encode(open("favicon.ico", "rb").read()).decode()}" alt="Bruno Cruz" title="Bruno Cruz" width="42">
                </a>
            </div>
        </div>
        <br>
        """,
        unsafe_allow_html=True,
    )
    # Fetch and select locations
    locations = fetch_cities()
    selected_location_name = st.selectbox("Select location:", ["All"] + list(locations.keys()))
    selected_location_code = locations.get(selected_location_name)

    # Place to store start time
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()  # Store start time when the app runs

    # Measure elapsed time each time the user selects a new option
    st.session_state.start_time = time.time()  # Reset start time when combobox option changes

    # Fetch job listings
    jobs = fetch_all_jobs(location_code=selected_location_code if selected_location_name != "All" else None)

    if jobs:
        # Add the classification of Full-Time vs Part-Time to the job offers table
        job_offers, company_counts, location_distribution = [], {}, {}
        tech_distribution, role_distribution = {}, {}
        full_time_count, part_time_count = 0, 0  # New counters
        level_distribution = {"Junior": 0, "Mid-level": 0, "Senior": 0, "Unknown": 0}  # Track levels

        for job in jobs:
            roles, techs = extract_entities(job["title"])
            # Extract job level
            job_level = extract_job_level(job["title"])
            level_distribution[job_level] += 1

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
                "Location": ", ".join([loc["name"] for loc in job.get("locations", [])]) if job.get("locations") else "N/A",
                # "Offer": f'<a href="https://www.itjobs.pt/oferta/{job["id"]}" target="_blank">🔗 Link</a>',
                "Date Posted": format_date(job.get("updatedAt", "N/A")),
                "Job Type": job_type,
                # "Wage": wage if wage != "null" else "Not disclosed",
                "Allow Remote": allow_remote,
                #"Summary": job["summary"],
                # "Extracted Role": ", ".join(roles) if roles else "N/A",
                # "Extracted Tech": ", ".join(techs) if techs else "N/A",
            })

            # Count companies
            company_counts[job["company"]["name"]] = company_counts.get(job["company"]["name"], 0) + 1

        # Display job offers
        offers_df = pd.DataFrame(job_offers)
        st.write("###", len(jobs), "offer(s) found")
        st.dataframe(offers_df, use_container_width=True, hide_index=True, row_height=50)

        st.html("<hr>")

        # Display company counts
        company_counts_df = pd.DataFrame(list(company_counts.items()), columns=["Company", "Number of Offers"])
        st.write("###", len(company_counts_df), "unique companies")
        st.dataframe(company_counts_df.sort_values(by="Number of Offers", ascending=False), use_container_width=True, hide_index=True)

        # Location Distribution
        if selected_location_name == "All":
            st.write("### Location Distribution")
            location_df = pd.DataFrame(list(location_distribution.items()), columns=["Location", "Count"])
            loc_fig = px.bar(location_df, x="Location", y="Count", color="Location")
            loc_fig.update_xaxes(categoryorder='category ascending')
            st.plotly_chart(loc_fig)
            # Show top 3 techs
            top_loc = sorted(location_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            top_locs_df = pd.DataFrame(top_loc, columns=["Location", "Count"])  # Explicitly set the column names
            st.write("### TOP Locations")
            st.dataframe(top_locs_df, hide_index=True)
            
        st.html("<hr>")

        # Remote vs Non-Remote job count
        remote_count = sum(1 for job in jobs if job["allowRemote"])
        non_remote_count = len(jobs) - remote_count

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Allow-Remote vs. In-Person")
            remote_vs_non_remote_df = pd.DataFrame({"Type": ["Allow Remote", "In-Person"], "Count": [remote_count, non_remote_count]})
            fig = px.pie(remote_vs_non_remote_df, values="Count", names="Type", hole=0.2)
            st.plotly_chart(fig)

        with col2:
            st.write("### Full-Time vs. Part-Time")
            full_time_part_time_df = pd.DataFrame({"Type": ["Full-Time", "Part-Time"], "Count": [full_time_count, part_time_count]})
            fig = px.pie(full_time_part_time_df, values="Count", names="Type", hole=0.2)
            st.plotly_chart(fig)

        st.html("<hr>")

        if tech_distribution:
            # Display technology distribution
            st.write("### TOP 10 Technologies")
            tech_distribution_sorted = sorted(tech_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
            tech_distribution_df = pd.DataFrame(tech_distribution_sorted, columns=["Tech", "Count"])
            tech_fig = px.bar(tech_distribution_df, x="Tech", y="Count", color="Tech")
            tech_fig.update_xaxes(categoryorder='category ascending')
            st.plotly_chart(tech_fig)

        st.html("<hr>")

        if role_distribution:
            # Display role distribution
            st.write("### TOP 10 Roles")
            role_distribution_sorted = sorted(role_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
            role_distribution_df = pd.DataFrame(role_distribution_sorted, columns=["Role", "Count"])
            role_fig = px.bar(role_distribution_df, x="Role", y="Count", color="Role")
            role_fig.update_xaxes(categoryorder='category ascending')
            st.plotly_chart(role_fig)

        st.html("<hr>")

        # Job Level Distribution (Junior, Mid-level, Senior)
        st.write("### Job-Level Distribution")
        level_df = pd.DataFrame(list(level_distribution.items()), columns=["Level", "Count"])
        level_fig = px.bar(level_df, x="Level", y="Count", color="Level")
        level_fig.update_xaxes(categoryorder='category ascending')
        st.plotly_chart(level_fig)

        elapsed_time = calculate_elapsed_time(st.session_state.start_time)
        st.caption(f"Data fetched and processed in {elapsed_time}")

    else:
        st.warning("No jobs found.")

if __name__ == "__main__":
    main()
