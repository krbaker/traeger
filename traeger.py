import os
import json
import getpass
import requests
from requests.auth import HTTPBasicAuth
import time
import uuid
import urllib
import websockets
import asyncio
import ssl
import paho.mqtt.client as mqtt
import pprint



CLIENT_ID = "2fuohjtqv1e63dckp5v84rau0j"
AIRSHIP_USER = 'iyMjnbXwSb6YkuePXYP3vA'
AIRSHIP_PASS = 'XmmWBzX_RnG1EzmRmGXfJQ'
AIRSHIP_CHANNEL = '38a33729-835b-46b0-9f14-b16ff383d51c'
SEC_WebSocket_Key = "ZTU2YzIwMzQtZDBiMS00Nw=="

def on_connect(client, userdata, flags, rc):
    print("YES!")
    print(str(userdata))

def fail():
    print("No :-(")

pp = pprint.PrettyPrinter(indent=4)

def on_message(client, userdata, message):
    print("Something!")
    print("Received message on topic '"
          + message.topic + "' with QoS " + str(message.qos))
    pp.pprint(json.loads(message.payload))

class traeger:
    def __init__(self, config_file="~/.traeger"):
        self.config = {}
        self.config_file = os.path.expanduser(config_file)
        if os.path.exists(self.config_file):
            try:
                self.config = json.load(open(self.config_file))
            except ValueError:
                pass
        self.mqtt_expires = 0
        self.mqtt_url = None
        if not "uuid" in self.config:
            self.config["uuid"] = str(uuid.uuid1())

    def refresh(self):
        if not "token" in self.config  or self.token_remaining() < 60:
            request_time = time.time()
            r = requests.post("https://cognito-idp.us-west-2.amazonaws.com/", json = 
                    {"AuthFlow":"USER_PASSWORD_AUTH",
                     "AuthParameters":{"USERNAME":self.config["username"],
                                       "PASSWORD":self.config["password"]},
                     "ClientId": CLIENT_ID},
                              headers = {'Content-Type': 'application/x-amz-json-1.1',
                                         'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'})
            response = r.json()
            self.config["expires"] = response["AuthenticationResult"]["ExpiresIn"] + request_time
            self.config["token"] = response["AuthenticationResult"]["IdToken"]

    def get_self(self):
        r = requests.get("https://1ywgyc65d1.execute-api.us-west-2.amazonaws.com/prod/users/self",
                         headers = {'authorization': self.config["token"]})
        json = r.json()
        self.urbanAirshipId = json["urbanAirshipId"] 
        return r.json()

    def get_mqtt(self):
        base = time.time()
        if self.mqtt_expires < base:
            r = requests.post("https://1ywgyc65d1.execute-api.us-west-2.amazonaws.com/prod/mqtt-connections",
                              headers = {'authorization': self.config["token"]})
            json = r.json()
            self.mqtt_expires = json["expirationSeconds"] - 30 + base
            self.mqtt_url = json["signedUrl"]
        return json

    def get_mqtt_client(self):
        print ("Trying to build client...")
        mqtt_parts = urllib.parse.urlparse(self.mqtt_url)
        mqtt_client = mqtt.Client(transport = "websockets")
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        headers = {
            "Host": "{0:s}".format(mqtt_parts.netloc),
            }
        mqtt_client.ws_set_options(path="{}?{}".format(mqtt_parts.path, mqtt_parts.query), headers=headers)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        mqtt_client.tls_set_context(context)
        mqtt_client.connect(mqtt_parts.netloc, 443)
        mqtt_client.loop_start()
        return mqtt_client

    def associate(self):
        r = requests.post("https://device-api.urbanairship.com/api/named_users/associate", json = {
                "channel_id": AIRSHIP_CHANNEL,
                "device_type": "android",
                "named_user_id": self.urbanAirshipId },
                          auth = HTTPBasicAuth(AIRSHIP_USER, 
                                               AIRSHIP_PASS),
                          headers = {'Content-Type': 'application/json',
                                     'Accept': 'application/vnd.urbanairship+json; version=3;'})
        return r.json()

    def token_remaining(self):
        if "expires" in self.config:
            return self.config["expires"] - time.time()
        return -1

    def set_username(self, user):
        self.config["username"] = user

    def set_password(self, passwd):
        self.config["password"] = passwd

    def save(self):
        f = open(self.config_file,"w+")
        json.dump(self.config, f)
        f.close()

if __name__ == "__main__":
    t = traeger()
    if not "username" in t.config:
        t.set_username(input("Enter Username : "))
    if not "password" in t.config:
        t.set_password(getpass.getpass())
    t.refresh()
    print (t.config["token"])
    print (t.config["expires"])
    print (t.token_remaining())
    print (t.get_self())
    print (t.associate())
    print (t.get_mqtt())
    client = t.get_mqtt_client()
    client.subscribe(("prod/thing/update/801F12CA03E1",1))
    while True:
        time.sleep(10)
        client.publish("prod/thing/update/801F12CA03E1", payload=None, qos=0, retain=False)
    #print ("Connecting")
    #s = t.get_mqtt_socket()
    #print ("Connceted")

    t.save()

