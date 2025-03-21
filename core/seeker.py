from core.npc import Npc

class Seeker(Npc):
    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.
    def think(self):
        self.emit_thought("Seeker thinking")
        