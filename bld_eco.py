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
    def GET_best_seen_ore(self, ct: Controller):
        """Get the nearest resource ore position FROM CORE\n
           Prior titanium > anxionite\n
           Return Position(-1, -1) if found nothing"""
        best_ore = Position(-1, -1)
        min_dis = 9999
        prior = "AXI"

        my_pos = ct.get_position()
        for ore in ctx.Ores.values():
            if ore.IS_ore_ignore(): continue

            if ore.harv: continue
            if ore.mark == 36: continue
            
            core_dis = ctx.CORE_POS.distance_squared(ore.pos)
            my_dis = ore.pos.distance_squared(my_pos)

            if ore.env == Environment.ORE_TITANIUM:
                if core_dis >= self.Core_Search_Range:
                    if ore.mark == 67 or ore.barr > 0:
                        continue
                prior = "TIT"

            elif ore.env == Environment.ORE_AXIONITE:
                continue
                if prior != "AXI": continue
                if barr or mval != -1: continue
                if my_dis > 9: continue
            
            if best_ore == Position(-1, -1) or core_dis < min_dis:
                best_ore, min_dis = ore.pos, core_dis
        return best_ore
    #endregion
    
    def ECO_update(self, ct: Controller):
        """Update for eco builders"""
        self.Core_Search_Range = 150 + ctx.Cur_Round // 2
        
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
            ctx.explore.MOVE_explore(ct, 10, 30)
            ctx.ORE_update(ct)
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
        if ctx.GET_marker_val(ct, ore_pos) == 36:
            return "LEAVE"
        
        # Move & place marker
        cur_dis = ore_pos.distance_squared(ct.get_position())
        if cur_dis <= 2:
            if ct.can_place_marker(ore_pos):
                ct.place_marker(ore_pos, 36)
            return "OKE"
        elif ct.get_move_cooldown() == 0:
            ctx.bugnav.MOVE_to_target(ct, ore_pos, False)
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
            
            

        if ctx.CHECK_harvester(ct, ore_pos):
            return "FAIL"
        
        if ctx.GET_marker_val(ct, ore_pos) != 67:
            if ct.can_destroy(ore_pos):
                ct.destroy(ore_pos)
        if ore_pos.distance_squared(ct.get_position()) > 2:
            return "MORE"
        
        # Build action
        if ct.get_action_cooldown() > 0: return "MORE"
        env = ct.get_tile_env(ore_pos)
        dis_to_core = ctx.CORE_POS.distance_squared(ore_pos)
        if env == Environment.ORE_AXIONITE:
            if ct.can_place_marker(ore_pos):
                ct.place_marker(ore_pos, 67)
            return "MARK"
        
        elif env == Environment.ORE_TITANIUM:
            if dis_to_core >= self.Core_Search_Range:
                if ct.can_build_barrier(ore_pos):
                    ct.build_barrier(ore_pos)
                    return "BLOCK"
                
            if ctx.Glob_Tit < ctx.Harvest_Cost:
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
        link = ctx.bugnav.MOVE_to_target_with_conveyor(ct, start_build_pos, ctx.CORE_POS)
        if link == "STUCK":
            return "STUCK"
        core_dis = ctx.CORE_POS.distance_squared(ct.get_position())
        if core_dis <= 2:
            return "DONE"
    #endregion

    def ECO_run(self, ct: Controller):
        """Main ECO builder function"""
        self.ECO_update(ct)

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

        ctx.ORE_debug()