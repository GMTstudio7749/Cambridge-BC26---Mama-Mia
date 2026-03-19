import random

from cambc import Controller, Direction, EntityType, Environment, Position
from robot import Robot
from enum import Enum
from movement import BugNav

class Builder(Robot):
	def __init__(self):
		super().__init__()
		self.state = "EXPLORE"
		self.closest_building_ore = None
		self.explore_pos = Position(1, -1)
		self.cur_target = Position(1, -1)
		self.pending_bridges = []
		self.is_returning = False

	def DETERMINE_state(self, ct):

		if(self.state == "BUILD_BACK_TO_CORE"):
			return "BUILD_BACK_TO_CORE"
		if(self.closest_building_ore is not None):
			return "BUILD"
		return "EXPLORE"


	def GOT_harvested(self, ct, tile_pos):
		if(ct.is_in_vision(tile_pos)):
			pos_id = ct.get_tile_building_id(tile_pos)
			pos_env = ct.get_entity_type(pos_id)
			return pos_env is not None and pos_env == EntityType.HARVESTER
		else:
			return False
	def GET_nearest_ore(self, ct: Controller):
		my_pos = ct.get_position(ct.get_id())
		nearby_tiles = ct.get_nearby_tiles()    
		nearest_pos = None
		min_dist = float('inf')
		for tile_pos in nearby_tiles:
			env = ct.get_tile_env(tile_pos)
			if env in [Environment.ORE_TITANIUM, Environment.ORE_AXIONITE]:
				if(self.GOT_harvested(ct, tile_pos)):
					continue
				dist = my_pos.distance_squared(tile_pos)
				if dist < min_dist:
					min_dist = dist
					nearest_pos = tile_pos         
		return nearest_pos

	def RUN(self, ct):

		self.state = self.DETERMINE_state(ct)
		if(self.state == "EXPLORE"):
			self.EXPLORE_state(ct)
		elif(self.state == "BUILD"):
			self.BUILD_state(ct)
		elif(self.state == "BUILD_BACK_TO_CORE"):
			self.BUILD_BACK_state(ct)

	def EXPLORE_state(self, ct):
		if(self.explore_pos == Position(1, -1) or ct.get_position() == self.explore_pos):
			self.explore_pos = Position(random.randint(0, ct.get_map_width()-1), random.randint(0, ct.get_map_height()-1))
		self.bug_nav.MOVE_to_target(ct, self.explore_pos, True)
		self.closest_building_ore = self.GET_nearest_ore(ct)

	def BUILD_state(self, ct):
		if(self.GOT_harvested(ct, self.closest_building_ore)):
			self.closest_building_ore = self.GET_nearest_ore(ct)
			if self.closest_building_ore is None:
				self.state = "BUILD_BACK_TO_CORE"
			return
		dist_sq = ct.get_position().distance_squared(self.closest_building_ore)
		if dist_sq <= 2:
			if ct.can_build_harvester(self.closest_building_ore):
				ct.build_harvester(self.closest_building_ore)
				self.pending_bridges.append(self.closest_building_ore)
				next_ore = self.GET_nearest_ore(ct)
				if next_ore is not None:
					self.closest_building_ore = next_ore
				else:
					self.closest_building_ore = None
					self.state = "BUILD_BACK_TO_CORE"
			return
		self.bug_nav.MOVE_to_target(ct, self.closest_building_ore, False)
	def is_connected_to_network(self, ct, pos):
		nearby_tile = ct.get_nearby_tiles()
		for tile in nearby_tile:
			eid = ct.get_tile_building_id(tile)
			if eid is not None:
				etype = ct.get_entity_type(eid)
				if etype == EntityType.BRIDGE or etype == EntityType.CORE:
					if pos.distance_squared(tile) <= 2:
						return True
		return False
	def BUILD_BACK_state(self, ct):
			my_pos = ct.get_position()
			dist_to_base = 0
			if len(self.pending_bridges) > 0:
				target_source = self.pending_bridges[0]
				dist_to_source = my_pos.distance_squared(target_source)
				dist_to_base = my_pos.distance_squared(self.core_pos)
				if not self.is_returning:
					if dist_to_source > 2:
						self.bug_nav.MOVE_to_target(ct, target_source, True)
						return
					else:
						self.is_returning = True
				if self.is_returning:
					self.bug_nav.MOVE_to_target_with_bridge(ct, self.core_pos)
					if dist_to_base <= 2:
						self.pending_bridges.pop(0)
						self.is_returning = False
					return
			if dist_to_base <= 2 :
				self.state = "EXPLORE"
			else:
				self.bug_nav.MOVE_to_target_with_bridge(ct, self.core_pos)	
