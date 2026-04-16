from cambc import Controller, Direction
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

        self.setup = False
        self.work = "NONE"

    #region ----- Builder GENERAL -----
    def BUILDER_setup(self, ct: Controller):
        """Setting up everything of a builder"""
        # CONSTANT
        ctx.MY_TEAM = ct.get_team()
        ctx.MAP_WIDTH = ct.get_map_width()
        ctx.MAP_HEIGHT = ct.get_map_height()

        ctx.CORE_POS, ctx.CORE_ID = ctx.GET_ally_core_pos_id(ct)
        ctx.CORE_DIR = ctx.CORE_POS.direction_to(ct.get_position())
        self.work = self.BUILDER_decide_work(ctx.CORE_DIR)

        # FUNCTION
        ctx.bugnav.SETUP(ct)

    def BUILDER_decide_work(self, core_dir: Direction):
        """Builder work decision func, depends on direction to ally CORE\n
           Center -> RUSH | Diagonal -> ECO | Straight -> GUARD"""
        if core_dir == Direction.CENTRE:
            return "RUSH"
        if core_dir in Diagonal_Dirs:
            return "ECO"
        else:
            return "GUARD"
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
        # SETUP
        if not self.setup:
            self.BUILDER_setup(ct)
            self.setup = True

        print(f"[WORK]: {self.work}\n")

        # General UPDATE
        ctx.UPD_round_turn(ct)
        ctx.bugnav.SENSE_nearby(ct)

        # WORK
        if self.work == "ECO":
            self.eco.ECO_run(ct)
        elif self.work == "RUSH":
            self.rush.RUSH_run(ct)
        elif self.work == "GUARD":
            self.guard.GUARD_run(ct)