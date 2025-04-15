# These are nodes that the path finding algos will traverse.
from typing import Tuple

class GridNode:
    def __init__(self, x: int, y: int, is_wall: bool = False):
        self.x = x
        self.y = y
        self.is_wall = is_wall
        self.reset_path_data()
        self.seen_by_hider = True # false if obstructed by wall
        self.seen_by_seeker = True # false if obstructed by wall
        self.stench = False
    
    def reset_path_data(self):
        self.g_score = 99999 # The path cost
        self.h_score = 0 # The heuristic
        # During pathfinding, each node will know which node comes before
        # it in the path to the goal.
        self.came_from = None 

    def get_f_score(self):
        return self.g_score + self.h_score
    
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)

    # Lets you compare two GridNodes with the < symbol,
    # "lt" stands for "less than".
    def __lt__(self, other):
        return self.get_f_score() < other.get_f_score()

    # Lets you compare two GridNodes with the == symbol,
    # "eq" is short for "equals".
    def __eq__(self, other):
        if not isinstance(other, GridNode):
            return False
        return self.x == other.x and self.y == other.y
    
    # This gets used when you put a GridNode into a set or something.
    def __hash__(self):
        return hash((self.x, self.y))