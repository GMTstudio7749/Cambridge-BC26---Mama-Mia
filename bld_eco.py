import random
from cambc import Controller, EntityType, Position
from bld_context import ctx
from utils import *

class Explore:
    """Class for explore purpose for builder"""
    def __init__(self):
        self.setup = False
        self.Explore_Dir = Direction.CENTRE
        self.Explore_Target = Position(-1, -1)
        self.Explore_Turn = -1
    
    def EXPLORE_DIR_fix(self, dir: Direction):
        """Fix a direction to diagonal for explore, return a fixed dir"""
        if dir in Diagonal_Dirs:
            return dir
        if dir == Direction.CENTRE:
            return Diagonal_Dirs[0]
        else:
            return dir.rotate_right()

    def EXPLORE_setup(self, core_dir: Direction):
        """Setup explore move function info"""
        self.Explore_Dir = self.EXPLORE_DIR_fix(core_dir)

    def IS_in_map(self, x: int, y: int):
        """Check if two int x, y is located in map"""
        if x < 0 or x >= ctx.MAP_WIDTH or y < 0 or y >= ctx.MAP_HEIGHT:
            return False
        return True

    def GET_next_bounce_dir(self, dir: Direction, edge_pos: Position):
        """Get the next bounce dir depends on current dir (diag) & edge pos"""
        bounce_dir = dir.opposite()
        for _ in range(4):
            bounce_dir = bounce_dir.rotate_right().rotate_right()
            
            dx, dy = bounce_dir.delta()
            nx, ny = edge_pos.x + dx, edge_pos.y + dy
            if not self.IS_in_map(nx, ny): continue
            return bounce_dir

        return Diagonal_Dirs[0]
    
    def GET_next_explore_target(self, ct: Controller, dir: Direction):
        """Get the next explore target, depends on dir and position\n
        if dir = Direction.CENTRE -> just random a diagonal dir"""
        X, Y = self.Explore_Target.x, self.Explore_Target.y
        if X < 0 or Y < 0:
            X, Y = ct.get_position().x, ct.get_position().y

        dx, dy = self.EXPLORE_DIR_fix(dir).delta()

        tx = (ctx.MAP_WIDTH - 1 - X) if dx == 1 else X
        ty = (ctx.MAP_HEIGHT - 1 - Y) if dy == 1 else Y

        t = tx if tx < ty else ty
        nx, ny = X + dx * t, Y + dy * t

        # --- bend ---
        o = random.randint(5, 10)
        W, H = ctx.MAP_WIDTH, ctx.MAP_HEIGHT

        for x, y in random.sample([(nx+o,ny),(nx-o,ny),(nx,ny+o),(nx,ny-o)], 4):
            if 0 <= x < W and 0 <= y < H and (x==0 or x==W-1 or y==0 or y==H-1):
                nx, ny = x, y
                break

        return Position(nx, ny)

    def MOVE_explore(self, ct: Controller, range_squared: int, max_turn: int):
        """Explore movement function, reset max_turn rounds\n
        Move to an accepted range within the explore target"""
        # SETUP
        if not self.setup:
            self.EXPLORE_setup(ctx.CORE_DIR)
            self.setup = True

        # WORK
        if self.Explore_Target == Position(-1, -1):
            self.Explore_Target = self.GET_next_explore_target(ct, self.Explore_Dir)
            self.Explore_Turn = max_turn

        my_pos = ct.get_position()
        cur_dis = my_pos.distance_squared(self.Explore_Target)
        if cur_dis <= range_squared or self.Explore_Turn < 1:
            self.Explore_Turn = max_turn
            self.Explore_Dir = self.GET_next_bounce_dir(self.Explore_Dir, self.Explore_Target)
            self.Explore_Target = self.GET_next_explore_target(ct, self.Explore_Dir)

        if ct.get_move_cooldown() == 0:
            self.Explore_Turn = self.Explore_Turn - 1
            ctx.bugnav.MOVE_to_target(ct, self.Explore_Target, True)

    def EXPLORE_debug(self, ct: Controller):
        """Explore debug function"""
        # Print
        print("\n== EXPLORE stat ==")
        print(f"Target: ({self.Explore_Target.x}, {self.Explore_Target.y})")
        print(f"Dir: {self.Explore_Dir.value}")
        print(f"Turn: {self.Explore_Turn}")
        # Draw
        ct.draw_indicator_dot(self.Explore_Target, 100, 100, 255)
        ct.draw_indicator_line(ct.get_position(), self.Explore_Target, 150, 150, 150)
          
