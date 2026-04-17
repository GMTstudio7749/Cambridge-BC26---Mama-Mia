from cambc import Controller, EntityType, Environment, Position, Team
from ore_info import OreInfo
from bld_move import BugNav
from utils import *

class BldContext:
    def __init__(self):
        # CLASS
        self.bugnav = BugNav()

        # CONSTANT
        self.MAP_WIDTH: int
        self.MAP_HEIGHT: int
        self.MY_TEAM: Team
        self.CORE_POS = Position(-1, -1)
        self.CORE_ID: int
        self.CORE_DIR: Direction

        # GLOBAL
        self.Cur_Round = -1
        self.Turn_Count = 0
        self.Ores: dict[tuple[int, int], OreInfo] = {}

    #region ----- ORE scan func -----
    def ORE_update(self, ct: Controller):
        """Scan vision to update ores"""
        # Scan in vision
        for tile_pos in ct.get_nearby_tiles():
            env = ct.get_tile_env(tile_pos)
            if env in ORE_ENV:
                self.ORE_status(ct, tile_pos)
        # Decrease ignore
        for ore in self.Ores.values():
            if ore.ignore > 0:
                ore.ignore -= 1

    def ORE_status(self, ct: Controller, ore_pos: Position):
        """Update an ore in vision"""
        if not ct.is_in_vision(ore_pos): return

        env = ct.get_tile_env(ore_pos)
        if env not in ORE_ENV: return

        mval = self.GET_marker_val(ct, ore_pos)
        harv = self.CHECK_harvester(ct, ore_pos)
        barr = self.CHECK_barrier(ct, ore_pos)

        linked_core = self.CHECK_ore_linked_core(ct, ore_pos)

        key = (ore_pos.x, ore_pos.y)
        # OLD
        if key in self.Ores:
            ore = self.Ores[key]

            ore.mark, ore.barr = mval, barr
            if not harv is None: ore.harv = harv
            if not linked_core is None: ore.linked_core = linked_core
        # NEW
        else:
            ore = OreInfo(ore_pos, env)
            ore.mark, ore.barr = mval, barr
            if not harv is None: ore.harv = harv
            if not linked_core is None: ore.linked_core = linked_core

            ore.ignore = 0

            self.Ores[key] = ore

    def ORE_ignore(self, ore_pos: Position, ignore_turn: int):
        """Ignore an ore position for ignore_turn turns"""
        key = (ore_pos.x, ore_pos.y)
        if key in self.Ores:
            self.Ores[key].ignore = ignore_turn

    def ORE_debug(self):
        """Print all ores status for debug purpose"""
        print("\n=== ORE STAT ===")
        for ore in self.Ores.values():
            print(ore)
            print("---------------")
    #endregion
    
    #region ----- UPDATE func -----
    def UPD_round_turn(self, ct: Controller):
        """Update info about global round and local turn count"""
        self.Cur_Round = ct.get_current_round()
        self.Turn_Count = self.Turn_Count + 1
    #endregion

    #region ----- IS func -----
    def IS_in_map(self, pos: Position):
        """Check if a position is located in map"""
        if pos.x >= 0 and pos.x < self.MAP_WIDTH:
            if pos.y >= 0 and pos.y < self.MAP_HEIGHT:
                return True
        return False

    #endregion

    #region ----- GET func -----
    def GET_step(self, pos_a: Position, pos_b: Position):
        """Get Manhattan distance between A and B (sum of dx + dy)"""
        return abs(pos_a.x - pos_b.x) + abs(pos_a.y - pos_b.y)
    
    def GET_ally_core_pos_id(self, ct: Controller):
        """Get our team core position & ID (vision only)\n
        Return Position(-1, -1), -1 if fails"""
        if self.CORE_POS != Position(-1, -1): return self.CORE_POS, self.CORE_ID

        nearby_building = ct.get_nearby_buildings()
        for id in nearby_building:
            if ct.get_team(id) != ct.get_team(): continue
            if ct.get_entity_type(id) == EntityType.CORE:
                return ct.get_position(id), id
        return Position(-1, -1), -1
    
    def GET_tile_building(self, ct: Controller, tile_pos: Position):
        """Get the tile building TYPE & TEAM\n
           If out of vision / found nothing -> return EntityType.MARKER, MY_TEAM"""
        none = tuple[EntityType.MARKER, self.MY_TEAM]
        if not self.IS_in_map(tile_pos): return none
        if not ct.is_in_vision(tile_pos): return none

        ID = ct.get_tile_building_id(tile_pos)
        if ID is None: return none
        return ct.get_entity_type(ID), ct.get_team(ID)
        
    def GET_marker_val(self, ct: Controller, tile_pos: Position):
        """Get the value of the marker placed on a position\n
           If there is no marker / out of vision / enemy -> -1"""
        if not ct.is_in_vision(tile_pos): return -1

        ID = ct.get_tile_building_id(tile_pos)
        if ID is None: return -1
        if ct.get_entity_type(ID) == EntityType.MARKER:
            if ct.get_team(ID) == self.MY_TEAM:
                return ct.get_marker_value(ID)
        return -1
    
    #endregion

    #region ----- CHECK func -----
    def CHECK_harvester(self, ct: Controller, tile_pos: Position):
        """Check if a harvester is placed on a position\n
           Return 0 = None | 1 = Friendly | 2 = Enemy\n
           If out of vision, return 0"""
        if not ct.is_in_vision(tile_pos): return 0

        ID = ct.get_tile_building_id(tile_pos)
        if ID is None: return 0
        if ct.get_entity_type(ID) == EntityType.HARVESTER:
            if ct.get_team(ID) == self.MY_TEAM:
                return 1
            else:
                return 2
        return 0

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
            if etype in TURRET_TYPE:
                epos = ct.get_position(ent_id)
                cur_dis = my_pos.distance_squared(epos)
                if cur_dis < min_dis:
                    min_dis = cur_dis
                    turr_pos = epos
        return turr_pos

    def CHECK_ore_protected(self, ct: Controller, ore_pos: Position):
        """Check if the ore in vision is protected 4 sides\n
           Also return False if 13 <= dis_to_ore <= vision, None if out of vision"""
        if ore_pos == Position(-1, -1): return True
        if not ct.is_in_vision(ore_pos): return None

        # Ore check
        if not ct.is_tile_passable(ore_pos): return True 
        if ore_pos.distance_squared(ct.get_position()) > 13: return False	

        # Side check
        dxy = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        side_cnt = 0
        for dx, dy in dxy:
            check_pos = Position(ore_pos.x + dx, ore_pos.y + dy)
            if not self.IS_in_map(check_pos): continue

            # Wall
            if ct.get_tile_env(check_pos) != Environment.EMPTY:
                side_cnt += 1
                continue

            # Building
            ID = ct.get_tile_building_id(check_pos)
            if ID is None: continue

            type = ct.get_entity_type(ID)
            if ct.get_team(ID) != self.MY_TEAM:
                if type != EntityType.HARVESTER:
                    continue
            elif type == EntityType.ROAD: continue
            elif type == EntityType.MARKER: continue
            elif type == EntityType.BUILDER_BOT: continue

            side_cnt += 1
        return (side_cnt == 4)
    
    def CHECK_ore_linked_core(self, ct: Controller, ore_pos: Position):
        """Check if an ore is linked back core, depends on conveyors nearby\n
           Return None if dis > 13"""
        # Side check
        dxy = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        for dx, dy in dxy:
            check_pos = Position(ore_pos.x + dx, ore_pos.y + dy)
            if not self.IS_in_map(check_pos): continue
            if not ct.is_in_vision(check_pos): continue

            # Building
            ID = ct.get_tile_building_id(check_pos)
            if ID is None: continue
            type = ct.get_entity_type(ID)
            if ct.get_team(ID) == self.MY_TEAM:
                if type in CONVEY_TYPE:
                    return True
                
        # Decide
        if ore_pos.distance_squared(ct.get_position()) > 13: return None
        return False
    #endregion
    
    #region ----- DEBUG func -----
    #endregion

ctx = BldContext()