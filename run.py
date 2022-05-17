import sys

from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from bobnet import Bob

# Start game
if __name__ == "__main__":
    run_game(                                           # run_game is a function that runs the game.
        maps.get("2000AtmospheresAIE"),                 # the map we are playing on
        [Bot(Race.Protoss, Bob()),                      # runs our coded bot, protoss race, and we pass our bot object 
        Computer(Race.Terran, Difficulty.VeryHard)],    # runs a pre-made computer agent, zerg race, with a hard difficulty.
        realtime=False,                                 # When set to True, the agent is limited in how long each step can take to process.
    )
