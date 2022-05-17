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
        ...