import pandas as pd
import numpy as np
import json
import pickle
import nltk
import random
from keras.models import load_model
from nltk.stem import WordNetLemmatizer
import time

model = load_model("chatbot_model.h5")
intents = json.loads(open("intents.json").read())
words = pickle.load(open("words.pkl", "rb"))
classes = pickle.load(open("classes.pkl", "rb"))

lemmatizer = WordNetLemmatizer()


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(
        word.lower()) for word in sentence_words]
    return sentence_words


def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
    return np.array(bag)


def getResponse(ints, intents_json):
    try:
        tag = ints[0]["intent"]
        list_of_intents = intents_json["intents"]
        for i in list_of_intents:

            if i["tag"] == tag:
                result = random.choice(i["responses"])
                return result
                break
    except:
        return "I don't understand..."


def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


if __name__ == "__main__":
    dataset = pd.read_excel("dataset.xlsx")
    total = dataset.shape[0]
    correct = 0
    for i,row in dataset.iterrows():
        perc = round(((i+1)/total)*100)
        print(f'Evaluating model... {perc} %  completed', end='\r')
        ints = predict_class(row["Questions"], model)
        response = getResponse(ints, intents)
        response = str(response)
        if response == row["Responses"]:
            correct += 1
        time.sleep(0.2)
    print(f"-----------------------------------------------------\nAccuracy: {correct}/{total} {round((correct/total)*100,2)} %\n-----------------------------------------------------")
