
#
# upload(): ---------------------------------------------------------------
# Method called when data is successfully received
#
# Parameter definition:
# 	temperature_data: Python List of temperature values recorded
# 	humidity_data   : Python List of humidity values recorded
#   pressure_data   : Python List of pressure values recorded
#   unix_timestamp  : Python List of Unix Timestamp values at which above parameters are recorded
# 
# Note: Temperature, humidity, pressure values are all recorded at the same time
#		=> Temperature, humidity, pressure have the same Timestamp
#

import paho.mqtt.client as mqtt
import ssl, socket
import json

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc, *extra_params):
   print(('Connected with result code '+str(rc)))
   # Subscribing in on_connect() means that if we lose the connection and
   # reconnect then subscriptions will be renewed.
   client.subscribe('v1/devices/me/attributes')
   client.subscribe('v1/devices/me/attributes/response/+')
   client.subscribe('v1/devices/me/rpc/request/+')


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
   print('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
   if msg.topic.startswith( 'v1/devices/me/rpc/request/'):
       requestId = msg.topic[len('v1/devices/me/rpc/request/'):len(msg.topic)]
       print('This is a RPC call. RequestID: ' + requestId + '. Going to reply now!')
       client.publish('v1/devices/me/rpc/response/' + requestId, "{\"value1\":\"A\", \"value2\":\"B\"}", 1)

def upload(temperature_data, unix_timestamp, humidity_data, pressure_data):
    for i,w in enumerate(unix_timestamp):
        json_array={"Bosch_temperature":temperature_data[i],"Bosch_humidity":humidity_data[i],"Bosch_pressure":pressure_data[i]}
        json_data = json.dumps(json_array)
        print(json_data)
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.publish('v1/devices/me/attributes',str(json_data), 1)

        client.tls_set(ca_certs="mqttserver.pub.pem", certfile="mqttclient.nopass.pem", keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                               tls_version=ssl.PROTOCOL_TLSv1, ciphers=None);

        client.tls_insecure_set(False)
        client.connect('thingsboard', 8883, 1)
	      print("Entered upload method")


        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
#         client.loop_forever()
