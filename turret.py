from cambc import Controller, Position, Team
from utils import *
from global_func import *
from functools import cmp_to_key

class Turret():
	def __init__(self):
		self.setup = False
		self.my_pos = Position(-1, -1)
		self.my_type : EntityType
		self.MY_TEAM : Team
		self.non_target : set[int] = set()
		self.assignable_as_non_target = [EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR, EntityType.BRIDGE]

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
		for id in ct.get_nearby_entities() :
			if ct.get_team(id) == self.MY_TEAM or ct.get_entity_type(id) not in self.assignable_as_non_target or id in self.non_target :
				continue
			if ct.get_entity_type(id) == EntityType.BRIDGE :
				pos = ct.get_bridge_target(id)
				target_id = None
				if ct.is_in_vision(pos) :
					target_id = ct.get_tile_building_id(pos)
				if target_id is None or target_id in self.non_target or ct.get_team(target_id) == self.MY_TEAM :
					self.assign_non_hostile(id,ct)

	def assign_non_hostile( self, id : int, ct : Controller ) :
		if id in self.non_target :
			return
		self.non_target.add(id)
		pos = ct.get_position(id)
		next_id = None
		if ct.is_in_vision(pos.add(Direction.NORTH)) :
			next_id = ct.get_tile_building_id(pos.add(Direction.NORTH))
		if next_id is not None and next_id in self.assignable_as_non_target and ct.get_direction(next_id) == Direction.SOUTH and ct.get_team(next_id) == self.MY_TEAM :
			self.assign_non_hostile(next_id, ct)
		next_id = None
		if ct.is_in_vision(pos.add(Direction.SOUTH)) :
			next_id = ct.get_tile_building_id(pos.add(Direction.SOUTH))
		if next_id is not None and next_id in self.assignable_as_non_target and ct.get_direction(next_id) == Direction.NORTH and ct.get_team(next_id) == self.MY_TEAM :
			self.assign_non_hostile(next_id, ct)
		next_id = None
		if ct.is_in_vision(pos.add(Direction.EAST)) :
			next_id = ct.get_tile_building_id(pos.add(Direction.EAST))
		if next_id is not None and next_id in self.assignable_as_non_target and ct.get_direction(next_id) == Direction.WEST and ct.get_team(next_id) == self.MY_TEAM :
			self.assign_non_hostile(next_id, ct)
		next_id = None
		if ct.is_in_vision(pos.add(Direction.WEST)) :
			next_id = ct.get_tile_building_id(pos.add(Direction.WEST))
		if next_id is not None and next_id in self.assignable_as_non_target and ct.get_direction(next_id) == Direction.EAST and ct.get_team(next_id) == self.MY_TEAM :
			self.assign_non_hostile(next_id, ct)


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
		if self.my_type == EntityType.GUNNER :
			self.GUNNER_run(ct)

	def SENTINEL_run(self, ct: Controller) :
		"""Main sentinel runner"""
		if ct.get_ammo_amount() == 0 :
			return
		
		enemy_turrets = [64,Position(-1,-1)]
		enemy_builds = [64,Position(-1,-1)]
		enemy_transports = [64,Position(-1,-1)]
		enemy_core = Position(-1,-1)
		enemy_barriers = [64,Position(-1,-1)]
		target_type : EntityType
		target_hp : int
		target_pos : Position
		target : int | None

		for pos in self.targetable :
			target = ct.get_tile_builder_bot_id(pos)
			if target is None :
				target = ct.get_tile_building_id(pos)
			if target is None or target in self.non_target :
				continue
			target_hp = ct.get_hp(target)
			target_pos = ct.get_position(target)

			if ct.get_team(target) != self.MY_TEAM and ct.can_fire(target_pos) :
				target_type = ct.get_entity_type(target)
				if target_type == EntityType.SENTINEL or target_type == EntityType.BREACH or target_type == EntityType.GUNNER or target_type == EntityType.LAUNCHER : #This category directly threatens ally units
					if target_hp < enemy_turrets[0] :
						enemy_turrets[0] = target_hp
						enemy_turrets[1] = target_pos
				elif target_type == EntityType.BUILDER_BOT or target_type == EntityType.FOUNDRY : #This category decides the win/loss of the game
					if target_hp < enemy_builds[0] :
						enemy_builds[0] = target_hp
						enemy_builds[1] = target_pos
				elif target_type == EntityType.CORE :
					enemy_core = target_pos
				elif target_type == EntityType.CONVEYOR or target_type == EntityType.ARMOURED_CONVEYOR or target_type == EntityType.BRIDGE : #This category decides enemy's prosperity
					if target_hp < enemy_transports[0] :
						enemy_transports[0] = target_hp
						enemy_transports[1] = target_pos
				elif target_type == EntityType.BARRIER : #This category is mandatory to destroy
					if target_hp < enemy_barriers[0] :
						enemy_barriers[0] = target_hp
						enemy_barriers[1] = target_pos

		if enemy_turrets[1] != Position(-1,-1):
			ct.fire(enemy_turrets[1])
		elif enemy_builds[1] != Position(-1,-1):
			ct.fire(enemy_builds[1])
		elif enemy_core != Position(-1,-1) :
			ct.fire(enemy_core)
		elif enemy_transports[1] != Position(-1,-1):
			ct.fire(enemy_transports[1])
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
		nearby_tiles = set(ct.get_nearby_tiles())
		delete_list : list[Position] = []

		for tile in nearby_tiles : #Registering vulnerable ally buildings
			id = ct.get_tile_building_id(tile)
			if id is not None :
				type = ct.get_entity_type(id)
			else :
				continue
			if ct.get_team(id) == self.MY_TEAM and type != EntityType.LAUNCHER and type != EntityType.BARRIER :
				delete_list.append(tile)

		for tile in delete_list : #Making sure landing location doesn't provide enemy with offensive opportunity
			nearby_tiles.discard(tile)
			nearby_tiles.discard(tile.add(Direction.NORTH))
			nearby_tiles.discard(tile.add(Direction.SOUTH))
			nearby_tiles.discard(tile.add(Direction.EAST))
			nearby_tiles.discard(tile.add(Direction.WEST))
			nearby_tiles.discard(tile.add(Direction.NORTHEAST))
			nearby_tiles.discard(tile.add(Direction.NORTHWEST))
			nearby_tiles.discard(tile.add(Direction.SOUTHEAST))
			nearby_tiles.discard(tile.add(Direction.SOUTHWEST))

		for tile in nearby_tiles: #Registering landing locations
			dir = self.my_pos.direction_to(tile)
			dist = self.my_pos.distance_squared(tile)
			if ct.can_launch(target, tile) and (dir not in throw_dir or throw_dir[dir][0] < dist) :
				throw_dir[dir] = (dist, tile)

		to_right = rotation
		to_left = rotation
		check_dirs = [ rotation ]
		for _ in range(3) :
			to_right.rotate_right()
			to_left.rotate_left()
			if rand.gen() % 2 == 0 :
				check_dirs.append(to_left)
				check_dirs.append(to_right)
			else :
				check_dirs.append(to_right)
				check_dirs.append(to_left)
		check_dirs.append(rotation.opposite())

		for d in check_dirs:
			if d in throw_dir:
				ct.launch(target, throw_dir[d][1])
				return
	def gunner_custom_comp(self, x : Position, y : Position) :
		return ( self.my_pos.distance_squared(x) < self.my_pos.distance_squared(y) ) - ( self.my_pos.distance_squared(x) > self.my_pos.distance_squared(y) )
	def GUNNER_run(self, ct : Controller ) :
		"""Main gunner runner"""
		if ct.get_ammo_amount() == 0 :
			return
		
		north_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.NORTH,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		south_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.SOUTH,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		east_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.EAST,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		west_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.WEST,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		northeast_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.NORTHEAST,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		northwest_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.NORTHWEST,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		southeast_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.SOUTHEAST,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		southwest_attackables = sorted(ct.get_attackable_tiles_from(self.my_pos,Direction.SOUTHWEST,self.my_type),key = cmp_to_key(self.gunner_custom_comp))
		check_list = [
			Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.NORTHEAST, Direction.NORTHWEST, Direction.SOUTHEAST, Direction.SOUTHWEST
			]
		score : dict[int,list[Direction]] = {}
		cur : list[Position]
		rotation = ct.get_direction()

		for dir in check_list :
			if dir == Direction.NORTH :
				cur = north_attackables
			elif dir == Direction.SOUTH :
				cur = south_attackables
			elif dir == Direction.EAST :
				cur = east_attackables
			elif dir == Direction.WEST :
				cur = west_attackables
			elif dir == Direction.NORTHEAST :
				cur = northeast_attackables
			elif dir == Direction.NORTHWEST :
				cur = northwest_attackables
			elif dir == Direction.SOUTHEAST :
				cur = southeast_attackables
			elif dir == Direction.SOUTHWEST :
				cur = southwest_attackables

			point = 0
			for pos in cur :
				target = ct.get_tile_building_id(pos)
				if target is None :
					target = ct.get_tile_builder_bot_id(pos)
				if target is None or ct.get_entity_type(target) == EntityType.MARKER or target in self.non_target :
					continue
				target_type = ct.get_entity_type(target)
				if ct.get_team(target) == self.MY_TEAM and target_type != EntityType.ROAD :
					break
				if target_type == EntityType.SENTINEL or target_type == EntityType.BREACH or target_type == EntityType.GUNNER or target_type == EntityType.LAUNCHER : #This category directly threatens ally units
					point += 103
				elif target_type == EntityType.CORE : #This category is the most beneficial target for this unit
					point += 25
				elif target_type == EntityType.CONVEYOR or target_type == EntityType.ARMOURED_CONVEYOR or target_type == EntityType.BRIDGE or target_type == EntityType.FOUNDRY : #This category is immovable and decides enemy's prosperity, hence allows efficient&fast destruction
					point += 13
				elif target_type == EntityType.BARRIER : #This category is mandatory to destroy
					point += 4
				elif target_type == EntityType.BUILDER_BOT : #This category is movable and tanky, making it hard to destroy quickly and effectively
					point += 1
				elif target_type == EntityType.HARVESTER : #Prioritize not harming harvesters
					break

			if dir == rotation and point > 0 :
				point += 51
			if point not in score :
				score[point] = []
			score[point].append(dir)

		point = list(score.keys())[-1]
		desired_rotation = score[point][rand.gen()%len(score[point])]
		if desired_rotation != rotation and point > 3 and ct.can_rotate(desired_rotation) :
			ct.rotate(desired_rotation)
			self.TURRET_update(ct)

		for pos in self.targetable :
			target = ct.get_tile_builder_bot_id(pos)
			if target is None :
				target = ct.get_tile_building_id(pos)
			if target is None or ct.get_entity_type(target) == EntityType.MARKER :
				continue
			if ct.get_team(target) == self.MY_TEAM and target_type != EntityType.ROAD :
				return
			if ct.can_fire(pos):
				ct.fire(pos)
				return