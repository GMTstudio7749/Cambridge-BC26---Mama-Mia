from cambc import Controller, EntityType, Position
from bld_context import ctx
from utils import *

class AttackableInfo:
    __slots__ = ("pos", "score", "type", "ignore")

    def __init__(self, pos, score, type):
        self.pos = pos
        self.score = score
        self.type = type
        self.ignore = 0

class BldRush():
    def __init__(self):
        self.state = "FIND_CORE"
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
        self.protected_map = {}

        self.bots_pos = {}
        self.return_home = False

        self.already_find_closest_harvester = False
        self.closest_harvester = Position(-1, -1)
        self.harvester_hp = 0

        self.hijack_state = "INIT"
        self.hijack_target_pos = Position(-1, -1)
        self.hijack_previous_pos = Position(-1, -1)

        self.forbidden_tiles = set()
        self.traced_gunners = set()

        self.Glob_Tit = -1


        self.current_max_attack_turn_count = 0
    def RUSH_mark_position(self, pos: Position, is_protected: bool):
        self.protected_map[(pos.x, pos.y)] = is_protected
    def RUSH_can_destroy(self, pos: Position):
        return not self.protected_map.get((pos.x, pos.y), False)
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
            elif(self.MODE == "CONCENTRATE"):
                if(bid == ct.get_id()):
                    pass
                else:
                    self.bots_pos[i] = 2
                    if(bteam == ct.get_team()):
                        spread.append(i)
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

                if not ctx.IS_in_map(Position(x, y)):
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
                if(self.MODE == "CONCENTRATE"):
                    self.attackables[i][j].ignore = 0
                else:
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




    def GOT_nearby_working_bot(self, ct, attackable_pos):
        if(not ct.is_in_vision(attackable_pos) or not ctx.IS_in_map(attackable_pos)):
            return 0
        if(self.MODE == "HARASS" or self.MODE == "TRACE" or self.MODE == "CONCENTRATE"):
            out = self.bots_pos.get(attackable_pos, 0)
            return out

        else:
            # ct.draw_indicator_line(ct.get_position(), attackable_pos, 255, 255, 25)
            if(not ct.is_in_vision(attackable_pos) or not ctx.IS_in_map(attackable_pos)):
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
            if(btype in TURRET_TYPE):
                return 1, ATTACK_TYPE.DONE 
            return 1, ATTACK_TYPE.PLACE_TURRET
        if(btype == EntityType.CONVEYOR or btype == EntityType.BRIDGE):
            score = 20
            if(self.MODE == "CONCENTRATE"):
                score += self.GOT_nearby_working_bot(ct, attackable_pos)
            else:
                score -= self.GOT_nearby_working_bot(ct, attackable_pos)

            score -= ct.get_position().distance_squared(attackable_pos) ** 0.5 * 0.1
            if(self.enemy_core_pos != Position(-1, -1)):
                if(self.MODE == "TRACE"):
                    score += self.enemy_core_pos.distance_squared(attackable_pos) **0.5 * 0.01
                else:
                    score -= self.enemy_core_pos.distance_squared(attackable_pos) **0.5 * 0.01
            return score, ATTACK_TYPE.NORMAL
        if(btype == EntityType.ROAD):
            return 2, ATTACK_TYPE.PLACE_TURRET
        if(btype == EntityType.CORE):
            return 0, ATTACK_TYPE.NONE
        return 1, ATTACK_TYPE.NONE

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
            if(self.return_home):
                self.state = "BACK_TO_CORE"
            else:
                self.state = "ATTACK"

    def RUSH_back_to_core(self, ct):
        target = Position(-1, -1)
        index = -1
        for i in range(len(self.tried_place_marker)):
            if(self.tried_place_marker[i] == False):
                if(not ctx.IS_in_map(self.place_marker_pos[i])):
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

    def RUSH_attack(self, ct: Controller):
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
            ctx.bugnav.MOVE_to_target(ct, self.enemy_core_pos, False, 0, 0, 2)
        for bid in ct.get_nearby_buildings():
            if ct.get_team(bid) != ct.get_team() and ct.get_entity_type(bid) in [EntityType.GUNNER, EntityType.SENTINEL]:
                bpos = ct.get_position(bid)
                for d in Direction:
                    check_pos = bpos.add(d)  
                    if ct.is_in_vision(check_pos):
                        target_bid = ct.get_tile_building_id(check_pos)
                        if target_bid is not None and ct.get_team(target_bid) != ct.get_team():
                            btype = ct.get_entity_type(target_bid)
                            if btype in [EntityType.CONVEYOR, EntityType.BRIDGE]:
                                self.RUSH_mark_position(check_pos, True)
        if(self.target_attackable != Position(-1, -1)):
            self.attack_turn_count = self.current_max_attack_turn_count
            if(self.attackables[self.target_attackable.x][self.target_attackable.y].type == ATTACK_TYPE.NORMAL):
                self.state = "ATTACK_TARGET_NORMAL"

    def RUSH_trace_from_gunner(self, ct: Controller, gunner_pos: Position, gunner_id: int):
        queue = [gunner_pos]
        visited = set()
        visited.add((gunner_pos.x, gunner_pos.y))
        while len(queue) > 0:
            current_pos = queue.pop(0)
            for d in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
                next_pos = current_pos.add(d)                
                if (next_pos.x, next_pos.y) in visited or not ct.is_in_vision(next_pos):
                    continue                         
                bid = ct.get_tile_building_id(next_pos)
                if bid is not None and ct.get_team(bid) != ct.get_team():
                    btype = ct.get_entity_type(bid)
                    lead_to_gunner = False
                    if btype == EntityType.CONVEYOR:
                        conveyor_dir = ct.get_direction(bid)
                        if next_pos.add(conveyor_dir) == current_pos:
                            lead_to_gunner = True
                    elif btype == EntityType.BRIDGE:
                        if ct.get_bridge_target(bid) == current_pos:
                            lead_to_gunner = True
                    if lead_to_gunner == True:
                        visited.add((next_pos.x, next_pos.y))
                        self.forbidden_tiles.add((next_pos.x, next_pos.y))
                        queue.append(next_pos)
                    
        self.traced_gunners.add(gunner_id)
    
    def RUSH_update_protection(self, ct: Controller):
        for bid in ct.get_nearby_buildings():
            if ct.get_team(bid) == ct.get_team() and ct.get_entity_type(bid) == EntityType.GUNNER:
                if bid not in self.traced_gunners:
                    gunner_pos = ct.get_position(bid)
                    if gunner_pos.distance_squared(self.enemy_core_pos) < 64:
                        self.RUSH_trace_from_gunner(ct, gunner_pos, bid)


    def BUILD_defend_launcher(self, ct: Controller, loc: Position):
        if(ct.get_action_cooldown() > 0):
            return True

        for dir in All_Dirs:
            pos = loc.add(dir)
            if(not ct.is_in_vision(pos) or not ctx.IS_in_map(pos)):
                continue

            botid = ct.get_tile_builder_bot_id(pos)
            botTeam = ct.get_team(botid)
            if(botid == None or botTeam == ct.get_team()):
                continue
            gotLauncher = False
            for i in Dirs:


                launcherPos = pos.add(i)
                if(not ct.is_in_vision(launcherPos) or not ctx.IS_in_map(launcherPos)):
                    continue
                bid = ct.get_tile_building_id(launcherPos)
                btype = ct.get_entity_type(bid)
                bteam = ct.get_team(bid)
                if(bid != None and btype == EntityType.LAUNCHER and bteam == ct.get_team()):
                    gotLauncher = True
            if(gotLauncher):
                continue
            for i in Dirs:
                launcherPos = pos.add(i)
                if(not ct.is_in_vision(launcherPos)  or not ctx.IS_in_map(launcherPos)):
                    continue
                bid = ct.get_tile_building_id(launcherPos)
                btype = ct.get_entity_type(bid)
                bteam = ct.get_team(bid)
                
                if(btype == EntityType.ROAD and bteam == ct.get_team()):
                    if(ct.can_destroy(launcherPos)):
                        ct.destroy(launcherPos)
                    
                if(ct.can_build_launcher(launcherPos)):
                    ct.build_launcher(launcherPos)
                    return True
            return False
        return True
            

    def RUSH_attack_target_normal(self, ct: Controller):
        if(self.attackables[self.target_attackable.x][self.target_attackable.y].type == ATTACK_TYPE.NORMAL):
            if(self.MODE == "HARASS" or self.MODE == "TRACE"):
                self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = 40
            else:
                self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = 10

        if(ct.is_in_vision(self.target_attackable)):
            if(ctx.bugnav.tooCloseToDanger(ct, self.target_attackable)):
                ctx.bugnav.safeFuzzyMove(ct, self.target_attackable.direction_to(ct.get_position()).opposite())
                self.state = "ATTACK"
                return
            # print(self.GOT_nearby_working_bot(ct, self.target_attackable))
            if((self.MODE == "HARASS" or self.MODE == "TRACE") and self.GOT_nearby_working_bot(ct, self.target_attackable) > 0):
                if(self.BUILD_defend_launcher(ct, self.target_attackable)):
                    pass
                else:
                    self.attack_turn_count -= 5

            bid = ct.get_tile_building_id(self.target_attackable)
            btype = ct.get_entity_type(bid)
            bteam = ct.get_team(bid)

            if(bid != None and bteam == ct.get_team()):
                self.state = "ATTACK"
                return

            if(bid == None):
                if(self.target_attackable == ct.get_position()):
                    for dir in Dirs:
                        if(ct.can_move(dir)):
                            ct.move(dir)
                            break
            
            if(self.target_attackable.x - self.enemy_core_pos.x < 4 and self.target_attackable.y - self.enemy_core_pos.y < 4):
                gunnerDir = self.target_attackable.direction_to(self.enemy_core_pos)
                if(ct.can_build_gunner(self.target_attackable, gunnerDir)):
                    ct.build_gunner(self.target_attackable, gunnerDir)
                    self.state = "ATTACK"
                    return
            else:
                sentinelDir = self.target_attackable.direction_to(self.enemy_core_pos)
                if ct.can_build_sentinel(self.target_attackable, sentinelDir):
                    ct.build_sentinel(self.target_attackable, sentinelDir)
                    self.state = "ATTACK"
                    return
            if(ct.can_build_barrier(self.target_attackable)):
                ct.build_barrier(self.target_attackable)
                self.state = "ATTACK"
                return
            conDir = Direction.SOUTH
            if(self.enemy_core_pos != Position(-1, -1)):
                conDir = self.enemy_core_pos.direction_to(self.target_attackable)
            if(ct.can_build_conveyor(self.target_attackable, conDir)):
                ct.build_conveyor(self.target_attackable, conDir)
                self.state = "ATTACK"
                return
            if(ct.can_build_road(self.target_attackable)):
                ct.build_road(self.target_attackable)
                self.state = "ATTACK"
                return



            
            if(self.MODE == "NORMAL"):
                nextPos = Position(-1, -1)
                if(btype == EntityType.CONVEYOR):
                    nextPos = self.target_attackable.add(ct.get_direction(bid))
                elif(btype == EntityType.BRIDGE):
                    nextPos = ct.get_bridge_target(bid)
                if(self.attackables[nextPos.x][nextPos.y].type == ATTACK_TYPE.DONE):
                    self.state = "ATTACK"
                    return

                if(nextPos != Position(-1, -1) and self.attackables[nextPos.x][nextPos.y].score > 0 and  self.attackables[nextPos.x][nextPos.y].ignore < 5):
                    self.target_attackable = nextPos
                    self.attack_turn_count = self.current_max_attack_turn_count
            elif(self.MODE == "TRACE"):
                nextPos = Position(-1, -1)
                for bid in ct.get_nearby_buildings():
                    pos = ct.get_position(bid)
                    btype = ct.get_entity_type(bid)
                    if(btype == EntityType.CONVEYOR):
                        if(pos.add(ct.get_direction(bid)) == self.target_attackable):
                            nextPos = pos
                            break
                    if(btype == EntityType.BRIDGE):
                        if(ct.get_bridge_target(bid) == self.target_attackable):
                            nextPos = pos
                            break


                if(nextPos != Position(-1, -1) and self.attackables[nextPos.x][nextPos.y].score > 0 and  self.attackables[nextPos.x][nextPos.y].ignore < 5):
                    self.target_attackable = nextPos
                    self.attack_turn_count = self.current_max_attack_turn_count
            else:
                currentConnects = []
                current = self.target_attackable
                max_stack = 20
                while(max_stack >= 0):
                    max_stack -= 1
                    if(not ct.is_in_vision(current)):
                        break
                    bid = ct.get_tile_building_id(current)
                    bteam = ct.get_team(bid)
                    btype = ct.get_entity_type(bid)
                    if(bid == None):
                        break
                    if(btype in TURRET_TYPE and bteam == ct.get_team()):
                        self.state = "ATTACK"
                        break
                    
                    nextPos = None
                    if(btype == EntityType.CONVEYOR):
                        nextPos = current.add(ct.get_direction(bid))
                    if(btype == EntityType.BRIDGE):
                        nextPos = ct.get_bridge_target(bid)
                    current = nextPos 
                    if(nextPos in currentConnects or nextPos == None):
                        break
                    
                    currentConnects.append(nextPos)

            if(ct.can_destroy(self.target_attackable)):
                ct.destroy(self.target_attackable)

            # if(ct.get_position() == self.target_attackable):
            #     for dir in Dirs:
            #         pos = self.target_attackable.add(dir)
            #         bid = ct.get_tile_building_id(pos)
            #         bteam = ct.get_team(bid)
            #         btype = ct.get_entity_type(bid)
            #         if(bid == None or (bteam == ct.get_team() and btype == EntityType.ROAD)):
            #             if(ct.can_destroy(pos)):
            #                 ct.destroy(pos)
            #             if(ct.can_build_barrier(pos)):
            #                 ct.build_barrier(pos)
            if(ct.can_fire(self.target_attackable) and self.target_attackable not in self.forbidden_tiles):
                ct.fire(self.target_attackable)
                
        else:
            self.attack_turn_count = self.current_max_attack_turn_count
        
        if(ct.get_position().distance_squared(self.target_attackable) <= 2):
            moveDir = ct.get_position().direction_to(self.target_attackable)
            if(ct.can_move(moveDir)):
                ct.move(moveDir)

        else:
            ctx.bugnav.MOVE_to_target(ct, self.target_attackable, False, 0, 0, 2)
    
    def RUSH_get_closest_enemy_harvester_to_core(self, ct: Controller):
        if ct.get_position().distance_squared(self.enemy_core_pos) > 2:
            ctx.bugnav.MOVE_to_target(ct, self.enemy_core_pos, False, 0, 0, 2)
            return
        enemy_building = ct.get_nearby_buildings()
        min_dist = 676767
        for bid in enemy_building:
            bteam = ct.get_team(bid)
            bpos = ct.get_position(bid)
            if(bteam == ct.get_team()):
                pass
            else:
                if ct.get_entity_type(bid) == EntityType.MARKER:
                    value = ct.get_marker_value(bid)
                    if value == 67:
                        self.closest_harvester = bpos
                        dist_to_core = min_dist
                        break
                elif ct.get_entity_type(bid) == EntityType.HARVESTER:
                    dist_to_core = self.enemy_core_pos.distance_squared(bpos)
                    if dist_to_core < min_dist:
                        min_dist = dist_to_core
                        self.closest_harvester = bpos
        if min_dist == 676767:
            max_dist = 0
            #If we can't find any harvester go find the farthest conveyor from core(less defense ig)
            for bid in enemy_building:
                bteam = ct.get_team(bid)
                bpos = ct.get_position(bid)
                if bteam == ct.get_team():
                    pass
                else:
                    if ct.get_entity_type(bid) == EntityType.CONVEYOR or ct.get_entity_type(bid) == EntityType.BRIDGE:
                        dist_to_core = self.enemy_core_pos.distance_squared(bpos)
                        if dist_to_core > max_dist:
                            max_dist = dist_to_core
                            self.closest_harvester = bpos
    def RUSH_target_enemy_nearest_harvester(self, ct: Controller):
        self.RUSH_get_closest_enemy_harvester_to_core(ct)
        if ct.get_position().distance_squared(self.closest_harvester) > 2:
            ctx.bugnav.MOVE_to_target(ct, self.closest_harvester, False, 0, 0, 2)
            return
        bid = ct.get_tile_building_id(self.closest_harvester)
        
        if bid is not None and ct.get_team(bid) != ct.get_team():
            if ct.can_fire(self.closest_harvester) and self.closest_harvester not in self.forbidden_tiles:
                ct.fire(self.closest_harvester)
        else:
            if ct.can_place_marker(self.closest_harvester):
                ct.place_marker(self.closest_harvester, 67)
        #Placing turrests or sth after destroy the enemy nearest harvester







    def RUSH_run(self, ct: Controller):
        """Main RUSH builder function"""
        print(self.MODE)
            
        if(ct.get_current_round() == 1):
            self.return_home = True


        if(not self.setup):
            if(ct.get_current_round() == 4):
                self.MODE = "HARASS"
            if(ct.get_current_round() == 3):
                self.MODE = "TRACE"
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
        
        print(self.attack_turn_count)
        if(self.target_attackable != Position(-1, -1)):
            self.attack_turn_count -= 1

        if(self.attack_turn_count < 0):
            self.attack_turn_count = 0
            if(self.target_attackable != Position(-1, -1)):
                self.attackables[self.target_attackable.x][self.target_attackable.y].ignore = 50
                self.MODE = "HARASS"
            self.state = "ATTACK"

        self.RUSH_sense_nearby(ct)
        self.RUSH_update_protection(ct)

        if(ct.get_hp() < ct.get_max_hp() ):
            if(ct.can_heal(ct.get_position())):
                ct.heal(ct.get_position())

        if(ct.get_current_round() > 100):
            self.MODE = "CONCENTRATE"

        if(self.MODE == "CONCENTRATE"):
            self.current_max_attack_turn_count = MAX_ATTACK_TURN_COUNT_CONCENTRATE
        else:
            self.current_max_attack_turn_count = MAX_ATTACK_TURN_COUNT


        if(self.state == "FIND_CORE"):
            self.RUSH_find_core(ct)
        elif(self.state == "ATTACK"):
            self.RUSH_attack(ct)
        elif(self.state == "ATTACK_TARGET_NORMAL"):
            self.RUSH_attack_target_normal(ct)
        #If the rush don't work, change state for everyone to target enemy nearest harvestor
        elif(self.state == "RUSH_FAIL"):
            self.RUSH_target_enemy_nearest_harvester(ct)
        elif(self.state == "BACK_TO_CORE"):
            self.RUSH_back_to_core(ct)
            
            

        self.RUSH_invariant_action(ct)

    def RUSH_invariant_action(self, ct: Controller):
        self.Glob_Tit = ct.get_global_resources()


        if(self.enemy_core_pos != Position(-1, -1)):
            if(ct.get_position().distance_squared(self.enemy_core_pos) < 8):
                for dir in All_Dirs:
                    if(self.Glob_Tit < ct.get_conveyor_cost()):
                        break
                    pos = ct.get_position().add(dir)
                    if(not ctx.IS_in_map(pos)):
                        continue
                    bid = ct.get_tile_building_id(pos)
                    btype = ct.get_entity_type(bid)
                    bteam = ct.get_team(bid)
                    if((bteam == ct.get_team() and btype == EntityType.ROAD) or btype == EntityType.MARKER):
                        if(ct.can_destroy(pos)):
                            ct.destroy(pos)
                    gotLauncher = False
                    for i in Dirs:
                        loc = pos.add(i)
                        if(not ctx.IS_in_map(loc)):
                            continue
                        # ct.draw_indicator_line(loc, pos, 255, 255, 255)
                        bid = ct.get_tile_building_id(loc)
                        btype = ct.get_entity_type(bid)
                        bteam = ct.get_team(bid)
                        if(bteam == ct.get_team() and btype == EntityType.LAUNCHER):
                            gotLauncher = True

                    if(not gotLauncher):
                        if(ct.can_build_launcher(pos)):
                            ct.build_launcher(pos)
                            break

                    if(ct.can_build_barrier(pos)):
                        ct.build_barrier(pos)
                        break
                    conDir = Direction.SOUTH
                    if(self.enemy_core_pos != Position(-1, -1)):
                        conDir = self.enemy_core_pos.direction_to(self.target_attackable)
                    if(ct.can_build_conveyor(pos, conDir)):
                        ct.build_conveyor(pos, conDir)
                        break

        if(self.target_attackable != Position(-1, -1) and self.state == "ATTACK_TARGET_NORMAL" and self.MODE == "CONCENTRATE"):
            if(self.Glob_Tit > ct.get_barrier_cost()):
                
                
                if(self.target_attackable == ct.get_position()):
                    for i in Dirs:
                        loc = ct.get_position().add(i)
                        bid = ct.get_tile_building_id(loc)
                        btype = ct.get_entity_type(bid)
                        bteam = ct.get_team(bid)
                        if((bteam == ct.get_team() and btype == EntityType.ROAD) or btype == EntityType.MARKER):
                            if(ct.can_destroy(loc)):
                                ct.destroy(loc)
                        if(ct.can_build_barrier(loc)):
                            ct.build_barrier(loc)
                

        bid = ct.get_tile_building_id(ct.get_position())
        btype = ct.get_entity_type(bid)
        bteam = ct.get_team(bid)
        if(bteam != ct.get_team()):
            #conveyorDir = Direction.SOUTH
            #if ct.get_entity_type(bid) == EntityType.CONVEYOR:
                #conveyorDir = ct.get_direction(bid)
                #if(ct.can_fire(ct.get_position())):
                    #ct.fire(ct.get_position())
                #if ct.can_build_conveyor(ct.get_position(), conveyorDir.opposite()):
                    #ct.build_conveyor(ct.get_position(), conveyorDir.opposite())
            if(ct.can_fire(ct.get_position()) and ct.get_position() not in self.forbidden_tiles):
                ct.fire(ct.get_position())