
import paho.mqtt.client as mqtt
import ssl, socket
import json
import drivercode
import threading
#from threading import Timer
import time
import calendar
import geocoder
import os
import packetoperations

client = None
stop_session_counter = 0
start_session_live = False
stop_session_live = False
interval_state = False
interval_call = None
test_counter = 0
received_interval_counter = 0
interval_logging_counter = 0

# Location test values
longitude = "103.820060"
latitude  = "1.272505"

class RepeatedTimer(object):
  def __init__(self, interval, function):#, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    #self.args = args
    #self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function()#(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False

 # Initiates start_session()
 # Handles button spamming
def start_session_no_spam():

   global start_session_live
   global stop_session_live

   if (start_session_live == False):
     while True:
       # Attempt the session
       try:
          drivercode.start_session()
       # If session attempt fails because of DBus...
       except:
          print("Entered exception block")
          continue

       start_session_live = True  
       stop_session_live = False
       print("Start session successful")

       break

def stop_session_no_spam():

     global start_session_live
     global stop_session_live

     if (stop_session_live == False):    

       while True:
         # Attempt the session
         try:
            drivercode.stop_session()
         # If session attempt fails because of DBus...
         except:
            print("Entered exception block")
            continue

         stop_session_live = True
         start_session_live = False  
         print("Stop session successful")
         break

