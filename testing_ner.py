import json

# Load the job data from the file (for demonstration, you can replace this with your own data)
with open('jobs_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

formatted_data = []

# Loop through each job in the "results"
for job in data["results"]:
    job_text = job["title"]
    job_entities = []

    # Add job role as an entity (e.g., "Programador C# e PHP")
    job_entities.append({
        "start": job_text.find(job["title"]),
        "end": job_text.find(job["title"]) + len(job["title"]),
        "label": "JOB_ROLE"
    })

    # Add technology as an entity (e.g., "C#", "PHP") - assuming technologies are part of job title or description
    # Example: looking for specific tech keywords in job title or description
    technologies = ["C#", "PHP", "Python", "AWS", "Java", "JavaScript", "Node.js"]  # Add more tech keywords as needed

    for tech in technologies:
        tech_start = job_text.find(tech)
        if tech_start != -1:  # If technology is found
            job_entities.append({
                "start": tech_start,
                "end": tech_start + len(tech),
                "label": "TECHNOLOGY"
            })

    # Add the formatted data
    formatted_data.append({
        "text": [job_text],
        "entities": job_entities
    })

# Save the formatted data to a new JSON file
with open('formatted_jobs_entities.json', 'w', encoding='utf-8') as f:
    json.dump(formatted_data, f, ensure_ascii=False, indent=4)

print("Formatted data saved to 'formatted_jobs_entities.json'")
