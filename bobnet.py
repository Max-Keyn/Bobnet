from re import M
from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.ids.unit_typeid import UnitTypeId
from sc2.data import Result
import numpy as np
import math
import cv2
import random


class Bob(BotAI):  # inhereits from BotAI (part of BurnySC2)
    def __init__(self, in_queue, out_queue):
        super(Bob, self).__init__()

        self.in_queue = in_queue
        self.out_queue = out_queue

    async def on_start(self):
        # Do things here before the game starts
        print("Game started")

    # on_step is a method that is called every step of the game.
    async def on_step(self, iteration: int):
        action = self.in_queue.get()
        '''
        0: expand (ie: move to next spot, or build to 16 (minerals)+3 assemblers+3)
        1: build stargate (or up to one) (evenly)
        2: build voidray (evenly)
        3: send scout (evenly/random/closest to enemy?)
        4: attack (known buildings, units, then enemy base, just go in logical order.)
        5: voidray flee (back to base)
        '''
        if action == 0:
            await self.expand()
        elif action == 1:
            await self.build_stargate()
        elif action == 2:
            await self.build_voidray()
        elif action == 3 :
            await self.send_scout(iteration)
        elif action == 4:
            await self.attack()
        elif action == 5:
            await self.flee_to_base()

        await self.distribute_workers() # put idle workers back to work

        m = self.render_map()
        # self.print_map(m)
        reward = self.calculate_reward()
        
        res = {}
        res["map"] = m
        res["reward"] = reward
        res["done"] = False

        self.out_queue.put(res)

    def calculate_reward(self):
        reward = 0
        try:
            attack_count = 0
            # iterate through our void rays:
            for voidray in self.units(UnitTypeId.VOIDRAY):
                # if voidray is attacking and is in range of enemy unit:
                if voidray.is_attacking and voidray.target_in_range:
                    if self.enemy_units.closer_than(8, voidray) or self.enemy_structures.closer_than(8, voidray):
                        # reward += 0.005 # original was 0.005, decent results, but let's 3x it. 
                        reward += 0.015  
                        attack_count += 1

        except Exception as e:
            print("reward",e)
            reward = 0
        return reward

    def default_on_step_callback(self, iteration: int):
        print(f"{iteration}, n_workers: {self.workers.amount}, n_idle_workers: {self.workers.idle.amount},",
              f"minerals: {self.minerals}, gas: {self.vespene}, cannons: {self.structures(UnitTypeId.PHOTONCANNON).amount},",
              f"pylons: {self.structures(UnitTypeId.PYLON).amount}, nexus: {self.structures(UnitTypeId.NEXUS).amount}",
              f"gateways: {self.structures(UnitTypeId.GATEWAY).amount}, cybernetics cores: {self.structures(UnitTypeId.CYBERNETICSCORE).amount}",
              f"stargates: {self.structures(UnitTypeId.STARGATE).amount}, voidrays: {self.units(UnitTypeId.VOIDRAY).amount}, supply: {self.supply_used}/{self.supply_cap}")

    async def expand(self):
        try:
            found_something = False
            if self.supply_left < 4:
                # build pylons.
                if self.already_pending(UnitTypeId.PYLON) == 0:
                    if self.can_afford(UnitTypeId.PYLON):
                        await self.build(UnitTypeId.PYLON, near=random.choice(self.townhalls))
                        found_something = True

            if not found_something:

                for nexus in self.townhalls:
                    # get worker count for this nexus:
                    worker_count = len(self.workers.closer_than(10, nexus))
                    if worker_count < 22:  # 16+3+3
                        if nexus.is_idle and self.can_afford(UnitTypeId.PROBE):
                            nexus.train(UnitTypeId.PROBE)
                            found_something = True

                    # have we built enough assimilators?
                    # find vespene geysers
                    for geyser in self.vespene_geyser.closer_than(10, nexus):
                        # build assimilator if there isn't one already:
                        if not self.can_afford(UnitTypeId.ASSIMILATOR):
                            break
                        if not self.structures(UnitTypeId.ASSIMILATOR).closer_than(2.0, geyser).exists:
                            await self.build(UnitTypeId.ASSIMILATOR, geyser)
                            found_something = True

            if not found_something:
                if self.already_pending(UnitTypeId.NEXUS) == 0 and self.can_afford(UnitTypeId.NEXUS):
                    await self.expand_now()

        except Exception as e:
            print(e)

    async def build_stargate(self):
        try:
            # iterate thru all nexus and see if these buildings are close
            for nexus in self.townhalls:
                # is there is not a gateway close:
                if not self.structures(UnitTypeId.GATEWAY).closer_than(10, nexus).exists:
                    # if we can afford it:
                    if self.can_afford(UnitTypeId.GATEWAY) and self.already_pending(UnitTypeId.GATEWAY) == 0:
                        # build gateway
                        await self.build(UnitTypeId.GATEWAY, near=nexus)

                # if the is not a cybernetics core close:
                if not self.structures(UnitTypeId.CYBERNETICSCORE).closer_than(10, nexus).exists:
                    # if we can afford it:
                    if self.can_afford(UnitTypeId.CYBERNETICSCORE) and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0:
                        # build cybernetics core
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=nexus)

                # if there is not a stargate close:
                if not self.structures(UnitTypeId.STARGATE).closer_than(10, nexus).exists:
                    # if we can afford it:
                    if self.can_afford(UnitTypeId.STARGATE) and self.already_pending(UnitTypeId.STARGATE) == 0:
                        # build stargate
                        await self.build(UnitTypeId.STARGATE, near=nexus)

        except Exception as e:
            print(e)

    async def build_voidray(self):
        try:
            if self.can_afford(UnitTypeId.VOIDRAY):
                for sg in self.structures(UnitTypeId.STARGATE).ready.idle:
                    if self.can_afford(UnitTypeId.VOIDRAY):
                        sg.train(UnitTypeId.VOIDRAY)

        except Exception as e:
            print(e)

    async def send_scout(self, iteration):
        # are there any idle probes:
        try:
            self.last_sent
        except:
            self.last_sent = 0

        # if self.last_sent doesnt exist yet:
        if (iteration - self.last_sent) > 200:
            try:
                if self.units(UnitTypeId.PROBE).idle.exists:
                    # pick one of these randomly:
                    probe = random.choice(self.units(UnitTypeId.PROBE).idle)
                else:
                    probe = random.choice(self.units(UnitTypeId.PROBE))
                # send probe towards enemy base:
                probe.attack(self.enemy_start_locations[0])
                self.last_sent = iteration

            except Exception as e:
                pass

    async def attack(self):
        try:
            # take all void rays and attack!
            for voidray in self.units(UnitTypeId.VOIDRAY).idle:
                # repair low Void Rays:
                if voidray.health_percentage < 0.5:
                    voidray.attack(self.start_location)

                # if we can attack:
                elif self.enemy_units.closer_than(10, voidray):
                    # attack!
                    voidray.attack(random.choice(
                        self.enemy_units.closer_than(10, voidray)))
                # if we can attack:
                elif self.enemy_structures.closer_than(10, voidray):
                    # attack!
                    voidray.attack(random.choice(
                        self.enemy_structures.closer_than(10, voidray)))
                # any enemy units:
                elif self.enemy_units:
                    # attack!
                    voidray.attack(random.choice(self.enemy_units))
                # any enemy structures:
                elif self.enemy_structures:
                    # attack!
                    voidray.attack(random.choice(self.enemy_structures))
                # if we can attack:
                elif self.enemy_start_locations:
                    # attack!
                    voidray.attack(self.enemy_start_locations[0])

        except Exception as e:
            print(e)

    async def flee_to_base(self):
        if self.units(UnitTypeId.VOIDRAY).amount > 0:
            for vr in self.units(UnitTypeId.VOIDRAY):
                vr.attack(self.start_location)

    # def set_on_step_callback(self,env, callback):
    #     self.env = envW
    #     self.on_step_callback = callback

    def on_end(self, result):
        res = {}
        res["done"] = True
        if result.value ==  Result.Victory:
            res["reward"] = 500
        else:
            res["reward"] = -500
        m = self.render_map()
        res["map"] = m
        self.out_queue.put(res)
        print("Game ended.")
        # Do things here after the game ends

    # Print Map with opencv
    def print_map(self, map):
        cv2.imshow('Map', cv2.flip(cv2.resize(map, None, fx=4,
                   fy=4, interpolation=cv2.INTER_NEAREST), 0))
        cv2.waitKey(1)

    # Render Map
    def render_map(self):
        map = np.zeros(
            (self.game_info.map_size[0], self.game_info.map_size[1], 4), dtype=np.uint8)
        # map is a numpy array of size (224, 224, 4)
        # add the terrain heightmap to the map
        map[:, :, 3] = self._game_info.terrain_height.data_numpy[:, :]

        # draw minerals
        for mineral in self.mineral_field:
            pos = mineral.position
            fraction = mineral.mineral_contents / 1800
            if mineral.is_visible:
                c = [175, 255, 255]
                c = [int(fraction*i) for i in c]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                c = [20, 75, 50]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw the enemy start location:
        for enemy_start_location in self.enemy_start_locations:
            pos = enemy_start_location
            c = [0, 0, 255]
            c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw the enemy units:
        # Todo draw enemy units per type
        for enemy_unit in self.enemy_units:
            pos = enemy_unit.position
            c = [100, 0, 255]

            # get unit health fraction:
            fraction = enemy_unit.health / \
                enemy_unit.health_max if enemy_unit.health_max > 0 else 0.0001
            c = [int(fraction*i) for i in c]
            c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw the enemy structures:
        for enemy_structure in self.enemy_structures:
            pos = enemy_structure.position
            c = [0, 100, 255]
            # get structure health fraction:
            fraction = enemy_structure.health / \
                enemy_structure.health_max if enemy_structure.health_max > 0 else 0.0001
            c = [int(fraction*i) for i in c]
            c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw our structures:
        for our_structure in self.structures:
            # if it's a nexus:
            if our_structure.type_id == UnitTypeId.NEXUS:
                pos = our_structure.position
                c = [255, 255, 175]
                # get structure health fraction:
                fraction = our_structure.health / \
                    our_structure.health_max if our_structure.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                pos = our_structure.position
                c = [0, 255, 175]
                # get structure health fraction:
                fraction = our_structure.health / \
                    our_structure.health_max if our_structure.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c

         # draw the vespene geysers:
        for vespene in self.vespene_geyser:
            # draw these after buildings, since assimilators go over them.
            pos = vespene.position

            fraction = vespene.vespene_contents / 2250

            if vespene.is_visible:
                c = [255, 175, 255]
                c = [int(fraction*i) for i in c]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                c = [50, 20, 75]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c

           # draw our units:
        for our_unit in self.units:
            # if it is a voidray:
            # Todo add all unit types
            if our_unit.type_id == UnitTypeId.VOIDRAY:
                pos = our_unit.position
                c = [255, 75, 75]
                # get health:
                fraction = our_unit.health / our_unit.health_max if our_unit.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
            else:
                pos = our_unit.position
                c = [175, 255, 0]
                # get health:
                fraction = our_unit.health / our_unit.health_max if our_unit.health_max > 0 else 0.0001
                c = [int(fraction*i) for i in c]
                c.append(map[math.ceil(pos.y)][math.ceil(pos.x)][3])
                map[math.ceil(pos.y)][math.ceil(pos.x)] = c
        return map
