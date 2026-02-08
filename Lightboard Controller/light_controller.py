import serial, struct, math, queue, time, threading

SERIAL_PORT = "COM5"
BAUDRATE = 115200

class LightController():
	_instance = None
	def __new__(cls):
		if cls._instance == None:
			cls._instance = super(LightController, cls).__new__(cls)
		return cls._instance
	
	def __init__(self):
		self._port_opened = False
		self._color_size = 0
		self._powered = False
		self._instruction_queue = queue.Queue(10)
		self._transmitting_instructions = False
	
	# Open the serial port connection
	def open_port(self):
		if self._port_opened:
			raise Exception("Failed to open port: Port connection already established.")
		self._serial = serial.Serial(SERIAL_PORT, baudrate=BAUDRATE)
		self._serial.reset_output_buffer()
		self._port_opened = True
	
	# Close the serial port connection
	def close_port(self):
		if not self._port_opened:
			raise Exception("Failed to close port: Cannot close unestablished port connection.")
		self._serial.close()
		self._port_opened = False
	
	# Send a payload over the serial port connection
	# Returns whether or not the write was successful
	def _transmit_data(self, data):
		if not self._port_opened:
			raise Exception("Failed to transmit data: Port connection not established.")
		bytes_written = self._serial.write(data)
		# for bt in data:
		# 	print_bits(bt,end="|")
		# print()
		return bytes_written == len(data)
	
	# Returns the light index from x and y coordinates (0,0 is top left)
	def xy_to_i(self, xy):
		x, y = xy
		x %= 20
		y %= 35
		i = (x + x % 2) * 35 - x % 2 + y * (-1) ** (x%2)
		# print(f"Converting ({x}, {y}) to {i}")
		return i
	
	# Turns the light monitor on/off
	# Returns whether or not the transmission was successful
	def _toggle_power(self):
		successful_transmit = self._transmit_data(struct.pack("BB",
				(0 if self._powered else 1) << 5,
				0 # Empty OP byte
			))
		if not successful_transmit: return False
		self._powered = not self._powered
		return True
	
	# Sets the color size on the monitor, and provides the list of colors for the palette
	# Returns whether or not the transmission was successful
	def _send_palette(self, colors = [0x00000000, 0xFFFFFFFF, 0xFF00FF00, 0xFFFF0000]):
		color_size = math.ceil(math.log2(len(colors)+1))
		if color_size >= 7:
			raise Exception("Failed to transmit palette: Too many colors.")
		header = struct.pack("BB",
				(0b01000000) | # OP code 1
				(color_size) << 3,
				len(colors)
			)
		for c in colors:
			header += struct.pack("I", c)
		successful_transmit = self._transmit_data(header)
		if not successful_transmit: return False
		self._color_size = color_size
		return True
	
	# Sends a list of colors to write to the board starting at some point
	# Returns whether or not the transmission was successful
	def _send_colors(self, color_ids, horizontal=True, start_point=0):
		color_ids.append(2 ** self._color_size - 1)
		header = struct.pack("BB", 
				(
					# op_code 2
					0b10000000 |
					# 1 bit for scanline direction
					(1 if horizontal else 0) << 5 |
					# first 2 bits of start_point
					(start_point // 256)
					# last 8 bits of start_point
				), start_point % 256
			)
		start_bit = 0
		latest_byte = 0
		for c in color_ids:
			remaining_space = 8 - start_bit
			if remaining_space >= self._color_size:
				# Next color fits in current byte
				latest_byte |= c << (remaining_space - self._color_size)
				start_bit = (start_bit + self._color_size - 1) % 8 + 1
			else:
				# Next color spills into next byte
				spillover_size = self._color_size - remaining_space
				latest_byte |= c >> spillover_size
				header += struct.pack("B",latest_byte)
				latest_byte = c % (2 ** spillover_size) << (8 - spillover_size)
				start_bit = spillover_size
		header += struct.pack("B",latest_byte)
		return self._transmit_data(header)

	# Tells the monitor to push all commands in the next frame
	# Returns whether or not the transmission was successful
	def _end_frame(self):
		return self._transmit_data(struct.pack("BB", 0x00, 0xFF))
	
	def queue_instruction(self, instr_id, *args, **kwargs):
		match instr_id:
			case 0 | "toggle_power":
				self._instruction_queue.put(lambda: self._toggle_power(*args, **kwargs))
			case 1 | "send_palette":
				self._instruction_queue.put(lambda: self._send_palette(*args, **kwargs))
			case 2 | "send_colors":
				self._instruction_queue.put(lambda: self._send_colors(*args, **kwargs))
			case 3 | "end_frame":
				self._instruction_queue.put(lambda: self._end_frame(*args, **kwargs))
	
	def transmit_instructions(self, stop_trigger):
		while not stop_trigger.is_set():
			while self._serial.in_waiting == 0:
				pass
			bytes_received = self._serial.read_all()
			# print("\033[0;31mReceived:\033[0;37m")
			# for x in bytes_received:
			# 	print_bits(x,end=".")
			# print()
			try:
				next_instruction = self._instruction_queue.get(block=False)
				# print("\033[0;31mTransmitting\033[0;37m")
				next_instruction()
				self._instruction_queue.task_done()
			except queue.Empty:
				pass

def print_bits(bt, end="\n"):
	for x in range(7, -1, -1):
		print((bt % (2**(x+1))) // (2**x), end="")
	print(end, end="")

myLtCtlr = LightController()
myLtCtlr.open_port()
stop_trigger = threading.Event()
instruction_thread = threading.Thread(target=myLtCtlr.transmit_instructions, args=(stop_trigger,))
instruction_thread.daemon = True
instruction_thread.start()
myLtCtlr.queue_instruction(0)
myLtCtlr.queue_instruction(1)
myLtCtlr.queue_instruction(2, color_ids = [2, 2, 2, 2], start_point=3)
myLtCtlr.queue_instruction(3)
time.sleep(3)
myLtCtlr.queue_instruction(0)
myLtCtlr._instruction_queue.join()
stop_trigger.set()
instruction_thread.join()
myLtCtlr.close_port()
