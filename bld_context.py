from cambc import Controller, EntityType, Environment, Position, Team
from ore_info import OreInfo
from bld_move import BugNav, Explore
from utils import *

class BldContext:
    """Class context (shared variables / lists) for builder"""
    def __init__(self):
        # Class
        self.bugnav = BugNav()
        self.explore = Explore()

        # CONSTANT
        self.MY_TEAM: Team
        self.CORE_POS = Position(-1, -1)

        # GLOBAL
        self.Cur_Round = -1
        self.Ores: dict[tuple[int, int], OreInfo] = {}

        # RESOURCE
        self.Glob_Tit = -1
        self.Glob_Anx = -1

        # COST
        self.Builder_Cost = -1
        self.Harvest_Cost = -1
        self.Convey_Cost = -1
        self.Gunner_Cost = -1
        self.Road_Cost = -1
        self.Spawn_Limit = -1

    #region ----- ORE scan functions -----
    def ORE_update(self, ct: Controller):
        """Scan vision to update ores"""
        # Scan in vision
        for tile_pos in ct.get_nearby_tiles():
            env = ct.get_tile_env(tile_pos)
            if env in Ore_Env:
                self.ORE_status(ct, tile_pos)
        # Decrease ignore
        for ore in self.Ores.values():
            if ore.ignore > 0:
                ore.ignore -= 1

    def ORE_status(self, ct: Controller, ore_pos: Position):
        """Update an ore in vision"""
        if not ct.is_in_vision(ore_pos): return

        env = ct.get_tile_env(ore_pos)
        if env not in Ore_Env: return

        mval = self.GET_marker_val(ct, ore_pos)
        harv = self.CHECK_harvester(ct, ore_pos)
        barr = self.CHECK_barrier(ct, ore_pos)

        key = (ore_pos.x, ore_pos.y)
        # OLD
        if key in self.Ores:
            ore = self.Ores[key]

            ore.mark, ore.harv, ore.barr = mval, harv, barr
            if mval == 36 and ore.ignore == 0:
                ore.ignore = MAX_ORE_IGNORE_TURN
        # NEW
        else:
            ore = OreInfo(ore_pos, env)
            ore.mark, ore.harv, ore.barr = mval, harv, barr

            ore.ignore = 0
            if mval == 36:
                ore.ignore = MAX_ORE_IGNORE_TURN

            self.Ores[key] = ore

    def ORE_debug(self):
        """Print all ores status for debug purpose"""
        print("\n=== ORE STAT ===")
        for ore in self.Ores.values():
            print(ore)
            print("-------------")
        print()
    #endregion

    #region ----- GET functions -----
    def GET_core_pos(self, ct: Controller):
        """Get our team core position (vision only)"""
        if self.CORE_POS != Position(-1, -1): return

        nearby_building = ct.get_nearby_buildings()
        for id in nearby_building:
            if ct.get_team(id) != ct.get_team(): continue
            if ct.get_entity_type(id) == EntityType.CORE:
                self.CORE_POS = ct.get_position(id)
                break
    
    def GET_marker_val(self, ct: Controller, tile_pos: Position):
        """Get the value of the marker placed on a position\n
           If there is no marker / out of vision -> -1\n
           If it is the opposite team marker -> -2"""
        if not ct.is_in_vision(tile_pos): return -1

        ID = ct.get_tile_building_id(tile_pos)
        if ID is None: return -1
        if ct.get_entity_type(ID) == EntityType.MARKER:
            if ct.get_team(ID) == self.MY_TEAM:
                return ct.get_marker_value(ID)
            else: return -2
        return -1
    
    #endregion

    #region --- CHECK FUNCTION ---
    def CHECK_harvester(self, ct: Controller, tile_pos: Position):
        """Check if a harvester is placed on a position\n
           If out of vision, return True"""
        if not ct.is_in_vision(tile_pos): return False

        ID = ct.get_tile_building_id(tile_pos)
        if ID is None: return False
        if ct.get_entity_type(ID) == EntityType.HARVESTER:
            return True
        return False

    def CHECK_barrier(self, ct: Controller, tile_pos: Position):
        """Check barrier is placed on a position\n
        Return 0 = Nothing, 1 = Ally barrier, 2 = Enemy barrier"""
        if not ct.is_in_vision(tile_pos): return 0

        ID = ct.get_tile_building_id(tile_pos)
        if ID is None: return 0
        if ct.get_entity_type(ID) == EntityType.BARRIER:
            if ct.get_team(ID) == ct.get_team():
                return 1
            else: return 2
        return 0

    def CHECK_enemy_turret(self, ct: Controller):
        """Return the nearest enemy turret in vision\n
           Return Pos(-1, -1) if found nothing"""
        turr_pos = Position(-1, -1)
        min_dis = 999
        my_pos = ct.get_position()

        vision = ct.get_nearby_units()
        for ent_id in vision:
            if ct.get_team(ent_id) != self.MY_TEAM:
                continue
            etype = ct.get_entity_type(ent_id)
            if etype in Turret_Type:
                epos = ct.get_position(ent_id)
                cur_dis = my_pos.distance_squared(epos)
                if cur_dis < min_dis:
                    min_dis = cur_dis
                    turr_pos = epos
        return turr_pos

    def CHECK_ore_protected(self, ct: Controller, ore_pos: Position):
        """Check if the ore in vision is protected 4 sides\n
        Also return False if 13 <= dis_to_ore <= vision, True if out of vision"""
        if ore_pos == Position(-1, -1): return True
        if not ct.is_in_vision(ore_pos): return True

        # Ore check
        if not ct.is_tile_passable(ore_pos): return True 
        if ore_pos.distance_squared(ct.get_position()) > 13: return False	

        # Side check
        side_cnt = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx != 0 and dy != 0: continue
                if dx == dy == 0: continue

                pos = Position(ore_pos.x + dx, ore_pos.y + dy)
                id = ct.get_tile_building_id(pos)
                if id is None: continue
                type = ct.get_entity_type(id)
                if type != EntityType.HARVESTER:
                    if ct.get_team(id) != self.MY_TEAM:
                        continue
                side_cnt += 1
        return (side_cnt == 4)
    #endregion


# Class instance
ctx = BldContext()