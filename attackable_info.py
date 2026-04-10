from cambc import Environment, Position

class AttackableInfo:
    __slots__ = ("pos", "score", "type", "ignore")

    def __init__(self, pos, score, type):
        self.pos = pos
        self.score = score
        self.type = type
        self.ignore = 0