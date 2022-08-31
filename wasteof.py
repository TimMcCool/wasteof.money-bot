from threading import Thread
import requests
import os, json
os.system("pip install websocket-client")

agent = "Mozilla/5.0 (<system-information>) <platform> (<platform-details>) <extensions>"
    
import websocket

class Session:
    
    def __init__(self, session_id, **entries):

        self.session_id = session_id
        self.__dict__.update(entries)

    
    def post_reply(self, content, *, image=None, post_id, parent):
        if image is None: 
            content = '<p>'+content+'</p>'
        else:
            content = '<p>'+content+'</p><img src=\"'+image+'\" alt=\"Image\" height=\"50\">'
        r = requests.post(
            f"https://api.wasteof.money/posts/{post_id}/comments",
            headers = {
                "accept-language": "en,en;q=0.9",
                "authorization": self.session_id,
                "content-type": "application/json",
                "sec-ch-ua": "\"Google Chrome\";v=\"95\", \"Chromium\";v=\"95\", \";Not A Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "referrer": "https://wasteof.money/",
                "referrerPolicy": "strict-origin-when-cross-origin",

            },
            json = {"content":content,"parent":parent}
        )
        print(r, r.text)
        return r.json()

    def get_messages(self):
        return requests.get(
            "https://api.wasteof.money/messages/unread/?limit=10",
            headers =  {
                "accept-language": "de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "authorization": self.session_id,
                "if-none-match": "W/\"74d-WwvpAmJblcKDRZ3Yq6XM4IRYEgU\"",
                "sec-ch-ua": "\"Microsoft Edge\";v=\"95\", \"Chromium\";v=\"95\", \";Not A Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "referrer": "https://wasteof.money/",
                "referrerPolicy": "strict-origin-when-cross-origin",
            }
        ).json()



class MessageEvents:
    '''
    Calls events when the wasteof user receives a message
    '''

    def __init__(self, session_id):
        self.session_id = session_id
        self.on_count_update = None
        self.running = False
        self.ws = websocket.WebSocket()

    def parse_count(self, msg):
        return msg.split(",")[1][:-1]
    
    def receive(self):
        r = self.ws.recv()
        if "updateMessageCount" in r:
            count = self.parse_count(r)
            if self.on_count_update is not None:
                self.on_count_update(int(count))
                    
    def connect(self):

        r = requests.get(
            f"https://api.wasteof.money/socket.io/?EIO=4&transport=polling&t=0",
            headers= {"User-Agent":agent}
            
        ) #get WS_SID
        WS_SID = json.loads(r.text[1:])["sid"]
        print(WS_SID)


        r = requests.post(
            f"https://api.wasteof.money/socket.io/?EIO=4&transport=polling&t=0&sid={WS_SID}",
            data = '40{"token":"'+self.session_id+'"}',
            headers= {"User-Agent":agent}

        ) #confirm WS_SID   
           
        r = requests.get(
            f"https://api.wasteof.money/socket.io/?EIO=4&transport=polling&t=0&sid={WS_SID}",
            headers= {"User-Agent":agent}

        ) #idk tbh
        if "updateMessageCount" in r.text:
            count = self.parse_count(r.text)
            if self.on_count_update is not None:
                self.on_count_update(int(count))

        
        ####
        self.ws.connect(
            f"wss://api.wasteof.money/socket.io/?EIO=4&transport=websocket&sid={WS_SID}",
            enable_multithread=True,
        )

        self.ws.send("2probe")
        self.receive()
        self.ws.send("5")
        self.receive()
        
            
    def event(self, f):
        if f.__name__ == "on_count_update":
            self.on_count_update = f

    def _run(self):
        
        self.connect()
        
        while self.running:
            self.ws.send("3")
            try:
                self.receive()
            except Exception as e:
                print("disconnected", e)
                self.connect()

            
    def start(self, thread=True):
        self.running = True
        if thread:
            self.thread = Thread(target=self._run)
            self.thread.start()
        else:
            self._run()

    
class Client:
    '''
    A framework for creating wasteof bots, inspired by discord.py
    '''

    def __init__(self, session_id, *, username, prefix):
        self.session = Session(session_id)
        self.commands = []
        self.on_ready = None
        self.running = False
        self.prefix = prefix
        self.messages = []
        self.username = username

    def command(self, f):
        self.commands.append(f)
    
    def event(self, f):
        if f.__name__ == "on_ready":
            self.on_ready = f

    
    def _run(self):
        events = MessageEvents(os.environ["session"])

        @events.event
        def on_count_update(new_count):
            print(new_count)
            self.messages = self.session.get_messages()["unread"]
            
        events.start()

        self.messages = self.session.get_messages()["unread"]
        message_cache = self.messages

        replied_cache = []
        for message in self.messages:
            if message['type'] == "comment":
                try:
                    replied_cache.append(message["data"]["comment"]["_id"])
                except Exception as e:
                    print(e)


        while self.running:
            if message_cache != self.messages:
                for message in self.messages:
                    try:
                        if message['type'] == "comment" or message['type'] == "comment_reply":
                            if not message in message_cache or replied_cache:
                                ts = message['time']
                                if message['to']['name'] == self.username:
                                    content = message["data"]["comment"]["content"].replace("<p>","").replace("</p>","")                                    
                                    if not message["data"]["comment"]["_id"] in replied_cache:
                                        replied_cache.append(message["data"]["comment"]["_id"])
                                        if content.startswith(self.prefix):
                                            args = content.split(" ")
                                            args.pop(0)
                                            request = args.pop(0)
                                            print(request)
                                            matching = list(filter(lambda x : x.__name__ == request, self.commands))
                                            if matching == []:
                                                output = "Request not found!"
                                            else:
                                                try:
                                                    output = matching[0](*args)
                                                except Exception as e:
                                                    output = str(e)

                                            image = None
                                            if output[2] == True:
                                                image = output[1]
                                                output = output[0]
                                            output=output.encode("latin-1","ignore")
                                            output = output.decode("utf-8")

                                            
                                            new_post = self.session.post_reply(output, image=image, post_id=message["data"]["post"]["_id"], parent=message["data"]["comment"]["_id"])
                                            print(new_post) 
                            else:
                                continue
                    except Exception as e:
                        print("error", e)
                message_cache = self.messages

    
    def run(self, thread=False):
        self.running = True
        if thread:
            self.thread = Thread(target=self._run)
            self.thread.start()
        else:
            self._run()

            
    def stop(self):
        self.running = False

