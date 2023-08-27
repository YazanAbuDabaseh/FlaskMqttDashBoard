# this is a simple mqtt publisher using locan broker
# https://www.youtube.com/watch?v=c_DPKujOmGw

import paho.mqtt.client as paho
import sys
import random

#client_id = f'python-mqtt-{random.randint(0, 1000)}'
client = paho.Client()

host = "broker.emqx.io"
port = 1883
timeout = 60
if client.connect(host, port, timeout) != 0:
    print("could not connect to btoker!")
    sys.exit(-1)

topic = "test/status/Yazan1231231"
msg = 1235245245
qos = 0
client.publish(topic, msg, qos)
print("Done!!")


client.disconnect()