from cambc import Controller, EntityType, Position, Team
from bld_context import ctx
from utils import *
from attackable_info import AttackableInfo

class BldRush():
    def __init__(self):
        self.state = "ATTACK"
        self.enemy_core_pos = Position(-1, -1)
        self.explored_sym = [False, False, False]
        self.explored_sym_loc = [Position(-1, -1), Position(-1, -1), Position(-1, -1)]
        self.sym = None

        self.setup = False

        self.attackables = []
        self.target_attackable = Position(-1, -1)

        self.attack_turn_count = 0

    def GET_best_seen_attackable(self, ct):
        best_attackable = None
        best_score = 0
        for i in range(len(self.attackables)):
            for j in range(len(self.attackables[i])):
                attackable = self.attackables[i][j] 
                if(attackable.ignore > 0):
                    continue
                score = attackable.score
                if(score > best_score):
                    best_attackable, best_score = attackable, score
        return best_attackable

    def ATTACKABLE_update(self, ct: Controller):
        for i in range(len(self.attackables)):
            for j in range(len(self.attackables[i])):
                if(self.attackables[i][j].ignore > 0):
                    self.attackables[i][j].ignore -= 1

        for tile_pos in ct.get_nearby_tiles():
            self.ATTACKABLE_status(ct, tile_pos)
    
    def ATTACKABLE_status(self, ct: Controller, attackable_pos: Position):
        if(not ct.is_in_vision(attackable_pos)): return
        
        score, atype = self.GET_attackable_info(ct, attackable_pos)
    
        if(atype == self.attackables[attackable_pos.x][attackable_pos.y].type):
            pass
        else:
            attackable = AttackableInfo(attackable_pos, score, atype)
            self.attackables[attackable_pos.x][attackable_pos.y] = attackable
        if(self.GOT_nearby_working_allies(ct, attackable_pos) > 0):
            self.attackables[attackable_pos.x][attackable_pos.y].ignore = MAX_ATTACKABLE_IGNORE_TURN 

    def GOT_nearby_working_allies(self, ct, attackable_pos):
        out = 0
        # for dir in All_Dirs:
        #     pos = attackable_pos.add(dir)
        #     if(not ct.is_in_vision(pos) or not ctx.explore.IS_in_map(pos.x, pos.y)):
        #         continue
        #     bid = ct.get_tile_builder_bot_id(pos)
        #     bteam = ct.get_team(bid)
        #     if(bteam == ct.get_team()):
        #         out += 1
        # return out
    
        if(not ct.is_in_vision(attackable_pos) or not ctx.explore.IS_in_map(attackable_pos.x, attackable_pos.y)):
            return 0
        bid = ct.get_tile_builder_bot_id(attackable_pos)
        if(bid != ct.get_id()):
            return 1
        return 0


    def GET_attackable_info(self, ct, attackable_pos):
        env = ct.get_tile_env(attackable_pos)
        bid = ct.get_tile_building_id(attackable_pos)
        btype = ct.get_entity_type(bid)
        bteam = ct.get_team(bid)
        
        if(env == Environment.WALL):
            return 0, ""
        if(bid == None):
            return 1, ""
        if(bteam == ct.get_team()):
            return 1, ""
        if(btype == EntityType.CONVEYOR or btype == EntityType.BRIDGE):
            score = 10
            if(self.enemy_core_pos != Position(-1, -1)):
                score -= self.enemy_core_pos.distance_squared(attackable_pos) **0.5 * 0.01
            return score, "NORMAL"
        if(btype == EntityType.ROAD):
            return 2, ""
        if(btype == EntityType.CORE):
            return 0, ""
        return 0, ""

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
        target = ctx.CORE_POS
        if(ct.get_position().distance_squared(target) > 2):
            ctx.bugnav.MOVE_to_target(ct, target, False)
        else:
            for dir in All_Dirs:
                pos = target.add(dir).add(dir)
                if(abs(pos.x - ctx.CORE_POS.x) > 3 or abs(pos.y - ctx.CORE_POS.y) > 3 ):
                    continue
                if(ct.can_place_marker(pos)):
                    ct.place_marker(pos, self.sym)
                    self.state = "ATTACK"
                    return
                
    def RUSH_attack(self, ct):
        if(self.enemy_core_pos == Position(-1, -1)):
            for bid in ct.get_nearby_buildings():
                btype = ct.get_entity_type(bid)
                bteam = ct.get_team(bid)
                if(bteam != ct.get_team() or btype != EntityType.MARKER):
                    continue
                val = ct.get_marker_value(bid)
                if(0 <= val and val <= 3):
                    self.sym = val

            if(self.sym != None):
                self.enemy_core_pos = self.explored_sym_loc[self.sym]
                
            return

        self.target_attackable = self.GET_best_seen_attackable(ct)

        if self.target_attackable == None:
            ctx.bugnav.MOVE_to_target(ct, self.enemy_core_pos, False)
        if(self.target_attackable != None):
            self.attack_turn_count = 50
            if(self.target_attackable.type == "NORMAL"):
                self.state = "ATTACK_TARGET_NORMAL"

    def RUSH_attack_target_normal(self, ct):
        self.target_attackable.ignore = MAX_ATTACKABLE_IGNORE_TURN
        if(ct.is_in_vision(self.target_attackable.pos)):
            # if(self.GOT_nearby_working_allies(ct, self.target_attackable.pos) > 0):
            #     self.target_attackable.ignore = MAX_ATTACKABLE_IGNORE_TURN
            #     self.state = "ATTACK"
            #     return
            bid = ct.get_tile_building_id(self.target_attackable.pos)
            btype = ct.get_entity_type(bid)
            bteam = ct.get_team(bid)

            if(bid == None):
                if(self.target_attackable.pos.distance_squared(ct.get_position()) == 0):
                    for dir in Dirs:
                        if(ct.can_move(dir)):
                            ct.move(dir)
                            break
                elif(self.target_attackable.pos.distance_squared(ct.get_position()) > 2):
                    ctx.bugnav.MOVE_to_target(ct, self.target_attackable.pos, False)
            
            gunnerDir = self.target_attackable.pos.direction_to(self.enemy_core_pos)
            if(ct.can_build_gunner(self.target_attackable.pos, gunnerDir)):
                ct.build_gunner(self.target_attackable.pos, gunnerDir)
                self.state = "ATTACK"
                return
            if(bteam == ct.get_team() and btype == EntityType.GUNNER):
                self.state = "ATTACK"
                return
            
            nextPos = Position(-1, -1)
            if(btype == EntityType.CONVEYOR):
                nextPos = self.target_attackable.pos.add(ct.get_direction(bid))
            elif(btype == EntityType.BRIDGE):
                nextPos = ct.get_bridge_target(bid)

            if(nextPos != Position(-1, -1) and self.attackables[nextPos.x][nextPos.y].score > 0):
                self.target_attackable = self.attackables[nextPos.x][nextPos.y]
            
            if(ct.can_fire(self.target_attackable.pos)):
                ct.fire(self.target_attackable.pos)

        ctx.bugnav.MOVE_to_target(ct, self.target_attackable.pos, False)
    

    def RUSH_run(self, ct: Controller):
        """Main RUSH builder function"""

        if(ct.get_current_round() == 1):
            self.state = "FIND_CORE"
        if(not self.setup):
            self.setup = True
            defaultInfo = AttackableInfo(Position(0, 0), 0, "")
            for i in range(ct.get_map_width()):
                self.attackables.append([])
                for j in range(ct.get_map_height()):
                    defaultInfo.pos = Position(i, j)
                    self.attackables[i].append(defaultInfo)
            self.explored_sym_loc =  [Position(ct.get_map_width()-ctx.CORE_POS.x-1, ctx.CORE_POS.y),  Position(ct.get_map_width()-ctx.CORE_POS.x-1, ct.get_map_height()-ctx.CORE_POS.y-1),Position(ctx.CORE_POS.x, ct.get_map_height()-ctx.CORE_POS.y-1) ]

        print(self.state)
        self.ATTACKABLE_update(ct)
        
        if(self.attack_turn_count > 0):
            self.attack_turn_count -= 1
            if(self.attack_turn_count == 0):
                self.state = "ATTACK"

        if(self.state == "FIND_CORE"):
            self.RUSH_find_core(ct)
        elif(self.state == "ATTACK"):
            self.RUSH_attack(ct)
        elif(self.state == "ATTACK_TARGET_NORMAL"):
            self.RUSH_attack_target_normal(ct)
        elif(self.state == "BACK_TO_CORE"):
            self.RUSH_back_to_core(ct)
            

        