
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

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'


def generic_error_cb(error):
    print('D-Bus call failed: ' + str(error))
    mainloop.quit()

def read_log_handler(value):
	print("Entered read_log_handler")
	print(value)
	mainloop.quit()

def read_log_status():

    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char001b'
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    #print(chrc)
    print("--------------------------------")
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)

    global read_log_chrc
    read_log_chrc = (chrc, chrc_props)
    #print(read_log_chrc)
    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    read_log_chrc[0].ReadValue({'offset': dbus.UInt16(offset, variant_level=1)}, dbus_interface=GATT_CHRC_IFACE, reply_handler = read_log_handler, error_handler= generic_error_cb)
    print('Set readValue...')

def process_services():

    service_path  = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a'
    service       = bus.get_object(BLUEZ_SERVICE_NAME, service_path)
    service_props = service.GetAll(GATT_SERVICE_IFACE, dbus_interface=DBUS_PROP_IFACE)
    
    print(service_props)
    uuid = service_props['UUID']
    print(uuid)

    # chrc_paths = service_props['Characteristics']
    # for chrc_path in chrc_paths:
    #     print(chrc_path)

def main():

	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	global bus
	bus = dbus.SystemBus()
	global mainloop
	mainloop = GObject.MainLoop()

	# Let's connect to the bluetooth peripheral
	tdl_mac_address = "A0:E6:F8:6C:8B:87"
	device = bluezutils.find_device(tdl_mac_address, None)
	device.Connect()
	print("Connected!")
	
	read_log_status()

	mainloop.run()

if __name__ == '__main__':
    main()

# sys.exit(0)