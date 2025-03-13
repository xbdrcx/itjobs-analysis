# pip install transformers datasets spacy torch doccano
# spacy download en_core_web_trf
# https://github.com/doccano/doccano
# doccano init
# doccano createuser --username admin --password admin
# doccano webserver --port 8000
from app import fetch_all_jobs
from datasets import Dataset
from transformers import Trainer, TrainingArguments
from transformers import AutoTokenizer, AutoModelForTokenClassification
import json

data = fetch_all_jobs()

# Load a pre-trained model (e.g., BERT for token classification)
model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"  # Fine-tuned on CoNLL-03 NER dataset
model = AutoModelForTokenClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Example labeled dataset (this is a small example, replace it with your data)
data_example = {
    'text': ["John is a Data Scientist proficient in Python and AWS."],
    'entities': [
        {"start": 13, "end": 28, "label": "JOB_ROLE"},
        {"start": 41, "end": 47, "label": "TECHNOLOGY"},
        {"start": 52, "end": 55, "label": "TECHNOLOGY"}
    ]
}

# Convert to Dataset format
dataset = Dataset.from_dict(data)

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples['text'], truncation=True, padding=True, is_split_into_words=True)
    labels = examples['entities']  # Adjust as needed based on your labeling format
    return tokenized_inputs, labels

dataset = dataset.map(tokenize_and_align_labels, batched=True)

training_args = TrainingArguments(
    output_dir='./results',  # where to save the model
    evaluation_strategy="epoch",  # evaluation after each epoch
    learning_rate=5e-5,
    per_device_train_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    save_steps=10,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    eval_dataset=dataset,  # You can create a separate validation set
)

trainer.train()

text = "Looking for a Software Engineer with experience in JavaScript and React."
inputs = tokenizer(text, return_tensors="pt")
outputs = model(**inputs)

# Extract entities (you'll need post-processing to map token IDs back to entities)
# Print or visualize the results (e.g., using spaCy or simple output parsing)

def format_job_data():
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
