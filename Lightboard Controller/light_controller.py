class LightController():
	instance = None
	def __new__(cls):
		if cls.instance == None:
			cls.instance = super(LightController, cls).__new__(cls)
		return cls.instance
	
	def __init__(self):
		pass
	
	def xy_to_i(self, xy):
		x, y = xy
		x %= 20
		y %= 35
		i = (x + x % 2) * 35 - x % 2 + y * (-1) ** (x%2)
		# print(f"Converting ({x}, {y}) to {i}")
		return i

myLtCtlr = LightController()