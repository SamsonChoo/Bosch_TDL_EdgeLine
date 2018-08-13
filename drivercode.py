
from optparse import OptionParser, make_option
import re
import sys
import dbus
import dbus.mainloop.glib
from dbus.mainloop.glib import DBusGMainLoop
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

import bluezutils
#import gattoperations as gatt
#import gattcallbacks as cb
import packetoperations

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE =    'org.bluez.GattDescriptor1'

#BOSCH_MAC_ADDRESS =  "A0:E6:F8:6C:8B:87"

bus = None
mainloop_start = None
mainloop_stop = None
mainloop = None
# global receive_state
receive_state = False

packet_arr = []

temp_packet_holder = []

counter_realtime_status = 0
counter_data_transfer_status = 0
counter_data_transfer_download = 0
counter_start_session = 0
auth_connection_counter = 0
default_status_value_counter = 0
data_transfer_status_changed_counter = 0
transfer_ongoing_counter = 0
temp_packet_holder_counter = 0
delete_logged_data_counter = 0

def reset_counters():

	global counter_realtime_status
	global counter_data_transfer_status
	global counter_data_transfer_download
	global counter_start_session 
	global auth_connection_counter 
	global default_status_value_counter
	#global data_transfer_status_changed_counter 
	global transfer_ongoing_counter 
	global temp_packet_holder_counter 
	global delete_logged_data_counter 


	counter_realtime_status = 0
	counter_data_transfer_status = 0
	counter_data_transfer_download = 0
	counter_start_session = 0
	auth_connection_counter = 0
	default_status_value_counter = 0
	#data_transfer_status_changed_counter = 0
	transfer_ongoing_counter = 0
	temp_packet_holder_counter = 0
	delete_logged_data_counter = 0

def terminate():
	global mainloop
	global bus
	mainloop.quit()
	mainloop = None
	bus = None
	print("Terminated mainloop")

def disconnect_device(mac_address):

	tdl_mac_address = "A0:E6:F8:6C:8B:87"
	device = bluezutils.find_device(mac_address, None)
	device.Disconnect()
	print("Disconnected")	

def connect_device(mac_address):
	tdl_mac_address = "A0:E6:F8:6C:8B:87"
	device = bluezutils.find_device(mac_address, None)
	device.Connect()
	print("Connected")	

# ------------------------------------Callbacks------------------------------------


# Error handler, called on any generic error
def generic_error_cb(error):

    print('D-Bus call failed: ' + str(error))
    terminate()

def read_log_cb(value):
	#print("Entered read_log_handler")
	print(value)
	#terminate()

def read_device_info_cb(value):
	print("Entered read device information callback")
	#print(value)
	packetoperations.process_serial_number(value)
	disconnect_device(BOSCH_MAC_ADDRESS)
	terminate()	

# def auth_connection_cb():
# 	return
	#print("Entered auth_connection handler")
	#terminate()
	#read_log_status()

#-----------------------------------------------------------------------	

def realtime_status_cb():
	print("Realtime status enabled")
	#global mainloop
	#smainloop.run()
	enable_data_transfer_status_notification(BOSCH_MAC_ADDRESS)

def realtime_status_changed_cb(iface, changed_props, invalidated_props):
	global counter_realtime_status
	#print(counter)
	if (counter_realtime_status == 0):
		counter_realtime_status += 1
		return

	#counter_realtime_status = 0
	# print("Realtime status changed")

	value = changed_props.get('Value', None)
	#print("Realtime status changed:")
	#print(value)

	# 25 -- connecion authenticated notification
	if(value[0] == 25):
		global auth_connection_counter
		if (auth_connection_counter == 0):
			auth_connection_counter += 1
			print("Connection authenticated")
			global receive_state

			# For start_session()
			if(receive_state == False):

				# Caveat to stop logging in start session
				#stop_logging()
				delete_logged_data(BOSCH_MAC_ADDRESS)

			# For stop_session()	
			else:
				print('Attempting to stop logging')
				stop_logging(BOSCH_MAC_ADDRESS)
		# stop_logging()	


	#terminate()
	elif (value[0] == 0):

		global default_status_value_counter

		# print("Check counter %d\n" %(default_status_value_counter))

		if (default_status_value_counter == 0):
			default_status_value_counter += 1

			# Stop session
			#global receive_state
			if(receive_state == True):
				print("Requesting data transfer")
				request_data_transfer_init(BOSCH_MAC_ADDRESS)

			# Start session
			else:
				# global counter_start_session
				# if (counter_start_session == 0):
				# 	counter_start_session += 1
				# 	delete_logged_data()
				# Disconnect from device
				print("Disconnecting in real time status changed")
				disconnect_device(BOSCH_MAC_ADDRESS)

				terminate()

	# Logged data deleted successfully
	elif (value[0] == 33 or value[0] == 17):

		global delete_logged_data_counter
		if (delete_logged_data_counter == 0):
			delete_logged_data_counter += 1
			print("Logged data deleted successfully")
			start_logging(BOSCH_MAC_ADDRESS)

