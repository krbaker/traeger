import time
import ssl
import paho.mqtt.client as mqtt
import requests
import uuid
import urllib
import json


CLIENT_ID = "2fuohjtqv1e63dckp5v84rau0j"

class traeger:
    def __init__(self, username, password, token = None, token_expires = 0, mqtt_url = None, mqtt_url_expires = 0, mqtt_uuid = str(uuid.uuid1())):
        self.username = username
        self.password = password
        self.token = token
        self.token_expires = token_expires
        self.mqtt_url = mqtt_url
        self.mqtt_url_expires = mqtt_url_expires
        self.mqtt_uuid = mqtt_uuid
        self.get_grills()
        self.mqtt_client = None
        self.grill_status = {}

    def token_remaining(self):
        return self.token_expires - time.time()

    def refresh_token(self):
        if self.token_remaining() < 60:
            request_time = time.time()
            r = requests.post("https://cognito-idp.us-west-2.amazonaws.com/", json = 
                    {"AuthFlow":"USER_PASSWORD_AUTH",
                     "AuthParameters":{"USERNAME": self.username,
                                       "PASSWORD": self.password},
                     "ClientId": CLIENT_ID},
                              headers = {'Content-Type': 'application/x-amz-json-1.1',
                                         'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'})
            response = r.json()
            self.token_expires = response["AuthenticationResult"]["ExpiresIn"] + request_time
            self.token = response["AuthenticationResult"]["IdToken"]

    def get_user_data(self):
        self.refresh_token()
        r = requests.get("https://1ywgyc65d1.execute-api.us-west-2.amazonaws.com/prod/users/self",
                         headers = {'authorization': self.token})
        json = r.json()
        return json

    def get_grills(self):
        json = self.get_user_data()
        self.grills = json["things"]
        return self.grills

    def mqtt_url_remaining(self):
        return self.mqtt_url_expires - time.time()

    def refresh_mqtt_url(self):
        self.refresh_token()
        if self.mqtt_url_remaining() < 60:
            mqtt_request_time = time.time()
            r = requests.post("https://1ywgyc65d1.execute-api.us-west-2.amazonaws.com/prod/mqtt-connections",
                              headers = {'authorization': self.token})
            json = r.json()
            self.mqtt_url_expires = json["expirationSeconds"] + mqtt_request_time
            self.mqtt_url = json["signedUrl"]

    def get_mqtt_client(self, on_connect, on_message):
        if self.mqtt_client == None:
            self.refresh_mqtt_url()
            mqtt_parts = urllib.parse.urlparse(self.mqtt_url)
            self.mqtt_client = mqtt.Client(transport = "websockets")
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            headers = {
                "Host": "{0:s}".format(mqtt_parts.netloc),
                }
            self.mqtt_client.ws_set_options(path="{}?{}".format(mqtt_parts.path, mqtt_parts.query), headers=headers)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.mqtt_client.tls_set_context(context)
            self.mqtt_client.connect(mqtt_parts.netloc, 443)
            self.mqtt_client.loop_start()
        return self.mqtt_client

    def grill_message(self, client, userdata, message):
        if message.topic.startswith("prod/thing/update/"):
            grill_id = message.topic[len("prod/thing/update/"):]
            self.grill_status[grill_id] = json.loads(message.payload)
        
    def grill_connect(self, client, userdata, flags, rc):
        pass
    
    def get_grill_status(self, timeout = 10):
        client = self.get_mqtt_client(self.grill_connect, self.grill_message)
        for grill in self.grills:
            if grill["thingName"] in self.grill_status:
                del self.grill_status[grill["thingName"]]
            client.subscribe(("prod/thing/update/{}".format(grill["thingName"]),1))
        for grill in self.grills:
            remaining = timeout
            while not grill["thingName"] in self.grill_status and remaining > 0:
                time.sleep(1)
                remaining -= 1                    
        return self.grill_status
