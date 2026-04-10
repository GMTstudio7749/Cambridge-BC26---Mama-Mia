from cambc import Controller, Direction, EntityType, Position, Team
from cambc import GameConstants
from bld_context import ctx
from bld_eco import BldEco
from bld_rush import BldRush
from bld_guard import BldGuard
from utils import *

class Builder:
    def __init__(self):
        self.eco = BldEco()
        self.rush = BldRush()
        self.guard = BldGuard()

        self.work = "NONE"

    #region ----- Builder GENERAL -----
    def BUILDER_setup(self, ct: Controller):
        """Setting up everything of a builder"""
        # CONSTANT
        ctx.MY_TEAM = ct.get_team()
        ctx.MAP_WIDTH = ct.get_map_width()
        ctx.MAP_HEIGHT = ct.get_map_height()

        ctx.CORE_POS, ctx.CORE_ID = ctx.GET_ally_core_pos_id(ct)
        self.work = self.BUILDER_decide_work(ct.get_position())

        # CONTEXT
        ctx.Turn_Count = 0

        # FUNCTION
        ctx.bugnav.SETUP(ct)
        ctx.explore.EXPLORE_setup(ct, ct.get_position(), ctx.CORE_POS)

    def BUILDER_decide_work(self, my_pos: Position):
        """Builder work decision func, depends on direction to ally CORE\n
           Center -> RUSH | Diagonal -> ECO | Straight -> GUARD"""
        core_dir = my_pos.direction_to(ctx.CORE_POS)

        if core_dir == Direction.CENTRE:
            return "RUSH"
        if core_dir in Diagonal_Dirs:
            return "ECO"
        else:
            return "GUARD"
        
    def BUILDER_update_var(self, ct: Controller):
        """Builder update info about global values"""
        ctx.Cur_Round = ct.get_current_round()
        ctx.Turn_Count = ctx.Turn_Count + 1

        ctx.Glob_Tit, ctx.Glob_Anx = ct.get_global_resources()
        ctx.Builder_Cost, tmp = ct.get_builder_bot_cost()
        ctx.Harvest_Cost, tmp = ct.get_harvester_cost()
        ctx.Foundry_Cost, tmp = ct.get_foundry_cost()
        ctx.Convey_Cost, tmp = ct.get_conveyor_cost()
        ctx.Gunner_Cost, tmp = ct.get_gunner_cost()
        ctx.Road_Cost, tmp = ct.get_road_cost()
        ctx.Spawn_Limit = (
            50*ctx.Road_Cost +
            7*ctx.Convey_Cost +
            ctx.Gunner_Cost +
            3*ctx.Harvest_Cost
        )

    def BUILDER_update_func(self, ct: Controller):
        """Update information related to class / functions"""
        ctx.bugnav.SENSE_nearby(ct)
        ctx.ORE_update(ct)

    #endregion

    #region ----- Builder DEBUG -----
    def DEBUG_work(self):
        """Print current work of the builder"""
        print(f"[WORK]: {self.work}\n")

    def DEBUG_global_cost(self):
        """Print current costs for debug purpose"""
        print("\n== Global Cost ==")
        print("Conveyor:", ctx.Convey_Cost)
        print("Builder:", ctx.Builder_Cost)
        print("Harvester:", ctx.Harvest_Cost)
        print("Foundry:", ctx.Foundry_Cost)
        print("Gunner:", ctx.Gunner_Cost)
        print("Road:", ctx.Road_Cost)
        print("=> Expand limit:", ctx.Spawn_Limit)
        print("===================\n")
    #endregion
    
    #region ----- Builder FUNCTION -----
    '''def BUILDER_healing(self, ct: Controller):
        """Builder heal nearby ally entities if needed\n
           Prior healing itself first"""
        if ct.get_action_cooldown() > 0: return

        HP_HEAL = GameConstants.HEAL_AMOUNT
        # Myself first
        my_pos = ct.get_position()
        if ct.get_hp() + HP_HEAL < ct.get_max_hp():
            if ct.can_heal(my_pos):
                ct.heal(my_pos)

        # Nearby entities
        ally = ct.get_nearby_entities(dist_sq=2)
        for ID in ally:
            en_pos = ct.get_position(ID)
            if en_pos == my_pos: continue
            if ct.get_team(ID) != ctx.MY_TEAM: continue

            if ct.get_hp(ID) + HP_HEAL < ct.get_max_hp(ID):'''


    #endregion

    def BUILDER_run(self, ct: Controller):
        """Main builder robot runner"""
        self.DEBUG_work()
        self.BUILDER_update_var(ct)
        self.BUILDER_update_func(ct)

        if self.work == "ECO":
            self.eco.ECO_run(ct)
        elif self.work == "RUSH":
            self.rush.RUSH_run(ct)
        elif self.work == "GUARD":
            self.guard.GUARD_run(ct)