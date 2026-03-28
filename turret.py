from cambc import Controller, Position, Team
from utils import *

class Turret():
	def __init__(self):
		self.my_pos = Position(-1, -1)
		self.my_type = EntityType
		self.MY_TEAM = Team

		# Information
		self.nearby_entity = []

	def TURRET_setup(self, ct: Controller):
		"""Turret setup infos"""
		self.my_pos = ct.get_position()
		self.my_type = ct.get_entity_type()
		self.MY_TEAM = ct.get_team()

	def TURRET_update(self, ct: Controller):
		"""Turret update info about vision entity,..."""
		self.nearby_entity = ct.get_nearby_entities()
	
	def TURRET_run(self, ct: Controller):
		"""Main turret runner (all types)"""
		self.TURRET_update(ct)

		if self.my_type == EntityType.SENTINEL:
			self.SENTINEL_run(ct)

	def SENTINEL_run(self, ct: Controller) :
		"""Main sentinel runner"""
		
		# Priority 1 : Enemy bots
		for target in self.nearby_entity:
			if ct.get_team(target) != self.MY_TEAM and ct.get_entity_type(target) == EntityType.BUILDER_BOT and ct.can_fire(ct.get_position(target)) :
				ct.fire(ct.get_position(target))
				return
			
		# Priority 2 : Bridge & Conveyor...
		# Priority 3 : Enemy core...
		# Priority 4 : Barrier...