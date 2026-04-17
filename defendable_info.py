from cambc import Environment, Position

class DefendableInfo:
    __slots__ = ("pos", "score", "type", "ignore")

    def __init__(self, pos, score):
        self.pos = pos
        self.score = score