import time
from pynput import keyboard
from light_controller import LightController
from tetris import Tetris_Game
	
# Returns the light index from x and y coordinates (0,0 is top left)
def xy_to_i(xy):
	x, y = xy
	x %= 20
	y %= 35
	i = (x + x % 2) * 35 - x % 2 + y * (-1) ** (x%2)
	return i

board_offset_x = 5
board_offset_y = 5

def setup(light_board):
	light_board.send_colors([1 for y in range(22)], horizontal=False, start_point=xy_to_i((board_offset_x-1,board_offset_y-1)))
	light_board.send_colors([1 for y in range(22)], horizontal=False, start_point=xy_to_i((board_offset_x+10,board_offset_y-1)))
	light_board.send_colors([1 for x in range(10)], horizontal=True, start_point=xy_to_i((board_offset_x,board_offset_y-1)))
	light_board.send_colors([1 for x in range(10)], horizontal=True, start_point=xy_to_i((board_offset_x,board_offset_y+20)))
	light_board.end_frame()

my_tetris_game = Tetris_Game()
frame = 0
def loop(light_board):
	global frame
	if frame % 5 == 0:
		my_tetris_game.step_frame()
		for y in range(2,22):
			light_board.send_colors(my_tetris_game.board[y], start_point=xy_to_i((board_offset_x, y + board_offset_y - 2)))
		for y in range(my_tetris_game.current_tile.height):
			start_x = -1
			block = []
			for x in range(my_tetris_game.current_tile.width):
				if my_tetris_game.current_tile.profile[y][x]:
					if start_x == -1:
						start_x = x
					block.append(my_tetris_game.current_tile.profile[y][x])
			if len(block) >= 1 and my_tetris_game.tile_position[1] >= 2:
				block_coords = (my_tetris_game.tile_position[0] + start_x + board_offset_x, my_tetris_game.tile_position[1] + y + board_offset_y - 2)
				# print(f"Start x: {start_x}, Block_size: {len(block)}\nStart-point: {block_coords}, start_idx: {xy_to_i(block_coords)}")
				light_board.send_colors(block, start_point=xy_to_i(block_coords))
	light_board.end_frame()
	frame += 1
	time.sleep(.01)
	return False

def on_key_up(key):
	pass

last_input = time.time()
def on_key_down(key, light_board):
	global start_time
	# if time.time() - start_time < .1: return
	match key.char:
		case "a":
			my_tetris_game.translate_tile(-1)
		case "d":
			my_tetris_game.translate_tile(1)
		case "q":
			my_tetris_game.rotate_tile(-1)
		case "e":
			my_tetris_game.rotate_tile(1)
	light_board.end_frame()
	last_input = time.time()

def test_send(light_board):
	light_board.send_colors([1,1,1,1],start_point=172)
	light_board.send_colors([2,2,2,2],start_point=208)
	light_board.send_colors([3,3,3,3],start_point=243)
	light_board.end_frame()
	time.sleep(10)

game_over = False
with LightController() as light_board, keyboard.Listener(on_press=lambda key: on_key_down(key, light_board), on_release=on_key_up) as key_listener:
	light_board.toggle_power()
	# GRB
	light_board.send_palette([
		0x00000000, # DARK
		0xFFFFFFFF, # WHITE
		0xFFFF00FF, # CYAN
		0xFF0000FF, # BLUE
		0xFF55FF00, # ORANGE
		0xFFFFFF00, # YELLOW
		0xFFFF0000, # GREEN
		0xFF00BBFF, # PURPLE
		0xFF00FF00, # RED

	])
	# test_send(light_board)
	setup(light_board)
	while not game_over:
		game_over = loop(light_board)
		# input()
	light_board.toggle_power()
	key_listener.join()