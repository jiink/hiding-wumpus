import time
import csv
import os
import random
from typing import Dict, List
from constants import FPS
from models.grid import Grid
from models.vector import Vector2
from core.pathfinder import Pathfinder
from core.seeker import Seeker
from core.hider import Hider

class SimulationManager:
    def __init__(self, grid: Grid, pathfinder: Pathfinder, seeker: Seeker, hider: Hider):
        self.grid = grid
        self.pathfinder = pathfinder
        self.seeker = seeker
        self.hider = hider
        self.results = []
    
    def reset_game(self) -> None:
        self.hider.reset()
        self.seeker.reset()
        # Tell the seeker to freeze for a moment to give the hider a chance to run away.
        self.seeker.freeze()

    def run_simulation(self, iterations: int, level_name: str, hider_name: str):
        # Run multiple simulation rounds and collect data
        self.results = []

        for round_num in range(iterations):
            self.reset_game()
            # Run the simulation
            print(f"Round {round_num} begin!")
            start_time = time.time()
            result = self._run_single_round()
            result['sim_time'] = time.time() - start_time
            self.results.append(result)

        self.generate_report(level_name, hider_name, iterations)
    
    def _is_caught(self) -> bool:
        if self.seeker.is_frozen():
            return False
        # Check if hider is caught.
        seeker_pos = self.seeker.position.to_grid_pos()
        hider_pos = self.hider.position.to_grid_pos()
        return (abs(seeker_pos[0] - hider_pos[0]) == 0 and 
                abs(seeker_pos[1] - hider_pos[1]) == 0)
    
    def _run_single_round(self) -> Dict:
        # Run a single simulation round and return metrics
        # If the hider can stay away for this many in-game seconds
        # (not real seconds), it wins.
        max_game_time_s = 5 * 60
        steps = 0
        path_length = 0
        last_position = None
        timestep = FPS / 1000 # in in-game seconds
        max_steps = max_game_time_s / timestep
        num_steps_exposed = 0 # Keeping track of how long the hider has been exposed for.
        self.grid.nodes_gotten = 0
        was_caught = False
        while steps < max_steps:
            steps += 1
            
            # Update NPCs
            self.seeker.update(timestep)  # Fixed small time step for consistency
            self.hider.update(timestep)
            
            # Track path length
            current_pos = self.seeker.position.to_grid_pos()
            if last_position != current_pos:
                path_length += 1
                last_position = current_pos
            if self.grid.is_wall_between(self.seeker.position, self.hider.position):
                num_steps_exposed += 1
            
            # Check if caught
            if self._is_caught():
                was_caught = True
                break
        
        return {
            'caught': was_caught,
            'steps': steps,
            'time_elapsed': steps / FPS,
            'time_exposed': num_steps_exposed / FPS,
            'nodes_gotten': self.grid.nodes_gotten,
            'path_length': path_length,
            'final_distance': self._get_distance()
        }
    
    def _get_distance(self) -> int:
        # Get Manhattan distance between seeker and hider
        seeker_pos = self.seeker.position.to_grid_pos()
        hider_pos = self.hider.position.to_grid_pos()
        return abs(seeker_pos[0] - hider_pos[0]) + abs(seeker_pos[1] - hider_pos[1])
    
    def generate_report(self, level_name: str, hider_name: str, iterations: int) -> None:
        # Save results to CSV
        if not self.results:
            print("No results to export")
            return
        sanitized_level_name = level_name.replace(" ", "_")
        sanitized_hider_name = hider_name.replace(" ", "")

        # Construct the file name dynamically
        csv_filename = f"sim_results_{sanitized_level_name}_{sanitized_hider_name}_{iterations}.csv"

        # File path to save CSV file
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sim_folder = os.path.join(project_root, "simulation")
        file_path = os.path.join(sim_folder, csv_filename)

        # Prepare CSV file
        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
            print(f"Results saved to {os.path.abspath(file_path)}")
        except Exception as e:
            print(f"Failed to save CSV: {e}")
