
def process_packet(packet_arr):
	print("Processing packets")

	# Number of bytes in each packet sent by TDL device
	packet_size = 20
	#"".join(map(chr,packet_arr))
	#print(type(packet_arr[0]))
	# print(packet_arr[0])
	# print(packet_arr[1])
	# print(packet_arr[20])
	# print(packet_arr[21])
	# print(packet_arr[40])
	# print(packet_arr[41])		
	# print(packet_arr[60])
	# print(packet_arr[61])

	# print(packet_arr[80])
	# print(packet_arr[81])

	# Number of packets
	n_packets = ((packet_arr[2] & 0xFF) << 8) + (packet_arr[3] & 0xFF)

	print(n_packets)

	data_size = len(packet_arr)

	total_packets = (data_size/packet_size) - 1

	print(total_packets)
