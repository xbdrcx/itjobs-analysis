from transformers import pipeline

# Initialize a pre-trained NER model pipeline
nlp = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

# Example job titles
job_titles = [
    "Software Engineer",
    "Data Scientist",
    "Python Developer",
    "Senior JavaScript Developer"
]

for job_title in job_titles:
    ner_results = nlp(job_title)
    roles = [entity['word'] for entity in ner_results if entity['entity'] == 'B-ORG']  # You can filter entities by type
    technologies = [entity['word'] for entity in ner_results if entity['entity'] == 'B-MISC']  # Adjust as needed
    
    print(f"Job Title: {job_title} -> Roles: {roles} -> Technologies: {technologies}")
