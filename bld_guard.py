from cambc import Controller, Position, Direction
from bld_context import ctx
from utils import *

class DefendableInfo:
    __slots__ = ("pos", "score", "type", "ignore")

    def __init__(self, pos, score):
        self.pos = pos
        self.score = score


class BldGuard():
    def __init__(self):
        self.setup = False
        self.state = "EXPLORE"

        # CONSTANT
        self.CORE_ZONE = 400

        # WANDERING
        self.follow_enemy_ID = -1
        self.follow_enemy_turn = 0

        # HEALING
        self.Core_HP = -1
        self.Target_Heal_Pos = Position(-1, -1)
        
        # Hotspot
        self.HS_Step_From_Core = 5
        self.HS_Accept_Range   = 5
        self.HS_Visit_Turn = 50

        self.Curr_Spot_Dir = Direction.CENTRE
        self.Spot_Target = Position(-1, -1)
        self.Spot_Turn = -1

        self.defendables = []
        self.defendable_target = Position(-1, -1)

        self.ally_bots = {}
        self.enemy_bots = {}

        self.fix_connects = set()
        self.fix_target = Position(-1, -1)
        
    def GUARD_sense_nearby(self, ct):
        self.ally_bots = {}
        self.enemy_bots = {}

        spread = []
        spread2 = []
        for bid in ct.get_nearby_units():
            i = ct.get_position(bid) 
            btype = ct.get_entity_type(bid)
            bteam = ct.get_team(bid)
            if(btype != EntityType.BUILDER_BOT or ct.get_id() == bid):
                continue

            if(bteam == ct.get_team()):
                self.ally_bots[i] = 1
                spread.append(i)
            else:
                self.enemy_bots[i] = 1
                # spread2.append(i)

        for pos in spread:
            for dx in [-2, 0, 2]:
                for dy in [-2, 0, 2]:
                    nx = pos.x + dx
                    ny = pos.y + dy
                    newPos = Position(nx, ny)

                    self.ally_bots[newPos] = self.ally_bots.get(newPos, 0) + 1
        for i in spread2:
            for dir in Dirs:
                pos = i.add(dir)
                self.enemy_bots[pos] = self.enemy_bots.get(pos, 0) + 1



    def DEFENDABLE_update(self, ct):
        for tile_pos in ct.get_nearby_tiles(13):
            self.DEFENDABLE_status(ct, tile_pos)
    
    
    def DEFENDABLE_status(self, ct: Controller, defendable_pos: Position):
        if(not ct.is_in_vision(defendable_pos)): return
        score = self.GET_defendable_info(ct, defendable_pos)
        self.defendables[defendable_pos.x][defendable_pos.y].score = score

    def GET_best_defendable_target(self, ct):
        best_defendable = Position(-1, -1)
        best_score = 0
        cur = ct.get_position()

        for dx in range(-15, 15):
            for dy in range(-15, 15):
                x = cur.x + dx
                y = cur.y + dy

                if not ctx.IS_in_map(Position(x, y)):
                    continue

                score = self.defendables[x][y].score
                if score > best_score:
                    best_defendable, best_score = self.defendables[x][y].pos, score
        print(best_score)
        if(best_score > 0):
            return best_defendable
        return Position(-1, -1)

    def IS_connect_broken(self, ct, pos, bid, btype, bteam):
        if(bteam != ct.get_team()):
            return False
        if(btype != EntityType.CONVEYOR and btype != EntityType.BRIDGE and not (btype == EntityType.HARVESTER and not ctx.CHECK_ore_linked_core(ct, pos))):
            return False
        nextPos = Position(-1, -1)
        if(btype == EntityType.CONVEYOR):
            conDir = ct.get_direction(bid)
            nextPos = pos.add(conDir)
        if(btype == EntityType.BRIDGE):
            nextPos = ct.get_bridge_target(bid)
        if(btype == EntityType.HARVESTER):
            return True
        if(not ct.is_in_vision(nextPos)):
            return False
        bid = ct.get_tile_building_id(nextPos)
        btype = ct.get_entity_type(bid)
        bteam = ct.get_team(bid)

        if(bteam != ct.get_team() or (btype != EntityType.CONVEYOR and btype != EntityType.BRIDGE and btype != EntityType.CORE and btype != EntityType.FOUNDRY and btype != EntityType.SPLITTER)):
            return True
        return False

    def GET_start_build_pos(self, ct: Controller, ore_pos: Position):
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

            if env != Environment.ORE_TITANIUM: prior = "EMPTY"
            # Compare distance
            dis = check_pos.distance_squared(ctx.CORE_POS)
            if best_pos == Position(-1, -1) or dis < min_dis:
                best_pos, min_dis = check_pos, dis
        return best_pos
    
    def GET_defendable_info(self, ct, defendable_pos):
        env = ct.get_tile_env(defendable_pos)
        bid = ct.get_tile_building_id(defendable_pos)
        btype = ct.get_entity_type(bid)
        bteam = ct.get_team(bid)
        bhp = ct.get_hp(bid)
        bmaxhp = ct.get_max_hp(bid)

        score = 0

        if(self.IS_connect_broken(ct, defendable_pos, bid, btype, bteam)):
            self.fix_connects.add(defendable_pos)
        else:
            if(defendable_pos in self.fix_connects):
                self.fix_connects.remove(defendable_pos)

        if(defendable_pos == self.defendable_target):
            score -= 2

        score -= self.ally_bots.get(defendable_pos, 0) * 4
        score += ((bmaxhp - bhp) / bmaxhp) * 4

        score += self.enemy_bots.get(defendable_pos, 0) * 2
        # score -= ct.get_position().distance_squared(defendable_pos) ** 0.5 * 0.1
        score += max(0, 4 - ctx.CORE_POS.distance_squared(defendable_pos) ** 0.5 * 0.5 )
        
        if(btype == EntityType.CONVEYOR or btype == EntityType.BRIDGE) and bhp < bmaxhp:
            score += 2
            score += ((bmaxhp - bhp) / bmaxhp) * 8

        if(bhp < bmaxhp or self.enemy_bots.get(defendable_pos, 0) > 0) and bteam == ct.get_team():
            return score
        return 0
    
    #region ----- GET function -----
    def GET_next_hotspot(self, step_from_core: int):
        """Get the next hotspot for guardian, depends on step from core"""
        if self.Curr_Spot_Dir == Direction.CENTRE:
            self.Curr_Spot_Dir = Direction.NORTH

        cx, cy = ctx.CORE_POS.x, ctx.CORE_POS.y
        dx, dy = self.Curr_Spot_Dir.delta()
        if dx != 0 and dy != 0: # Diagonal
            INV_SQRT2 = 0.7  # 1 / sqrt(2)
            nx = cx + int(dx * step_from_core * INV_SQRT2)
            ny = cy + int(dy * step_from_core * INV_SQRT2)
        else: # Straight
            nx = cx + dx * step_from_core
            ny = cy + dy * step_from_core
        nx = max(0, min(nx, ctx.MAP_WIDTH - 1))
        ny = max(0, min(ny, ctx.MAP_HEIGHT - 1))

        self.Curr_Spot_Dir = self.Curr_Spot_Dir.rotate_right().rotate_right().rotate_right()
        return Position(int(nx), int(ny))
    
    def GET_best_enemy_bot_ID(self, ct: Controller, vision_dis: int, dis_to_core: int):
        """Get nearest enemy builder ID within vision_dis\n
           Depends on dis_to_core also, if dis_to_core = -1, choose nearest\n
           Return -1 if found nothing"""
        best_ID = -1
        min_dis = -1
        vision = ct.get_nearby_units(dist_sq=vision_dis)
        for ID in vision:
            if ct.get_team(ID) == ctx.MY_TEAM: continue
            type = ct.get_entity_type(ID)
            if type == EntityType.BUILDER_BOT:
                en_pos = ct.get_position(ID)
                if dis_to_core > 1:
                    core_dis = en_pos.distance_squared(ctx.CORE_POS)
                    if core_dis > dis_to_core: continue

                # Compare
                my_pos = ct.get_position()
                my_dis = en_pos.distance_squared(my_pos)
                if best_ID == -1 or my_dis < min_dis:
                    best_ID = ID
        return best_ID
    
    def GET_worst_convey(self, ct: Controller):
        """Get the worst status conveyor position in vision\n
           If found nothing, return Position(-1, -1)"""
        vision = ct.get_nearby_buildings()
        my_pos = ct.get_position()

        worst_pos = Position(-1, -1)
        min_dis, min_hp = -1, -1
        prior = "NO_BOT"

        for ID in vision:
            if ct.get_team(ID) != ctx.MY_TEAM: continue
            if not ct.get_entity_type(ID) in CONVEY_TYPE: continue
            hp = ct.get_hp(ID)
            if hp + GameConstants.HEAL_AMOUNT > ct.get_max_hp(ID): continue
            conv_pos = ct.get_position(ID)
            my_dis = my_pos.distance_squared(conv_pos)
            if worst_pos == Position(-1, -1) or my_dis < min_dis:
                worst_pos, min_dis, min_hp = conv_pos, my_dis, hp
            elif my_dis == min_dis and hp < min_hp:
                worst_pos, min_hp = conv_pos, hp
        return worst_pos
    #endregion

    #region ----- Guard GENERAL -----
    def GUARD_setup(self, ct):
        """Setup for Guardian builder"""
        
        
        self.HS_Step_From_Core = 0.07 * ct.get_current_round() +5



        self.Curr_Spot_Dir = ctx.CORE_DIR

        width = ct.get_map_width()
        height = ct.get_map_height()
        self.defendables = [
            [DefendableInfo(Position(i, j), 0) for j in range(height)]
            for i in range(width)
        ]

    def GUARD_update_info(self, ct: Controller):
        """Update status for Guardian builder"""
        # old
        if ct.is_in_vision(ctx.CORE_POS):
            self.Core_HP = ct.get_hp(ctx.CORE_ID)
        self.follow_enemy_turn = (self.follow_enemy_turn + 40 + 1) % 100 - 40


        # new
        self.DEFENDABLE_update(ct)

    def GUARD_update_hotspot(self):
        """Update new hotspot for guardian"""
        pass
    
    #endregion

    #region ----- Guard DEBUG -----
    def DEBUG_guard_hotspot(self, ct: Controller):
        """Debug guardian current all hotspot"""
        # Print
        print("\n=== Hot Spot ===")
        print(f"Target: {self.Spot_Target.x, self.Spot_Target.y}")
        print(f"Turn: {self.Spot_Turn}")
        print(f"MAX step from core: {self.HS_Step_From_Core}")
        print(f"MAX accept range: {self.HS_Accept_Range}")
        print(f"MAX visit turn: {self.HS_Visit_Turn}")
        # Draw
        # ct.draw_indicator_dot(self.Spot_Target, 200, 255, 200)
    
    def DEBUG_guard_info(self, ct: Controller):
        """Debug function for guardian info"""
        # Print
        print(f"Follow: {self.follow_enemy_ID}")
        print(f"Follow turn: {self.follow_enemy_turn}")
        print(f"Core HP: {self.Core_HP}")
        print(f"Target Heal: ({self.Target_Heal_Pos})")
        # Draw
        # ct.draw_indicator_dot(self.Target_Heal_Pos, 100, 255, 100)
    #endregion

    #region ----- Guard MOVE / ACT -----
    def GUARD_visit_hotspot(self, ct: Controller):
        """Guardian visit hotspot function, reset max_turn rounds\n
           Move to an accepted range within the spot target"""
        if self.Spot_Target == Position(-1, -1):
            self.Spot_Turn = self.HS_Visit_Turn
            self.Spot_Target = self.GET_next_hotspot(self.HS_Step_From_Core)

        my_pos = ct.get_position()
        cur_dis = my_pos.distance_squared(self.Spot_Target)
        if cur_dis <= self.HS_Accept_Range or self.Spot_Turn < 1:
            self.Spot_Turn = self.HS_Visit_Turn
            self.Spot_Target = self.GET_next_hotspot(self.HS_Step_From_Core)

        self.Spot_Turn = self.Spot_Turn - 1
        if ct.get_move_cooldown() == 0:
            ctx.bugnav.MOVE_to_target(ct, self.Spot_Target, True, 2, 2, -2)

    #endregion

    def GET_best_fix_target(self, ct):
        bestDist = 9999
        bestPos = Position(-1, -1)
        for pos in self.fix_connects:
            if(pos.distance_squared(ct.get_position()) < bestDist):
                bestPos = pos
                bestDist = pos.distance_squared(ct.get_position())
        return bestPos

    #region ----- Guard STATE -----
    def GUARD_wandering(self, ct: Controller):
        """Guardian move to hotspot / wandering for work function"""
        self.defendable_target = self.GET_best_defendable_target(ct)
        self.fix_target = self.GET_best_fix_target(ct)

        if(self.fix_target != Position(-1, -1)):
            self.state = "LINK_BACK_TO_CORE"
            return
        elif(self.defendable_target == Position(-1, -1)):
            if ct.get_move_cooldown() == 0:
                self.GUARD_visit_hotspot(ct)
        else:
            ct.draw_indicator_line(ct.get_position(), self.defendable_target, 255, 0, 0)
            
            if(ct.get_position().distance_squared(self.defendable_target) > 2):
                ctx.bugnav.MOVE_to_target(ct, self.defendable_target, False, 0, 0, 0, -80)

    def GUARD_target_heal(self, ct: Controller, heal_pos: Position):
        """Guardian state to target pos that need heal"""
        if heal_pos == Position(-1, -1): return

        my_dis = heal_pos.distance_squared(ct.get_position())
        if ct.get_move_cooldown() == 0 and my_dis > 2:
            ctx.bugnav.MOVE_to_target(ct, heal_pos, False)

        if ct.can_heal(heal_pos):
            ct.heal(heal_pos)
            
    #endregion

    def GUARD_link_back_core(self, ct: Controller, start_build_pos: Position):
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
        if ctx.bugnav.lastConnect.distance_squared(ctx.CORE_POS) <= 2:
            ctx.bugnav.lastConnect = Position(-1, -1)
            return "DONE"
        if link == "STUCK":
            ctx.bugnav.lastConnect = Position(-1, -1)
            return "STUCK"
    #endregion

    #region ----- ECO state -----
    def ECO_switch_explore(self, ct: Controller):
        """Switch state "EXPLORE" immediately in order to save cooldown"""
        self.state = "EXPLORE"
        self.fix_target = Position(-1, -1)

    def GUARD_run(self, ct: Controller):
        """Main GUARDIAN builder function"""
        if not self.setup:
            self.setup = True
            self.GUARD_setup(ct)

        print(self.state)

        # UPDATE
        ctx.ORE_update(ct)
        self.GUARD_sense_nearby(ct)
        print("NOW1: ", ct.get_cpu_time_elapsed())

        self.GUARD_update_info(ct)
        if(self.state == "EXPLORE"):
            self.GUARD_wandering(ct)
        elif(self.state == "LINK_BACK_TO_CORE"):
            ct.draw_indicator_line(ct.get_position(),  self.fix_target, 255, 255, 0)
            if(ct.is_in_vision(self.fix_target)):
                bid = ct.get_tile_building_id(self.fix_target)
                btype = ct.get_entity_type(bid)
                if(btype == EntityType.HARVESTER):
                    if(ctx.CHECK_ore_linked_core(ct, self.fix_target)):
                        self.state = "EXPLORE"
                        return
                    self.fix_target = self.GET_start_build_pos(ct, self.fix_target)

            x = self.GUARD_link_back_core(ct, self.fix_target)
            print("LINK BACK CORE:", x)
            if x in ["DONE", "STUCK"]:
                self.state = "EXPLORE"
                return
        # WORK


        self.GUARD_invariant_action(ct)

        # DEBUG
        self.DEBUG_guard_info(ct)
        self.DEBUG_guard_hotspot(ct)
        # ctx.ORE_debug()


    def BUILDER_heal_lowest_tile(self, ct):
        best_hp_pos = Position(-1, -1)
        lowest_hp = 99999
        for dir in All_Dirs:
            pos = ct.get_position().add(dir)
            if(not ctx.IS_in_map(pos)):
                continue
            bid = ct.get_tile_building_id(pos)
            bteam = ct.get_team(bid)
            bhp = ct.get_hp(bid)
            maxbhp = ct.get_max_hp(bid)
            if(bteam == ct.get_team() and bhp < maxbhp and bhp < lowest_hp and ct.can_heal(pos)):
                lowest_hp = bhp
                best_hp_pos = pos
        if(ct.can_heal(best_hp_pos)):
            ct.heal(best_hp_pos)


    def GUARD_invariant_action(self, ct):
        self.BUILDER_heal_lowest_tile(ct)