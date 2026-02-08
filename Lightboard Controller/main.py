import time
from light_controller import LightController

with LightController() as myLtCtlr:
	myLtCtlr.toggle_power()
	myLtCtlr.send_palette()
	myLtCtlr.send_colors([2, 2, 2, 2], start_point=3)
	myLtCtlr.end_frame()
	time.sleep(1)
	myLtCtlr.toggle_power()