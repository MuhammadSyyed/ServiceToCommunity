from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
import nltk
import pandas as pd
import re
import json
import time
import random
import _thread
from textblob import TextBlob
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import remove_stopwords
import requests

# nltk.download('punkt')
# nltk.download('wordnet')

lock = _thread.allocate_lock()
def save_json_file(name, content):
    with lock:
        with open(name, "w") as file:
            json.dump(content, file, indent=4)
            file.close()
    
def read_json_file(name):
    with lock:
        with open(name, "r") as file:
            file_content = json.load(file)
            file.close()
            return file_content

def correct_spelling(text):
    blob = TextBlob(text)
    return str(blob.correct())

def find_synonyms(word):
    res = requests.get(f"https://www.thesaurus.com/browse/{word}")
    synonyms = re.search('words related to '+word.lower()+r', such as:(.*?).</span>' ,str(res.text)).group(1)
    synonyms = [word.strip().replace("and ","") for word in synonyms.split(",")]
    return synonyms

def preprocess_text(text):
    # Remove special characters
    text = re.sub('[^a-zA-Z0-9\s]', '', text)

    # Remove helping verbs
    words = text.split()
    words = [word for word in words if word.lower() not in ['am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
                                                            'has', 'had', 'do', 'does', 'did', 'shall', 'will', 'should', 'would', 'may', 'might', 'must', 'can', 'could']]
    text = ' '.join(words)

    # Remove stop words
    text = remove_stopwords(text)

    # Convert to lowercase
    text = text.lower()

    return text

def tokenize_text(text):
    # Tokenize text into individual words
    tokens = word_tokenize(text)
    return tokens

def lemmatize_text(tokens):
    # Initialize the WordNetLemmatizer
    lemmatizer = WordNetLemmatizer()

    # Lemmatize each word in the tokenized text
    lemmas = [lemmatizer.lemmatize(token,'n') for token in tokens]

    return lemmas

def preprocess(data):
    memory = read_json_file('intents.json')
    for pattern,responses in zip(data["Questions"],data["Responses"]):
        new_intent = {'tag':'','patterns':[],'responses':[]}
        processed_pattern = preprocess_text(pattern)
        tokens = tokenize_text(processed_pattern)
        lemmas = lemmatize_text(tokens)
        new_intent['tag'] = '_'.join(lemmas)
        new_intent["patterns"] = [pattern]
        new_intent["responses"] = responses.split("|")
        existing_tags = set(intent["tag"] for intent in memory["intents"])
        if new_intent["tag"] not in existing_tags:
            memory["intents"].append(new_intent)
        
        
    save_json_file("intents.json",memory)


if __name__ == '__main__':
    data = pd.read_excel('dataset.xlsx')
    preprocess(data)