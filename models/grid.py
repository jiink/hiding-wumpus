from typing import List, Optional, Tuple
import pygame

from constants import *
from models.grid_node import GridNode

# A grid has a bunch of gridnodes and draws them on the screen and all that.
# "Tile", "cell", and "gridnode" all refer to the same thing, sorry.
class Grid:
    def __init__(self, size: int, display_size: int):
        self.size = size
        self.display_size = display_size
        self.tile_size = display_size / size
        # Fill the grid with empty gridnodes
        self.nodes: List[List[GridNode]] = []
        for y in range(size):
            row = []
            for x in range(size):
                row.append(GridNode(x, y))
            self.nodes.append(row)
    
    # true if cell coordinates given are within the grid.
    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size
    
    # Returns Optional[GridNode], which means it could be a GridNode,
    # or it could be None (which is like null)
    def get_node(self, x: int, y: int) -> Optional[GridNode]:
        if not self.is_valid_position(x, y):
            return None
        return self.nodes[y][x]
    
    # Changes the tile at the given cell-coordinates to
    # be a wall or not a wall.
    # Returns true if successful, false if it couldn't be done.
    def toggle_wall(self, x: int, y: int) -> bool:
        if not self.is_valid_position(x, y):
            return False
        node = self.nodes[y][x]
        node.is_wall = not node.is_wall
        return True
    
    # Returns the nodes surrounding the given node. 
    def get_neighbors(self, node: GridNode) -> List[GridNode]:
        neighbors = []
        # Including diagonals (8 directions)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = node.x + dx, node.y + dy
                if self.is_valid_position(nx, ny):
                    neighbor = self.nodes[ny][nx]
                    if not neighbor.is_wall:
                        neighbors.append(neighbor)
        return neighbors

    # Converts a world-space or tile coordinate to where it is on the screen.
    def grid_to_screen(self, grid_x: float, grid_y: float) -> Tuple[float, float]:
        screen_x = grid_x * self.tile_size
        screen_y = grid_y * self.tile_size + UI_HEIGHT
        return (screen_x, screen_y)

    # Converts screen coordinates to a coordinate of a tile on the grid.
    # Good for finding out where you clicked or something.
    def screen_to_grid(self, screen_x: float, screen_y: float) -> Tuple[int, int]:
        grid_x = int(screen_x / self.tile_size)
        grid_y = int((screen_y - UI_HEIGHT) / self.tile_size)
        # Clamp to be within grid
        grid_x = max(0, min(grid_x, self.size - 1))
        grid_y = max(0, min(grid_y, self.size - 1))
        return (grid_x, grid_y)
    
    # In pygame, a "surface" is like a render texture in other frameworks/engines.
    def draw(self, surface: pygame.Surface):
        # tiles
        for y in range(self.size):
            for x in range(self.size):
                node = self.nodes[y][x]
                color = WALL_TILE_COLOR if node.is_wall else EMPTY_TILE_COLOR
                rect = pygame.Rect(
                    *self.grid_to_screen(x, y),
                    self.tile_size,
                    self.tile_size
                )
                pygame.draw.rect(surface, color, rect)
        # grid lines
        for i in range(self.size + 1):
            pos = i * self.tile_size
            pygame.draw.line(
                surface, GRID_LINE_COLOR,
                (0, pos + UI_HEIGHT),
                (self.display_size, pos + UI_HEIGHT)
            )
            pygame.draw.line(
                surface, GRID_LINE_COLOR,
                (pos, UI_HEIGHT),
                (pos, self.display_size + UI_HEIGHT)
            )
