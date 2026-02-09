import random

class Tetris_Game():
	def __init__(self):
		self.board = [[0 for x in range(10)] for y in range(22)]
		self.bag = []
		self.used = []
		self.current_tile = None
		self.tile_position = None

	def fill_bag(self):
		for x in range(len(self.used)):
			self.bag.append(self.used.pop())
		random.shuffle(self.bag)
	
	def draw_tile(self):
		if len(self.bag) == 0:
			self.fill_bag()
		self.current_tile = self.bag.pop()
		self.used.append(self.current_tile)
		self.tile_position = [4, 0]

	def lower_tile(self):
		if self.current_tile == None:
			self.draw_tile()
		tile_x, tile_y = self.tile_position
		cant_fall = False
		for x in range(4):
			for y in range(3,-1,-1):
				if self.current_tile.profile[y][x]:
					if self.board[tile_y + y + 1][tile_x + x]:
						cant_fall = True
					break
			if cant_fall: break
		

class Tile():
	def __init__(self, profile):
		self.profile = profile