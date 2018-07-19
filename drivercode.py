
from optparse import OptionParser, make_option
import re
import sys
import dbus
import dbus.mainloop.glib
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

bus = None
mainloop = None

receive_state = False

packet_arr = []

counter_realtime_status = 0
counter_data_transfer_status = 0
counter_data_transfer_download = 0

def terminate():
	mainloop.quit()

# ------------------------------------Callbacks------------------------------------


# Error handler, called on any generic error
def generic_error_cb(error):

    print('D-Bus call failed: ' + str(error))
    terminate()

def read_log_cb(value):
	#print("Entered read_log_handler")
	print(value)
	#terminate()

# def auth_connection_cb():
# 	return
	#print("Entered auth_connection handler")
	#terminate()
	#read_log_status()

#-----------------------------------------------------------------------	

def realtime_status_cb():
	print("Realtime status enabled")
	enable_data_transfer_status_notification()

def realtime_status_changed_cb(iface, changed_props, invalidated_props):
	global counter_realtime_status
	#print(counter)
	if (counter_realtime_status == 0):
		counter_realtime_status += 1
		return

	#counter_realtime_status = 0
	# print("Realtime status changed")

	value = changed_props.get('Value', None)
	print("Realtime status changed:")
	print(value)

	# 25 -- connecion authenticated notification
	if(value[0] == 25):
		print("Connection authenticated")
		if(receive_state == False):
			delete_logged_data()
		else:
			stop_logging()	


	#terminate()
	elif (value[0] == 0):
		# Stop session
		if(receive_state == True):
			request_data_transfer_init()

		# Start session
		else:
			print("Entered default status value")
			#Disconnect from device
			tdl_mac_address = "A0:E6:F8:6C:8B:87"
			device = bluezutils.find_device(tdl_mac_address, None)
			device.Disconnect()


	# Logged data deleted successfully
	elif (value[0] == 33):		
		print("Logged data deleted successfully")
		start_logging()
def data_transfer_status_cb():
	print("Data transfer status enabled")
	enable_data_transfer_download_notification()
	#terminate()

def data_transfer_status_changed_cb(iface, changed_props, invalidated_props):
	global counter_data_transfer_status
	#print(counter)
	if (counter_data_transfer_status == 0):
		counter_data_transfer_status += 1
		return

	#counter_data_transfer_status = 0
	#print("Data transfer status changed")
	value = changed_props.get('Value', None)
	if (value[0] == 1):
		print("Transfer ongoing")
	if(value[0] == 2):
		print("Transfer done!")

		#Disconnect from device
		tdl_mac_address = "A0:E6:F8:6C:8B:87"
		device = bluezutils.find_device(tdl_mac_address, None)
		device.Disconnect()

		print ("Disconnected")
		global packet_arr
		#packet_arr = []
		packetoperations.process_packet(packet_arr)

		terminate()	

def data_transfer_download_cb():
	print("Data transfer download enabled")
	#terminate()

def data_transfer_download_changed_cb(iface, changed_props, invalidated_props):
	#print("Entered on transfer download changed")
	global counter_data_transfer_download
	#print(counter)
	if (counter_data_transfer_download == 0):
		counter_data_transfer_download += 1
		return

	#counter_data_transfer_download = 0
	#print(changed_props)
	value = changed_props.get('Value', None)
	global packet_arr
	#packet_arr = []
	#print(value)
	packet_arr.extend(value)		
	#print(value)
	#print("\n")

def request_from_packet_cb():
	request_data_transfer_packet_zero()	

def request_from_packet_zero_cb():
	request_data_transfer()	
#----------------------------------------------------------------------------------

def read_log_status():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char001d'
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

# Authenticate connection with device
# 	-> Required to perform any write operation
# Default pin : 1-2-3-4
# Currently PIN is hardcoded, no need to manually enter
def auth_connection():

    # Update to required characteristic 
    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char0036'
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
    #print("Value written")

def delete_logged_data():

	# Update to required characteristic 
    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char0038'
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

def request_data_transfer_init():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service003a/char003e'
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

def request_data_transfer_packet_zero():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service003a/char003e'
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

def request_data_transfer():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service003a/char003e'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE)



def stop_logging():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char001b'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x00])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE)	    
    #print("Transfer requested")
def start_logging():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char001b'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, 
    									   dbus_interface=GATT_CHRC_IFACE)	    
    #print("Transfer requested")

def start_session():
	
	# Not receiving any data in this session
	global receive_state
	receive_state = False

	# Connect to 
	# 1. Authenticate connection
	auth_connection()

	# 2. 

def stop_session():

	# Receiving data in this session
	global receive_state
	receive_state = True

	# 1. Authenticate Connection
	auth_connection()

	# 2. Stop Logging
	# stop_logging()

	# 3. Request bulk data transfer
	#request_data_transfer() 


def enable_realtime_status_notification():

	# Enable realtime status information notification .......................
	char_path_realtime_status = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char001d'
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

def enable_data_transfer_status_notification():

	char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service003a/char003b'
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

def enable_data_transfer_download_notification():

	char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service003a/char0040'
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



def main():

	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	global bus
	# SystemBus is global and usually started durong boot
	bus = dbus.SystemBus()
	global mainloop
	mainloop = GObject.MainLoop()

	# Connect to TDL device
	tdl_mac_address = "A0:E6:F8:6C:8B:87"
	device = bluezutils.find_device(tdl_mac_address, None)
	device.Connect()
	print("Connected!")

	# Trigger enabling notifications
	enable_realtime_status_notification()

	# Toggle between start/stop session
	stop_session()
	#start_session()

	mainloop.run()

if __name__ == '__main__':
    main()

# sys.exit(0)