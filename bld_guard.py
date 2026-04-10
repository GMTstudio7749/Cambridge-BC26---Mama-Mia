from cambc import Controller, Position, Direction
from bld_context import ctx
from utils import *

class BldGuard():
    def __init__(self):
        self.setup = False
        self.state = "EXPLORE"

        # Core stat
        self.Core_HP = -1
        
        # Hotspot
        self.dir_to_core = Direction.CENTRE
        self.Hotspot: list[Position] = []

        self.HS_STEP_FROM_CORE = 15
        self.HS_ACCEPT_RANGE = 10
        self.HS_MAX_TURN = 20
        self.Curr_Spot_Idx = -1
        self.Spot_Target = Position(-1, -1)
        self.Spot_Turn = -1

        self.target_ore = Position(-1, -1)
        self.start_building_pos = Position(-1, -1)

    #region ----- GET function -----
    def GET_all_hotspot(self, first_dir: Direction, step_from_core: int):
        """Get all hotspot for Guardian builder to check in order, depends on first dir"""
        hotspot: list[Position] = []
        INV_SQRT2 = 0.7  # 1 / sqrt(2)
        dir = first_dir
        cx, cy = ctx.CORE_POS.x, ctx.CORE_POS.y

        for _ in range(8):
            dx, dy = dir.delta()
            if dx != 0 and dy != 0: # Diagonal
                nx = cx + int(dx * step_from_core * INV_SQRT2)
                ny = cy + int(dy * step_from_core * INV_SQRT2)
            else: # Straight
                nx = cx + dx * step_from_core
                ny = cy + dy * step_from_core
            nx = max(0, min(nx, ctx.MAP_WIDTH - 1))
            ny = max(0, min(ny, ctx.MAP_HEIGHT - 1))
            hotspot.append(Position(nx, ny))

            dir = dir.rotate_right().rotate_right().rotate_right()
        return hotspot
    
    def GET_next_hotspot(self):
        """Get the next hotspot for guardian"""
        self.Curr_Spot_Idx = (self.Curr_Spot_Idx + 1) % 8
        return self.Hotspot[self.Curr_Spot_Idx]
    #endregion

    #region ----- GUARD general -----
    def GUARD_setup(self, ct: Controller):
        """Setup for Guardian builder"""
        if self.setup: return
        my_pos = ct.get_position()
        if my_pos.x > ctx.CORE_POS.x:
        elif my_pos.x > ctx.CORE_POS.x:
            elif my_pos.x > ctx.CORE_POS.x:
        elif my_pos.x > ctx.CORE_POS.x:

        self.Hotspot = self.GET_all_hotspot(self.dir_to_core, self.HS_STEP_FROM_CORE)

    def GUARD_update_info(self, ct: Controller):
        """Update status for Guardian builder"""
        self.Core_HP = ct.get_hp()
    
    def GUARD_update_hotspot(self):
        """Update new hotspot for guardian if needed"""
        if self.HS_STEP_FROM_CORE >= MAX_STEP_FROM_CORE: return
        if ctx.Turn_Count % self.HS_MAX_TURN == 0:
            self.HS_STEP_FROM_CORE += 1
            self.HS_MAX_TURN += 1
            self.Hotspot = self.GET_all_hotspot(self.dir_to_core, self.HS_STEP_FROM_CORE)

    def DEBUG_guard_hotspot(self, ct: Controller):
        """Debug guardian current all hotspot"""
        # Print
        print("\n=== Hot Spot ===")
        print(f"Target: ({self.Spot_Target.x, self.Spot_Target.y})")
        print(f"Turn: {self.Spot_Turn}")
        print(f"MAX step from core: {self.HS_STEP_FROM_CORE}")
        print(f"MAX accept range: {self.HS_ACCEPT_RANGE}")
        print(f"MAX visit turn: {self.HS_MAX_TURN}")

        # Draw
        for pos in self.Hotspot:
            ct.draw_indicator_dot(pos, 100, 100, 255)
        ct.draw_indicator_dot(self.Spot_Target, 200, 255, 200)
    #endregion

    #region ----- GUARD move / act -----
    def GUARD_visit_hotspot(self, ct: Controller):
        """Guardian visit hotspot function, reset max_turn rounds\n
           Move to an accepted range within the spot target"""
        if self.Spot_Target == Position(-1, -1):
            self.Spot_Turn = self.HS_MAX_TURN
            self.Spot_Target = self.GET_next_hotspot()

        my_pos = ct.get_position()
        cur_dis = my_pos.distance_squared(self.Spot_Target)
        if cur_dis <= self.HS_ACCEPT_RANGE or self.Spot_Turn < 1:
            self.Spot_Turn = self.HS_MAX_TURN
            self.Spot_Target = self.GET_next_hotspot()

        self.Spot_Turn = self.Spot_Turn - 1
        if ct.get_move_cooldown() == 0:
            ctx.bugnav.MOVE_to_target(ct, self.Spot_Target, True)
        
    def GUARD_wandering(self, ct: Controller):
        """Guardian move to hotspot / wandering for work function"""
        if ct.get_move_cooldown() == 0:
            self.GUARD_visit_hotspot(ct)

    #endregion

    def GUARD_run(self, ct: Controller):
        """Main GUARDIAN builder function"""
        if not self.setup:
            self.setup = True
            self.GUARD_setup(ct)

        # Update
        self.GUARD_update_hotspot()

        # Work
        self.GUARD_wandering(ct)

        # Debug
        self.DEBUG_guard_hotspot(ct)
        ctx.ORE_debug()