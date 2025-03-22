import random

import pygame
from core.npc import Npc

class HiderA(Npc):

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # this is an instance variable so we can see it 
            # drawn to the screen in think_draw()
            self.candidates = [] # (node, score)
    
    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.
    def think(self):
        # if it's already in an unseen area, don't do anything
        here = self.grid.get_node(*self.position.to_grid_pos())
        if here is not None and not here.seen_by_seeker:
            self.emit_thought("I'm fine.")
            return
        self.emit_thought("Gotta run!")
        # associate scores with nodes
        self.candidates = [] # (node, score)
        for node in self.grid.all_nodes():
            if not node.is_wall and not node.seen_by_seeker:
                # associate each candidate node with a score
                # Big part of it is how deep in the shadow it is -- that is,
                # going to a spot that's far from a visible area. I found out
                # This is an uninformed search problem called "distance transform"!
                # It can be done with BFS. A naive way would be to find the distance from
                # every shadowed node to the nearest seen node by doing a BFS on each 
                # shadowed node, but a better way is to do a BFS from every seen node simulatneously.
                # This is not as hard as it sounds, as all it means is that I would make the 
                # queue start off not with nothing, but with all the nodes seen by the seeker.
                shadow_depth_score = self.grid.distance_from_seen(node)
                distance_score = self.position.distance_to(node.get_position()) / self.grid.size
                self.candidates.append((node, shadow_depth_score + distance_score))
        
        # want to pick the candidate with the lowest score
        self.candidates.sort(key=lambda x: x[1], reverse=False) # ascending
        # get the lowest score candidate
        
        if len(self.candidates) > 0:
            best_candidate = self.candidates[0][0]
            self.set_target(*best_candidate.get_position())

    # for debug visuals for seeing what it's thinking
    def think_draw(self, surface: pygame.Surface):
        for node, score in self.candidates:
            pos = node.get_position()
            screen_pos = self.grid.grid_to_screen(pos[0] + 0.5, pos[1] + 0.5)
            radius = int(score * 20)  # Scale the score to a radius between 0 and 20
            pygame.draw.circle(surface, (200, 200, 200), screen_pos, radius)