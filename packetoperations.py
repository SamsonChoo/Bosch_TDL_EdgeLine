
import drivercode
import senddata
import datetime

global serial_number

temperature_data = []
unix_timestamp   = []
shock_timestamp  = []
humidity_data    = []
pressure_data    = []
battery_data     = []

traverse_state = True
test_counter = 0

# Reset required for successive calls
def reset_data_holders():

    global battery_data
    global temperature_data
    global unix_timestamp
    global humidity_data
    global pressure_data
    global traverse_state
    global shock_timestamp

    temperature_data = []
    unix_timestamp   = []
    humidity_data    = []
    pressure_data    = []
    battery_data     = []
    shock_timestamp  = []

    traverse_state = True

# Base = 0.5 -- Device temperature reading resolution
def round_temperature(x, prec = 1,base = 0.5):
    return round(base * round(float(x)/base), prec)

def process_serial_number(packet_arr):
    
    global serial_number

    serial_number_string = ''.join(chr(i) for i in packet_arr)

    # String holding serial number - 1704130026808
    print(serial_number_string)

    production_date = str(serial_number_string[0:6])

    print(production_date)

    year = "20" + production_date[0:2]

    print(year)

    month = production_date[2:4]
    print('Month')
    print(month)
    
    #month = int(month)

    #print(month)

    #month = datetime.date(1900, month, 1).strftime('%B')

    #print(month)

    day = production_date[4:6]

    #print(day)

    serial_number = serial_number_string[6:11]

    #print(serial_number)

    factory_line = serial_number_string[11:13]

    #print(factory_line)
    
    senddata.upload_device_info(year, month, day, serial_number, factory_line)
        

