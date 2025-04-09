import pygame

import heapq as hq

from math import inf
from core.npc import Npc
from models.grid_node import GridNode
from collections import deque

class HiderB(Npc):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_move = True
        # this is an instance variable so we can see it 
        # drawn to the screen in think_draw()
        self.possible_locations: dict[GridNode, float] = {}
        self.wall_distances: dict[GridNode, float] = {}
        self.shadow_distances: dict[GridNode, float] = {}
        self.dist_to_me: dict[GridNode, float] = {}
        self.blind_spot_shadow_size: dict[GridNode, float] = {}
        self.debug_nodes: list[GridNode] = []
        self.debug_text: list[str] = []
    
    def reset_mind(self) -> None:
        self.possible_locations: dict[GridNode, float] = {}
        self.wall_distances: dict[GridNode, float] = {}
        self.shadow_distances: dict[GridNode, float] = {}
        self.dist_to_me: dict[GridNode, float] = {}
        self.blind_spot_shadow_size: dict[GridNode, float] = {}
        self.debug_nodes: list[GridNode] = []
        self.debug_text: list[str] = []

    def create_possible_locations(self) -> None:
        for node in self.grid.all_nodes():
            if not node.seen_by_seeker and not node.is_wall:
                self.possible_locations[node] = 0
            else:
                self.possible_locations[node] = -inf

    def create_wall_distances(self) -> None:
        # Get all the unseen spots that are closest to a wall
        starting_points: set[GridNode] = set()
        for node in self.grid.all_nodes():
            if self.possible_locations[node] != 0: continue
            if any(
                [n.is_wall for n in self.grid.get_neighbors(node, wall_ok=True)]
            ):
                starting_points.add(node)
        # Default values
        for node, v in self.possible_locations.items():
            self.wall_distances[node] = inf if v == 0 else -inf
        # BFS out from all the points, keeping track of the min dist to a wall, to store which nodes are closest to walls
        for node in starting_points:
            q = deque()
            seen = set()
            q.append((node, 0))
            while q:
                node, dist = q.popleft()
                if node in seen:
                    continue
                seen.add(node)
                self.wall_distances[node] = min(self.wall_distances[node], dist)
                for n in self.grid.get_neighbors(node, wall_ok=False):
                    if self.possible_locations[n] == 0 and n not in seen:
                        q.append((n, dist + 1))
        # Debug purposes (comment or remove the return to see the wall scoring)
        return
        for node, dist in self.wall_distances.items():
            if dist == -inf: continue
            self.debug_nodes.append(node)
            self.debug_text.append(str(dist))
    
    def create_shadow_distances(self) -> None:
        # Get all the unseen spots that are closest to a wall
        starting_points: set[GridNode] = set()
        for node in self.grid.all_nodes():
            if self.possible_locations[node] != 0: continue
            if any(
                [not n.is_wall and n.seen_by_seeker for n in self.grid.get_neighbors(node, wall_ok=True)]
            ):
                starting_points.add(node)
        # Default values
        for node, v in self.possible_locations.items():
            self.shadow_distances[node] = inf if v == 0 else -inf
        # BFS out from all the points, keeping track of the min dist to a wall, to store which nodes are closest to walls
        for node in starting_points:
            q = deque()
            seen = set()
            q.append((node, 0))
            while q:
                node, dist = q.popleft()
                if node in seen:
                    continue
                seen.add(node)
                self.shadow_distances[node] = min(self.shadow_distances[node], dist)
                for n in self.grid.get_neighbors(node, wall_ok=False):
                    if self.possible_locations[n] == 0 and n not in seen:
                        q.append((n, dist + 1))
        for node, dist in self.shadow_distances.items():
            # Dist == inf means that the node is not reachable, so make it -inf
            # to indicate that it is not a possible location
            if dist == inf: self.shadow_distances[node] = -inf
        # Debug purposes (comment or remove the return to see the shadow scoring)
        return
        for node, dist in self.shadow_distances.items():
            if dist == -inf: continue
            self.debug_nodes.append(node)
            self.debug_text.append(str(dist))

    def create_dist_to_me(self, pos) -> None:
        # Dijkstra out from the seeker to find dists to all nodes
        pq = []
        dists = {}
        for node in self.grid.all_nodes():
            dists[node] = inf
        dists[pos] = 0
        hq.heappush(pq, (0, pos))
        while pq:
            dist, node = hq.heappop(pq)
            if dists[node] < dist:
                continue
            for n in self.grid.get_neighbors(node, wall_ok=False):
                if dists[n] > dist + 1:
                    dists[n] = dist + 1
                    hq.heappush(pq, (dists[n], n))
        for node, v in self.possible_locations.items():
            if v == 0 and self.shadow_distances[node] != -inf:
                self.dist_to_me[node] = dists[node]
            else:
                self.dist_to_me[node] = -inf
        # Debug purposes (comment or remove the return to see the dist scoring)
        return
        for node, dist in self.dist_to_me.items():
            if dist == -inf: continue
            self.debug_nodes.append(node)
            self.debug_text.append(str(dist))

    def create_blind_spot_shadow_size(self) -> None:
        seen = {k:(v==-inf) for k,v in self.dist_to_me.items()}
        for node in self.grid.all_nodes():
            if seen[node]: continue
            q = deque()
            q.append(node)
            tempseen = set()
            while q:
                curr = q.popleft()
                if curr in tempseen: continue
                tempseen.add(curr)
                for n in self.grid.get_neighbors(curr, wall_ok=False):
                    if seen[n]: continue
                    q.append(n)
            for n in tempseen:
                seen[n] = True
                self.blind_spot_shadow_size[n] = len(tempseen)
        # Debug purposes (comment or remove the return to see the size scoring)
        return
        for node, dist in self.blind_spot_shadow_size.items():
            if dist == -inf: continue
            self.debug_nodes.append(node)
            self.debug_text.append(str(dist))

    @staticmethod
    def score_with_range(value: float, min_value: float, max_value: float) -> float:
        if max_value - min_value == 0:
            return 0
        return (value - min_value) / (max_value - min_value)

    @staticmethod
    def invert_in_range(value: float, min_value: float, max_value: float) -> float:
        return max_value - (value - min_value)

    def determine_best_location(self) -> GridNode:
        # Multiplier applied to each category for scoring
        weights = {
            "distance to walls": 3,
            "distance to shadows": 2,
            "distance to hider": 4,
            "size of blind spot": 1
        }

        possibilities: dict[GridNode, float] = {k:0 for k,v in self.shadow_distances.items() if v != -inf}

        if not possibilities.keys(): return None

        # Distance to walls calculation
        furthest_dist = max(self.wall_distances.values() or [0])
        closest_dist = 0
        for node in possibilities.keys():
            possibilities[node] += self.score_with_range(
                self.invert_in_range(
                    self.wall_distances[node],
                    closest_dist,
                    furthest_dist
                ),
                closest_dist,
                furthest_dist
            ) * weights["distance to walls"] * 10
            print(possibilities[node])
        # Distance to shadows calculation
        furthest_dist = max(self.shadow_distances.values() or [0])
        closest_dist = 0
        for node in possibilities.keys():
            possibilities[node] += self.score_with_range(
                self.shadow_distances[node],
                closest_dist,
                furthest_dist
            ) * weights["distance to shadows"] * 10
        # Distance to hider calculation
        furthest_dist = max(self.dist_to_me.values() or [0])
        closest_dist = 0
        for node in possibilities.keys():
            possibilities[node] += self.score_with_range(
                self.invert_in_range(
                    self.dist_to_me[node],
                    closest_dist,
                    furthest_dist
                ),
                closest_dist,
                furthest_dist
            ) * weights["distance to hider"] * 10
        # Size of blind spot calculation
        furthest_dist = max(self.blind_spot_shadow_size.values() or [0])
        closest_dist = 0
        for node in possibilities.keys():
            possibilities[node] += self.score_with_range(
                self.blind_spot_shadow_size[node],
                closest_dist,
                furthest_dist
            ) * weights["size of blind spot"] * 10
        return max(possibilities, key=possibilities.get)
        # Debug purposes (comment or remove the return to see the final scoring)
        for node, dist in possibilities.items():
            if dist == -inf: continue
            self.debug_nodes.append(node)
            self.debug_text.append(str(round(dist, 2)))

    def think(self):
        self.reset_mind()

        location = self.grid.get_node(*self.position.to_grid_pos())
        
        # Only stop if we are not seen by the seeker and we got where we think is best
        if not location.seen_by_seeker and location == self.best_location:
            self.emit_thought("I'm safe")
            return

        self.emit_thought("uh oh")

        # Consider if the seeker can see the hiding spot
        self.create_possible_locations() # normal grid iter
        # Consider how close the hiding spot is to a wall (closer is better)
        self.create_wall_distances() # bfs from walls into hiding spots
        # Consider how close the hiding spot is to the seekers fov
        self.create_shadow_distances() # bfs from shadows into hiding spots
        # Consider how close I am to the hiding spot
        self.create_dist_to_me(location) # dijkstra from seeker to hiding spots
        # Consider how much wiggle room the hiding spot has before seeker sees it
        self.create_blind_spot_shadow_size() # bfs all hiding spot groups

        self.best_location = self.determine_best_location()
        if self.best_location is None:
            self.emit_thought("I can't go anywhere :(")
            return
        self.set_target(*self.best_location.get_position())
    
    def draw(self, surface: pygame.Surface, debug: bool):
        if debug:
            font = pygame.font.Font(None, 15)
            text_color = (0, 0, 0)
            if not self.debug_text or not len(self.debug_text) == len(self.debug_nodes):
                self.debug_text = [""] * len(self.debug_nodes)
            for node, text in zip(self.debug_nodes, self.debug_text):
                nodepos = node.get_position()
                screenpos = self.grid.grid_to_screen(nodepos[0] + 0.5, nodepos[1] + 0.5)
                rectsize = 16
                rect = pygame.Rect(
                    screenpos[0] - rectsize // 2,
                    screenpos[1] - rectsize // 2,
                    rectsize,
                    rectsize
                )
                pygame.draw.rect(surface, (255, 255, 255), rect)
                text_surface = font.render(text, True, text_color)
                text_rect = text_surface.get_rect(center=rect.center)
                surface.blit(text_surface, text_rect)
        super().draw(surface, debug)