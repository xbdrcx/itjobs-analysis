# python -m pip install playwright
# python -m playwright install
from playwright.async_api import async_playwright

async def setup_playwright():
    from playwright.__main__ import main
    main(["install", "chromium"])  # Automatically installs chromium if not installed


BASE_URL = "https://www.itjobs.pt/emprego?location=14&date=7d&page="

async def scrape(keys):
    keys = [k.lower() for k in keys]  # Normalize keywords
    jobs = []  # List to store all jobs 🔥

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL + "1")
        await page.wait_for_selector("ul.pagination")

        pagination = await page.query_selector("ul.pagination")
        last_page_number = 1
        if pagination:
            page_numbers = await pagination.query_selector_all("li")
            if len(page_numbers) > 1:
                last_page_number = int((await page_numbers[-2].text_content()).strip())
                print(f"Last page number: {last_page_number}")

        # Loop through each page
        for page_num in range(1, last_page_number + 1):
            print(f"Scraping page {page_num}...")
            await page.goto(BASE_URL + str(page_num))
            await page.wait_for_selector("ul.list-unstyled.listing")

            job_blocks = await page.query_selector_all("div.block.borderless")
            if job_blocks:
                for job_block in job_blocks:
                    posted_date = await job_block.query_selector("div.date-box")
                    date_text = "N/A"
                    if posted_date:
                        day = await (await posted_date.query_selector("div.d-d")).text_content()
                        month = await (await posted_date.query_selector("div.d-m")).text_content()
                        date_text = f"{day.strip()} {month.strip()}"

                    job_titles = await job_block.query_selector_all("div.list-title a")
                    companies = await job_block.query_selector_all("div.list-name")

                    for job, company in zip(job_titles, companies):
                        job_title = (await job.text_content()).strip()
                        company_name = (await company.text_content()).strip()
                        job_url = await job.get_attribute("href")

                        if job_url:
                            job_url = "https://www.itjobs.pt" + job_url

                        # Filter by keywords 🔥
                        if not keys or any(k in job_title.lower() for k in keys):
                            jobs.append({
                                "Job Title": job_title,
                                "Company": company_name,
                                "Posted Date": date_text,
                                "URL": job_url,
                            })

        await browser.close()
        print(f"Total jobs scraped: {len(jobs)}")
        return jobs  # Now returning the list of jobs 🎯
