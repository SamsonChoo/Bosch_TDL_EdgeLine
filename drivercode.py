
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
import gattoperations as gatt
import gattcallbacks as cb

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'

bus = None
mainloop = None

counter = 0

def terminate():
	mainloop.quit()

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

def realtime_status_cb():
	print("Realtime status enabled")

def realtime_status_changed_cb(iface, changed_props, invalidated_props):
	global counter
	#print(counter)
	if (counter == 0):
		counter += 1
		return

	# print("Realtime status changed")

	value = changed_props.get('Value', None)
	if(value[0] == 25):
		print("Connection authenticated")
	terminate()

def data_transfer_status_cb(value):
	print("Change in data transfer status")

def data_transfer_download_cb(value):
	print("Downloading Data")	
	


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


# First time device initialisation
# Includes setting min, max paramater bound
# Example: Set min & max temperature to set off alarm event
def init_tdl():

	auth_connection()



def enable_notifications():

	# Enable realtime status information notification .......................
	char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char001d'
	chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
	chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
	chrc_arr = (chrc, chrc_props)

	# Listen for changes
	chrc_arr_prop_iface = dbus.Interface(chrc_arr[0], DBUS_PROP_IFACE)
	chrc_arr_prop_iface.connect_to_signal("PropertiesChanged",
                                          realtime_status_changed_cb)

	# Subscribe to notifications
	chrc_arr[0].StartNotify(reply_handler=realtime_status_cb,
	                         	 error_handler=generic_error_cb,
	                             dbus_interface=GATT_CHRC_IFACE)


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
	bus = dbus.SystemBus()
	global mainloop
	mainloop = GObject.MainLoop()

	# Connect to TDL device
	tdl_mac_address = "A0:E6:F8:6C:8B:87"
	device = bluezutils.find_device(tdl_mac_address, None)
	device.Connect()
	print("Connected!")

	# mainloop.run()
	enable_notifications()

	init_tdl()

	mainloop.run()

if __name__ == '__main__':
    main()

# sys.exit(0)