from math import inf
import queue
import random
from typing import List, Tuple

import pygame
from core.npc import Npc
from models.grid_node import GridNode

class HiderA(Npc):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_move = True
        # this is an instance variable so we can see it 
        # drawn to the screen in think_draw()
        self.candidates: dict[GridNode, float] = {} # index by node to get score
        self.shadow_depths: dict[GridNode, float] = {} # index by node to get depth
    
    # Finds the distances between every shadowed node and the nearest node seen
    # by the seeker and stores it in self.shadow_depths
    def calculate_shadow_depths(self) -> None:
        # this is multi-source BFS
        # good resource: https://medium.com/geekculture/multisource-bfs-for-your-faang-coding-interviews-d5177753f507
        que = queue.Queue() # could use [], but this has faster operations I heard
        all_nodes = self.grid.all_nodes()
        # Store distance from each node to a seen node. it's a dictionary!
        self.shadow_depths: dict[GridNode, float] = {} # AKA distances
        
        for i in range(0, len(all_nodes)):
            self.shadow_depths[all_nodes[i]] = inf
        # Initialize the queue. usually in BFS we would start the queue with one
        # node, but we can just start it will all the nodes. Let the queue
        # begin with all seen nodes.
        for node in all_nodes:
            if node.seen_by_seeker:
                que.put(node)
                self.shadow_depths[node] = 0
        dist = 1 # This will increment for every level of BFS done. You can 
        # also think of that as time. imagine the seen areas grow by 1 tile
        # for every 'time step', and the last shadows to be reached are the
        # deepest and take the most time to get to.
        que.put(None) # This is just a marker. Once this `None` is hit in the
        # queue, we know to increment the `dist`
        while not que.empty():
            node = que.get()
            if node is None:
                dist += 1
                if not que.empty():
                    # put another layer marker
                    que.put(None)
            else:
                for n in self.grid.get_neighbors(node):
                    if self.shadow_depths[n] == inf:
                        self.shadow_depths[n] = dist
                        que.put(n)
        # all done, now you can look in self.shadow_depths for the result

    # Returns the distance from the given node to the nearest node seen by the 
    # seeker.
    def distance_from_seen(self, node: GridNode) -> int:
        return self.shadow_depths[node]
    
    # return the maximum value from self.shadow_depths (that isn't inf)
    def get_max_shadow_depth(self) -> int:
        max_depth = 0
        for depth in self.shadow_depths.values():
            if depth < inf and depth > max_depth:
                max_depth = depth
        return max_depth

    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.        
    def think(self):
        # if it's already in an unseen area, don't do anything
        here = self.grid.get_node(*self.position.to_grid_pos())
        if here is not None and not here.seen_by_seeker:
            self.emit_thought("I'm fine.")
        else:
            self.emit_thought("Gotta run!")
        self.calculate_shadow_depths() # Need to do this before calling distance_from_seen() later
        max_shdw_dpth = self.get_max_shadow_depth()
        # associate scores with nodes
        self.candidates.clear()
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
                if max_shdw_dpth > 0:
                    shadow_depth_score = 1 - (self.distance_from_seen(node) / float(max_shdw_dpth))
                else:
                    shadow_depth_score = 0
                distance_score = self.position.distance_to(node.get_position()) / self.grid.size
                self.candidates[node] = shadow_depth_score + distance_score

        # want to pick the candidate with the lowest score
        best_candidate = min(self.candidates, key=self.candidates.get, default=None)
        if best_candidate is not None:
            self.set_target(*best_candidate.get_position())

    def draw(self, surface: pygame.Surface, debug: bool):
        # Custom drawing code
        if debug:
            for node, score in self.candidates.items():
            # Skip infinite scores and nodes that are walls or seen by seeker
                if score == float('inf') or node.is_wall or node.seen_by_seeker:
                    continue
                    
                pos = node.get_position()
                screen_pos = self.grid.grid_to_screen(pos[0] + 0.5, pos[1] + 0.5)
                
                # Ensure score is finite and within reasonable bounds
                try:
                    radius = int(min(20, max(0, score * 20)))  # Clamp between 0 and 20
                except (ValueError, OverflowError):
                    continue  # Skip if score is still problematic
                    
                # Create a translucent surface for the circle
                circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(circle_surface, (200, 200, 200, 20), (radius, radius), radius)
                surface.blit(circle_surface, (screen_pos[0] - radius, screen_pos[1] - radius))
        # Call the base class's draw method
        super().draw(surface, debug)