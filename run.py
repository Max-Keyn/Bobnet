import sys
import os
from psutil import Process

from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from bobnet import Bob
from multiprocessing import Queue, Process
import time

from stable_baselines3 import PPO
from sc2env import Starcraft2Env



# Start game
# def start_game(in_queue, out_queue):
#     run_game(                                           # run_game is a function that runs the game.
#         maps.get("2000AtmospheresAIE"),                 # the map we are playing on
#         [Bot(Race.Protoss, Bob(in_queue,out_queue)),                      # runs our coded bot, protoss race, and we pass our bot object 
#         Computer(Race.Terran, Difficulty.Hard)],        # runs a pre-made computer agent, zerg race, with a hard difficulty.
#         realtime=False,                                 # When set to True, the agent is limited in how long each step can take to process.
#     )

if __name__ == "__main__":

    models_dir = f"models/PPO-{int(time.time())}"
    logdir = f"logs/PPO-{int(time.time())}"

    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    # Create gym environment
    env = Starcraft2Env()

    # Create a neural network
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=logdir)
    
    # Train the network
    TIMESTEPS = 1000
    for i in range(10000000000):
        model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False,tb_log_name="PPO")
        model.save(f"{models_dir}/PPO-{TIMESTEPS*i}")
