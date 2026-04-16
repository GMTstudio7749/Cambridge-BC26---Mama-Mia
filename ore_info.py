from cambc import Environment, Position

class OreInfo:
    """Ore information class"""
    def __init__(self, pos, env):
        self.pos: Position = pos
        self.env: Environment = env

        # Building on ore
        self.mark: int = 0
        self.harv: int = 0
        self.barr: int = 0

        # Ore status
        self.ignore: int = 0
        self.linked_core: bool = False

    def IS_ore_ignore(self):
        """Check if an ore is being ignored"""
        return self.ignore > 0
    
    def __repr__(self):
        """Debug output of an ore"""
        e = "..."
        if self.env == Environment.ORE_TITANIUM: e = "TIT"
        elif self.env == Environment.ORE_AXIONITE: e = "AXI"

        m = "None"
        if self.mark > 0: m = str(self.mark)
        elif self.mark == -2: m = "Enemy"

        b = "None"
        if self.barr == 1: b = "Our team"
        elif self.barr == 2: b = "Enemy"

        return (
            f"* {e}({self.pos.x}, {self.pos.y})\n"
            f"Harv: {self.harv}\n"
            f"Mark: {m} | Barr: {b}\n"
            f"[Ignore]: {self.ignore}\n"
            f"[Core linked]: {self.linked_core}"
        )