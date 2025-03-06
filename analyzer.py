from collections import defaultdict
import pandas as pd
import json, re

# Load keywords from JSON 🔥
def load_keywords():
    with open("keywords.json", "r") as file:
        return json.load(file)

# Match keywords with regex
def match_keywords(text, keywords):
    matches = set()
    for keyword in keywords:
        if re.search(rf"\b{keyword}\b", text, re.IGNORECASE):
            matches.add(keyword)
    return matches

# Analyze Job Titles
def extract_entities(df):
    keywords = load_keywords()
    tech_matches = defaultdict(int)
    role_matches = defaultdict(int)

    for title in df["Job Title"]:
        techs = match_keywords(title, keywords["technologies"])
        roles = match_keywords(title, keywords["roles"])

        for tech in techs:
            tech_matches[tech] += 1
        for role in roles:
            role_matches[role] += 1

    tech_df = pd.DataFrame(tech_matches.items(), columns=["Technology", "Frequency"]).sort_values(by="Frequency", ascending=False)
    role_df = pd.DataFrame(role_matches.items(), columns=["Role", "Frequency"]).sort_values(by="Frequency", ascending=False)

    return tech_df, role_df
