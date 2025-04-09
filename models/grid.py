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

    # If you iterate over all the nodes using self.nodes, you'll need a nested
    # for loop. Alternatively, you can use this flattening to iterate with
    # one for loop
    def all_nodes(self) -> List[GridNode]:
        return [node for row in self.nodes for node in row]
    
    # Returns true if there is a solid tile between the two tile positions
    # on the grid. Used for calculating visibility.
    def is_wall_between(self, pos0: Tuple[int, int], pos1: Tuple[int, int]):
        x0, y0 = pos0
        x1, y1 = pos1
        # Really, this is just a line drawing algorithm (Bresenham's)
        # but instead of drawing pixels at each coordinate we just
        # check if the tile is solid or not
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while (x0, y0) != (x1, y1):
            node = self.get_node(x0, y0)
            if node is not None and node.is_wall:
                return True
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return False # if this func is giving trouble, check this final tile too.

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
    # `wall_ok`: When true, returns includes wall tiles as neighbors
    def get_neighbors(self, node: GridNode, wall_ok: bool = False) -> List[GridNode]:
        neighbors = []
        # Including diagonals (8 directions)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: # the center is not a neighbor
                    continue
                nx, ny = node.x + dx, node.y + dy
                if self.is_valid_position(nx, ny):
                    neighbor = self.nodes[ny][nx]
                    if not wall_ok and neighbor.is_wall:
                        continue
                    # tricky part: don't want paths to go through diagonal walls.
                    if dx != 0 and dy != 0 \
                    and self.get_node(node.x + dx, node.y) and self.get_node(node.x, node.y + dy) \
                    and self.get_node(node.x + dx, node.y).is_wall and self.get_node(node.x, node.y + dy).is_wall:
                        # _X_
                        # X X
                        # _X_
                        continue
                    neighbors.append(neighbor)
        return neighbors

    # Converts a world-space or tile coordinate to where it is on the screen.
    def grid_to_screen(self, grid_x: float, grid_y: float) -> Tuple[float, float]:
        screen_x = grid_x * self.tile_size
        screen_y = grid_y * self.tile_size + UI_HEIGHT
        return (screen_x, screen_y)
    
    # set all nodes to non-walls
    def clear(self):
        for row in self.nodes:
            for node in row:
                node.is_wall = False

    # Converts screen coordinates to a coordinate of a tile on the grid.
    # Good for finding out where you clicked or something.
    def screen_to_grid(self, screen_x: float, screen_y: float) -> Tuple[int, int]:
        grid_x = int(screen_x / self.tile_size)
        grid_y = int((screen_y - UI_HEIGHT) / self.tile_size)
        # Clamp to be within grid
        grid_x = max(0, min(grid_x, self.size - 1))
        grid_y = max(0, min(grid_y, self.size - 1))
        return (grid_x, grid_y)
    
    @staticmethod
    def add_colors(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> Tuple[int, int, int]:
        return tuple(min(c1 + c2, 255) for c1, c2 in zip(color1, color2))
    
    # In pygame, a "surface" is like a render texture in other frameworks/engines.
    # If partial is true, then tiles will either be white if in view of seeker, or 
    # black otherwise. That's meant for human seeker to not have unfair visibility.
    def draw(self, surface: pygame.Surface, partial: bool):
        # tiles
        for y in range(self.size):
            for x in range(self.size):
                node = self.nodes[y][x]
                if partial:
                    if node.seen_by_seeker:
                        color = (190, 190, 190)
                    else:
                        color = (0, 0, 0)  # Black for unseen tiles
                    if node.is_wall:
                        color = (80, 60, 190)
                else:
                    if node.is_wall:
                        color = WALL_TILE_COLOR
                    else:
                        color = EMPTY_TILE_COLOR
                    if node.seen_by_seeker:
                        color = self.add_colors(color, (0, 0, 50))
                    if node.seen_by_hider:
                        color = self.add_colors(color, (50, 0, 0))
                
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
