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
        self.MODE = "NORMAL"
        
        self.place_marker_pos = []
        self.tried_place_marker = []

        self.bots_pos = {}

    def RUSH_sense_nearby(self, ct):
        self.bots_pos = {}
        spread = []
        for bid in ct.get_nearby_units():

            i = ct.get_position(bid) 
            btype = ct.get_entity_type(bid)
            bteam = ct.get_team(bid)
            if(btype != EntityType.BUILDER_BOT ):
                continue

            if(self.MODE == "NORMAL"):
                if(bid == ct.get_id() or bteam != ct.get_team()):
                    pass
                else:
                    self.bots_pos[i] = 1
            else:
                if(bid == ct.get_id()):
                    pass
                else:
                    self.bots_pos[i] = 1
                    if(bteam != ct.get_team()):
                        spread.append(i)
                    
        for i in spread:
            for dir in Dirs:
                pos = i.add(dir)
                self.bots_pos[pos] = self.bots_pos.get(pos, 0) + 1
        print("4: ", ct.get_cpu_time_elapsed())


    def GET_best_seen_attackable(self, ct):
        best_attackable = Position(-1, -1)
        best_score = 0
        cur = ct.get_position()

        for dx in range(-15, 16):
            for dy in range(-15, 16):
                x = cur.x + dx
                y = cur.y + dy

                if not ctx.explore.IS_in_map(x, y):
                    continue

                attackable = self.attackables[x][y]

                if attackable.ignore > 0:
                    continue

                score = attackable.score
                if score > best_score:
                    best_attackable, best_score = attackable.pos, score
        if(best_score > 3):
            return best_attackable
        return Position(-1, -1)
    
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
            self.attackables[attackable_pos.x][attackable_pos.y].score = score
            self.attackables[attackable_pos.x][attackable_pos.y].type = atype

        else:
            self.attackables[attackable_pos.x][attackable_pos.y].pos = attackable_pos
            self.attackables[attackable_pos.x][attackable_pos.y].score = score
            self.attackables[attackable_pos.x][attackable_pos.y].type = atype
            self.attackables[attackable_pos.x][attackable_pos.y].ignore = 0


        if(self.MODE == "HARASS" and self.attackables[attackable_pos.x][attackable_pos.y].type == ATTACK_TYPE.NORMAL and self.GOT_nearby_working_bot(ct, attackable_pos) > 0):
            self.attackables[attackable_pos.x][attackable_pos.y].ignore = MAX_ATTACKABLE_IGNORE_TURN 
    

    def GOT_nearby_working_bot(self, ct, attackable_pos):
        if(not ct.is_in_vision(attackable_pos) or not ctx.explore.IS_in_map(attackable_pos.x, attackable_pos.y)):
            return 0
        if(self.MODE == "HARASS"):
            out = self.bots_pos.get(attackable_pos, 0)
            return out
        else:
            # ct.draw_indicator_line(ct.get_position(), attackable_pos, 255, 255, 25)
            if(not ct.is_in_vision(attackable_pos) or not ctx.explore.IS_in_map(attackable_pos.x, attackable_pos.y)):
                return 0
            if(ct.get_position() == attackable_pos):
                return 0
            return self.bots_pos.get(attackable_pos, 0)


    def GET_attackable_info(self, ct, attackable_pos):
        env = ct.get_tile_env(attackable_pos)
        bid = ct.get_tile_building_id(attackable_pos)
        btype = ct.get_entity_type(bid)
        bteam = ct.get_team(bid)
        

        if(ctx.bugnav.tooCloseToDanger(ct, attackable_pos)):
            return 0, ATTACK_TYPE.NONE
        if(env == Environment.WALL):
            return 0, ATTACK_TYPE.NONE
        if(bid == None):
            return 1, "PLACE_TURRET"
        if(bteam == ct.get_team()):
            return 1, ATTACK_TYPE.PLACE_TURRET
        if(btype == EntityType.CONVEYOR or btype == EntityType.BRIDGE):
            score = 20
            score -= self.GOT_nearby_working_bot(ct, attackable_pos)
            score -= ct.get_position().distance_squared(attackable_pos) ** 0.5 * 0.1
            if(self.enemy_core_pos != Position(-1, -1)):
                score -= self.enemy_core_pos.distance_squared(attackable_pos) **0.5 * 0.01
            return score, ATTACK_TYPE.NORMAL
        if(btype == EntityType.ROAD):
            return 2, ATTACK_TYPE.PLACE_TURRET
        if(btype == EntityType.CORE):
            return 0, ATTACK_TYPE.NONE
        return 0, ATTACK_TYPE.NONE

    def RUSH_find_core(self, ct):
        explorePos = Position(-1, -1)

        for i in range(3):
            if(self.explored_sym[i] == False):
                explorePos = self.explored_sym_loc[i]
                break

        ctx.bugnav.MOVE_to_target(ct, explorePos, False )
        

        for i in range(3):
            pos = self.explored_sym_loc[i]
            if(ct.is_in_vision(pos)):
                bid = ct.get_tile_building_id(pos)
                bteam = ct.get_team(bid)
                if(bid != None and ct.get_entity_type(bid) == EntityType.CORE and bteam != ct.get_team()):
                    self.sym = i
                self.explored_sym[i] = True

                

        if(self.sym != None):
            self.enemy_core_pos = self.explored_sym_loc[self.sym]
            self.state = "BACK_TO_CORE"

    def RUSH_back_to_core(self, ct):
        target = Position(-1, -1)
        index = -1
        for i in range(len(self.tried_place_marker)):
            if(self.tried_place_marker[i] == False):
                if(not ctx.explore.IS_in_map(self.place_marker_pos[i].x, self.place_marker_pos[i].y)):
                    self.tried_place_marker[i] = True
                    continue
                if(ct.is_in_vision(self.place_marker_pos[i])):
                    env = ct.get_tile_env(self.place_marker_pos[i])
                    if(env == Environment.WALL):
                        self.tried_place_marker[i] = True
                        continue
                target = self.place_marker_pos[i]
                index = i
                break
        
        if(ct.get_position().distance_squared(target) > 2):
            ctx.bugnav.MOVE_to_target(ct, target, False)
        else:
            bid = ct.get_tile_building_id(target)
            bteam = ct.get_team(bid)
            btype = ct.get_entity_type(bid)
            if(bteam == ct.get_team()):
                if(btype == EntityType.ROAD):
                    if(ct.can_destroy(target)):
                        ct.destroy(target)
            if(ct.can_place_marker(target)):
                ct.place_marker(target, self.sym)
                self.state = "ATTACK"
                return
            self.tried_place_marker[index] = True
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
        # for i in ct.get_nearby_tiles():
            # print(self.attackables[i.x][i.y].pos, self.attackables[i.x][i.y].score)
        if self.target_attackable == Position(-1, -1):
            ctx.bugnav.MOVE_to_target(ct, self.enemy_core_pos, False)
        if(self.target_attackable != Position(-1, -1)):
            self.attack_turn_count = MAX_ATTACK_TURN_COUNT
            if(self.attackables[self.target_attackable.x][self.target_attackable.y].type == ATTACK_TYPE.NORMAL):
                self.state = "ATTACK_TARGET_NORMAL"

    def RUSH_attack_target_normal(self, ct):
        if(self.attackables[self.target_attackable.x][self.target_attackable.y].type == ATTACK_TYPE.NORMAL):
            if(self.MODE == "HARASS"):
                self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = 30
            else:
                self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = 10

        if(ct.is_in_vision(self.attackables[self.target_attackable.x][self.target_attackable.y].pos)):
            if(ctx.bugnav.tooCloseToDanger(ct, self.attackables[self.target_attackable.x][self.target_attackable.y].pos)):
                ctx.bugnav.safeFuzzyMove(ct, self.attackables[self.target_attackable.x][self.target_attackable.y].pos.direction_to(ct.get_position()).opposite())
                self.state = "ATTACK"
                return
            # print(self.GOT_nearby_working_bot(ct, self.attackables[self.target_attackable.x][self.target_attackable.y].pos))
            if(self.MODE == "HARASS" and self.GOT_nearby_working_bot(ct, self.attackables[self.target_attackable.x][self.target_attackable.y].pos) > 0):
                self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = MAX_ATTACKABLE_IGNORE_TURN
                self.state = "ATTACK"
                return

            bid = ct.get_tile_building_id(self.attackables[self.target_attackable.x][self.target_attackable.y].pos)
            btype = ct.get_entity_type(bid)
            bteam = ct.get_team(bid)

            if(bid == None):
                if(self.attackables[self.target_attackable.x][self.target_attackable.y].pos.distance_squared(ct.get_position()) == 0):
                    for dir in Dirs:
                        if(ct.can_move(dir)):
                            ct.move(dir)
                            break
            
            gunnerDir = self.attackables[self.target_attackable.x][self.target_attackable.y].pos.direction_to(self.enemy_core_pos)
            if(ct.can_build_gunner(self.attackables[self.target_attackable.x][self.target_attackable.y].pos, gunnerDir)):
                ct.build_gunner(self.attackables[self.target_attackable.x][self.target_attackable.y].pos, gunnerDir)
                self.state = "ATTACK"
                return

            if(bteam == ct.get_team() and btype == EntityType.GUNNER):
                self.state = "ATTACK"
                return
            
            if(self.MODE == "NORMAL"):
                nextPos = Position(-1, -1)
                if(btype == EntityType.CONVEYOR):
                    nextPos = self.attackables[self.target_attackable.x][self.target_attackable.y].pos.add(ct.get_direction(bid))
                elif(btype == EntityType.BRIDGE):
                    nextPos = ct.get_bridge_target(bid)
                if(self.attackables[nextPos.x][nextPos.y].ignore > 0):
                    self.state = "ATTACK"
                    return
                if(nextPos != Position(-1, -1) and self.attackables[nextPos.x][nextPos.y].score > 0):
                    self.target_attackable = nextPos
                    self.attack_turn_count = MAX_ATTACK_TURN_COUNT
            if(ct.can_fire(self.attackables[self.target_attackable.x][self.target_attackable.y].pos)):
                ct.fire(self.attackables[self.target_attackable.x][self.target_attackable.y].pos)
        else:
            self.attack_turn_count = MAX_ATTACK_TURN_COUNT
        ctx.bugnav.MOVE_to_target(ct, self.attackables[self.target_attackable.x][self.target_attackable.y].pos, False)
    

    def RUSH_run(self, ct: Controller):
        """Main RUSH builder function"""
        print(self.MODE)
        
        if(ct.get_current_round() == 1):
            self.state = "FIND_CORE"
        if(not self.setup):
            if(ct.get_current_round() == 4):
                self.MODE = "HARASS"
            self.setup = True
            
            width = ct.get_map_width()
            height = ct.get_map_height()

            print("1: ",ct.get_cpu_time_elapsed())

            self.attackables = [
                [AttackableInfo(Position(i, j), 0, ATTACK_TYPE.NONE) for j in range(height)]
                for i in range(width)
            ]
            print("2: ",ct.get_cpu_time_elapsed())

            self.explored_sym_loc =  [Position(ct.get_map_width()-ctx.CORE_POS.x-1, ctx.CORE_POS.y),  Position(ct.get_map_width()-ctx.CORE_POS.x-1, ct.get_map_height()-ctx.CORE_POS.y-1),Position(ctx.CORE_POS.x, ct.get_map_height()-ctx.CORE_POS.y-1) ]

            self.tried_place_marker = [False] * 16
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTH).add(Direction.SOUTHEAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTH).add(Direction.SOUTHWEST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTH).add(Direction.SOUTH))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTH).add(Direction.SOUTHEAST).add(Direction.EAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTH).add(Direction.SOUTHWEST).add(Direction.WEST))

            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.EAST).add(Direction.NORTHEAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.EAST).add(Direction.SOUTHEAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.EAST).add(Direction.EAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.EAST).add(Direction.NORTHEAST).add(Direction.NORTH))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.EAST).add(Direction.SOUTHEAST).add(Direction.SOUTH))

            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.WEST).add(Direction.NORTHWEST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.WEST).add(Direction.SOUTHWEST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.WEST).add(Direction.WEST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.WEST).add(Direction.NORTHWEST).add(Direction.NORTH))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.WEST).add(Direction.SOUTHWEST).add(Direction.SOUTH))

            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.NORTHEAST).add(Direction.NORTHEAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.NORTHWEST).add(Direction.NORTHWEST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTHEAST).add(Direction.SOUTHEAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTHWEST).add(Direction.SOUTHWEST))

            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.NORTH).add(Direction.NORTH).add(Direction.NORTH))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.SOUTH).add(Direction.SOUTH).add(Direction.SOUTH))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.EAST).add(Direction.EAST).add(Direction.EAST))
            self.place_marker_pos.append(ctx.CORE_POS.add(Direction.WEST).add(Direction.WEST).add(Direction.WEST))
            print("3    : ",ct.get_cpu_time_elapsed())



        print(self.state)
        self.ATTACKABLE_update(ct)
        
        if(self.attack_turn_count > 0):
            self.attack_turn_count -= 1
            if(self.attack_turn_count == 0):
                if(self.target_attackable != Position(-1, -1)):
                    self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = 50
                    self.MODE = "HARASS"
                self.state = "ATTACK"
        self.RUSH_sense_nearby(ct)

        if(self.attackables[self.target_attackable.x][self.target_attackable.y] != None):
            ct.draw_indicator_line(ct.get_position(), self.attackables[self.target_attackable.x][self.target_attackable.y].pos,255, 0, 0)
        if(self.state == "FIND_CORE"):
            self.RUSH_find_core(ct)
        elif(self.state == "ATTACK"):
            self.RUSH_attack(ct)
        elif(self.state == "ATTACK_TARGET_NORMAL"):
            self.RUSH_attack_target_normal(ct)
        elif(self.state == "BACK_TO_CORE"):
            self.RUSH_back_to_core(ct)
            
            

        if(ct.get_hp() < ct.get_max_hp() ):
            if(ct.can_heal(ct.get_position())):
                ct.heal(ct.get_position())