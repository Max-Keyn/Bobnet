from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.data import Difficulty, Race  # difficulty for bots, race for the 1 of 3 races
from sc2.main import run_game  # function that facilitates actually running the agents in games
from sc2.player import Bot, Computer  #wrapper for whether or not the agent is one of your bots, or a "computer" player
from sc2 import maps  # maps method for loading maps to play in.
from sc2.ids.unit_typeid import UnitTypeId
import numpy as np
import math
import random
import cv2

class Bob(BotAI): # inhereits from BotAI (part of BurnySC2)
    async def on_step(self, iteration: int): # on_step is a method that is called every step of the game.
        map = self.render_map()
        self.print_map(map)

    # Print Map with opencv
    def print_map(self, map):
        cv2.imshow('Map', cv2.flip(cv2.resize(map,None,fx=4, fy=4, interpolation=cv2.INTER_NEAREST), 0))
        cv2.waitKey(1)

    # Render Map
    def render_map(self):
        map = np.zeros((self.game_info.map_size[0], self.game_info.map_size[1], 4), dtype=np.uint8)
        # map is a numpy array of size (224, 224, 4)
        # add the terrain heightmap to the map
        map[:, :, 3] = self._game_info.terrain_height.data_numpy[:,:]
        
        # draw minerals
        for mineral in self.mineral_field:
            pos = mineral.position
            fraction = mineral.mineral_contents / 1800
            if mineral.is_visible:
                c = [175, 255, 255]
                c = [int(fraction*i) for i in c]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                c =  [20,75,50]  
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c  

        # draw the enemy start location:
        for enemy_start_location in self.enemy_start_locations:
            pos = enemy_start_location
            c = [0, 0, 255]
            c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw the enemy units:
        # Todo draw enemy units per type
        for enemy_unit in self.enemy_units:
            pos = enemy_unit.position
            c = [100, 0, 255]
            
            # get unit health fraction:
            fraction = enemy_unit.health / enemy_unit.health_max if enemy_unit.health_max > 0 else 0.0001
            c = [int(fraction*i) for i in c]
            c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c
        
        # draw the enemy structures:
        for enemy_structure in self.enemy_structures:
            pos = enemy_structure.position
            c = [0, 100, 255]
            # get structure health fraction:
            fraction = enemy_structure.health / enemy_structure.health_max if enemy_structure.health_max > 0 else 0.0001
            c = [int(fraction*i) for i in c]
            c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw our structures:
        for our_structure in self.structures:
            # if it's a nexus:
            if our_structure.type_id == UnitTypeId.NEXUS:
                pos = our_structure.position
                c = [255, 255, 175]
                # get structure health fraction:
                fraction = our_structure.health / our_structure.health_max if our_structure.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                pos = our_structure.position
                c = [0, 255, 175]
                # get structure health fraction:
                fraction = our_structure.health / our_structure.health_max if our_structure.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c

         # draw the vespene geysers:
        for vespene in self.vespene_geyser:
            # draw these after buildings, since assimilators go over them. 
            pos = vespene.position
            
            fraction = vespene.vespene_contents / 2250

            if vespene.is_visible:
                c = [255, 175, 255]
                c = [int(fraction*i) for i in c]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                c = [50,20,75]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c

           # draw our units:
        for our_unit in self.units:
            # if it is a voidray:
            # Todo add all unit types
            if our_unit.type_id == UnitTypeId.VOIDRAY:
                pos = our_unit.position
                c = [255, 75 , 75]
                # get health:
                fraction = our_unit.health / our_unit.health_max if our_unit.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                pos = our_unit.position
                c = [175, 255, 0]
                # get health:
                fraction = our_unit.health / our_unit.health_max if our_unit.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append( map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
        return map
