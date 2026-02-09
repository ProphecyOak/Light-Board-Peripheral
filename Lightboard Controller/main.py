import time
from pynput import keyboard
from light_controller import LightController

def frame(light_board, key_listener):
	pass

game_over = False
with LightController() as light_board, keyboard.Listener() as key_listener:
	light_board.toggle_power()
	light_board.send_palette()
	while not game_over:
		game_over = frame(light_board, key_listener)
	light_board.toggle_power()