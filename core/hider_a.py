import random
from core.npc import Npc

class HiderA(Npc):
    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.
    def __init__(self, grid, pathfinder, color, can_think=True):
        super().__init__(grid, pathfinder, color, can_think)
        self.auto_move = True
        
    def think(self):
        self.emit_thought("thinking...")
        # Random spot
        while True:
            x = random.randint(0, self.grid.size - 1)
            y = random.randint(0, self.grid.size - 1)
            if self.set_target(x, y):
                break
