import time
import random
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List
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
    
    def run_simulation(self, iterations: int):
        """Run multiple simulation rounds and collect data"""
        self.results = []
        
        for _ in range(iterations):
            # Reset positions
            self.seeker.position = Vector2(0.5, 0.5)  # Center of starting cell
            self.hider.position = Vector2(self.grid.size-0.5, self.grid.size-0.5)  # Center of opposite corner
            
            # Run the simulation
            start_time = time.time()
            result = self._run_single_round()
            result['time'] = time.time() - start_time
            self.results.append(result)
        
        self.generate_report()
    
    def _run_single_round(self) -> Dict:
        """Run a single simulation round and return metrics"""
        max_steps = 1000  # Prevent infinite loops
        steps = 0
        path_length = 0
        last_position = None
        
        while steps < max_steps:
            steps += 1
            
            # Update NPCs
            self.seeker.update(0.1)  # Fixed small time step for consistency
            self.hider.update(0.1)
            
            # Track path length
            current_pos = self.seeker.position.to_grid_pos()
            if last_position != current_pos:
                path_length += 1
                last_position = current_pos
            
            # Check if caught
            if self._is_caught():
                return {
                    'success': True,
                    'steps': steps,
                    'path_length': path_length,
                    'final_distance': self._get_distance()
                }
        
        return {
            'success': False,
            'steps': steps,
            'path_length': path_length,
            'final_distance': self._get_distance()
        }
    
    def _is_caught(self) -> bool:
        """Check if hider is caught (same position or adjacent)"""
        seeker_pos = self.seeker.position.to_grid_pos()
        hider_pos = self.hider.position.to_grid_pos()
        return (abs(seeker_pos[0] - hider_pos[0]) <= 1 and 
                abs(seeker_pos[1] - hider_pos[1]) <= 1)
    
    def _get_distance(self) -> int:
        """Get Manhattan distance between seeker and hider"""
        seeker_pos = self.seeker.position.to_grid_pos()
        hider_pos = self.hider.position.to_grid_pos()
        return abs(seeker_pos[0] - hider_pos[0]) + abs(seeker_pos[1] - hider_pos[1])
    
    def generate_report(self):
        """Generate and display performance report"""
        if not self.results:
            return
        
        df = pd.DataFrame(self.results)
        
        # Success rate
        success_rate = df['success'].mean() * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Average metrics
        print(f"Average Steps: {df['steps'].mean():.1f}")
        print(f"Average Path Length: {df['path_length'].mean():.1f}")
        print(f"Average Time: {df['time'].mean():.3f}s")
        
        # Plot results
        plt.figure(figsize=(12, 4))
        
        # Success rate plot
        plt.subplot(1, 3, 1)
        df['success'].value_counts().plot(kind='bar')
        plt.title('Success Rate')
        plt.xticks([0, 1], ['Failed', 'Success'], rotation=0)
        
        # Steps distribution plot
        plt.subplot(1, 3, 2)
        df['steps'].plot(kind='hist', bins=20)
        plt.title('Steps Distribution')
        
        # Path length vs success
        plt.subplot(1, 3, 3)
        df.boxplot(column='path_length', by='success')
        plt.title('Path Length by Outcome')
        
        plt.tight_layout()
        plt.show()