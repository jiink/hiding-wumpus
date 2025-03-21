import random
from core.npc import Npc

class HiderA(Npc):
    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.
    def think(self):
        
        # if it's already in an unseen area, don't do anything
        here = self.grid.get_node(*self.position.to_grid_pos())
        if here is not None and not here.seen_by_seeker:
            self.emit_thought("I'm fine.")
            return
        self.emit_thought("Gotta run!")
        candidate_pos = []
        for node in self.grid.all_nodes():
            if not node.seen_by_seeker:
                candidate_pos.append(node.get_position())
        if len(candidate_pos) > 0:
            # pick a random spot 
            new_pos = random.choice(candidate_pos)
            self.set_target(*new_pos)
