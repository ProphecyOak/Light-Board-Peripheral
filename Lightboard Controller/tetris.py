import random

BOARD_HEIGHT = 22
BOARD_WIDTH = 10

class Tetris_Game():
	def __init__(self):
		self.active = True
		self.board = [[0 for x in range(BOARD_WIDTH)] for y in range(BOARD_HEIGHT)]
		self.bag = []
		self.used = [
			Tile([[0,0,0,0],[0,0,0,0],[2,2,2,2],[0,0,0,0]]), # I
			Tile([[3,0,0],[3,3,3],[0,0,0]]), # J
			Tile([[0,0,4],[4,4,4],[0,0,0]]), # L
			Tile([[0,5,5],[0,5,5],[0,0,0]],dont_rotate=True), # O
			Tile([[0,6,6],[6,6,0],[0,0,0]]), # S
			Tile([[0,7,0],[7,7,7],[0,0,0]]), # T
			Tile([[8,8,0],[0,8,8],[0,0,0]]), # Z
		]
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
		self.tile_position = [3, 0]

	def lower_tile(self):
		if self.current_tile == None:
			self.draw_tile()
		tile_x, tile_y = self.tile_position
		cant_fall = False
		for x in range(self.current_tile.width):
			for y in range(self.current_tile.height - 1, -1, -1):
				if self.current_tile.profile[y][x]:
					if tile_y + y + 1 == BOARD_HEIGHT or self.board[tile_y + y + 1][tile_x + x]:
						cant_fall = True
					break
			if cant_fall: break
		if cant_fall:
			for x in range(self.current_tile.width):
				for y in range(self.current_tile.height):
					if self.current_tile.profile[y][x]:
						self.board[tile_y + y][tile_x + x] = self.current_tile.profile[y][x]
			self.draw_tile()
		else:
			self.tile_position[1] += 1
	
	def translate_tile(self, direction=1):
		tile_x, tile_y = self.tile_position
		x_start = 0 if direction == 1 else (self.current_tile.width - 1)
		x_end = self.current_tile.width if direction == 1 else -1
		for y in range(self.current_tile.height):
			farthest_in_row = -1
			for x in range(x_start, x_end, direction):
				if self.current_tile.profile[y][x]:
					farthest_in_row = x
			if farthest_in_row > -1:
				if ((direction == 1 and tile_x + farthest_in_row == BOARD_WIDTH - 1) or
						(direction == -1 and tile_x + farthest_in_row == 0)):
					return
		self.tile_position[0] += direction
	
	def rotate_tile(self, direction=1):
		self.current_tile.rotate(direction)
	
	def step_frame(self):
		if self.active:
			self.lower_tile()

class Tile():
	def __init__(self, profile, dont_rotate=False):
		self.initial = profile
		self.rotatable = not dont_rotate
		self.profile = [[x for x in y] for y in self.initial]
		self.width = len(self.initial[0])
		self.height = len(self.initial)

	def rotate(self, direction):
		#TODO CHECK THAT IT WONT RUN INTO STUFF
		#TODO ALSO FIGURE OUT THE DEAL WITH WALL KICKS ETC (SRS)
		if self.rotatable:
			new_profile = []
			for x in range(direction % 4):
				#TODO ACTUALLY MAKE THIS GO THE RIGHT DIRECTION OR SOMETHING?
				new_profile = [[y for y in list(row)[::-1]] for row in zip(*self.profile)]
			self.profile = new_profile
		return self