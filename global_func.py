import os
import time
class RANDOM():
    def __init__(self):
        self.mod = 2**31 - 1
    def gen(self,seed : int = int(os.getpid() + time.time()), left : int = 0, right : int = 0 ) -> int:
        seed ^= (seed << 13)
        seed ^= (seed >> 17)
        seed ^= (seed << 5)
        seed %= self.mod
        if right != 0 :
            seed %= right-left+1
            seed += left
        return seed
rand = RANDOM()