import streamlit as st
import pandas as pd
import asyncio, platform
from scraper import scrape

st.set_page_config(page_icon="🕵️‍♂️", page_title="ITJobs Scraper")
st.title("ITJobs Scraper 🕵️‍♂️")
st.caption("Search and analyze the IT job market in Portugal.")
st.markdown("Powered by [ITJobs](https://www.itjobs.pt/)")

# Windows Async Loop Fix
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize session state
if "first_run" not in st.session_state:
    st.session_state.first_run = True

# Input for Keywords
keys_input = st.text_input("Enter Keywords (comma separated)", "typescript,frontend,data engineer")
keys = [k.strip() for k in keys_input.split(",") if k.strip()]

def run_scraper(keywords=None):
    st.info("Running scraper... This may take a while ⏳")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    jobs = loop.run_until_complete(scrape(keywords))  # Now it returns a list of dictionaries 🔥

    if jobs:
        st.success("Scraping finished ✅")
        data = pd.DataFrame(jobs)  # Convert list of dictionaries into a DataFrame

        # Create clickable links for Streamlit table
        data["Offer"] = data["URL"].apply(
            lambda url: f'<a href="{url}" target="_blank">🔗 Link</a>' if pd.notnull(url) else ""
        )

        # Drop the URL column
        data = data.drop(columns=["URL"])

        st.write("### Scraped Jobs:")

        # Display the table without the index column using markdown
        table_html = data.to_html(index=False, escape=False)
        st.markdown(table_html, unsafe_allow_html=True)

        # Download CSV button
        st.download_button(
            label="Download CSV 📄",
            data=data.to_csv(index=False),
            file_name="scraped_jobs.csv",
            mime="text/csv",
        )

        # Create company offer count table
        company_counts = data["Company"].value_counts().reset_index()
        company_counts.columns = ["Company", "Number of Offers"]

        st.write("### Offers per Company:")
        st.dataframe(company_counts)

# Automatically run scraper on first app launch
if st.session_state.first_run:
    run_scraper([])
    st.session_state.first_run = False

if st.button("Run Scraper"):
    if not keys:
        st.warning("Please enter at least one keyword.")
    else:
        run_scraper(keys)
