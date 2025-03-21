import random
from core.npc import Npc

class HiderA(Npc):
    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.
    def think(self):
        self.emit_thought("thinking...")
        # Random spot
        while True:
            x = random.randint(0, self.grid.size - 1)
            y = random.randint(0, self.grid.size - 1)
            if self.set_target(x, y):
                break
