import os
import time
class RANDOM():
    def __init__(self):
        self.mod = 2**31 - 1
    def gen(self,seed : int = int(os.getpid() + time.time()) ) -> int:
        seed ^= (seed << 13)
        seed ^= (seed >> 17)
        seed ^= (seed << 5)
        return seed%self.mod
rand = RANDOM()