def interval_logging():

    print("Entered interval logging")

    # global interval_logging_counter
    # if (interval_logging_counter == 0):
    #   interval_logging_counter += 1
    #   return

    stop_session_no_spam()
    start_session_no_spam()


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc, *extra_params):
   #global client
   global test_counter
   global serial_number
   test_counter += 1
   print(('Connected with result code '+str(rc)))
   # Subscribing in on_connect() means that if we lose the connection and
   # reconnect then subscriptions will be renewed.
   client.subscribe('bosch/attribute')
   client.subscribe('bosch/telemetry')
   client.subscribe('bosch/rpc/' + str(serial_number) +'/')

   # Trying to get location, doesn't seem to work atm
   # Location from IP returns lat & long in Kansas, USA

   # Deprecated library for location
   # send_url = 'http://freegeoip.net/json'
   # r = requests.get(send_url)
   # j = json.loads(r.text)
   # lat = j['latitude']
   # lon = j['longitude']
   # print(lat)
   # print(type(lat))

   #g = geocoder.ip('15.211.146.34')
   #print(g.latlng)
   #location(g.latlng)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
   global serial_number
   
   print('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
   if msg.topic.startswith( 'bosch/rpc/' + str(serial_number) +'/'):
       requestId = msg.topic[len('bosch/rpc/' + str(serial_number) +'/'):len(msg.topic)]
       print('This is a RPC call. RequestID: ' + requestId + '. Going to reply now!')
       #client.publish('v1/devices/me/rpc/response/' + requestId, "{\"value1\":\"A\", \"value2\":\"B\"}", 1)

   global interval_state
   global interval_call
   global received_interval_counter

   if "true" in str(msg.payload):

    if (interval_state == False):

      start_session_no_spam()


   if "false" in str(msg.payload):

    if (interval_state == True):
      interval_state = False
      stop_session_no_spam()
      received_interval_counter = 0
      interval_call.stop()

    else:
      stop_session_no_spam()  


   if "500" in str(msg.payload):
   #global test_counter
   #if (test_counter == 1 or test_counter == 2):
      #global received_interval_counter
      if (received_interval_counter == 0):
        received_interval_counter += 1

        interval = str(msg.payload).split('"')[3]

        # Type cast
        try:
          interval = int(interval)
        except:
          print("Incorrect interval parameter received. Stopping log.")
          #stop_session_no_spam()
          return  

        # Interval sent from dashboard is in minutes, convert to seconds
        interval *= 60  
        #global interval_state
        # Run only if an interval is not set already
        if (interval_state == False):

          interval_state = True

          start_session_no_spam()

          # Hardcoded to 1 min = 60 sec logging for testing
          interval_call = RepeatedTimer(interval,interval_logging)

#def location(lat_long):          

#
# upload(): ---------------------------------------------------------------
# Method called when data is successfully received
#
# Parameter definition:
#   temperature_data: Python List of temperature values recorded
#   humidity_data   : Python List of humidity values recorded
#   pressure_data   : Python List of pressure values recorded
#   unix_timestamp  : Python List of Unix Timestamp values at which above parameters are recorded
# 
# Note: Temperature, humidity, pressure values are all recorded at the same time
#   => Temperature, humidity, pressure have the same Timestamp
#
#
def upload_data(serial_number, temperature_data, unix_timestamp, humidity_data, pressure_data, battery_data):
    #global latitude
    #global longitude
    global client
    json_array={}
    for i,w in enumerate(unix_timestamp):
        json_array={
	"ID":serial_number,
         "telemetry":
            {"ts":w, "values":
                {"Bosch-temperature":temperature_data[i],
               "Bosch-humidity":humidity_data[i],
               "Bosch-pressure":pressure_data[i], 
               "Bosch-battery":battery_data[i]
                }
             }
        }
        json_data = json.dumps(json_array)
        print(json_data)
        client.publish('bosch/telemtry',str(json_data), 1)

    #latitude = float(latitude)
    #latitude += 1
    #latitude = str(latitude)
        # client = mqtt.Client()
        # client.on_connect = on_connect
        # client.on_message = on_message

        # client.tls_set(ca_certs="mqttserver.pub.pem", certfile="mqttclient.nopass.pem", keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
        #                        tls_version=ssl.PROTOCOL_TLSv1, ciphers=None);

        # client.tls_insecure_set(False)
        # client.connect('thingsboard', 8883, 1)
        # print("Entered upload method")


        # # Blocking call that processes network traffic, dispatches callbacks and
        # # handles reconnecting.
        # # Other loop*() functions are available that give a threaded interface and a
        # # manual interface.
        # client.loop_forever()

# Parameters are all strings
# Method called only once on establishing connection
def upload_device_info(year, month, day, serial_number, factory_line):
    print("Entered device upload method")
    global client
    json_array = {}
    #json_array.append({"ts":1532681566000, "values": "Test_Upload"})
    month=calendar.month_name[int(month)]
    production_date = year + " " + month + " " + day
    #print(production_date)
    json_array={"ID":serial_number,
                "payload":
                {"Bosch-production-date": production_date,
                "Bosch-serial-number": serial_number,
                "Bosch-factory-line": factory_line}
               }
                         
    json_data = json.dumps(json_array)

    print(json_data)

    client.publish('bosch/attribute',str(json_data), 1)

def send_test_location():

  print("Entered send location method")

  global client
  json_array = []
  # test timestamps
  timestamp = []
  for i in range(0,72):
    timestamp.append(1532941500000 + i * 1000)

  # Test latitudes
  latitude = ["46.9287656",
"46.9283131",
"46.9282338",
"46.9281541",
"46.9280745",
"46.9279765",
"46.9278852",
"46.9277815",
"46.9276836",
"46.9275951",
"46.9274287",
"46.9273553",
"46.927356" ,
"46.9272912",
"46.9273532",
"46.9273618",
"46.9272823",
"46.9271988",
"46.9272078",
"46.9272591",
"46.9273014",
"46.9272618",
"46.9272441",
"46.9272195",
"46.9271681",
"46.9271349",
"46.9270779",
"46.9270253",
"46.9269912",
"46.9269634",
"46.9269282",
"46.926898" ,
"46.9268767",
"46.9269463",
"46.9270414",
"46.92711",
"46.9271516",
"46.927239" ,
"46.9272063",
"46.9271683",
"46.9271242",
"46.9270968",
"46.9270678",
"46.9270374",
"46.927034" ,
"46.9270142",
"46.9270046",
"46.9270182",
"46.9270626",
"46.9271179",
"46.9271721",
"46.9272498",
"46.9270652",
"46.9270162",
"46.9269837",
"46.9249767",
"46.9236719",
"46.9236271",
"46.9234525",
"46.9234812",
"46.9229831",
"46.9228859",
"46.9227945",
"46.9227008",
"46.9226081",
"46.9225276",
"46.922442" ,
"46.9222829",
"46.9221856",
"46.922115" ,
"46.9274247",
"46.9272316",
"46.9272423"]
  # Test longitudes
  longitude = ["3.2569153",
"3.2570746",
"3.2571643",
"3.2572556",
"3.2573218",
"3.2573608",
"3.2573636",
"3.2573633",
"3.2573595",
"3.2573934",
"3.2574248",
"3.2573397",
"3.2571939",
"3.2562013",
"3.2563165",
"3.25645",
"3.2565125",
"3.2565913",
"3.256725",
"3.2568793",
"3.2571319",
"3.2572572",
"3.2573876",
"3.2575186",
"3.2576359",
"3.2577744",
"3.2578872",
"3.2580108",
"3.2581512",
"3.2582936",
"3.2584194",
"3.2585443",
"3.2586903",
"3.2587964",
"3.2588106",
"3.2589101",
"3.2590354",
"3.2590781",
"3.2592086",
"3.2593389",
"3.2594541",
"3.2595854",
"3.2597251",
"3.2598587",
"3.260005",
"3.2601456",
"3.2602786",
"3.2604193",
"3.2605445",
"3.260655",
"3.2607623",
"3.2610836",
"3.261214",
"3.2610884",
"3.2609622",
"3.2592008",
"3.259914",
"3.2600307",
"3.2601549",
"3.2603292",
"3.260215",
"3.2602383",
"3.2602709",
"3.2603239",
"3.2603743",
"3.2604477",
"3.2605279",
"3.260583",
"3.2605743",
"3.2604765",
"3.258841",
"3.2610083",
"3.2610297"]

  for i,w in enumerate(timestamp):
        json_array.append({"ts":w, "values":{"Bosch-latitude":latitude[i],"Bosch-longitude":longitude[i]}})
        #latitude += 0.001

  json_data = json.dumps(json_array)
  print(json_data)
        # client = mqtt.Client()
        # client.on_connect = on_connect
        # client.on_message = on_message
  client.publish('v1/devices/me/telemetry',str(json_data), 1)


# Called to open a connection with Thingsboard
def establish_connection():

    #Scan for bosch devices
    f=open('scan.txt','w')
    f.write('')
    f.close()

    print('Scaning for Bosch devices...')
    os.system("sh scan.sh")

    f=open('scan.txt','r')
    content=f.read()
    while content=='':
        f=open('scan.txt','r')
        content=f.read()
    #

    devices=[]
    content=content.split('\n')

    for line in content:
        if 'Bosch' in line:
            devices.append(line.split(' ')[0])
    #
    print(devices)

    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set(ca_certs="ca.crt", certfile="test1.crt", keyfile="test1.key", cert_reqs=ssl.CERT_REQUIRED,
                               tls_version=ssl.PROTOCOL_TLSv1, ciphers=None);

    client.tls_insecure_set(True)
    client.connect('tb.hpe-innovation.center', 18883, 1)
    print("Connection established")


    #drivercode.get_device_information()
    #drivercode.stop_session()
    # while True:
    #    # Attempt to get device information
    #       drivercode.get_device_information()
    #    # If session attempt fails because of DBus...
    #    except:
    #       print("Entered exception block")
    #       continue

    #    break

    # To reset a start_session() that might be going on
    print("***************Resetting***************")
    #stop_session_no_spam()


    # Get device information 
    while True:
         # Attempt to get device information
        try:
            for dev in devices:
                drivercode.get_device_information(dev)
        # If session attempt fails because of DBus...
        except:
            print("Entered exception block in senddata")
            continue

        break

    # Send dummy location points
    #send_test_location()   


    client.loop_forever()
