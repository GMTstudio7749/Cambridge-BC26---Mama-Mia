from cambc import Controller, EntityType, Position, Team
from movement import BugNav, Explore
from utils import *

class Builder_Ore:
	def __init__(self):
		self.Count = 0
		self.Pos: list[Position] = []
		self.Env: list[Environment] = []
		self.Mark: list[int] = []
		self.Harv: list[bool] = []
		self.Barr: list[int] = []
		
		self.Ignore_Turn: list[int] = []
		self.MAX_IGNORE_TURN = 10

	def GET_marker_val(self, ct: Controller, tile_pos: Position):
		"""Get the value of the marker placed on a position\n
		   If there is no marker / out of vision -> -1\n
		   If it is the opposite team marker -> -2"""
		if not ct.is_in_vision(tile_pos): return -1

		ID = ct.get_tile_building_id(tile_pos)
		if ID is None: return -1
		if ct.get_entity_type(ID) == EntityType.MARKER:
			if ct.get_team(ID) == ct.get_team():
				return ct.get_marker_value(ID)
			else: return -2
		return -1
	
	def CHECK_harvester(self, ct: Controller, tile_pos: Position):
		"""Check if a harvester is placed on a position\n
		   If out of vision, return True"""
		if not ct.is_in_vision(tile_pos): return False

		ID = ct.get_tile_building_id(tile_pos)
		if ID is None: return False
		if ct.get_entity_type(ID) == EntityType.HARVESTER:
			return True
		return False
	
	def CHECK_barrier(self, ct: Controller, tile_pos: Position):
		"""Check barrier is placed on a position\n
		Return 0 = Nothing, 1 = Ally barrier, 2 = Enemy barrier"""
		if not ct.is_in_vision(tile_pos): return 0

		ID = ct.get_tile_building_id(tile_pos)
		if ID is None: return 0
		if ct.get_entity_type(ID) == EntityType.BARRIER:
			if ct.get_team(ID) == ct.get_team():
				return 1
			else: return 2
		return 0
	
	def ORE_update(self, ct: Controller):
		"""Scan vision to update new ores"""
		# Vision searching
		nearby_tiles = ct.get_nearby_tiles()
		for tile_pos in nearby_tiles:
			env = ct.get_tile_env(tile_pos)
			if env in Ore_Env:
				self.ORE_new_stat(ct, tile_pos)
		
		# Decrease ignore turn
		for i in range(self.Count):
			if self.Ignore_Turn[i] > 0:
				self.Ignore_Turn[i] = self.Ignore_Turn[i] - 1
	
	def ORE_new_stat(self, ct: Controller, ore_pos: Position):
		"""Update an ore in vision of its status"""
		if not ct.is_in_vision(ore_pos):
			return

		# Update stat
		env = ct.get_tile_env(ore_pos)
		if not env in Ore_Env: return
		mval = self.GET_marker_val(ct, ore_pos)
		harv = self.CHECK_harvester(ct, ore_pos)
		barr = self.CHECK_barrier(ct, ore_pos)
		
		# Update
		if ore_pos in self.Pos:
			idx = self.Pos.index(ore_pos)
			self.Mark[idx] = mval
			self.Harv[idx] = harv
			self.Barr[idx] = barr
			if mval == 36:
				if self.Ignore_Turn == 0:
					self.Ignore_Turn[idx] = self.MAX_IGNORE_TURN
		# New
		else:
			self.Count = self.Count + 1
			self.Pos.append(ore_pos)
			self.Env.append(env)
			self.Mark.append(mval)
			self.Harv.append(harv)
			self.Barr.append(barr)

			self.Ignore_Turn.append(0)
			if mval == 36:
				self.Ignore_Turn[self.Count] += self.MAX_IGNORE_TURN

	def ORE_debug(self):
		"""Output the current savings"""
		print("\n=== ORE STAT ===")
		for i in range(self.Count):
			pos = self.Pos[i]
			print("Pos("+str(pos.x)+", "+str(pos.y)+")")

			print("Env: ", end = "")
			if self.Env[i] == Environment.ORE_AXIONITE:
				print("AXI")
			elif self.Env[i] == Environment.ORE_TITANIUM:
				print("TIT")
			
			print("Harv:", str(self.Harv[i]))
			print("Mark:", str(self.Mark[i]))
			print("-------------")


