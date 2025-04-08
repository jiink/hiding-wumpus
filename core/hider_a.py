from math import inf
import math
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
        self.shadow_depths: dict[GridNode, float] = {} # index by node to get depth (distance from seen)
        self.wall_distances: dict[GridNode, float] = {} # index by node to get distance
    
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
    
    # This is pretty much a copy paste from calculate_shadow_depths
    # Finds the distances between every shadowed node and the nearest node seen
    # by the seeker and stores it in self.shadow_depths
    def calculate_wall_distances(self) -> None:
        # See calculate_shadow_depths for details and comments
        que = queue.Queue()
        all_nodes = self.grid.all_nodes()
        self.wall_distances: dict[GridNode, float] = {}
        for i in range(0, len(all_nodes)):
            self.wall_distances[all_nodes[i]] = inf
        # Initialize the queue.
        for node in all_nodes:
            if node.seen_by_seeker:
                que.put(node)
                self.wall_distances[node] = 0
        dist = 1 # This will increment for every level of BFS done.
        que.put(None) # This is just a marker.
        while not que.empty():
            node = que.get()
            if node is None:
                dist += 1
                if not que.empty():
                    que.put(None) # put another layer marker
            else:
                for n in self.grid.get_neighbors(node, True):
                    if self.wall_distances[n] == inf:
                        self.wall_distances[n] = dist
                        que.put(n)

    # Returns the distance from the given node to the nearest node seen by the 
    # seeker.
    def distance_from_seen(self, node: GridNode) -> int:
        return self.shadow_depths[node]
    
    # Returns the distance from the given node to the nearest wall.
    def distance_from_wall(self, node: GridNode) -> int:
        return self.wall_distances[node]
    
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
        self.calculate_wall_distances() # Need to do this before calling distance_from_wall() later
        max_shdw_dpth = self.get_max_shadow_depth()
        # associate scores with nodes
        self.candidates.clear()
        for node in self.grid.all_nodes():
            # Only consider these kinds of nodes. If you want to increase how partially
            # observable this system is, you could add `and node.seen_by_hider` to only consider
            # nodes within line of sight of the this guy. maybe we can compare them in analysis.
            if not node.is_wall:
                # associate each candidate node with a score. lower = better
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
                # only care about hugging walls if it's in the shadow
                wall_dist_score = 1 if node.seen_by_seeker else self.distance_from_wall(node) * 0.1 
                distance_score = self.position.distance_to(node.get_position()) / self.grid.size
                # TODO: stench score
                
                # TODO: right now it does nothing if it's caught in a bad spot and there aren't any good candidates. in this case, let it flee.
                # todo: feel free to multiply each term by something to balance things out
                self.candidates[node] = shadow_depth_score + distance_score + + wall_dist_score

        # want to pick the candidate with the lowest score. If it doesn't
        # work, pick the next best, and so on.
        sorted_candidates = sorted(self.candidates.items(), key=lambda item: item[1])
        for candidate, _ in sorted_candidates:
            if self.set_target(*candidate.get_position()):
                break

    @staticmethod
    def clamp(value, min_value, max_value):
        return max(min(value, max_value), min_value)

    def draw(self, surface: pygame.Surface, debug: bool):
        # Custom drawing code
        if debug:
            # remove any +/-infs
            filtered_candidates = {node: score for node, score in self.candidates.items() if score != float('inf') and score != float('-inf')}
            # Normalize scores for color mapping
            scores = list(filtered_candidates.values())
            if len(scores) > 0:
                min_score = min(scores)
                max_score = max(scores)
                range_score = max_score - min_score
                if range_score == 0:
                    return  # avoid divide by 0
                for node, score in filtered_candidates.items():
                    pos = node.get_position()
                    screen_pos = self.grid.grid_to_screen(pos[0] + 0.5, pos[1] + 0.5)

                    # Map score to color (gradient from green to red)
                    normalized_score = (score - min_score) / range_score
                    if math.isnan(normalized_score):  # Check for NaN explicitly
                        continue
                    red = int(normalized_score * 255)
                    green = int((1 - normalized_score) * 255)
                    color = (red, green, 0)  # RGB color

                    # Draw a small square at the node's position
                    rect_size = 5  # Size of the square
                    rect = pygame.Rect(
                        screen_pos[0] - rect_size // 2,
                        screen_pos[1] - rect_size // 2,
                        rect_size,
                        rect_size
                    )
                    pygame.draw.rect(surface, color, rect)
        # Call the base class's draw method
        super().draw(surface, debug)