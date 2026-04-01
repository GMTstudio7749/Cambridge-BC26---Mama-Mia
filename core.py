import random
from cambc import Controller, Position
from utils import *

class Core:
	def __init__(self):
		self.my_pos = Position(-1, -1)
		self.state = "OPENING"
		self.builder_spawn = 0
		self.Cur_Round = -1

		# Resource
		self.Glob_Tit = -1
		self.Glob_Anx = -1

		# Cost
		self.Builder_Cost = -1
		self.Harvest_Cost = -1
		self.Convey_Cost = -1
		self.Gunner_Cost = -1
		self.Road_Cost = -1

		# Opening 
		self.open_spawn_dir = Direction.NORTHEAST
		self.open_builder_spawn = 0

		# Expanding
		self.EXPAND_ROUND = 200
		self.Spawn_Limit = -1

	def CORE_setup(self, ct: Controller):
		"""Core setup infos"""
		self.my_pos = ct.get_position()
		self.builder_spawn = 0

	def CORE_update(self, ct: Controller):
		"""Core update info about global values"""
		self.Cur_Round = ct.get_current_round()

		self.Glob_Tit, self.Glob_Anx = ct.get_global_resources()
		self.Builder_Cost, tmp = ct.get_builder_bot_cost()
		self.Harvest_Cost, tmp = ct.get_harvester_cost()
		self.Convey_Cost, tmp = ct.get_conveyor_cost()
		self.Gunner_Cost, tmp = ct.get_gunner_cost()
		self.Road_Cost, tmp = ct.get_road_cost()
		self.Spawn_Limit = (
			50*self.Road_Cost +
			7*self.Convey_Cost +
			self.Gunner_Cost +
			3*self.Harvest_Cost
		)

		print("\n=== Unit Cost ===")
		print("Conveyor:", self.Convey_Cost)
		print("Builder:", self.Builder_Cost)
		print("Harvester:", self.Harvest_Cost)
		print("Gunner:", self.Gunner_Cost)
		print("Road:", self.Road_Cost)
		print("=> Expand limit:", self.Spawn_Limit)
		print("===================\n")

	def CORE_spawn_builder(self, ct: Controller, spawn_dir: Direction):
		"""Core spawn builder depends on spawn dir, return bool value"""
		if ct.get_action_cooldown() > 0: return False
		if self.Builder_Cost > self.Glob_Tit: return False
		if self.builder_spawn >= MAX_BUILDER_COUNT: return False

		if spawn_dir == Direction.CENTRE:
			spawn_dir = random.choice(Dirs)

		spawn_pos = self.my_pos.add(spawn_dir)
		if ct.can_spawn(spawn_pos):
			ct.spawn_builder(spawn_pos)
			self.builder_spawn = self.builder_spawn + 1
			return True
		return False
	
	#region --- STATE FUNCTION ---
	def CORE_opening(self, ct: Controller):
		"""Core function for opening state, return True if work finished"""
		if self.builder_spawn >= MAX_BUILDER_OPENING:
			return True
		self.CORE_spawn_builder(ct, self.open_spawn_dir)
		self.open_spawn_dir = self.open_spawn_dir.rotate_right().rotate_right()
		return False
	
	def CORE_expanding(self, ct: Controller):
		"""Core function for expanding state, return True if work finished"""
		if self.Cur_Round < self.EXPAND_ROUND: return False
		
		'''if self.Cur_Round % 50 == 0:
			if self.builder_spawn < MAX_BUILDER_COUNT:
				if self.Glob_Tit > self.Builder_Cost + self.Spawn_Limit:
					self.CORE_spawn_builder(ct, self.open_spawn_dir)
					self.open_spawn_dir = self.open_spawn_dir.rotate_right().rotate_right()'''
		
		return False

	#endregion

	def CORE_run(self, ct: Controller):
		"""Main core runner"""
		self.CORE_update(ct)

		if self.state == "OPENING":
			if self.CORE_opening(ct):
				self.state = "EXPANDING"

		if self.state == "EXPANDING":
			self.CORE_expanding(ct)

		print("State: " + self.state)