from cambc import Environment, Position

class AttackableInfo:
    """Attackable information class"""
    def __init__(self, pos, score, type):
        self.pos: Position = pos
        self.score:int = score
        self.type: str = type
        self.ignore = 0

    def __repr__(self):
        """Debug output of an attackable"""
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
            f"* {e} ore: Pos({self.pos.x}, {self.pos.y})\n"
            f"[Ignore]: {self.ignore}\n"
            f"Mark: {m} | Harv: {self.harv} | Barr: {b}\n"
        )