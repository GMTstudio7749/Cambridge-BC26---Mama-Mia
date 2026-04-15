from cambc import Controller, EntityType, Position
from bld_context import ctx
from utils import *

class BldEco:
    def __init__(self):
        self.state = "EXPLORE"
        self.Core_Search_Range = -1

        self.target_ore = Position(-1, -1)
        self.start_building_pos = Position(-1, -1)

    #region ----- GET function -----
    def GET_best_seen_ore(self, ct: Controller, cook: str):
        """Get the best seen ore position, shortest distance to ore\n
           If cook == "TIT" => Prior TIT > AXI\n
           If cook == "AXI" => Choose AXI only\n
           Return Position(-1, -1) if found nothing"""
        best_ore = Position(-1, -1)
        min_dis = 9999
        prior = "AXI"
        
        my_pos = ct.get_position()
        for ore in ctx.Ores.values():
            # Critical condition
            if ore.IS_ore_ignore(): continue
            
            core_dis = ctx.CORE_POS.distance_squared(ore.pos)
            my_dis = ore.pos.distance_squared(my_pos)

            if ore.env == Environment.ORE_TITANIUM:
                if ore.harv and ore.linked_core: continue
                if core_dis >= self.Core_Search_Range:
                    if ore.barr == 1: # Ensure block barrier
                        continue
                prior = "TIT"

            elif ore.env == Environment.ORE_AXIONITE:
                if prior != "AXI": continue
                if ore.harv: continue
                if ore.barr or ore.mark != -1: continue
                if my_dis > 9: continue
            
            if best_ore == Position(-1, -1) or core_dis < min_dis:
                best_ore, min_dis = ore.pos, core_dis
        return best_ore
    #endregion
    
    #region ----- ECO general -----
    def ECO_update(self):
        """Update for eco builders"""
        self.Core_Search_Range = 100 + ctx.Cur_Round
    
    def ECO_debug(self, ct: Controller):
        """Debug eco builders"""
        # Output
        print("\n=== ECO stat ===")
        print(f"+ State: {self.state}")
        print(f"Target ore: ({self.target_ore.x},{self.target_ore.y})")
        print(f"Start_building_pos: ({self.start_building_pos.x},{self.start_building_pos.y})")
        # Draw
        ct.draw_indicator_dot(self.target_ore, 255, 255, 100)
    #endregion

    #region ----- ECO move / act -----
    def ECO_move_to_ore(self, ct: Controller, ore_pos: Position):
        """ECO builder move to targeted ore pos\n
           Return "OKE" if work finished, "LEAVE" if need to leave\n
           "MORE" if not yet finished"""
        '''if self.CHECK_ore_protected(ct, ore_pos):
            return "LEAVE"'''
        # if ctx.CHECK_harvester(ct, ore_pos): return "LEAVE"
        # if ctx.CHECK_barrier(ct, ore_pos) == 2: return "LEAVE"
        
        cur_dis = ore_pos.distance_squared(ct.get_position())
        if cur_dis <= 9: # Check for blockace, if too far still target
            if ctx.CHECK_harvester(ct, ore_pos): return "LEAVE"
            if ctx.CHECK_barrier(ct, ore_pos) > 0: return "LEAVE"
        if cur_dis <= 2: return "OKE"

        # Move to target
        elif ct.get_move_cooldown() == 0:
            ctx.bugnav.MOVE_to_target(ct, ore_pos, False)
            new_dis = ore_pos.distance_squared(ct.get_position())
            if new_dis <= 2: return "OKE"

        return "MORE"

    def ECO_build_at_ore(self, ct: Controller, ore_pos: Position):
        """ECO builder build machine / protect empty ore state function\n
           ONLY work with DISTANCE <= 8 from working ore\n
           Return "HARV" if build harvester, "BLOCK" if build barrier,\n
           "FAIL" if failed, "MORE" if not yet done"""
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
            
        if ctx.CHECK_harvester(ct, ore_pos): return "FAIL"
        if ctx.CHECK_barrier(ct, ore_pos) == 2: return "FAIL"

        if ore_pos.distance_squared(ct.get_position()) > 2:
            if ct.get_move_cooldown() > 0:
                ctx.bugnav.MOVE_to_target(ct, ore_pos, False)
            return "MORE"
        
        # Build action
        env = ct.get_tile_env(ore_pos)
        dis_to_core = ctx.CORE_POS.distance_squared(ore_pos)
        if env == Environment.ORE_AXIONITE:
            if ct.can_build_barrier(ore_pos):
                ct.build_barrier(ore_pos)
            return "BLOCK"
        
        elif env == Environment.ORE_TITANIUM:
            # WARNING: check building on ore for further decision
            # Case: Enemy passable building
            ID = ct.get_tile_building_id(ore_pos)
            if ID is not None:
                if ct.get_team(ID) != ctx.MY_TEAM:
                    pass
            # Case: Enemy unpassable building
            # Case: Ally building (no pass / unpass)
            # Case: Empty
            if ctx.GET_marker_val(ct, ore_pos) > 0:
                if ct.can_destroy(ore_pos):
                    ct.destroy(ore_pos)

            if dis_to_core >= self.Core_Search_Range:
                # if ct.can_build_barrier(ore_pos):
                    # ct.build_barrier(ore_pos)
                    return "BLOCK"
                
            if ctx.Glob_Tit < ctx.Harvest_Cost:
                return "MORE"

            # Destroy blockace
            bld_id = ct.get_tile_building_id(ore_pos)
            if bld_id is not None:
                type = ct.get_entity_type(bld_id)
                if type in [EntityType.BARRIER, EntityType.MARKER, EntityType.ROAD]:
                    if ct.can_destroy(ore_pos):
                        ct.destroy(ore_pos)

            # Build
            if ct.can_build_harvester(ore_pos):
                ct.build_harvester(ore_pos)

                best_pos = Position(-1, -1)
                min_dis = 9999
                dxy = [[-1, 0], [1, 0], [0, -1], [0, 1]]
                for dx, dy in dxy:
                    check_pos = Position(ore_pos.x + dx, ore_pos.y + dy)
                    if not ctx.IS_in_map(check_pos): continue
                    if not ct.is_in_vision(check_pos): continue

                    # Empty env only
                    env = ct.get_tile_env(check_pos)
                    if env != Environment.EMPTY: continue

                    # Check for buildings
                    ID = ct.get_tile_building_id(check_pos)
                    if ID is not None:
                        type = ct.get_entity_type(ID)
                        if not type in [EntityType.ROAD, EntityType.MARKER]:
                            continue

                    # Compare distance
                    dis = ctx.CORE_POS.distance_squared(check_pos)
                    if best_pos == Position(-1, -1) or dis < min_dis:
                        best_pos, min_dis = check_pos, dis
                self.start_building_pos = best_pos
                return "HARV"
        return "MORE"
    
    def ECO_link_back_core(self, ct: Controller, start_build_pos: Position):
        """ECO builder link harvester back to core
        Depends on start build position"""
        # Destroy under foot blocks first
        # my_pos = ct.get_position()
        # ID = ct.get_tile_building_id(my_pos)
        # if ID is not None:
        #     if ct.get_team(ID) != ctx.MY_TEAM:
        #         if ct.can_fire(my_pos):
        #             ct.fire(my_pos)
        #         return "FIRING"

        link = ctx.bugnav.MOVE_to_target_with_conveyor(ct, start_build_pos, ctx.CORE_POS)
        if link == "STUCK":
            return "STUCK"
        # core_dis = ctx.CORE_POS.distance_squared(ct.get_position())
        # if core_dis <= 2:
            # return "DONE"
    #endregion

    #region ----- ECO state -----
    def ECO_switch_explore(self, ct: Controller):
        """Switch state "EXPLORE" immediately in order to save cooldown"""
        self.state = "EXPLORE"
        self.target_ore = Position(-1, -1)
        self.start_building_pos = Position(-1, -1)
        self.ECO_explore(ct)

    def ECO_explore(self, ct: Controller):
        """ECO builder explore function"""
        # Haven't seen anything yet
        if self.target_ore == Position(-1, -1):
            self.target_ore = self.GET_best_seen_ore(ct, "TIT")
            
            if self.target_ore == Position(-1, -1):
                ctx.explore.MOVE_explore(ct, 10, 30)
                ctx.ORE_update(ct)
                self.target_ore = self.GET_best_seen_ore(ct, "TIT")
        
        # Head to targeting ore
        if self.target_ore != Position(-1, -1):
            x = self.ECO_move_to_ore(ct, self.target_ore)
            if x == "LEAVE":
                self.target_ore = Position(-1, -1)
                self.start_building_pos = Position(-1, -1)
            elif x == "OKE":
                self.state = "BUILD_AT_ORE"
                return
    
    #endregion

    def ECO_run(self, ct: Controller):
        """Main ECO builder function"""

        # UPDATE
        ctx.ORE_update(ct)
        ctx.UPD_resource_cost(ct)
        self.ECO_update()

        # WORK
        if self.state == "EXPLORE":
            self.ECO_explore(ct)

        if self.state == "BUILD_AT_ORE":
            x = self.ECO_build_at_ore(ct, self.target_ore)
            if x in ["MARK", "BLOCK", "FAIL"]:
                ctx.ORE_ignore(self.target_ore, 10)
                self.target_ore = Position(-1, -1)
                self.ECO_switch_explore(ct)
                
            elif x == "HARV":
                self.state = "LINK_BACK_CORE"
        
        if self.state == "LINK_BACK_CORE":
            x = self.ECO_link_back_core(ct, self.start_building_pos)
            if x in ["DONE", "STUCK"]:
                self.ECO_switch_explore(ct)
        
        # DEBUG
        self.ECO_debug(ct)
        # ctx.explore.EXPLORE_debug(ct)
        # ctx.ORE_debug()