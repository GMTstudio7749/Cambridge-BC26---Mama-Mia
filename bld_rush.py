from cambc import Controller, EntityType, Position, Team
from bld_context import ctx
from utils import *

class BldRush():
    def __init__(self):
        self.state = "ATTACK"
        self.enemy_core_pos = Position(-1, -1)
        self.explored_sym = [False, False, False]
        self.explored_sym_loc = [Position(-1, -1), Position(-1, -1), Position(-1, -1)]
        self.sym = None

    def RUSH_find_core(self, ct):
        explorePos = Position(-1, -1)
        currentCheck = 0;

        for i in range(3):
            if(self.explored_sym[i] == False):
                explorePos = self.explored_sym_loc[i]
                currentCheck = i
                break
        ctx.bugnav.MOVE_to_target(ct, explorePos, False )
        

        if(ct.is_in_vision(explorePos)):
            bid = ct.get_tile_building_id(explorePos)
            if(bid != None and ct.get_entity_type(bid) == EntityType.CORE):
                self.sym = currentCheck
            self.explored_sym[currentCheck] = True

                

        if(self.sym != None):
            self.enemy_core_pos = self.explored_sym_loc[self.sym]
            self.state = "BACK_TO_CORE"

    def RUSH_back_to_core(self, ct):
        dir = ct.get_position().direction_to(self.enemy_core_pos)
        target = ctx.CORE_POS.add(dir).add(dir)
        if(ct.get_position().distance_squared(target) > 2):
            ctx.bugnav.MOVE_to_target(ct, target, False)
        else:
            if(ct.can_place_marker(target)):
                ct.place_marker(target, self.sym)
                self.state = "ATTACK"
            
    def RUSH_run(self, ct: Controller):
        """Main RUSH builder function"""
        if(ct.get_current_round() == 1):
            self.explored_sym_loc =  [Position(ct.get_map_width()-ctx.CORE_POS.x-1, ctx.CORE_POS.y),  Position(ct.get_map_width()-ctx.CORE_POS.x-1, ct.get_map_height()-ctx.CORE_POS.y-1),Position(ctx.CORE_POS.x, ct.get_map_height()-ctx.CORE_POS.y-1) ]
            self.state = "FIND_CORE"
        if(self.state == "FIND_CORE"):
            self.RUSH_find_core(ct)
            
        elif(self.state == "ATTACK"):
            pass
        elif(self.state == "BACK_TO_CORE"):
            self.RUSH_back_to_core(ct)
            

        