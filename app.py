import streamlit as st
import pandas as pd
import asyncio, platform
from scraper import scrape
from analyzer import extract_entities

# TODO
# - Adicionar todas as cidades no ITJOBS a uma combobox
# - 

st.set_page_config(page_icon="💻", page_title="ITJobs Analyzer")
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

# Windows Async Loop Fix
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize session state
if "first_run" not in st.session_state:
    st.session_state.first_run = True

# Input for Keywords with placeholder
keys_input = st.text_input("Enter Keywords (comma separated)", placeholder="Machine Learning, Python, Frontend")
keys = [k.strip() for k in keys_input.split(",") if k.strip()]

# Run button below input
if st.button("Execute", key="run_scraper_button") or st.session_state.first_run:
    if not keys_input.strip():  # Check if the input is empty or whitespace
        keys = []  # Set to empty list to search for all jobs

    st.info("Executing... This may take a while ⏳")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    jobs = loop.run_until_complete(scrape(keys))

    if jobs:
        st.success("Execution complete ✅")
        data = pd.DataFrame(jobs)

        data["Offer"] = data["URL"].apply(
            lambda url: f'<a href="{url}" target="_blank">🔗 Link</a>' if pd.notnull(url) else ""
        )

        data = data.drop(columns=["URL"])

        st.write("### Scraped Jobs:")
        table_html = data.to_html(index=False, escape=False)
        st.markdown(table_html, unsafe_allow_html=True)

        st.download_button(
            label="Download CSV 📄",
            data=data.to_csv(index=False),
            file_name="scraped_jobs.csv",
            mime="text/csv",
        )

        company_counts = data["Company"].value_counts().reset_index()
        company_counts.columns = ["Company", "Number of Offers"]
        st.write("### Offers per Company:")
        st.dataframe(company_counts)

        st.write("### Detected Technologies and Roles")
        tech_df, role_df = extract_entities(data)

        st.write("#### Top Technologies")
        st.bar_chart(tech_df.set_index("Technology"))

        st.write("#### Roles Distribution")
        st.bar_chart(role_df.set_index("Role"))
    else:
        st.warning("No jobs found.")

    st.session_state.first_run = False
