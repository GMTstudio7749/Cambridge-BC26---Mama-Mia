import random

from cambc import Controller, Direction, EntityType, Environment, Position
from robot import Robot

class Core(Robot):
	def __init__(self):
		super().__init__()
		self.num_spawned = 0

	def RUN(self, ct):
		print("IM RUNNING")
		if self.num_spawned < 3:
			spawn_pos = ct.get_position().add(random.choice(self.DIRS))
			if ct.can_spawn(spawn_pos):
				ct.spawn_builder(spawn_pos)
				self.num_spawned += 1
