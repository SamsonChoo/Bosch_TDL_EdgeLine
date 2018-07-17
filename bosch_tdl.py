
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
	
	#readLogStatus()

if __name__ == '__main__':
    main()

# sys.exit(0)