import random

from cambc import Controller, EntityType, Position
from movement import BugNav, Explore
from utils import *


class Builder():
	def __init__(self):
		self.bug_nav = BugNav()
		self.explore = Explore()
		
		self.CORE_POS = Position(-1, -1)

		self.Tit_Ore_Queue = []
		self.Anx_Ore_Queue = []


		self.state = "EXPLORE"
		self.target_ore = Position(-1, -1)
		self.start_building_pos = Position(-1, -1)
		self.explore_pos = Position(-1, -1	)

		self.destroy_target = Position(-1, -1)

	#region --- QUEUE FUNCTION ---
	def QUEUE_ore_update(self, ct: Controller):
		"""Scan vision to update new ore"""
		nearby_tiles = ct.get_nearby_tiles()
		for tile_pos in nearby_tiles:
			env = ct.get_tile_env(tile_pos)
			if not env in Ore_Env: continue
			if self.CHECK_harvester(ct, tile_pos) or not self.CHECK_can_connect_harvester(ct, tile_pos):
				self.QUEUE_ore_pop(env, tile_pos)
				continue
			else:
				self.QUEUE_ore_push(env, tile_pos)

	def QUEUE_ore_push(self, env: Environment, tile_pos: Position):
		"""Push an ore element into queue"""
		if env == Environment.ORE_TITANIUM:
			if not tile_pos in self.Tit_Ore_Queue:
				self.Tit_Ore_Queue.append(tile_pos)
		elif env == Environment.ORE_AXIONITE:
			if not tile_pos in self.Anx_Ore_Queue:
				self.Anx_Ore_Queue.append(tile_pos)
	
	def QUEUE_ore_pop(self, env: Environment, tile_pos: Position):
		"""Pop out an ore element from queue"""
		if env == Environment.ORE_TITANIUM:
			if tile_pos in self.Tit_Ore_Queue:
				idx = self.Tit_Ore_Queue.index(tile_pos)
				self.Tit_Ore_Queue.pop(idx)
		elif env == Environment.ORE_AXIONITE:
			if tile_pos in self.Anx_Ore_Queue:
				idx = self.Anx_Ore_Queue.index(tile_pos)
				self.Anx_Ore_Queue.pop(idx)
	#endregion

	#region --- GET FUNCTION ---
	def GET_core_pos(self, ct: Controller):
		"""Get core position at first spawned"""
		if self.CORE_POS != Position(-1, -1): return

		nearby_building = ct.get_nearby_buildings(dist_sq = 2)
		for bld in nearby_building:
			if ct.get_entity_type(bld) == EntityType.CORE:
				self.CORE_POS = ct.get_position(bld)
				break



	def GET_nearest_ore(self, ct: Controller):
		"""Get the nearest resource ore position\n
		Prior titan queue > anxio queue > vision
		Return Position(-1, -1) if found nothing"""
		my_pos = ct.get_position()
		nearest_pos = Position(-1, -1)
		min_dis = 999

		# From queue
		if len(self.Tit_Ore_Queue)  > 0:
			for pos in self.Tit_Ore_Queue:
				dis = my_pos.distance_squared(pos)
				if dis < min_dis:
					nearest_pos, min_dis = pos, dis
		# else:
		# 	for pos in self.Anx_Ore_Queue:
		# 		dis = my_pos.distance_squared(pos)
		# 		if dis < min_dis:
		# 			nearest_pos, min_dis = pos, dis

		# From vision
		# nearby_tiles = ct.get_nearby_tiles()
		# for tile_pos in nearby_tiles:
		# 	env = ct.get_tile_env(tile_pos)
		# 	if not env in Ore_Env: continue
		# 	if self.CHECK_harvester(ct, tile_pos):
		# 		self.QUEUE_ore_pop(env, tile_pos)
		# 		continue

		# 	dis = my_pos.distance_squared(tile_pos)
		# 	if dis < min_dis:
		# 		min_dis = dis
		# 		nearest_pos = tile_pos
		return nearest_pos
	#endregion

	#region --- CHECK FUNCTION ---

	def IS_in_map(self, ct, x: int, y: int):
		"""Check if two int x, y is located in map"""
		if x < 0 or x >= ct.get_map_width() or y < 0 or y >= ct.get_map_height():
			return False
		return True

	def CHECK_harvester(self, ct: Controller, tile_pos: Position):
		"""Check if a harvester is placed on a position\n
		If out of vision, return True"""
		if(not self.explore.IS_in_map(tile_pos.x, tile_pos.y)): return False
		if not ct.is_in_vision(tile_pos): return False

		pos_id = ct.get_tile_building_id(tile_pos)
		pos_env = ct.get_entity_type(pos_id)
		if pos_env != EntityType.HARVESTER:
			return False

		check_dir = Direction.NORTH
		connected = False
		for i in range(4):
			check_pos = tile_pos.add(check_dir)
			if(not self.IS_in_map(ct, check_pos.x, check_pos.y) or not ct.is_in_vision(check_pos)):
				connected = True
				break

			check_building_id = ct.get_tile_building_id(check_pos)
			check_building_type = ct.get_entity_type(check_building_id)
			check_building_team = ct.get_team(check_building_id)
			if(check_building_id is not None and check_building_type in [EntityType.BRIDGE, EntityType.CONVEYOR] and check_building_team == ct.get_team()):
				connected = True
			check_dir = check_dir.rotate_right().rotate_right()

		return connected

	def CHECK_can_connect_harvester(self, ct: Controller, tile_pos: Position):
		if not ct.is_in_vision(tile_pos): return True


		check_dir = Direction.NORTH
		can_connect = False
		for i in range(4):
			check_pos = tile_pos.add(check_dir)
			if(not self.IS_in_map(ct, check_pos.x, check_pos.y) or not ct.is_in_vision(check_pos)):
				pass
			else:
				check_env = ct.get_tile_env(check_pos)
				if(check_env == Environment.ORE_TITANIUM or check_env == Environment.ORE_AXIONITE):
					pass
				else:
					check_building_id = ct.get_tile_building_id(check_pos)
					check_building_type = ct.get_entity_type(check_building_id)
					check_building_team = ct.get_team(check_building_id)
					if check_building_id is None or  check_building_team == ct.get_team():
						can_connect = True
			check_dir = check_dir.rotate_right().rotate_right()

		return can_connect





	def CHECK_enemy_turret(self, ct: Controller):
		"""Return the nearest enemy turret in vision\n
		Return Pos(-1, -1) if found nothing"""
		turr_pos = Position(-1, -1)
		min_dis = 999
		my_pos = ct.get_position()

		vision = ct.get_nearby_entities()
		for ent_id in vision:
			etype = ct.get_entity_type(ent_id)
			if etype in [EntityType.GUNNER, EntityType.SENTINEL, EntityType.BREACH]:
				epos = ct.get_position(ent_id)
				cur_dis = my_pos.distance_squared(epos)
				if cur_dis < min_dis:
					min_dis = cur_dis
					turr_pos = epos
		return turr_pos
	#endregion

	#region --- BUILDER WORK FUNCTION ---
	def BUILDER_setup(self, ct: Controller):
		"""Setting up everything of a builder"""
		self.GET_core_pos(ct)
		self.bug_nav.SETUP(ct)
		self.explore.EXPLORE_setup(ct, ct.get_position(), self.CORE_POS)

		if(ct.get_current_round() == 1):
			self.state = "EXPLORE"
		else:
			self.state = "DEFENSE"

	def BUILDER_defense(self, ct):
		self.explore.MOVE_explore_in_box(ct, 5, 20, max(self.CORE_POS.x - 10, 0),max(self.CORE_POS.y - 10, 0), min(self.CORE_POS.x + 10, ct.get_map_width() - 1), min(self.CORE_POS.y + 10, ct.get_map_height() - 1) )

	def BUILDER_explore(self, ct: Controller):
		"""Builder robot explore function"""
		self.explore.MOVE_explore_in_box(ct, 5, 20, max(self.CORE_POS.x - 10, 0),max(self.CORE_POS.y - 10, 0), min(self.CORE_POS.x + 10, ct.get_map_width() - 1), min(self.CORE_POS.y + 10, ct.get_map_height() - 1) )
		self.target_ore = self.GET_nearest_ore(ct)



	def BUILDER_build(self, ct: Controller):
		"""Builder robot building function"""
		if self.CHECK_harvester(ct, self.target_ore) or not self.CHECK_can_connect_harvester(ct, self.target_ore):
			self.target_ore = Position(-1, -1)
			return

		if(ct.get_position() == self.target_ore):
			builded = False
			for i in Cardinal_Dirs:
				pos = self.target_ore.add(i)
				if(not self.explore.IS_in_map(pos.x, pos.y)):
					continue
				bid = ct.get_tile_building_id(pos)
				btype = ct.get_entity_type(bid)
				team = ct.get_team(bid)
				if(bid != None and btype == EntityType.ROAD):
					if(ct.can_destroy(pos)):
						ct.destroy(pos)
				if(bid is None and ct.can_place_marker(pos )):
					ct.place_marker(pos, 67)
					builded = True
			
			if(not builded):
				self.start_building_pos = Position(-1, -1)
				self.state = "BUILD_HARVESTER"
				return



		# 	if ct.get_action_cooldown() != 0 or ct.get_harvester_cost()[0] > ct.get_global_resources()[0]:
		# 		return
		# 	if ct.can_build_harvester(self.target_ore):
		# 		ct.build_harvester(self.target_ore)
		# 	self.target_ore = Position(-1, -1)
		# 	self.start_building_pos = ct.get_position()
		# 	self.state = "BUILD_BACK_TO_CORE"
		# 	return
		
		if(self.target_ore.distance_squared(ct.get_position()) == 1):

			bid = ct.get_tile_building_id(self.target_ore)
			btype = ct.get_entity_type(bid)
			bteam = ct.get_team(bid)

			if(btype == EntityType.MARKER):
				if(ct.can_destroy(self.target_ore)):
					ct.destroy(self.target_ore)

			if(ct.can_build_road(self.target_ore)):
				ct.build_road(self.target_ore)
			moveDir = ct.get_position().direction_to(self.target_ore)
			if(ct.can_move(moveDir)):
				ct.move(moveDir)
		else:			
			self.bug_nav.MOVE_to_target(ct, self.target_ore, False)

	def BUILDER_back_core(self, ct: Controller):
		"""Builder robot build bridge back to core"""
		my_pos = ct.get_position()
		core_dis = my_pos.distance_squared(self.CORE_POS)
		


		if core_dis <= 1 or self.bug_nav.MOVE_to_target_with_conveyor(ct, self.start_building_pos, self.CORE_POS) == "STUCK" :
			self.state = "EXPLORE"
			return


	def BUILDER_build_harvester(self, ct):
		if(self.start_building_pos == Position(-1, -1)):
			for i in Cardinal_Dirs:
				pos = self.target_ore.add(i)
				bid = ct.get_tile_building_id(pos)
				btype = ct.get_entity_type(bid)
				bteam = ct.get_team(bid)
				env = ct.get_tile_env(pos)

				if(btype == EntityType.MARKER and bteam == ct.get_team() and env == Environment.EMPTY):
					self.start_building_pos = pos
					break
		if(ct.get_position() == self.target_ore):
			if(ct.can_destroy(self.start_building_pos)):
				ct.destroy(self.start_building_pos)
			conveyorDir = self.target_ore.direction_to(self.start_building_pos)
			if(ct.can_build_road(self.start_building_pos)):
				ct.build_road(self.start_building_pos)
			if(ct.can_move(conveyorDir)):
				ct.move(conveyorDir)


		bid = ct.get_tile_building_id(self.target_ore)
		btype = ct.get_entity_type(bid)
		bteam = ct.get_team(bid)
		
		if(btype == EntityType.ROAD and bteam == ct.get_team()):
			if(ct.can_destroy(self.target_ore)):
				ct.destroy(self.target_ore)

		if(ct.can_build_harvester(self.target_ore)):
			ct.build_harvester(self.target_ore)
			self.state = "BUILD_BACK_TO_CORE"


	#endregion

	def BUILDER_determine_state(self, ct):

		if(self.state == "DEFENSE"):
			return "DEFENSE"
		if(self.state == "BUILD_HARVESTER" and self.target_ore != Position(-1, -1)):
			return "BUILD_HARVESTER"
		if self.state == "BUILD" and self.target_ore != Position(-1, -1):
			return "BUILD"
		if(self.state == "BUILD_BACK_TO_CORE"):
			return "BUILD_BACK_TO_CORE"
		if(self.target_ore != Position(-1, -1)):
			return "BUILD"
		return "EXPLORE"

	def BUILDER_run(self, ct: Controller):
		"""Main builder robot runner"""
		self.bug_nav.SENSE_nearby(ct)
		self.QUEUE_ore_update(ct)

		self.state = self.BUILDER_determine_state(ct)
		print(self.state)

		if(self.state == "BUILD_HARVESTER"):
			self.BUILDER_build_harvester(ct)
		if(self.state == "DEFENSE"):
			self.BUILDER_defense(ct)
		elif self.state == "EXPLORE":
			self.BUILDER_explore(ct)
		elif self.state == "BUILD":
			self.BUILDER_build(ct)
		elif self.state == "BUILD_BACK_TO_CORE":
			self.BUILDER_back_core(ct)

