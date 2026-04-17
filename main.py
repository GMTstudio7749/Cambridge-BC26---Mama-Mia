import time
from cambc import Controller, EntityType
from core import Core
from builder import Builder
from turret import Turret
from utils import *
import random
random.seed(100)

class Player:
	def __init__(self):
		self.core_ctrl = Core()
		self.builder_ctrl = Builder()
		self.turret_ctrl = Turret()
		
		self.setup = False

		# Time debug
		self.start_time = -1
		self.peak_time = -1
		self.peak_round = -1
		self.sum_time = 0
		self.time_turn_cnt = 0
		self.aver_time = 0

	#region ----- DEBUG func -----
	def DEBUG_time(self, ct: Controller):
		"""Print the time runned till this moment"""
		curr_time = time.perf_counter_ns()
		nano = curr_time - self.start_time
		milli = nano / 1e6
		if milli > self.peak_time: 
			self.peak_time = milli
			self.peak_round = ct.get_current_round()
		self.sum_time += milli
		self.time_turn_cnt += 1
		self.aver_time = self.sum_time / self.time_turn_cnt
		print("\n====== TIME ======")
		print(f"Curr: {milli:.2f} ms", "#"*round((milli*7)))
		print(f"Aver: {self.aver_time:.2f} ms", "#"*round((self.aver_time*5)))
		print(f"Peak: {self.peak_time:.2f} ms > Round: {self.peak_round}")
		print("===================")

	#endregion

	def run(self, ct: Controller):
		my_type = ct.get_entity_type()
		
		if my_type == EntityType.CORE:
			self.core_ctrl.CORE_run(ct)

		elif my_type == EntityType.BUILDER_BOT:
			self.start_time = time.perf_counter_ns()
			self.builder_ctrl.BUILDER_run(ct)
			self.DEBUG_time(ct)
			
		elif my_type in TURRET_TYPE:
			self.turret_ctrl.TURRET_run(ct)