import paho.mqtt.client as mqtt
import config
import json
from datetime import datetime
from azure.iot.device import IoTHubDeviceClient
from azure.iot.device.exceptions import ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError
from azure.iot.device import Message
import requests

#callback
def on_data_recieved(client, userdata, msg):
    #unwrap message
    json_data = msg.payload.decode('utf-8')
    data = json.loads(json_data)

    #add timestamp to data
    data['measured_at'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    print(data)
    
    #send data to api
    post_data_to_api(json.dumps(data), "http://downeypi.local:5000/api/weather_data/post")

def post_data_to_api(data, api):
    r = requests.post(api, data)
    print(f"Status Code: {r.status_code}, Response: {r.json()}")

def send_data_to_iot_hub(device_client: IoTHubDeviceClient, message):
    telemetry = Message(json.dumps(message))
    telemetry.content_encoding = "utf-8"
    telemetry.content_type = "application/json"
    
    try:
        device_client.send_message(telemetry)
    except (ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError):
        raise("Message failed to send, skipping")
    else:
        print("Message successfully sent!", message)

device_client = IoTHubDeviceClient.create_from_connection_string(config.IOT_HUB_CONNECTION_STRING, connection_retry=False)
device_client.connect()

client = mqtt.Client('weather_data_client')
client.message_callback_add(config.TOPIC_SUB, on_data_recieved)
client.connect(config.MQTT_SERVER, 1883)
client.subscribe(config.TOPIC_SUB)
client.loop_forever()