# Method where the packet processing is performed
# Extracts all the data from the device
#   - Temperature, Pressure, Humidity
# 
def process_packet(packet_arr):

    reset_data_holders()

    print("Processing packets")
    # print('\n')
    # #print(packet_arr)
    # print('\n')
    # Number of bytes in each packet sent by TDL device
    packet_size = 20
    abs_min_temp = -40.0
    # Number of packets
    n_packets = ((packet_arr[2] & 0xFF) << 8) + (packet_arr[3] & 0xFF)

    print("Number of packets: %d" %(n_packets))

    data_size = len(packet_arr)
    print("Data Size: %d" %(data_size)) 

    total_packets = (data_size/packet_size) - 1

    print("Total packets received: %d" %(total_packets))
    #print(total_packets)

    packet_loss = n_packets - total_packets

    # Check for packet losss
    if (packet_loss == 0):
        print("All packets received")

        # Check if CRC32 polynomial is correct, currently not implemented

        # Index at which data stream starts
        init_offset = 8
        i = init_offset

        # Variable to know when to stop traversal
        global traverse_state

        while (i < data_size and traverse_state == True):   

            try:

                # Case when packet counter byte data is encountered
                if (i % packet_size == 0):
                    i += 2

                # Reference timestamp offset (32 bits = 4 bytes)
                for l in range(0,4):

                    i += 1;

                    # Check incremented index
                    if (i % packet_size == 0):
                        i += 2;
                
                # get event type (6 bits)
                event_type = (packet_arr[i] & 0xFC) >> 2

                print('Event type: %d' %(event_type))

                # Check for invalid event
                if (event_type > 4):
                    break

                # Regular measurement (what we need)
                elif (event_type == 0):

                # --------------------------------------------------------------------------------

                    #print("Entered regular measurement event") 

                    # For temperature offset
                    for j in range(0,3):
                        
                        i += 1
                        # Check incremented index
                        if (i % packet_size == 0):
                            i += 2

                    # Holding the 2 bits from the upper byte (in terms of significant digits) 
                    temp_hi_bits = ((packet_arr[i] & 0x03) & 0xFF) << 5

                    for j in range(0,1):
                        
                        i += 1
                        # Check incremented index
                        if (i % packet_size == 0):
                            i += 2;

                    # Holding the 5 bits from the lower byte (in terms of significant digits)
                    temp_lo_bits = ((packet_arr[i] & 0xF8) & 0xFF) >> 3

                    # Holding the 3 bits from the lower byte
                    temp_fraction_bits = ((packet_arr[i] & 0x07) & 0xFF) * 12.5

                    # Finally, after all the annoying bit arithmetic, I present to you - the temperature
                    temp_result = (temp_hi_bits + temp_lo_bits + abs_min_temp) + (temp_fraction_bits * 0.01)

                    # Round to nearest resolution
                    temp_result = round_temperature(temp_result)
                    
                    #print("Temperature result: %d" %(temp_result))

                    # Sanity check for zero padding bytes at the last of the packets
                    # Lazy, dirty trick -- will cause problems if temperature is actually -40 Celsius
                    # Assumption made that -40 Celsius is not encountered in logging
                    # To be updated...
                    if (temp_result != abs_min_temp):
                        
                        # Store the temperature data
                        global temperature_data
                        temperature_data.append(temp_result)


                        # Temporary indices to make life easier
                        timestamp_index = i
                        humidity_index  = i - 1
                        pressure_index  = i - 2

                        # Extract timestamp --------------------------------------------------

                        # Now we have to go backwards in the packet...
                        for k in range(0,8):

                            timestamp_index -= 1
                            
                            # Let's not forget to check if the index hits a packet # byte
                            if (timestamp_index % packet_size == 1):
                                timestamp_index -= 2

                        temp_timestamp = 0

                        # Let's extract the timestamp data!
                        for k in range(0,4):

                            if (timestamp_index % packet_size == 0):
                                timestamp_index += 2

                            temp_timestamp += (packet_arr[timestamp_index] & 0xFF) << (k * 8)

                            timestamp_index += 1

                        # Convert to milliseconds (ThingsBoard platform requirement)
                        temp_timestamp *= 1000;

                        global unix_timestamp
                        unix_timestamp.append(temp_timestamp);

                        # Extract humidity ---------------------------------------------------

                        # Lower 6 bits
                        humidity_lo_bits = ((packet_arr[humidity_index] & 0xFC) & 0xFF) >> 2
                        #print(humidity_lo_bits)

                        humidity_index -= 1

                        # Upper 2 bits
                        humidity_hi_bits = ((packet_arr[humidity_index] & 0x03) & 0xFF) << 6
                        #print(humidity_hi_bits)
                        humidity_result = (humidity_hi_bits + humidity_lo_bits)/2
                        #print(humidity_result) 
                        global humidity_data 
                        humidity_data.append(humidity_result)

                        # Extract pressure ---------------------------------------------------

                        # Lower 6 bits
                        pressure_lo_bits = ((packet_arr[pressure_index] & 0xFC) & 0xFF) >> 4

                        pressure_index -= 1

                        # # Upper 4 bits
                        pressure_hi_bits = ((packet_arr[pressure_index] & 0x0F) & 0xFF) << 6

                        pressure_result = pressure_hi_bits + pressure_lo_bits - 100

                        global pressure_data
                        pressure_data.append(pressure_result)

                        # Extract battery voltage -------------------------------------------

                        battery_index = pressure_index

                        # Lower 4 bits
                        battery_lo_bits = ((packet_arr[battery_index] & 0xF0) & 0xFF)

                        battery_index -= 1

                        # Upper 2 bits
                        battery_hi_bits = (packet_arr[battery_index] & 0x03) & 0xFF


                        battery_result = battery_hi_bits + (battery_lo_bits * (1/16))

                        global battery_data
                        global test_counter
                        test_counter += 1
                        battery_data.append(battery_result)

                    else:
                        #global traverse_state
                        traverse_state = False
                        break    

                # --------------------------------------------------------------------------------                        

                # Shock event
                elif (event_type == 1):

                    # Retrieve the timestamp at which shock occurred
                    shock_timestamp_index = i - 4
                    shock_temp_timestamp = 0

                    for j in range(0,4):

                        if (shock_timestamp_index % packet_size == 0):
                            shock_timestamp_index += 2

                        shock_temp_timestamp += (packet_arr[shock_timestamp_index] & 0xFF) << (k * 8)

                        shock_timestamp_index += 1

                    # Convert to milliseconds (ThingsBoard platform requirement)
                    shock_temp_timestamp *= 1000

                    shock_timestamp.append(shock_temp_timestamp)


                    for j in range(0,(6 - 1)):
                        
                        i += 1
                        # Check incremented index
                        if (i % packet_size == 0):
                            i += 2
                
                # Tilt event
                elif (event_type == 2):

                    for j in range(0,(9 - 1)):
                        
                        i += 1
                        # Check incremented index
                        if (i % packet_size == 0):
                            i += 2

                # Offline status event
                elif (event_type == 4):

                    for j in range(0,(5 - 1)):
                        
                        i += 1
                        # Check incremented index
                        if (i % packet_size == 0):
                            i += 2

                i += 1

            # Invalid index
            except:
                print('Entered exception block')
                break
            # Increment loop index  
            #i += 1 

    else:
        print("Packets lost: %d" %(packet_loss))

    print(unix_timestamp)
    print(shock_timestamp)

    # Call the method to upload data to dashboard
    senddata.upload_data(serial_number,
                         temperature_data,
                         unix_timestamp,
                         humidity_data,
                         pressure_data,
                         battery_data)          

