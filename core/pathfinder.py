import heapq
from typing import Dict, List, Set, Tuple

import pygame
from constants import *
from models.grid import Grid
from models.grid_node import GridNode

# Handles finding a path from one position to another using the grid.
# Runs the search algorithm.
class Pathfinder:
    def __init__(self, grid: Grid):
        self.grid = grid
        self.reset_path_data()
        self.path: List[GridNode] = []
        self.visited_nodes: Set[GridNode] = set()
        self.frontier_nodes: Set[GridNode] = set()
    
    def reset_path_data(self):
        for row in self.grid.nodes:
            for node in row:
                node.reset_path_data()
        self.path = []
        self.visited_nodes = set()
        self.frontier_nodes = set()
    
    # Given a node and the goal, calculate the heuristic that node
    # should have.
    @staticmethod
    def heuristic(node: GridNode, goal: GridNode) -> float:
        # simple distance for now
        return abs(node.x - goal.x) + abs(node.y - goal.y)
    
    # This is where the search algorithm happens!
    # Finds a path from the start grid coordinates to the goal grid coordinates.
    # Returns an in-order list of nodes to travel to get to the goal.
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], extra_costs: Dict[GridNode, float] = {}) -> List[GridNode]:
        self.reset_path_data() # clean up the frontier, node values, etc.
        # The asterisk syntax here unpacks the single (x, y) coordinate
        # tuple into two arguments.
        start_node = self.grid.get_node(*start)
        goal_node = self.grid.get_node(*goal)
        if not start_node or not goal_node:
            return []
        # We're not checking if it starts in a wall since I want an NPC to get
        # out of a wall if it's in one, but never enter a wall on purpose.
        if goal_node.is_wall: 
            return []
        start_node.g_score = 0 # the cost to get here is 0 'cause we start here.
        start_node.h_score = self.heuristic(start_node, goal_node)
        open_set = [] # the list the priority queue will store things in.
        # Python provides a priority queue implementation in this "heapq" thing.
        # Since GridNodes can be compared with the < sign, the heapq will work with that
        # and use that to find which node has the highest priority.
        heapq.heappush(open_set, start_node)
        # We will need to see if a given node is already in the priority queue,
        # so to make that faster we can use a hash set for fast lookups
        # instead of iterating over the priority queue.
        # So, this open_set_hash will contain the same things as open_set.
        open_set_hash = {start_node}
        while open_set: # So long as there are things to explore...
            # Expand the node with the lowest score.
            current_node = heapq.heappop(open_set)
            open_set_hash.remove(current_node)
            self.visited_nodes.add(current_node)
            if current_node == goal_node:
                # make the path, working backwards from the end
                path = []
                while current_node:
                    path.append(current_node)
                    current_node = current_node.came_from
                # flip it
                self.path = path[::-1]
                return self.path # early return!
            for neighbor in self.grid.get_neighbors(current_node):
                # This is where path costs get added up
                move_cost = 1 + extra_costs.get(neighbor, 0)
                m_g_score = current_node.g_score + move_cost
                # i ought to better understand what is going on in
                # this part...
                if m_g_score < neighbor.g_score:
                    neighbor.came_from = current_node
                    neighbor.g_score = m_g_score
                    neighbor.h_score = self.heuristic(neighbor, goal_node)
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, neighbor)
                        open_set_hash.add(neighbor)
                        self.frontier_nodes.add(neighbor)
        return []
    
    # Draws visuals to see what the AI is doing e.g. what path it's taking.
    def draw_debug(self, surface: pygame.Surface):
        for node in self.visited_nodes:
            x, y = self.grid.grid_to_screen(node.x + 0.5, node.y + 0.5)
            pygame.draw.circle(surface, VISITED_NODE_COLOR, (x, y), self.grid.tile_size * 0.1)
        for node in self.frontier_nodes:
            x, y = self.grid.grid_to_screen(node.x + 0.5, node.y + 0.5)
            pygame.draw.circle(surface, FRONTIER_NODE_COLOR, (x, y), self.grid.tile_size * 0.1)
        # the path
        if len(self.path) > 1:
            points = [
                self.grid.grid_to_screen(node.x + 0.5, node.y + 0.5)
                for node in self.path
            ]
            pygame.draw.lines(surface, PATH_COLOR, False, points, width=3)
