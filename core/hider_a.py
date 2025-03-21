import random
from core.npc import Npc


class HiderA(Npc):
    def think(self):
        print("Hider A thinking")
        # Random spot
        while True:
            x = random.randint(0, self.grid.size - 1)
            y = random.randint(0, self.grid.size - 1)
            if self.set_target(x, y):
                break
