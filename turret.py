from cambc import Controller, Position, Team
from utils import *

class Turret():
	def __init__(self):
		self.my_pos = Position(-1, -1)
		self.my_type = EntityType
		self.MY_TEAM = Team
		self.enemy_core_pos = Position(-1, -1)
		
		# Information
		self.nearby_entity = []

	def TURRET_setup(self, ct: Controller):
		"""Turret setup infos"""
		self.my_pos = ct.get_position()
		self.my_type = ct.get_entity_type()
		self.MY_TEAM = ct.get_team()

		for bid in ct.get_nearby_buildings():
			pos = ct.get_position(bid)
			btype = ct.get_entity_type(bid)
			bteam = ct.get_team(bid)

			if(btype == EntityType.CORE and bteam != ct.get_team()):
				self.enemy_core_pos = pos

	def TURRET_update(self, ct: Controller):
		"""Turret update info about vision entity,..."""
		self.nearby_entity = ct.get_nearby_entities()

	def TURRET_run(self, ct: Controller):
		"""Main turret runner (all types)"""
		self.TURRET_update(ct)

		if self.my_type == EntityType.SENTINEL:
			self.SENTINEL_run(ct)
		if self.my_type == EntityType.GUNNER:
			self.GUNNER_run(ct)
		if(self.my_type == EntityType.LAUNCHER):
			self.LAUNCHER_run(ct)

	def onTheMap(self, ct, loc):
		return (0 <= loc.x and loc.x < ct.get_map_width()) and (0 <= loc.y and loc.y < ct.get_map_height())


	def is_tile_passable(self, ct, pos):
		bbid = ct.get_tile_builder_bot_id(pos)
		if(bbid != None):
			return False
		
		bid = ct.get_tile_building_id(pos)
		btype = ct.get_entity_type(bid)
		bteam = ct.get_team(bid)

		if((btype == EntityType.CORE and bteam != ct.get_team()) or btype == EntityType.CONVEYOR or btype == EntityType.ROAD or btype == EntityType.BRIDGE):
			return True
		return False

	def FIND_best_launch_pos(self, ct: Controller):
		bestScore = -10**9
		bestPos = None

		myPos = ct.get_position()

		tiles = ct.get_nearby_tiles()

		for pos in tiles:
			if pos == myPos:
				continue

			if not self.is_tile_passable(ct, pos):
				continue

			dist = myPos.distance_squared(pos) ** 0.5
			score = dist 

			bid = ct.get_tile_building_id(pos)
			bteam = ct.get_team(bid)
			if bid is not None:
				btype = ct.get_entity_type(bid)

				if btype == EntityType.ROAD:
					score += 50 
				elif btype == EntityType.CONVEYOR:
					score += 20
				elif btype == EntityType.BRIDGE:
					score += 10
				elif btype == EntityType.CORE and bteam != ct.get_team():
					score += 100

			if not self.is_tile_passable(ct, pos):
				score -= 1000

			if score > bestScore:
				bestScore = score
				bestPos = pos

		return bestPos

	def LAUNCHER_run(self, ct):
		niceTarget = self.FIND_best_launch_pos(ct)
		# ct.draw_indicator_line(niceTarget, ct.get_position(), 255, 255, 0)
		for i in Dirs:
			pos = ct.get_position().add(i)
			if(not self.onTheMap(ct, pos)):
				continue
			bbid = ct.get_tile_builder_bot_id(pos)
			bbteam = ct.get_team(bbid)

			if(bbid != None and bbteam != ct.get_team()):
				if(ct.can_launch(pos, niceTarget)):
					ct.launch(pos, niceTarget)
					return

		for i in Dirs:
			pos = ct.get_position().add(i)
			if(not self.onTheMap(ct, pos)):
				continue
			bbid = ct.get_tile_builder_bot_id(pos)
			bbteam = ct.get_team(bbid)

			bid = ct.get_tile_building_id(pos)
			btype = ct.get_entity_type(bid)
			bteam = ct.get_team(bid)

			if(bbid != None and bbteam != ct.get_team()):
				if(ct.can_launch(pos, niceTarget)):
					ct.launch(pos, niceTarget)
					return
	
	def GUNNER_run(self, ct):
		if ct.get_action_cooldown() != 0:
			return

		my_team = ct.get_team()
		target_pos = ct.get_gunner_target()

		if target_pos is None:
			return

		if not ct.can_fire(target_pos):
			return

		building_id = ct.get_tile_building_id(target_pos)
		building_type = ct.get_entity_type(building_id)
		building_team = ct.get_team(building_id)
		bot_id = ct.get_tile_builder_bot_id(target_pos)

		if bot_id is not None:
			if ct.get_team(bot_id) != my_team:
				ct.fire(target_pos)
			return
		
		if building_id is not None:
			if(building_team != ct.get_team()):
				ct.fire(target_pos)
			else:
				if(building_type == EntityType.ROAD):
					ct.fire(target_pos)
			return

		ct.fire(target_pos)
		
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