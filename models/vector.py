# This class is LLM generated

import math
from typing import Tuple

class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def distance_to(self, other) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalized(self):
        length = self.length()
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    def to_grid_pos(self) -> Tuple[int, int]:
        return (int(self.x), int(self.y))