class Builder:
	def __init__(self):
		self.bug_nav = BugNav()
		self.explore = Explore()
		self.oreo = Builder_Ore()
		
		self.CORE_POS = Position(-1, -1)
		self.MY_TEAM = Team
		self.EXPAND_ROUND = None # Ignore this

		self.Cur_Round = -1
		self.Core_Search_Range = -1

		self.state = "EXPLORE"
		# EXPLORE
		self.target_ore = Position(-1, -1)
		self.start_building_pos = Position(-1, -1)

		# Resource
		self.Glob_Tit = -1
		self.Glob_Anx = -1

		# Cost
		self.Builder_Cost = -1
		self.Harvest_Cost = -1
		self.Convey_Cost = -1
		self.Gunner_Cost = -1
		self.Road_Cost = -1

	#region --- GET FUNCTION ---
	def GET_core_pos(self, ct: Controller):
		"""Get core position at first spawned"""
		if self.CORE_POS != Position(-1, -1): return

		nearby_building = ct.get_nearby_buildings(dist_sq = 2)
		for bld in nearby_building:
			if ct.get_entity_type(bld) == EntityType.CORE:
				self.CORE_POS = ct.get_position(bld)
				break
	
	def GET_marker_val(self, ct: Controller, tile_pos: Position):
		"""Get the value of the marker placed on a position\n
		   If there is no marker / out of vision -> -1\n
		   If it is the opposite team marker -> -2"""
		if not ct.is_in_vision(tile_pos): return -1

		ID = ct.get_tile_building_id(tile_pos)
		if ID is None: return -1
		if ct.get_entity_type(ID) == EntityType.MARKER:
			if ct.get_team(ID) == self.MY_TEAM:
				return ct.get_marker_value(ID)
			else: return -2
		return -1
	
	def GET_best_seen_ore(self, ct: Controller):
		"""Get the nearest resource ore position FROM CORE\n
		   Prior titanium > anxionite\n
		   Return Position(-1, -1) if found nothing"""
		best_ore = Position(-1, -1)
		min_dis = 9999
		prior = "AXI"

		my_pos = ct.get_position()
		for i in range(self.oreo.Count):
			if self.oreo.Ignore_Turn[i] > 0: continue

			pos, env = self.oreo.Pos[i], self.oreo.Env[i]
			mval = self.oreo.Mark[i]
			barr = self.oreo.Barr[i]
			if self.oreo.Harv[i]: continue
			if mval == 36: continue
			
			core_dis = self.CORE_POS.distance_squared(pos)
			my_dis = pos.distance_squared(my_pos)

			if env == Environment.ORE_TITANIUM:
				if core_dis >= self.Core_Search_Range:
					if mval == 67 or barr > 0:
						continue
				prior = "TIT"

			elif env == Environment.ORE_AXIONITE:
				continue
				if prior != "AXI": continue
				if barr or mval != -1: continue
				if my_dis > 9: continue
			
			if best_ore == Position(-1, -1) or core_dis < min_dis:
				best_ore, min_dis = pos, core_dis
		return best_ore
	#endregion

	#region --- CHECK FUNCTION ---
	def CHECK_harvester(self, ct: Controller, tile_pos: Position):
		"""Check if a harvester is placed on a position\n
		   If out of vision, return True"""
		if not ct.is_in_vision(tile_pos): return False

		ID = ct.get_tile_building_id(tile_pos)
		if ID is None: return False
		if ct.get_entity_type(ID) == EntityType.HARVESTER:
			return True
		return False

	def CHECK_enemy_turret(self, ct: Controller):
		"""Return the nearest enemy turret in vision\n
		   Return Pos(-1, -1) if found nothing"""
		turr_pos = Position(-1, -1)
		min_dis = 999
		my_pos = ct.get_position()

		vision = ct.get_nearby_units()
		for ent_id in vision:
			if ct.get_team(ent_id) != self.MY_TEAM:
				continue
			etype = ct.get_entity_type(ent_id)
			if etype in Turret_Type:
				epos = ct.get_position(ent_id)
				cur_dis = my_pos.distance_squared(epos)
				if cur_dis < min_dis:
					min_dis = cur_dis
					turr_pos = epos
		return turr_pos
	
	def CHECK_ore_building(self, ct: Controller, ore_pos: Position):
		"""Check the type of the building on ore\n
		   Return False if ore is empty / out of vision"""
		if ore_pos == Position(-1, -1): return True
		if not ct.is_in_vision(ore_pos): return False

		if self.CHECK_harvester(ct, ore_pos):
			return True
		if self.GET_marker_val(ct, ore_pos) != -1:
			return True
		
		return False

	def CHECK_ore_protected(self, ct: Controller, ore_pos: Position):
		"""Check if the ore in vision is protected 4 sides\n
		Also return False if 13 <= dis_to_ore <= vision, True if out of vision"""
		if ore_pos == Position(-1, -1): return True
		if not ct.is_in_vision(ore_pos): return True

		# Ore check
		if not ct.is_tile_passable(ore_pos): return True 
		if ore_pos.distance_squared(ct.get_position()) > 13: return False	

		# Side check
		side_cnt = 0
		for dx in range(-1, 2):
			for dy in range(-1, 2):
				if dx != 0 and dy != 0: continue
				if dx == dy == 0: continue

				pos = Position(ore_pos.x + dx, ore_pos.y + dy)
				id = ct.get_tile_building_id(pos)
				if id is None: continue
				type = ct.get_entity_type(id)
				if type != EntityType.HARVESTER:
					if ct.get_team(id) != self.MY_TEAM:
						continue
				side_cnt += 1
		return (side_cnt == 4)
	#endregion

	#region --- BUILDER INFO ---
	def BUILDER_setup(self, ct: Controller):
		"""Setting up everything of a builder"""
		self.GET_core_pos(ct)
		self.MY_TEAM = ct.get_team()
		self.bug_nav.SETUP(ct)
		self.explore.EXPLORE_setup(ct, ct.get_position(), self.CORE_POS)

	def BUILDER_update(self, ct: Controller):
		"""Builder update info about global values"""
		self.Cur_Round = ct.get_current_round()
		self.Core_Search_Range = 100 + self.Cur_Round # NEED MODIFY

		self.Glob_Tit, self.Glob_Anx = ct.get_global_resources()
		self.Builder_Cost, tmp = ct.get_builder_bot_cost()
		self.Harvest_Cost, tmp = ct.get_harvester_cost()
		self.Convey_Cost, tmp = ct.get_conveyor_cost()
		self.Gunner_Cost, tmp = ct.get_gunner_cost()
		self.Road_Cost, tmp = ct.get_road_cost()
		self.Spawn_Limit = (
			50*self.Road_Cost +
			7*self.Convey_Cost +
			self.Gunner_Cost +
			3*self.Harvest_Cost
		)

		print("\n=== Unit Cost ===")
		print("Conveyor:", self.Convey_Cost)
		print("Builder:", self.Builder_Cost)
		print("Harvester:", self.Harvest_Cost)
		print("Gunner:", self.Gunner_Cost)
		print("Road:", self.Road_Cost)
		print("=> Expand limit:", self.Spawn_Limit)
		print("===================\n")
	#endregion

	#region --- BUILDER STATE WORK ---
	def BUILDER_switch_explore(self, ct: Controller):
		"""Switch state explore immediately in order to save cooldown"""
		self.state = "EXPLORE"
		self.target_ore = Position(-1, -1)
		self.start_building_pos = Position(-1, -1)
		self.BUILDER_explore(ct)

	def BUILDER_explore(self, ct: Controller):
		"""Builder robot explore function"""
		self.target_ore = self.GET_best_seen_ore(ct)
		if self.target_ore == Position(-1, -1):
			self.explore.MOVE_explore(ct, 10, 30)
			self.oreo.ORE_update(ct)
			self.target_ore = self.GET_best_seen_ore(ct)
		
		if self.target_ore != Position(-1, -1):
			x = self.BUILDER_move_to_ore(ct, self.target_ore)
			if x == "LEAVE":
				self.target_ore = Position(-1, -1)
				self.start_building_pos = Position(-1, -1)
			elif x == "OKE":
				self.state = "BUILD_AT_ORE"
				return
	
	def BUILDER_move_to_ore(self, ct: Controller, ore_pos: Position):
		"""Builder move to targeted ore position\n
		   Place a marker (36) on the ore to announce occupied\n
		   Return "OKE" if work finished, "LEAVE" if need to leave\n
		   "MORE" if not yet finished"""
		'''if self.CHECK_ore_protected(ct, ore_pos):
			return "LEAVE"'''
		if self.GET_marker_val(ct, ore_pos) == 36:
			return "LEAVE"
		
		# Move & place marker
		cur_dis = ore_pos.distance_squared(ct.get_position())
		if cur_dis <= 2:
			if ct.can_place_marker(ore_pos):
				ct.place_marker(ore_pos, 36)
			return "OKE"
		elif ct.get_move_cooldown() == 0:
			self.bug_nav.MOVE_to_target(ct, ore_pos, False)
			new_dis = ore_pos.distance_squared(ct.get_position())
			if new_dis <= 2:
				if ct.can_place_marker(ore_pos):
					ct.place_marker(ore_pos, 36)				
				return "OKE"

		return "MORE"

	def BUILDER_build_at_ore(self, ct: Controller, ore_pos: Position):
		"""Builder build machine / protect empty ore state function\n
		   ONLY work with DISTANCE <= 8 from working ore\n
		   Return "HARV" if build harvester, "BLOCK" if build barrier,\n
		   FAIL if failed, MORE if not yet done"""
		if ore_pos == Position(-1, -1): return "FAIL"

		'''# Move if distance > 8
		if ct.get_move_cooldown() == 0:
			my_pos = ct.get_position()
			my_dis = ore_pos.distance_squared(my_pos)
			if my_dis > 8:
				self.BUILDER_move_to_ore(ct, ore_pos)'''

		'''# Protect ore
		if not self.CHECK_ore_protected(ct, ore_pos):
			if ct.get_move_cooldown() == 0:
				if not ct.is_tile_passable(ore_pos):
					mval = self.GET_marker_val(ct, ore_pos)
					if mval > 0 or mval == -2:
						if ct.can_destroy(ore_pos):
							ct.destroy(ore_pos)
				if ct.is_tile_passable(ore_pos):
					self.bug_nav.MOVE_to_target(ct, ore_pos, False)
			convey_pos = ore_pos.add(Direction.NORTH)
			if can_place

		# Build
		if self.CHECK_ore_protected(ct, ore_pos):
			if ore_pos.distance_squared(ct.get_position()) == 0:
				if ct.get_move_cooldown() > 0:
					for d in Dirs:
						if ct.can_move(d):
							ct.move(d)
							break'''
			
			

		if self.CHECK_harvester(ct, ore_pos):
			return "FAIL"
		
		if self.GET_marker_val(ct, ore_pos) != 67:
			if ct.can_destroy(ore_pos):
				ct.destroy(ore_pos)
		if ore_pos.distance_squared(ct.get_position()) > 2:
			return "MORE"
		
		# Build action
		if ct.get_action_cooldown() > 0: return "MORE"
		env = ct.get_tile_env(ore_pos)
		dis_to_core = self.CORE_POS.distance_squared(ore_pos)
		if env == Environment.ORE_AXIONITE:
			if ct.can_place_marker(ore_pos):
				ct.place_marker(ore_pos, 67)
			return "MARK"
		
		elif env == Environment.ORE_TITANIUM:
			if dis_to_core >= self.Core_Search_Range:
				if ct.can_build_barrier(ore_pos):
					ct.build_barrier(ore_pos)
					return "BLOCK"
				
			if self.Glob_Tit < self.Harvest_Cost:
				return "MORE"

			# Destroy blockace
			bld_id = ct.get_tile_building_id(ore_pos)
			if bld_id is not None:
				type = ct.get_entity_type(bld_id)
				if type in [EntityType.BARRIER, EntityType.MARKER]:
					if ct.can_destroy(ore_pos):
						ct.destroy(ore_pos)

			# Build
			if ct.can_build_harvester(ore_pos):
				ct.build_harvester(ore_pos)
				my_pos = ct.get_position()
				self.start_building_pos = my_pos
				if my_pos.distance_squared(ore_pos) == 1:
					self.start_building_pos = my_pos
				else:
					for dir in Straight_Dirs:
						next_pos = my_pos.add(dir)
						if next_pos.distance_squared(ore_pos) == 1:
							self.start_building_pos = next_pos
							break
				return "HARV"
		return "MORE"
	
	def BUILDER_link_back_core(self, ct: Controller, start_build_pos: Position):
		"""Builder link harvester back to core
		Depends on start build position"""
		link = self.bug_nav.MOVE_to_target_with_conveyor(ct, start_build_pos, self.CORE_POS)
		if link == "STUCK":
			return "STUCK"
		core_dis = self.CORE_POS.distance_squared(ct.get_position())
		if core_dis <= 2:
			return "DONE"
	#endregion

	def BUILDER_run(self, ct: Controller):
		"""Main builder robot runner"""
		self.bug_nav.SENSE_nearby(ct)
		self.BUILDER_update(ct)
		self.oreo.ORE_update(ct)

		if self.state == "EXPLORE":
			self.BUILDER_explore(ct)

		if self.state == "BUILD_AT_ORE":
			x = self.BUILDER_build_at_ore(ct, self.target_ore)
			if x in ["MARK", "BLOCK", "FAIL"]:
				self.target_ore = Position(-1, -1)
				self.BUILDER_switch_explore(ct)
			elif x == "HARV":
				self.state = "LINK_BACK_CORE"
		
		if self.state == "LINK_BACK_CORE":
			x = self.BUILDER_link_back_core(ct, self.start_building_pos)
			if x in ["DONE", "STUCK"]:
				self.BUILDER_switch_explore(ct)

		print(self.state)
		print("Target ore: (", self.target_ore.x, self.target_ore.y, ")")
		ct.draw_indicator_dot(self.target_ore, 255, 255, 100)

		self.oreo.ORE_debug()