class BldEco:
    def __init__(self):
        # CLASS
        self.explore = Explore()
        
        # SELF
        self.setup = False
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
            if ore.IS_ore_ignore(): continue
            
            core_dis = ctx.CORE_POS.distance_squared(ore.pos)
            my_dis = ore.pos.distance_squared(my_pos)

            if ore.env == Environment.ORE_TITANIUM:
                if ore.harv == 1 and ore.linked_core: continue
                if core_dis >= self.Core_Search_Range:
                    if ore.barr == 1: # Ensure block barrier
                        continue
                prior = "TIT"

            elif ore.env == Environment.ORE_AXIONITE:
                continue
                if prior != "AXI": continue
                if ore.harv == 1: continue
                if ore.barr or ore.mark != -1: continue
                if my_dis > 9: continue
            
            if best_ore == Position(-1, -1) or core_dis < min_dis:
                best_ore, min_dis = ore.pos, core_dis
        print("[BEST ORE]:", best_ore)
        return best_ore
    #endregion
    
    #region ----- ECO general -----
    def ECO_setup(self):
        """Setup info / func for ECO builder"""
        pass

    def ECO_update(self): # NEED MODIFY
        """Update for eco builders"""
        self.Core_Search_Range = 1000 + ctx.Cur_Round
    
    def ECO_choose_start_build_pos(self, ct: Controller, ore_pos: Position):
        """Choose start building pos to LINK BACK CORE"""
        best_pos = Position(-1, -1)
        min_dis = 9999
        dxy = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        prior = "ORE"
        for dx, dy in dxy:
            check_pos = Position(ore_pos.x + dx, ore_pos.y + dy)
            if not ctx.IS_in_map(check_pos): continue
            if not ct.is_in_vision(check_pos): continue

            # Empty env only
            env = ct.get_tile_env(check_pos)
            if env == Environment.WALL: continue
            if env == Environment.ORE_TITANIUM and prior != "ORE": continue

            # Check for buildings
            ID = ct.get_tile_building_id(check_pos)
            if ID is not None:
                type = ct.get_entity_type(ID)
                if type == EntityType.HARVESTER: continue
                if ct.get_team(ID) != ctx.MY_TEAM:
                    if not type in [EntityType.ROAD, EntityType.MARKER]:
                        continue

            if env == Environment.EMPTY: prior = "EMPTY"
            # Compare distance
            dis = ctx.CORE_POS.distance_squared(check_pos)
            if best_pos == Position(-1, -1) or dis < min_dis:
                best_pos, min_dis = check_pos, dis
        return best_pos
        
    def DEBUG_eco(self, ct: Controller):
        """Debug ECO builders"""
        # Output
        print("\n=== ECO stat ===")
        print(f"[State]: {self.state}")
        print(f"Target ore: ({self.target_ore.x},{self.target_ore.y})")
        print(f"Start_building_pos: ({self.start_building_pos.x},{self.start_building_pos.y})")
        print(f"Last Connect: ({ctx.bugnav.lastConnect.x, ctx.bugnav.lastConnect.y}")
        # Draw
        ct.draw_indicator_dot(self.target_ore, 255, 255, 0)
        ct.draw_indicator_dot(ctx.bugnav.lastConnect, 0, 255, 255)
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
            if ctx.CHECK_harvester(ct, ore_pos) == 1: return "LEAVE"
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
        harv_check = ctx.CHECK_harvester(ct, ore_pos)
        if harv_check != 0:
            if ctx.CHECK_ore_linked_core(ct, ore_pos):
                return "FAIL"
        if ctx.CHECK_barrier(ct, ore_pos) == 2: return "FAIL"
        
        if ore_pos.distance_squared(ct.get_position()) > 2:
            if ct.get_move_cooldown() > 0:
                ctx.bugnav.MOVE_to_target(ct, ore_pos, False)
            return "MORE"
        
        if harv_check == 2:
            self.start_building_pos = self.ECO_choose_start_build_pos(ct, ore_pos)
            return "HARV"
        
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
                type = ct.get_entity_type(ID)
                if ct.get_team(ID) == ctx.MY_TEAM:
                    if type != EntityType.HARVESTER:
                        if ct.can_destroy(ore_pos):
                            ct.destroy(ore_pos)
                else:
                    if ct.is_tile_passable(ore_pos):
                        if ct.get_position().distance_squared(ore_pos) > 0:
                            ctx.bugnav.MOVE_to_target(ct, ore_pos, False)
                        if ct.can_destroy(ore_pos):
                            ct.destroy(ore_pos)
            # Case: Enemy unpassable building
            # Case: Ally building (no pass / unpass)
            # Case: Empty

            if dis_to_core >= self.Core_Search_Range:
                if ct.can_build_barrier(ore_pos):
                    ct.build_barrier(ore_pos)
                    return "BLOCK"

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
                self.start_building_pos = self.ECO_choose_start_build_pos(ct, ore_pos)
                return "HARV"
        return "MORE"
    
    def ECO_link_back_core(self, ct: Controller, start_build_pos: Position):
        """ECO builder link harvester back to core
        Depends on start build position"""
        # DESTROY under foot blocks first
        my_pos = ct.get_position()
        if ctx.bugnav.lastConnect != Position(-1, -1):
            dis_to_connect = my_pos.distance_squared(ctx.bugnav.lastConnect)
            if dis_to_connect <= 2:
                ID = ct.get_tile_building_id(my_pos)
                if ID is not None:
                    if ct.get_team(ID) != ctx.MY_TEAM:
                        if ct.can_fire(my_pos):
                            ct.fire(my_pos)
                        return "FIRING"

        # BUILD next conv
        link = ctx.bugnav.MOVE_to_target_with_conveyor(ct, start_build_pos, ctx.CORE_POS)
        if link == "STUCK":
            return "STUCK"
        core_dis = ctx.CORE_POS.distance_squared(ct.get_position())
        if core_dis <= 2:
            ctx.bugnav.lastConnect = Position(-1, -1)
            return "DONE"
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
                self.explore.MOVE_explore(ct, 10, 30)
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
        # SETUP
        if not self.setup:
            self.ECO_setup()
            self.setup = True

        # UPDATE
        ctx.ORE_update(ct)
        ctx.UPD_resource_cost(ct)
        self.ECO_update()

        # WORK
        if self.state == "EXPLORE":
            self.ECO_explore(ct)

        if self.state == "BUILD_AT_ORE":
            x = self.ECO_build_at_ore(ct, self.target_ore)
            print("BUILD AT ORE:", x)
            if x in ["MARK", "BLOCK", "FAIL"]:
                ctx.ORE_ignore(self.target_ore, 100)
                self.target_ore = Position(-1, -1)
                self.ECO_switch_explore(ct)
                
            elif x == "HARV":
                self.state = "LINK_BACK_CORE"
        
        if self.state == "LINK_BACK_CORE":
            x = self.ECO_link_back_core(ct, self.start_building_pos)
            print("LINK BACK CORE:", x)
            if x in ["DONE", "STUCK"]:
                self.ECO_switch_explore(ct)
            
        
        # DEBUG
        self.DEBUG_eco(ct)
        # self.explore.EXPLORE_debug(ct)
        # ctx.ORE_debug()