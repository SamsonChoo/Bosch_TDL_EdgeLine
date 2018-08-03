import senddata
#import drivercode

def main():

	# Establish connection and wait for command from dashboard
	senddata.establish_connection()
	print("StartProcess")

if __name__ == '__main__':
     main()