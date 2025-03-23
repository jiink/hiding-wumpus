import json
from models.grid import Grid
from models.vector import Vector2
class LevelManager:
    @staticmethod
    def save_level(grid: Grid, npc, vector_class, filename="level.json"):
        level_data = {
            "grid_size": grid.size,
            "walls": [],
            "npc_position": npc.position.to_tuple(),
            "target_position": npc.target.to_tuple() if npc.target else None
        }
        
        for y in range(grid.size):
            for x in range(grid.size):
                node = grid.get_node(x, y)
                if node.is_wall:
                    level_data["walls"].append((x, y))
        
        with open(filename, 'w') as f:
            json.dump(level_data, f)
    
    @staticmethod
    def load_level(grid: Grid, npc, vector_class, filename="level.json"):
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)
            
            # Reset grid
            for y in range(grid.size):
                for x in range(grid.size):
                    grid.get_node(x, y).is_wall = False
            
            # Set walls
            for x, y in level_data["walls"]:
                grid.get_node(x, y).is_wall = True
            
            # Set NPC position
            npc.position = vector_class(*level_data["npc_position"])
            
            # Set target position
            if level_data["target_position"]:
                npc.target = vector_class(*level_data["target_position"])
                npc.update_path()
            else:
                npc.target = None
                npc.path = []
            
            return True
        except FileNotFoundError:
            return False