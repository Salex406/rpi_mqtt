import paho.mqtt.client as mqtt
import time

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("base/relay/led1")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client(client_id="mqtt-iprofi_165438284-xqoa45")
client.on_connect = on_connect
client.on_message = on_message

client.connect("sandbox.rightech.io", 1883, 60)
client.loop_start()
tmp =1 

while True:
	print("OK")
	client.publish("base/state/temperature", payload=str(tmp))
	tmp += 1
	time.sleep(4)
