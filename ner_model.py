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
