import wasteof
import requests, urllib
import os
import random
from flask import Flask
import imgbbpy

#session = wasteof.Session(os.environ["session"])
#session.post_reply("test reply", parent="630d461537a6aba9065f8a6c", post_id="6184165e9dd808c2c76f9e2d")

client = wasteof.Client(os.environ["session"], prefix="@pico-bot ", username="pico-bot")
imgbb_client = imgbbpy.SyncClient(os.environ["imgbbapi"])

@client.command
def messages(scratcher):

    try:
        count = requests.get(
            f"http://explodingstar.pythonanywhere.com/scratch/user/messages/{scratcher}/",
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
            },
        )
        count = count.json()['count']
        return f"<strong>{scratcher}</strong> has <strong>{count:,}</strong> unread messages!"
    except Exception:
        return  "Scratcher not found"

@client.command
def profile(scratcher):
    data = requests.get(f"http://explodingstar.pythonanywhere.com/scratch/user/profile/{scratcher}").json()
    return f"<strong>{scratcher}'s Profile</strong></p><p><em>About me:</em></p><p>"+data['profile']['bio'].replace('\n', '</p><p>')+"</p><p><em>What I am working on:</em></p><p>"+data['profile']['status'].replace('\n', '</p><p>')+"</p><p><em>Join Date:</em></p><p>"+data['history']['joined'][:-14]

@client.command
def nfe(project_id):
    try:
        return f"<strong>Moderation status:</strong> "+requests.get("https://jeffalo.net/api/nfe/?project="+project_id).json()["status"]
    except Exception:
        return "Something went wrong, try again"

@client.command
def yoshi():
    search = "YOSHI"
    data = requests.get(f"https://tenor.googleapis.com/v2/search?q={search}&key={os.environ['tenorapi']}&client_key='WasteOf Bot'&limit=50").json()
    gif = random.choice(data["results"])
    gif = gif['media_formats']['gif']['url']

    r = requests.get(gif)
    with open('image.gif', 'wb') as f:
        f.write(r.content)
    image = imgbb_client.upload(file='image.gif')

    return '', image.url, True

@client.command
def calc(equation):
    if "os" in equation or "requests" in equation or "self" in equation or "environ" in equation:
        return "Don't try to hack me 😡"
    return f"🔢 {equation} = "+str(eval(equation))
client.run(thread=True)

# Server:

app = Flask(__name__)

@app.route('/')
def index():
    return {"status":"up"}

app.run("0.0.0.0", port=8080)
