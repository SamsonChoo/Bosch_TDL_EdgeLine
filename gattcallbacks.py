import drivercode as main
# All callbacks for read/write/notify operations
# ----------------------------------------------

def generic_error_cb(error):

    print('D-Bus call failed: ' + str(error))
    main.terminate()

def auth_connection_cb():
	print("Entered auth_connection callback")
	main.terminate()