
import senddata

temperature_data = []
unix_timestamp   = []
humidity_data    = []
pressure_data	 = []

def process_packet(packet_arr):
    print("Processing packets")
    print('\n')
    print(packet_arr)
    print('\n')
	# Number of bytes in each packet sent by TDL device
    packet_size = 20
    abs_min_temp = -40.0
	# Number of packets
    n_packets = ((packet_arr[2] & 0xFF) << 8) + (packet_arr[3] & 0xFF)

    print(n_packets)

    data_size = len(packet_arr)

    total_packets = (data_size/packet_size) - 1

    print(total_packets)

    packet_loss = n_packets - total_packets

	# Check for packet losss
    if (packet_loss == 0):
        print("All packets received")

		# Check if CRC32 polynomial is correct, currently not implemented

		# Index at which data stream starts
        init_offset = 8
        i = init_offset
        while i < data_size:	
        #for i in range(init_offset, data_size):

            try:

            	#print("Entered try block")

				# Sanity checks
                if (i >= (data_size - packet_size)):
                    break;

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

                #print(event_type)
                #print(i)

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
                    print(temp_hi_bits)
                    for j in range(0,1):
                		
                        i += 1
                		# Check incremented index
                        if (i % packet_size == 0):
                       		i += 2;

                    # Holding the 5 bits from the lower byte (in terms of significant digits)
                    temp_lo_bits = ((packet_arr[i] & 0xF8) & 0xFF) >> 3
                    print(temp_lo_bits)
                    # Holding the 3 bits from the lower byte
                    temp_fraction_bits = ((packet_arr[i] & 0x07) & 0xFF) * 12.5
                    print(i)
                    print(temp_fraction_bits)
                    # Finally, after all the annoying bit arithmetic, I present to you - the temperature
                    temp_result = (temp_hi_bits + temp_lo_bits + abs_min_temp) + (temp_fraction_bits * 0.01)
                    
                    # To match the iOS app temperature readings, anomaly in TDL documentation and iOS app readings
                    temp_result -= 0.5
                    print(temp_result)
                    # Sanity check for zero padding bytes at the last of the packets
                    # Lazy, dirty trick -- will cause problems if temperature is actually -40 Celsius
                    # Assumption made that -40 Celsius is not encountered in logging
                    # To be updated...
                    if (temp_result != abs_min_temp):
                        
                        # Store the temperature data
                        global temperature_data
                        temperature_data.append(temp_result)


                        # Temporary indices to make life easier
                        timestamp_index = i;
                        humidity_index  = i - 1;
                        pressure_index  = i - 2;

                        # Extract timestamp --------------------------------------------------

                        #Now we have to go backwards in the packet...
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
                        print(humidity_lo_bits)

                        humidity_index -= 1

                        # Upper 2 bits
                        humidity_hi_bits = ((packet_arr[humidity_index] & 0x03) & 0xFF) << 6
                        print(humidity_hi_bits)
                        humidity_result = (humidity_hi_bits + humidity_lo_bits)/2
                        print(humidity_result) 
                        global humidity_data 
                        humidity_data.append(humidity_result)

                        # Extract pressure ---------------------------------------------------

                        # Lower 6 bits
                        pressure_lo_bits = ((bdt_data_array[pressure_index] & 0xFC) & 0xFF) >> 4

                        pressure_index -= 1

                        # Upper 4 bits
                        pressure_hi_bits = ((bdt_data_array[pressure_index] & 0x0F) & 0xFF) << 6

                        pressure_result = pressure_hi_bits + pressure_lo_bits - 100

                        # global pressure_data
                        # pressure_data.append(pressure_result)

                # --------------------------------------------------------------------------------                        

                elif (event_type == 1):

                	for j in range(0,(6 - 1)):
                		
                		i += 1
                		# Check incremented index
                    	if (i % packet_size == 0):
                       		i += 2
                
            	elif (event_type == 2):

                	for j in range(0,(9 - 1)):
                		
                		i += 1
                		# Check incremented index
                    	if (i % packet_size == 0):
                       		i += 2

                elif (event_type == 4):

                	for j in range(0,(5 - 1)):
                		
                		i += 1
                		# Check incremented index
                    	if (i % packet_size == 0):
                       		i += 2


            # Invalid index
            except:
            	print('Entered exception block')
            	break
            # Increment loop index	
            i += 1	

    else:
    	print("Packets lost: " + packet_loss)

    senddata.upload(temperature_data,
					unix_timestamp,
					humidity_data,
					pressure_data)	       	

#                             // Extract humidity -------------------------------------------------

#                             // Lower 6 bits
#                             int humidity_lo_bits = ((bdt_data_array[humidity_index] & 0xFC) & 0xFF) >> 2;

#                             humidity_index -= 1;

#                             // Upper 2 bits
#                             int humidity_hi_bits = ((bdt_data_array[humidity_index] & 0x03) & 0xFF) << 6;

#                             int humidity_result = (humidity_hi_bits + humidity_lo_bits)/2;

#                             humidity_data.add(humidity_result);

#                             // Extract pressure -------------------------------------------------

#                             // Lower 6 bits
#                             int pressure_lo_bits = ((bdt_data_array[pressure_index] & 0xFC) & 0xFF) >> 4;

#                             pressure_index -= 1;

#                             // Upper 4 bits
#                             int pressure_hi_bits = ((bdt_data_array[pressure_index] & 0x0F) & 0xFF) << 6;

#                             int pressure_result = pressure_hi_bits + pressure_lo_bits - 100;

#                             pressure_data.add(pressure_result);





#                         }

#                         break;
#                     }

#                     // ------------------ The events below are not yet implemented ------------------

#                     // Shock event
#                     case 1: {
#                         for (int j = 0; j < (6-1); j++) {
#                             i += 1;
#                             if (i >= (data_size - PACKET_SIZE))
#                                 break outer_loop;
#                             if (i % PACKET_SIZE == 0)
#                                 i += 2;
#                         }
#                         break;
#                     }

#                     // Tilt event
#                     case 2: {
#                         for (int j = 0; j < (9-1); j++) {
#                             i += 1;
#                             if (i >= (data_size - PACKET_SIZE))
#                                 break outer_loop;
#                             if (i % PACKET_SIZE == 0)
#                                 i += 2;
#                         }
#                         break;
#                     }

#                     // Offline status (?) event
#                     case 4: {
#                         for (int j = 0; j < (5-1); j++) {
#                             i += 1;
#                             if (i >= (data_size - PACKET_SIZE))
#                                 break outer_loop;
#                             if (i % PACKET_SIZE == 0)
#                                 i += 2;
#                         }
#                         break;
#                     }

#                 }
#             }


#         }

#         else
#             log("Packets lost: " + packet_loss);


#         return "Operation successful";

# }