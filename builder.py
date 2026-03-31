import random

from cambc import Controller, EntityType, Position
from movement import BugNav, Explore
from utils import *


class Builder():
    is_assigned = False
    def __init__(self):
        self.bug_nav = BugNav()
        self.explore = Explore()
        
        self.CORE_POS = Position(-1, -1)

        self.Tit_Ore_Queue = []
        self.Anx_Ore_Queue = []

        self.check_anxionite_builder = False
        self.check_build_foundry = False
        self.check_build_splitter = False
        self.first_anx_connected = False
        self.first_tit_connected = False
        self.first_anx_connected = False
        self.first_tit_connected = False



        self.state = "EXPLORE"
        self.target_anx_ore = Position(-1,-1)
        self.target_tit_ore = Position(-1, -1)
        self.conveyor_target = Position(-1,-1)
        self.target_ore = Position(-1, -1)
        self.splitter_pos = Position(-1,-1)
        self.foundry_pos = Position(-1,-1)
        self.start_building_pos = Position(-1, -1)
        self.explore_pos = Position(-1, -1)
        self.foundry_and_splitter_pos = Position(-1,-1)
        self.enemy_core_pos = Position(-1, -1)

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
    
    
    def GET_empty_target(self, ct: Controller, pos: Position):
        for d in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            target_pos = pos.add(d)
            if self.IS_in_map(ct, target_pos.x, target_pos.y) == False:
                continue
            if ct.is_tile_empty(target_pos):
                next_pos = target_pos.add(d)
                if next_pos == pos or not self.IS_in_map(ct, next_pos.x, next_pos.y):
                    continue
                if ct.is_tile_empty(next_pos):
                    return [target_pos, next_pos]
        return None
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

    def BUILDER_explore(self, ct: Controller):
        """Builder robot explore function"""
        self.explore.MOVE_explore(ct, 20, 70)
        self.target_ore = self.GET_nearest_ore(ct)
        if not self.check_anxionite_builder:
            self.target_ore = self.GET_nearest_ore(ct)

    def BUILDER_build(self, ct: Controller):
        """Builder robot building function"""
        if self.CHECK_harvester(ct, self.target_ore) or not self.CHECK_can_connect_harvester(ct, self.target_ore):
            self.target_ore = Position(-1, -1)
            return

        if(ct.get_position().distance_squared(self.target_ore) == 1):
            if ct.get_action_cooldown() != 0 or ct.get_harvester_cost()[0] > ct.get_global_resources()[0]:
                return
            if ct.can_build_harvester(self.target_ore):
                ct.build_harvester(self.target_ore)
            self.target_ore = Position(-1, -1)
            self.start_building_pos = ct.get_position()
            self.state = "BUILD_BACK_TO_CORE"
            return
            
        
        self.bug_nav.MOVE_to_target(ct, self.target_ore, False)

    def BUILDER_build_foundry_and_splitter(self, ct: Controller):
        """Build both foundry and splitter to use"""
        if self.foundry_pos == Position(-1, -1):
            self.GET_core_pos(ct)
            if self.CORE_POS == Position(-1, -1): return
            for d in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
                target_pos = self.CORE_POS.add(d).add(d) 
                if self.IS_in_map(ct, target_pos.x, target_pos.y) and ct.is_tile_empty(target_pos):
                    next_pos = target_pos.add(d)
                    if self.IS_in_map(ct, next_pos.x, next_pos.y) and ct.is_tile_empty(next_pos):
                        self.foundry_pos = target_pos
                        self.splitter_pos = next_pos
                        break
            if self.foundry_pos == Position(-1, -1): return
        my_pos = ct.get_position()
        if not self.check_build_foundry:
            dist = my_pos.distance_squared(self.foundry_pos)
            if dist > 2:
                self.bug_nav.MOVE_to_target(ct, self.foundry_pos, False)
                return
            
            if ct.get_action_cooldown() == 0 and ct.can_build_foundry(self.foundry_pos):
                ct.build_foundry(self.foundry_pos)
                self.check_build_foundry = True
            return
        if self.check_build_splitter == False:
            dist = my_pos.distance_squared(self.splitter_pos)
            if dist > 2:
                self.bug_nav.MOVE_to_target(ct, self.splitter_pos, False)
                return             
            if ct.get_action_cooldown() == 0:
                #if not ct.is_tile_empty(self.splitter_pos):
                    #if ct.can_destroy(self.splitter_pos):
                        #ct.destroy(self.splitter_pos)
                    #return
                splitter_dir = self.splitter_pos.direction_to(self.CORE_POS).opposite()
                if ct.can_build_splitter(self.splitter_pos, splitter_dir.opposite()):
                    ct.build_splitter(self.splitter_pos, splitter_dir.opposite())
                    self.check_build_splitter = True
                    self.check_anxionite_builder = False
                    self.state = "BUILD_CONVEYOR_TO_FOUNDRY"
    def BUILDER_build_conveyor_to_foundry(self, ct: Controller):
        if self.start_building_pos == Position(-1, -1):
            if len(self.Anx_Ore_Queue) > 0:
                self.target_anx_ore = self.Anx_Ore_Queue[0]
                self.bug_nav.MOVE_to_target(ct, self.target_anx_ore, False)
                if ct.get_position().distance_squared(self.target_anx_ore) == 1:
                    if ct.get_action_cooldown() != 0 or ct.get_harvester_cost()[0] > ct.get_global_resources()[0]:
                        return
                    if ct.can_build_harvester(self.target_anx_ore):
                        ct.build_harvester(self.target_anx_ore)
                        self.start_building_pos = ct.get_position()
                    self.target_anx_ore = Position(-1, -1)
            else:
                self.explore.MOVE_explore(ct, 20, 70)
        else:
            if ct.get_position().distance_squared(self.foundry_pos) <= 1 or self.bug_nav.MOVE_to_target_with_conveyor(ct, self.start_building_pos, self.foundry_pos) == "STUCK":
                self.state = "BUILD_CONVEYOR_TO_SPLITTER"
                return
    def BUILDER_build_conveyor_to_splitter(self, ct: Controller):
        if self.start_building_pos == Position(-1, -1):
            if len(self.Tit_Ore_Queue) > 0:
                self.target_tit_ore = self.Tit_Ore_Queue[0]
                self.bug_nav.MOVE_to_target(ct, self.target_tit_ore, False)
                if ct.get_position().distance_squared(self.target_tit_ore) == 1:
                    if ct.get_action_cooldown() != 0 or ct.get_harvester_cost()[0] > ct.get_global_resources()[0]:
                        return
                    if ct.can_build_harvester(self.target_tit_ore):
                        ct.build_harvester(self.target_tit_ore)
                        self.start_building_pos = ct.get_position()
                    self.target_tit_ore = Position(-1, -1)
            else:
                self.explore.MOVE_explore(ct, 20, 70)
        else:
            if ct.get_position().distance_squared(self.foundry_pos) <= 1 or self.bug_nav.MOVE_to_target_with_conveyor(ct, self.start_building_pos, self.foundry_pos) == "STUCK":
                self.state = "GET_ENEMY_CORE_POS"
                return
    def BUILDER_get_enemy_core_pos(self, ct: Controller):
        """Find enemy core position"""
        self.GET_core_pos(ct)
        possible_enemy_core_pos_1 = Position(ct.get_map_width() - self.CORE_POS.x, self.CORE_POS.y)
        possible_enemy_core_pos_2 = Position(ct.get_map_width() - self.CORE_POS.x,ct.get_map_height() - self.CORE_POS.y)
        possible_enemy_core_pos_3 = Position(self.CORE_POS.x,ct.get_map_height() - self.CORE_POS.y)
        self.bug_nav.MOVE_to_target(ct, possible_enemy_core_pos_1, False)
        bld1 = ct.get_tile_building_id(ct.get_position())
        if ct.get_entity_type(bld1) == EntityType.CORE:
            self.enemy_core_pos = possible_enemy_core_pos_1
        self.bug_nav.MOVE_to_target(ct, possible_enemy_core_pos_2, False)
        bld2 = ct.get_tile_building_id(ct.get_position())
        if ct.get_entity_type(bld2) == EntityType.CORE:
            self.enemy_core_pos = possible_enemy_core_pos_2
        self.bug_nav.MOVE_to_target(ct, possible_enemy_core_pos_3, False)
        bld3 = ct.get_tile_building_id(ct.get_position())
        if ct.get_entity_type(bld3) == EntityType.CORE:
            self.enemy_core_pos = possible_enemy_core_pos_3

                
    def BUILDER_back_core(self, ct: Controller):
        """Builder robot build bridge back to core"""
        my_pos = ct.get_position()
        core_dis = my_pos.distance_squared(self.CORE_POS)
        
        if core_dis <= 1 or self.bug_nav.MOVE_to_target_with_conveyor(ct, self.start_building_pos, self.CORE_POS) == "STUCK" :
            self.state = "EXPLORE"
            return



    #endregion

    def BUILDER_run(self, ct: Controller):
        """Main builder robot runner"""
        self.bug_nav.SENSE_nearby(ct)
        self.QUEUE_ore_update(ct)
        if Builder.is_assigned == False and ct.get_current_round() == 1:
            Builder.is_assigned = True
            self.check_anxionite_builder = True
            self.foundry_and_splitter_pos = ct.get_position()
            self.state = "BUILD_ANX"

        if self.check_anxionite_builder == True:
            self.state = "BUILD_ANX"
        elif self.state == "BUILD_CONVEYOR_TO_FOUNDRY":
            self.state = "BUILD_CONVEYOR_TO_FOUNDRY"
        elif self.state == "BUILD_CONVEYOR_TO_SPLITTER":
            self.state = "BUILD_CONVEYOR_TO_SPLITTER"
        elif self.state == "GET_ENEMY_CORE_POS":
            self.state = "GET_ENEMY_CORE_POS"
        elif self.state == "BUILD_BACK_TO_CORE":
            self.state = "BUILD_BACK_TO_CORE"
        elif self.target_ore != Position(-1, -1):
            self.state = "BUILD"
        else:
            self.state = "EXPLORE"
        print(self.state)

        if self.state == "BUILD_ANX":
            self.BUILDER_build_foundry_and_splitter(ct)
        elif self.state == "BUILD_CONVEYOR_TO_FOUNDRY":
            self.BUILDER_build_conveyor_to_foundry(ct)
        elif self.state == "BUILD_CONVEYOR_TO_SPLITTER":
            self.BUILDER_build_conveyor_to_splitter(ct)
        elif self.state == "GET_ENEMY_CORE_POS":
            self.BUILDER_get_enemy_core_pos(ct)
        elif self.state == "EXPLORE":
            self.BUILDER_explore(ct)
        elif self.state == "BUILD":
            self.BUILDER_build(ct)
        elif self.state == "BUILD_BACK_TO_CORE":
            self.BUILDER_back_core(ct)