def data_transfer_status_cb():
	print("Data transfer status enabled")
	enable_data_transfer_download_notification(BOSCH_MAC_ADDRESS)
	#terminate()

def data_transfer_status_changed_cb(iface, changed_props, invalidated_props):
	global counter_data_transfer_status
	#print(counter)
	if (counter_data_transfer_status == 0):
		counter_data_transfer_status += 1
		return

	global data_transfer_status_changed_counter
	#print("Entered data transfer status changed cb")
	# if (data_transfer_status_changed_counter == 0):
	# 	data_transfer_status_changed_counter += 1
	#print("Entered data transfer status changed cb")
	#counter_data_transfer_status = 0
	#print("Data transfer status changed")
	value = changed_props.get('Value', None)

	if (value[0] == 1):
		global transfer_ongoing_counter
		if (transfer_ongoing_counter == 0):
			transfer_ongoing_counter += 1
			print("Transfer ongoing")

	if (value[0] == 2):
		if (data_transfer_status_changed_counter == 0):
			data_transfer_status_changed_counter += 1
			print("Transfer done!")

			#Disconnect from device
			print("Disconnecting in data transfer status")
			disconnect_device(BOSCH_MAC_ADDRESS)

			global packet_arr
			#packet_arr = []
			packetoperations.process_packet(packet_arr)
			packet_arr = []
			print("Terminating...")
			terminate()	

def data_transfer_download_cb():
	print("Data transfer download enabled")
	# All notifications now enabled...
	#global mainloop
	#mainloop.run()
	auth_connection(BOSCH_MAC_ADDRESS)
	#terminate()

def data_transfer_download_changed_cb(iface, changed_props, invalidated_props):
	# print("Entered on transfer download changed")
	global counter_data_transfer_download
	global temp_packet_holder
	global temp_packet_holder_counter
	global packet_arr
	#print(counter)
	if (counter_data_transfer_download == 0):
		counter_data_transfer_download += 1
		return
	#print("Entered on transfer download changed")
	#counter_data_transfer_download = 0
	#print(changed_props)
	if (temp_packet_holder_counter == 0):
		temp_packet_holder_counter += 1
		value = changed_props.get('Value', None)
		temp_packet_holder = value
		#global packet_arr
		#packet_arr = []
		# print(value)
		# print(type(value))
		packet_arr.extend(value)		
		#print(value)
		#print("\n")

	value = changed_props.get('Value', None)

	if(value == temp_packet_holder):
		return
	else:
		# Update packet holder 
		temp_packet_holder = value
		# print(value)
		# print('\n')
		packet_arr.extend(value)


def request_from_packet_cb():
	request_data_transfer_packet_zero(BOSCH_MAC_ADDRESS)	

def request_from_packet_zero_cb():
	request_data_transfer(BOSCH_MAC_ADDRESS)	
#----------------------------------------------------------------------------------

