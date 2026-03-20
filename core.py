from cambc import Controller, Position
from utils import *

class Core():
	def __init__(self):
		self.setup = False
		self.my_pos = Position(-1, -1)
		self.state = "OPENING"

		self.glob_tit = -1
		self.glob_anx = -1
		self.builder_cost = -1

		self.spawn_dir = Direction.NORTHEAST
		self.builder_spawn = 0

	def CORE_setup(self, ct: Controller):
		"""Core setup infos"""
		self.my_pos = ct.get_position()

	def CORE_update(self, ct: Controller):
		"""Core update info about global values"""
		self.glob_tit, self.glob_anx = ct.get_global_resources()
		self.builder_cost, tmp = ct.get_builder_bot_cost()

	def CORE_spawn_builder(self, ct: Controller):
		"""Core spawn builder"""
		if self.builder_cost > self.glob_tit: return

		print("Borning a builder bot!")
		spawn_pos = self.my_pos.add(self.spawn_dir)
		self.spawn_dir = self.spawn_dir.rotate_right().rotate_right()

		if ct.can_spawn(spawn_pos):
			ct.spawn_builder(spawn_pos)
			self.builder_spawn += 1

	def CORE_run(self, ct: Controller):
		"""Main core runner"""
		if not self.setup:
			self.CORE_setup(ct)
			self.setup = True
		
		self.CORE_update(ct)

		if self.state == "OPENING":
			if self.builder_spawn < Max_Builder_Opening:
				self.CORE_spawn_builder(ct)
			else:
				self.state = "EXPANDING"

		elif self.state == "EXPANDING":
			pass
			if self.glob_tit > 300 * self.builder_spawn:
				self.CORE_spawn_builder(ct)

		print("State: " + self.state)
