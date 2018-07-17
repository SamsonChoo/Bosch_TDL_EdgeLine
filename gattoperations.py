import dbus
import gattcallbacks as cb

# Authenticate connection with device
# 	-> Required to perform any write operation
# Default pin : 1-2-3-4
# Currently PIN is hardcoded, no need to manually enter
def auth_connection():

    # Update to required characteristic 
    char_path = '/org/bluez/hci0/dev_A0_E6_F8_6C_8B_87/service001a/char0036'
    bus = dbus.SystemBus();
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, char_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)
    chrc_arr = (chrc, chrc_props)

    #read_log_chrc[0].ReadValue(dbus_interface=GATT_CHRC_IFACE, reply_handler=read_log_handler, error_handler=generic_error_cb)
    offset = 0
    message_bytes = ''.join(chr(x) for x in [0x01, 0x02, 0x03, 0x04])
    chrc_arr[0].WriteValue(message_bytes, {'offset': dbus.UInt16(offset, variant_level=1)}, dbus_interface=GATT_CHRC_IFACE, reply_handler = cb.auth_connection_cb, error_handler= cb.generic_error_cb)
    print("Value written")


# First time device initialisation
# Includes setting min, max paramater bound
# Example: Set min & max temperature to set off alarm event
def init_tdl():

	auth_connection()