def read_log_status(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service001a/char001d'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)

    read_log_chrc = (chrc, chrc_props)
    #print(read_log_chrc)
    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    read_log_chrc[0].ReadValue({'offset': dbus.UInt16(offset, variant_level=1)}, 
    							dbus_interface=GATT_CHRC_IFACE, 
    							reply_handler = read_log_cb, error_handler= generic_error_cb)
    #print('Set readValue...')

def read_device_information(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service0009/char000e'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)

    read_log_chrc = (chrc, chrc_props)
    #print(read_log_chrc)
    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    read_log_chrc[0].ReadValue({'offset': dbus.UInt16(offset, variant_level=1)}, 
    							dbus_interface=GATT_CHRC_IFACE, 
    							reply_handler = read_device_info_cb, error_handler= generic_error_cb)



# Authenticate connection with device
# 	-> Required to perform any write operation
# Default pin : 1-2-3-4
# Currently PIN is hardcoded, no need to manually enter
def auth_connection(mac_address):

    # Update to required characteristic 
    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service001a/char0036'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01, 0x02, 0x03, 0x04])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE) 
    									   #reply_handler=auth_connection_cb, 
    									   #error_handler=generic_error_cb)
    print("Authenticating connection...")

def delete_logged_data(mac_address):

	# Update to required characteristic 
    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service001a/char0038'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE) 
    									   #reply_handler=auth_connection_cb, 
    									   #error_handler=generic_error_cb)
    print('Wrote delete logged data cmd')									   	    

def request_data_transfer_init(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service003a/char003e'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x02])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE,
    									   reply_handler=request_from_packet_cb,
    									   error_handler=generic_error_cb)	    
    print("Transfer requested")

def request_data_transfer_packet_zero(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service003a/char003e'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x00])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE,
    									   reply_handler=request_from_packet_zero_cb,
    									   error_handler=generic_error_cb)

def request_data_transfer(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service003a/char003e'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE)



def stop_logging(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service001a/char001b'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x00])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE)	    
    #print("Transfer requested")
def start_logging(mac_address):

    char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service001a/char001b'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE)	    
    #print("Transfer requested")

# Method called to start logging for data
def start_session():
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	global bus
	# SystemBus is global and usually started during boot
	bus = dbus.SystemBus()
	global mainloop
	mainloop = GObject.MainLoop()

	reset_counters()

	# Argument check
	#print(sys.argv)

	# Connect to TDL device
	connect_device(BOSCH_MAC_ADDRESS)

	# Trigger enabling notifications
	# enable_realtime_status_notification()
	# Not receiving any data in this session
	global receive_state
	receive_state = False

	# Trigger enabling notifications
	enable_realtime_status_notification(BOSCH_MAC_ADDRESS)

	mainloop.run()

# Method called to stop logging and receive data
def stop_session():

	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	global bus
	#SystemBus is global and usually started during boot
	bus = dbus.SystemBus()
	global mainloop
	mainloop = GObject.MainLoop()

	global data_transfer_status_changed_counter
	data_transfer_status_changed_counter = 0
	reset_counters()

	# Connect to TDL device
	connect_device(BOSCH_MAC_ADDRESS)

	global receive_state
	receive_state = True

	#mainloop.run()
	# Trigger enabling notifications
	#print("Attempting to enable notifications")
	enable_realtime_status_notification(BOSCH_MAC_ADDRESS)

	mainloop.run()	
	# Receiving data in this session
	# global receive_state
	# receive_state = True
	#mainloop.run()
	# 1. Authenticate Connection
	#auth_connection()

	#mainloop.run()

	# 2. Stop Logging
	# stop_logging()

	# 3. Request bulk data transfer
	#request_data_transfer() 

def get_device_information(mac_address):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    global bus

	# SystemBus is global and usually started during boot
    bus = dbus.SystemBus()
    global mainloop
    mainloop = GObject.MainLoop()

    global BOSCH_MAC_ADDRESS
    BOSCH_MAC_ADDRESS = mac_address
	# Connect to TDL device
    connect_device(BOSCH_MAC_ADDRESS)

    read_device_information(BOSCH_MAC_ADDRESS)

    mainloop.run()	


def enable_realtime_status_notification(mac_address):

	# Enable realtime status information notification .......................
	char_path_realtime_status = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service001a/char001d'
	chrc_realtime_status = bus.get_object(BLUEZ_SERVICE_NAME, char_path_realtime_status)
	chrc_props_realtime_status = chrc_realtime_status.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	chrc_arr_realtime_status = (chrc_realtime_status, chrc_props_realtime_status)

	# Listen for changes
	chrc_arr_prop_iface_realtime_status = dbus.Interface(chrc_arr_realtime_status[0], DBUS_PROP_IFACE)
	chrc_arr_prop_iface_realtime_status.connect_to_signal("PropertiesChanged",
                                          realtime_status_changed_cb)

	# Subscribe to notifications
	chrc_arr_realtime_status[0].StartNotify(reply_handler=realtime_status_cb,
	                         	 error_handler=generic_error_cb,
	                             dbus_interface=GATT_CHRC_IFACE)

def enable_data_transfer_status_notification(mac_address):

	char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service003a/char003b'
	chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	chrc_arr = (chrc, chrc_props)

	# Listen for changes
	chrc_arr_prop_iface = dbus.Interface(chrc_arr[0], DBUS_PROP_IFACE)
	chrc_arr_prop_iface.connect_to_signal("PropertiesChanged",
                                          data_transfer_status_changed_cb)

	# Subscribe to notifications
	chrc_arr[0].StartNotify(reply_handler=data_transfer_status_cb,
	                         	 error_handler=generic_error_cb,
	                             dbus_interface=GATT_CHRC_IFACE)

def enable_data_transfer_download_notification(mac_address):

	char_path = '/org/bluez/hci0/dev_'+mac_address.replace(':','_')+'/service003a/char0040'
	chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	chrc_arr = (chrc, chrc_props)

	# Listen for changes
	chrc_arr_prop_iface = dbus.Interface(chrc_arr[0], DBUS_PROP_IFACE)
	chrc_arr_prop_iface.connect_to_signal("PropertiesChanged",
                                          data_transfer_download_changed_cb)

	# Subscribe to notifications
	chrc_arr[0].StartNotify(reply_handler=data_transfer_download_cb,
	                        error_handler=generic_error_cb,
	                        dbus_interface=GATT_CHRC_IFACE)	

#--------------------------------------------------------------------------------------

	# Enable data transfer status notification .......................
	# char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char003b'
	# chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	# chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	# chrc_arr = (chrc, chrc_props)

	# # Listen for changes
	# chrc_arr_prop_iface = dbus.Interface(chrc_arr[0], DBUS_PROP_IFACE)
	# chrc_arr_prop_iface.connect_to_signal("PropertiesChanged",
 #                                          data_transfer_status_changed_cb)

	# # Subscribe to notifications
	# chrc_arr[0].StartNotify(reply_handler=data_transfer_status_cb,
	#                          	 error_handler=generic_error_cb,
	#                              dbus_interface=GATT_CHRC_IFACE)

#--------------------------------------------------------------------------------------

	# Enable data transfer download notification .......................
	# char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char003b'
	# chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	# chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	# chrc_arr = (chrc, chrc_props)

	# # Listen for changes
	# chrc_arr_prop_iface = dbus.Interface(chrc_arr[0], DBUS_PROP_IFACE)
	# chrc_arr_prop_iface.connect_to_signal("PropertiesChanged",
 #                                          data_transfer_download_changed_cb)

	# # Subscribe to notifications
	# chrc_arr[0].StartNotify(reply_handler=data_transfer_download_cb,
	#                          	 error_handler=generic_error_cb,
	#                              dbus_interface=GATT_CHRC_IFACE)


	# Enable data transfer status information notification ..................
	# char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char003b'
	# chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	# chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	# chrc_arr = (chrc, chrc_props)

	# chrc_arr[0].StartNotify(reply_handler=data_transfer_status_cb,
	#                          	 error_handler=generic_error_cb,
	#                              dbus_interface=GATT_CHRC_IFACE)

	# print("Enabled notifications for data transfer status")

	#Enable data transfer download notification .............................
	# char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char003b'
	# chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	# chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	# chrc_arr = (chrc, chrc_props)

	# chrc_arr[0].StartNotify(reply_handler=data_transfer_download_cb,
	#                          	 error_handler=generic_error_cb,
	#                              dbus_interface=GATT_CHRC_IFACE)

	# print("Enabled notifications for data transfer download")



# def main():

# 	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
# 	global bus
# 	# SystemBus is global and usually started durong boot
# 	bus = dbus.SystemBus()
# 	global mainloop
# 	mainloop = GObject.MainLoop()

# 	# Argument check
# 	#print(sys.argv)

# 	# Connect to TDL device
# 	connect_device()

# 	# Trigger enabling notifications
# 	enable_realtime_status_notification()

# 	# Toggle between start/stop session
# 	if (sys.argv[1] == 'start'):
# 		print('Start session')
# 		start_session()
# 	elif (sys.argv[1] == 'stop'):
# 		print('Stop session')
# 		stop_session()	
# 	# stop_session()
# 	#start_session()

# 	mainloop.run()

# if __name__ == '__main__':
#     main()

#sys.exit(0)
