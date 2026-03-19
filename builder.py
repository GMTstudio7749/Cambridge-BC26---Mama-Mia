import random

from cambc import Controller, EntityType, Environment, Position
from movement import BugNav
from utils import *

class Builder():
	def __init__(self):
		self.setup = False

		self.core_pos = Position(-1, -1)

		self.state = "EXPLORE"
		self.closest_building_ore = Position(-1, -1)
		self.explore_pos = Position(-1, -1)

		self.bug_nav = BugNav()

	def GET_core_pos(self, ct: Controller):
		"""Get core position at first spawned"""
		if self.core_pos != Position(-1, -1): return

		nearby_building = ct.get_nearby_buildings(dist_sq = 2)
		for bld in nearby_building:
			if ct.get_entity_type(bld) == EntityType.CORE:
				self.core_pos = ct.get_position(bld)
				break

	def GET_nearest_ore(self, ct: Controller):
		"""Get the nearest resource ore position\n
		Return Position(-1, -1) if found nothing"""
		my_pos = ct.get_position()
		nearest_pos = Position(-1, -1)
		min_dis = 999

		nearby_tiles = ct.get_nearby_tiles()
		for tile_pos in nearby_tiles:
			env = ct.get_tile_env(tile_pos)
			if not env in Ore_Env: continue
			if self.CHECK_harvester(ct, tile_pos):
				continue

			dis = my_pos.distance_squared(tile_pos)
			if dis < min_dis:
				min_dis = dis
				nearest_pos = tile_pos
		return nearest_pos

	def CHECK_harvester(self, ct: Controller, tile_pos: Position):
		"""Check if a harvester is placed on a position\n
		If out of vision, return True"""
		if not ct.is_in_vision(tile_pos): return True

		pos_id = ct.get_tile_building_id(tile_pos)
		pos_env = ct.get_entity_type(pos_id)
		if pos_env != EntityType.HARVESTER:
			return False
		return True
	
	def BUILDER_explore(self, ct: Controller):
		"""Builder robot explore function"""
		if(self.explore_pos == Position(-1, -1) or ct.get_position() == self.explore_pos):
			self.explore_pos = Position(random.randint(0, ct.get_map_width()-1), random.randint(0, ct.get_map_height()-1))
		self.bug_nav.MOVE_to_target(ct, self.explore_pos, True)
		self.closest_building_ore = self.GET_nearest_ore(ct)

	def BUILDER_build(self, ct: Controller):
		"""Builder robot building function"""
		if self.CHECK_harvester(ct, self.closest_building_ore):
			self.closest_building_ore = Position(-1, -1)
			return

		if ct.can_build_harvester(self.closest_building_ore):
			ct.build_harvester(self.closest_building_ore)
			self.closest_building_ore = Position(-1, -1)
			self.state = "BUILD_BACK_TO_CORE"
			return
		
		self.bug_nav.MOVE_to_target(ct, self.closest_building_ore, False)

	def BUILDER_back_core(self, ct: Controller):
		"""Builder robot build bridge back to core"""
		my_pos = ct.get_position()
		core_dis = my_pos.distance_squared(self.core_pos)
		if core_dis <= 1:
			self.state = "EXPLORE"
			return
		self.bug_nav.MOVE_to_target_with_bridge(ct, self.core_pos)

	def BUILDER_run(self, ct: Controller):
		"""Main builder robot runner"""
		if not self.setup:
			self.bug_nav.SETUP(ct)
			self.GET_core_pos(ct)
			self.setup = True

		self.bug_nav.SENSE_nearby(ct)

		if self.closest_building_ore != Position(-1, -1):
			self.state = "BUILD"
		elif self.state != "BUILD_BACK_TO_CORE":
			self.state = "EXPLORE"
		print(self.state)

		if self.state == "EXPLORE":
			self.BUILDER_explore(ct)
		elif self.state == "BUILD":
			self.BUILDER_build(ct)
		elif self.state == "BUILD_BACK_TO_CORE":
			self.BUILDER_back_core(ct)