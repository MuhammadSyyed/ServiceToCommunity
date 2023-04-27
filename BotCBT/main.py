import requests
import pickle
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from keras.models import load_model
from datetime import datetime
import json
import random
import numpy as np
import nltk
import uvicorn
from nltk.stem import WordNetLemmatizer
from pyngrok import ngrok
import shutup
from pydantic import BaseModel
shutup.please()
lemmatizer = WordNetLemmatizer()

app = FastAPI()


model = load_model("chatbot_model.h5")
intents = json.loads(open("intents.json").read())
words = pickle.load(open("words.pkl", "rb"))
classes = pickle.load(open("classes.pkl", "rb"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(
        word.lower()) for word in sentence_words]
    return sentence_words


def send_message(to, msg):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": msg
        }
    }
    header = {
        'Authorization': 'Bearer EAANdsVolZChABAFrNtfXtUhSBRjCZBxnZBUsfkEBQZBfVvBA2dhdK09eZBmcU8LHHDZCIUdomFfOsev6AcZAvmnJ1tDmv8STAhF6ZCiIDZBxKusZCSRZBG40hASemiLOhjJF6edBbsErbij81ghZC6YJTRMHETzGPZCcKLpVLo8D9YU3ml8IZCJLXh7xRGp0pS1AdHHB5qWAuOceeoTRWy1MofZBJ5J0cCkpWmaspUZD',
        'Content-Type': 'application/json'
    }

    requests.post("https://graph.facebook.com/v16.0/111080325182382/messages",
                  json=data, headers=header)
    print("sent")
# define endpoint


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


@app.get("/")
def Home():
    return "Welcome home"


@app.get("/webhooks")
async def connect(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    verify_token: str = Query(..., alias="hub.verify_token")
):
    print(hub_mode, hub_challenge, verify_token)
    return int(hub_challenge)


@app.post("/webhooks")
def get_message(request_body: dict = Body(...)):
    try:
        number = request_body["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        msg = request_body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
        print(f"{number}:{msg}")
        ints = predict_class(msg, model)
        response = getResponse(ints, intents)
        response = str(response)
        send_message(number, response)
        return {"message": "success"}
    except Exception as e:
        print(e)
        return {"message": "failed"}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    try:
        while True:

            msg = await websocket.receive_text()
            print(msg)
            if msg == 'ping':
                message = {"sender": "bot", "msg": "Hello how can i help you?"}
            elif msg == 'close':
                # await websocket.send_json({"sender": "you", "msg": msg})
                # await websocket.send_json({"sender": "bot", "msg": "Okay bye!"})
                await websocket.close()
                break
            else:
                await websocket.send_json({"sender": "you", "msg": msg})
                ints = predict_class(msg, model)
                response = getResponse(ints, intents)
                response = str(response)
                print(response)
                message = {"sender": "bot", "msg": response}

            await websocket.send_json(message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"time": current_time,
                   "clientId": client_id, "message": "Offline"}
        await manager.broadcast(json.dumps(message))

if __name__ == "__main__":
    public_url = ngrok.connect(8000).public_url
    print(public_url)
    uvicorn.run(app, host="0.0.0.0", port=8000)
