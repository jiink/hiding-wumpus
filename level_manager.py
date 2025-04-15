import json
import os
from models.grid import Grid
from models.vector import Vector2

class LevelManager:
    SAVE_DIR = "saved_levels"  # Folder to store levels

    @staticmethod
    def ensure_save_dir():
        """Create the save directory if it doesn't exist."""
        if not os.path.exists(LevelManager.SAVE_DIR):
            os.makedirs(LevelManager.SAVE_DIR)

    @staticmethod
    def save_level(grid: Grid, npc, vector_class, level_name: str):
        """Save the level with a custom name."""
        LevelManager.ensure_save_dir()
        filename = os.path.join(LevelManager.SAVE_DIR, f"{level_name}.json")
        
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
        print(f"Level saved as: {filename}")

    @staticmethod
    def load_level(grid: Grid, npc, vector_class, level_name: str):
        """Load a level by name."""
        filename = os.path.join(LevelManager.SAVE_DIR, f"{level_name}.json")
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)
            
            # Reset grid
            for y in range(grid.size):
                for x in range(grid.size):
                    grid.get_node(x, y).is_wall = False
            
            # Load walls
            for x, y in level_data["walls"]:
                grid.get_node(x, y).is_wall = True
            
            # Mark tiles as changed
            grid.tiles_changed = True

            # Load NPC position
            npc.position = vector_class(*level_data["npc_position"])
            
            # Load target (if exists)
            if level_data["target_position"]:
                npc.target = vector_class(*level_data["target_position"])
                npc.update_path()
            else:
                npc.target = None
                npc.path = []
            
            print(f"Level loaded: {filename}")
            return True
        except FileNotFoundError:
            print(f"Error: Level '{level_name}' not found.")
            return False

    @staticmethod
    def list_saved_levels():
        """Returns a list of saved level names without .json extension"""
        LevelManager.ensure_save_dir()
        try:
            return [f[:-5] for f in os.listdir(LevelManager.SAVE_DIR) 
                if f.endswith('.json') and os.path.isfile(os.path.join(LevelManager.SAVE_DIR, f))]
        except Exception:
            return []