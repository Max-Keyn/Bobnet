import gym
from gym import spaces
import numpy as np

from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from bobnet import Bob
from multiprocessing import Queue, Process




# Start game
def start_game(in_queue, out_queue):
    run_game(                                           # run_game is a function that runs the game.
        maps.get("2000AtmospheresAIE"),                 # the map we are playing on
        [Bot(Race.Protoss, Bob(in_queue,out_queue)),                      # runs our coded bot, protoss race, and we pass our bot object 
        Computer(Race.Terran, Difficulty.Hard)],        # runs a pre-made computer agent, zerg race, with a hard difficulty.
        realtime=False,                                 # When set to True, the agent is limited in how long each step can take to process.
    )

# def on_game_step(env, game_step):
#     print("on_game_step")
#     env.on_gym_step_cv.wait()
#     print("wait complete")

class Starcraft2Env(gym.Env):
    """Custom Environment that follows gym interface"""
    def __init__(self):
        super(Starcraft2Env, self).__init__()
        # Define action and observation space
        # They must be gym.spaces objects
        # Example when using discrete actions:
        self.bot_queue = Queue()
        self.env_queue = Queue()
        self.game_thread = None
        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=-1500, high=1500,
                                                shape=(224, 224, 4), dtype=np.uint8)

    def step(self, action):
        self.env_queue.put(action)
        res = self.bot_queue.get()


        # reward = 0
        # done = False
        info = {}
        
        # observation = res["map"] 
        return  res["map"], res["reward"], res["done"], info

    def reset(self):
        print("Reset the environment")
        if self.game_thread is not None:
            self.game_thread.join()

        # Start the game
        self.game_thread = Process(target=start_game, args=(self.env_queue, self.bot_queue))
        self.game_thread.start()

        map = np.zeros((224, 224, 4), dtype='uint8')
        observation = map
        reward = 0
        done = False
        info = {}
        # empty action waiting for the next one!
        # data = {"state": map, "reward": 0, "action": None, "done": False}

        # run incredibot-sct.py non-blocking:

        return observation #, reward, done, info #can't be included
