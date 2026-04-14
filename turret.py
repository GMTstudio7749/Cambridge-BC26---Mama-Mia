from cambc import Controller, Position, Team
from utils import *

class Turret():
	def __init__(self):
		self.setup = False
		self.my_pos = Position(-1, -1)
		self.my_type : EntityType
		self.MY_TEAM : Team

		# Information
		self.targetable = []

	def TURRET_setup(self, ct: Controller):
		"""Turret setup infos"""
		self.my_pos = ct.get_position()
		self.my_type = ct.get_entity_type()
		self.MY_TEAM = ct.get_team()

	def TURRET_update(self, ct: Controller):
		"""Turret update info about vision entity,..."""
		self.targetable = ct.get_attackable_tiles()

	def TURRET_run(self, ct: Controller):
		"""Main turret runner (all types)"""
		# SETUP
		if not self.setup:
			self.TURRET_setup(ct)
			self.setup = True
		
		# UPDATE
		self.TURRET_update(ct)

		# WORK
		if self.my_type == EntityType.SENTINEL:
			self.SENTINEL_run(ct)
		if self.my_type == EntityType.LAUNCHER:
			self.LAUNCHER_run(ct)

	def SENTINEL_run(self, ct: Controller) :
		"""Main sentinel runner"""
		enemy_turrets = [64,Position(-1,-1)]
		enemy_builds = [64,Position(-1,-1)]
		enemy_transports = [64,Position(-1,-1)]
		enemy_core : Position
		enemy_barriers = [64,Position(-1,-1)]
		target_type : EntityType
		target_hp : int
		target_pos : Position
		target : int | None
		for pos in self.targetable :
			if ct.get_tile_builder_bot_id(pos) is not None :
				target = ct.get_tile_builder_bot_id(pos)
			elif ct.get_tile_building_id(pos) is not None :
				target = ct.get_tile_building_id(pos)
			else :
				continue
			target_hp = ct.get_hp(target)
			target_pos = ct.get_position(target)
			if ct.get_team(target) != self.MY_TEAM and ct.can_fire(target_pos) :
				target_type = ct.get_entity_type(target)
				if target_type == EntityType.SENTINEL or target_type == EntityType.BREACH or target_type == EntityType.GUNNER or target_type == EntityType.LAUNCHER :
					if target_hp < enemy_turrets[0] :
						enemy_turrets[0] = target_hp
						enemy_turrets[1] = target_pos
				elif target_type == EntityType.BUILDER_BOT or target_type == EntityType.FOUNDRY :
					if target_hp < enemy_builds[0] :
						enemy_builds[0] = target_hp
						enemy_builds[1] = target_pos
				elif target_type == EntityType.CONVEYOR or target_type == EntityType.ARMOURED_CONVEYOR or target_type == EntityType.BRIDGE :
					if target_hp < enemy_transports[0] :
						enemy_transports[0] = target_hp
						enemy_transports[1] = target_pos
				elif target_type == EntityType.CORE :
					enemy_core = target_pos
				elif target_type == EntityType.BARRIER :
					if target_hp < enemy_barriers[0] :
						enemy_barriers[0] = target_hp
						enemy_barriers[1] = target_pos
		if enemy_turrets[1] != Position(-1,-1):
			ct.fire(enemy_turrets[1])
		elif enemy_builds[1] != Position(-1,-1):
			ct.fire(enemy_builds[1])
		elif enemy_transports[1] != Position(-1,-1):
			ct.fire(enemy_transports[1])
		elif enemy_core != Position(-1,-1) :
			ct.fire(enemy_core)
		elif enemy_barriers[1] != Position(-1,-1):
			ct.fire(enemy_barriers[1])

	def LAUNCHER_run(self, ct : Controller) :
		"""Main launcher runner"""
		target = Position(-1, -1)
		throw_dir: dict[Direction, tuple[int, Position]] = {}

		for pos in self.targetable:
			unit = ct.get_tile_builder_bot_id(pos)
			if unit is None:
				continue

			if ct.get_entity_type(unit) == EntityType.BUILDER_BOT and ct.get_team(unit) != self.MY_TEAM:
				target = ct.get_position(unit)
				break

		if target == Position(-1, -1):
			return

		rotation = self.my_pos.direction_to(target)

		for tile in ct.get_nearby_tiles():
			dir = self.my_pos.direction_to(tile)
			dist = self.my_pos.distance_squared(tile)

			if ct.can_launch(target, tile):
				if dir not in throw_dir or throw_dir[dir][0] < dist:
					throw_dir[dir] = (dist, tile)

		check_dirs = [
			rotation,
			rotation.rotate_right(),
			rotation.rotate_left(),
			rotation.rotate_right().rotate_right(),
			rotation.rotate_left().rotate_left(),
			rotation.rotate_right().rotate_right().rotate_right(),
			rotation.rotate_left().rotate_left().rotate_left(),
			rotation.opposite()
		]

		for d in check_dirs:
			if d in throw_dir:
				ct.launch(target, throw_dir[d][1])
				return