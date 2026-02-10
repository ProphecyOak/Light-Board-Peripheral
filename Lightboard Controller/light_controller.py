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
	
	# Turns the light monitor on/off
	# Returns whether or not the transmission was successful
	def toggle_power(self):
		self._instruction_queue.put(struct.pack("BB",
				(0 if self._powered else 1) << 5,
				0 # Empty OP byte
			))
		self._powered = not self._powered
	
	# Sets the color size on the monitor, and provides the list of colors for the palette
	# Returns whether or not the transmission was successful
	def send_palette(self, colors = [0x00000000, 0xFFFFFFFF, 0xFF00FF00, 0xFFFF0000]):
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
		self._instruction_queue.put(header)
		self._color_size = color_size
	
	# Sends a list of colors to write to the board starting at some point
	# Returns whether or not the transmission was successful
	def send_colors(self, _color_ids, horizontal=True, start_point=0):
		color_ids = list(_color_ids)
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
		self._instruction_queue.put(header)

	# Tells the monitor to push all commands in the next frame
	# Returns whether or not the transmission was successful
	def end_frame(self):
		self._instruction_queue.put(struct.pack("BB", 0x00, 0xFF))
	
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
				self._transmit_data(next_instruction)
				self._instruction_queue.task_done()
			except queue.Empty:
				pass
	def __enter__(self):
		self.open_port()
		self.stop_trigger = threading.Event()
		self.instruction_thread = threading.Thread(target=self.transmit_instructions, args=(self.stop_trigger,))
		self.instruction_thread.daemon = True
		self.instruction_thread.start()
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		self._instruction_queue.join()
		self.stop_trigger.set()
		self.instruction_thread.join()
		self.close_port()
