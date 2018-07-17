
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



#def readLogStatus():

def process_services():

    service_path  = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a'
    service       = bus.get_object(BLUEZ_SERVICE_NAME, service_path)
    service_props = service.GetAll(GATT_SERVICE_IFACE, dbus_interface=DBUS_PROP_IFACE)
    
    uuid = service_props['UUID']
    print(uuid)

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
	
	process_services()
	#readLogStatus()

if __name__ == '__main__':
    main()

# sys.exit(0)