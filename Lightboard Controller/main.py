import serial
import struct
import time, math
from threading import Thread

def print_bits(bt, end="\n"):
	for x in range(7, -1, -1):
		print((bt % (2**(x+1))) // (2**x), end="")
	print(end, end="")

def print_bytes(bts, end="\n"):
	print("|", end="")
	for x in bts:
		print_bits(x, end="|")
	print(end=end)

class Board():
	color_size = 3
	# Allows color palette from 0 to (2 ** color_size - 1)
	# The last color is the stop bits (all ones)
	PORT = "COM5"
	ser = None
	port_opened = False
	
	def open_port():
		Board.ser = serial.Serial(Board.PORT, baudrate=115200)
		Board.ser.reset_output_buffer()
		Board.port_opened = True
		print("Connection Opened.")
	
	def close_port():
		Board.ser.close()
		Board.port_opened = False
		print("Connection Closed.")

	def transmit(bts, print_payload=False):
		if not Board.port_opened:
			Board.open_port()
		if print_payload:
			print("\033[0;31mTransmitting\033[0;37m")
			# for x in bts:
			# 	print_bits(x,end=" = ")
			# 	print(int(x))
			# # print_bytes(bts)
			# print()
		
		Board.ser.write(bts)

	def toggle_power(on=True):
		Board.transmit(struct.pack("BB",
				(
					(
						(0b00 << 1) | # OP code 0
						(1 if on else 0) # Toggle state
					) << 5
				),
				0 # Empty OP byte
			))
		
	# Last color of range is stop color
	def send_palette(colors = [0x00000000, 0xFFFFFFFF, 0xFF00FF00, 0xFFFF0000]):
		Board.color_size = math.ceil(math.log2(len(colors)+1))
		if Board.color_size >= 7:
			raise Exception("Palette Too Large.")
		header = struct.pack("BB",
				(0b01000000) | # OP code 1
				(Board.color_size) << 3,
				len(colors)
			)
		for c in colors:
			header += struct.pack("I", c)
		Board.transmit(header)

	def send_colors(horizontal=True, start_point=0, color_ids=[]):
		color_ids.append(2 ** Board.color_size - 1)
		header = struct.pack("BB", 
				(
					(
						(0b10 << 6) | # OP code 2
						(1 if horizontal else 0) << 5 | # Scanline direction
						(start_point // 256)
					)
				), start_point % 256 # Start position
			)

		start_bit = 0
		latest_byte = 0

		for i, c in enumerate(color_ids):
			remaining_space = 8 - start_bit
			if remaining_space >= Board.color_size:
				latest_byte |= c << (remaining_space - Board.color_size)
				start_bit = (start_bit + Board.color_size - 1) % 8 + 1

			else:
				spillover_size = Board.color_size - remaining_space
				latest_byte |= c >> spillover_size
				header += struct.pack("B",latest_byte)
				latest_byte = c % (2 ** spillover_size) << (8 - spillover_size)
				start_bit = spillover_size
		header += struct.pack("B",latest_byte)
		Board.transmit(header)

	def end_frame():
		Board.transmit(struct.pack("BB", 0x00, 0xFF))

commands = [
	lambda: Board.toggle_power(),
	lambda: Board.send_palette(),
	# lambda: Board.send_colors(color_ids = [2], start_point=600),
	lambda: Board.send_colors(color_ids = [2, 2, 2, 2], start_point=3),
	lambda: Board.send_colors(horizontal=False, start_point=20, color_ids = [1, 1, 1, 1]),
	lambda: Board.end_frame(),
	# lambda: Board.send_colors(color_ids = [1, 1, 1, 1], start_point=3),
	# lambda: Board.send_colors(horizontal=False, start_point=20, color_ids = [2, 2, 2, 2]),
	# lambda: Board.end_frame(),
	lambda: time.sleep(7),
	lambda: Board.toggle_power(False)
	]

print("`Ctrl + C` to stop")
def testTarget():
	command_num = 0
	Board.open_port()
	try:
		while True:
			while Board.ser.in_waiting == 0:
				pass
			bytes_received = Board.ser.read_all()
			# if len(bytes_received) > 1 or bytes_received[0] != 255:
			# 	print("\033[0;31mResponse:\033[0;37m")
			# 	for x in bytes_received:
			# 		print_bits(x,end=" = ")
			# 		print(int(x), end=" : ")
			# 		print(chr(int(x)))
			# 	print()
			if command_num < len(commands):
				commands[command_num]()
				command_num += 1
	except Exception as e:
		Board.close_port()

a = Thread(target=testTarget)
a.daemon = True
a.start()
a.join()