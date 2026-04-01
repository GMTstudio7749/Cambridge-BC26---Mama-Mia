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
		attack_pos = {}
		point = 0
		target_type = EntityType
		for target in self.nearby_entity :
			target_type = ct.get_entity_type(target)
			if ct.get_team(target) != self.MY_TEAM and ct.can_fire(ct.get_position(target)) :
				point = 0
				if target_type == EntityType.SENTINEL or target_type == EntityType.BREACH or target_type == EntityType.GUNNER or target_type == EntityType.LAUNCHER :
					point = 16
				elif target_type == EntityType.BUILDER_BOT or target_type == EntityType.FOUNDRY :
					point = 8
				elif target_type == EntityType.CONVEYOR or target_type == EntityType.ARMOURED_CONVEYOR or target_type == EntityType.BRIDGE :
					point = 4
				elif target_type == EntityType.CORE :
					point = 2
				else:
					point = 1
				attack_pos[ct.get_position(target)] += point
			if ct.get_team(target) == self.MY_TEAM and ct.can_fire(ct.get_position(target)) :
				point = 0
				if target_type == EntityType.SENTINEL or target_type == EntityType.BREACH or target_type == EntityType.GUNNER or target_type == EntityType.LAUNCHER :
					point = 16
				elif target_type == EntityType.BUILDER_BOT or target_type == EntityType.FOUNDRY :
					point = 8
				elif target_type == EntityType.CONVEYOR or target_type == EntityType.ARMOURED_CONVEYOR or target_type == EntityType.BRIDGE :
					point = 4
				elif target_type == EntityType.CORE :
					point = 2
				else:
					point = 1
				attack_pos[ct.get_position(target)] -= point
				
		target = Position(-1,-1)
		score = 0
		for key,value in attack_pos.items():
			if score > value:
				target = key
		if target != Position(-1,-1):
			if ct.can_fire(target):
				ct.fire(target)