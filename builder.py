import random

from cambc import Controller, Direction, EntityType, Environment, Position
from robot import Robot
from enum import Enum

class Builder(Robot):
	def __init__(self):
		super().__init__()
		self.state = "EXPLORE"
		self.closest_building_ore = None
		self.explore_pos = None

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
		if(self.explore_pos == None or ct.get_position() == self.explore_pos):
			self.explore_pos = Position(random.randint(0, ct.get_map_width()-1), random.randint(0, ct.get_map_height()-1))
		self.bug_nav.MOVE_to_target(ct, self.explore_pos, True)
		self.closest_building_ore = self.GET_nearest_ore(ct)

	def BUILD_state(self, ct):
		if(self.GOT_harvested(ct, self.closest_building_ore)):
			self.closest_building_ore = None
			return

		if ct.can_build_harvester(self.closest_building_ore):
			ct.build_harvester(self.closest_building_ore)
			self.closest_building_ore = None
			self.state = "BUILD_BACK_TO_CORE"
			return
		self.bug_nav.MOVE_to_target(ct, self.closest_building_ore, False)

	def BUILD_BACK_state(self, ct):
			dist_to_base = ct.get_position().distance_squared(self.core_pos)
			if dist_to_base <= 1:
				self.state = "EXPLORE"
				return	
			self.bug_nav.MOVE_to_target_with_bridge(ct, self.core_pos)