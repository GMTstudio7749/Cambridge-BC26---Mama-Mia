from cambc import Controller, EntityType, Position, Team
from bld_context import ctx
from bld_eco import BldEco
from bld_rush import BldRush

class Builder:
    def __init__(self):
        self.eco = BldEco()
        self.rush = BldRush()

        self.work = "RUSH"

    #region ----- Builder GENERAL -----
    def BUILDER_setup(self, ct: Controller):
        """Setting up everything of a builder"""
        ctx.GET_core_pos(ct)
        ctx.MY_TEAM = ct.get_team()
        ctx.bugnav.SETUP(ct)
        ctx.explore.EXPLORE_setup(ct, ct.get_position(), ctx.CORE_POS)

    def BUILDER_update_var(self, ct: Controller):
        """Builder update info about global values"""
        ctx.Cur_Round = ct.get_current_round()

        ctx.Glob_Tit, ctx.Glob_Anx = ct.get_global_resources()
        ctx.Builder_Cost, tmp = ct.get_builder_bot_cost()
        ctx.Harvest_Cost, tmp = ct.get_harvester_cost()
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
    def BUILDER_cost_debug(self):
        """Print current costs for debug purpose"""
        print("\n== Global Cost ==")
        print("Conveyor:", ctx.Convey_Cost)
        print("Builder:", ctx.Builder_Cost)
        print("Harvester:", ctx.Harvest_Cost)
        print("Gunner:", ctx.Gunner_Cost)
        print("Road:", ctx.Road_Cost)
        print("=> Expand limit:", ctx.Spawn_Limit)
        print("===================\n")

    #endregion

    def BUILDER_run(self, ct: Controller):
        """Main builder robot runner"""
        self.BUILDER_update_var(ct)
        self.BUILDER_update_func(ct)

        if self.work == "ECO":
            self.eco.ECO_run(ct)
        elif self.work == "RUSH":
            self.rush.RUSH_run(ct)
        
        self.BUILDER_cost_debug()