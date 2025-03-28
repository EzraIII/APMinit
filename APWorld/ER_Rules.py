from BaseClasses import CollectionState
from typing import (
    Dict,
    Callable,
    TYPE_CHECKING,
    List,
    )
from worlds.generic.Rules import set_rule  # , add_rule
from . import RuleUtils
# from .Options import MinitGameOptions

if TYPE_CHECKING:
    from . import MinitWorld
else:
    MinitWorld = object


class ER_MinitRules:
    world: MinitWorld
    player: int
    darkrooms: int
    region_rules: Dict[str, Callable[[CollectionState], bool]]

    location_rules: Dict[str, Callable[[CollectionState], bool]]

    helpers: Dict[str, Callable[[CollectionState], bool]]

    def __init__(self, world: MinitWorld) -> None:
        self.world = world
        self.player = world.player
        self.darkrooms = self.world.options.darkrooms

        self.helpers = {
            "swim": lambda state: state.has("ItemSwim", self.player),
            "darkroom1": lambda state: RuleUtils.has_darkroom(self.player, state, 1, self.darkrooms),
            "darkroom2": lambda state: RuleUtils.has_darkroom(self.player, state, 2, self.darkrooms),
            "darkroom3": lambda state: RuleUtils.has_darkroom(self.player, state, 3, self.darkrooms),
            "sword": lambda state: state.has("has_sword", self.player),
            "wateringcan": lambda state: state.has("ItemWateringCan", self.player),
            "presspass": lambda state: state.has("ItemPressPass", self.player),
            "basement": lambda state: state.has("ItemBasement", self.player),
            "tree": lambda state: state.has("has_sword", self.player) and state.has("ItemGlove", self.player),
            "chest": lambda state: RuleUtils.can_openChest(self.player, state),
            "box": lambda state: RuleUtils.can_passBoxes(self.player, state),
            }

        self.region_rules = {
            # "Menu -> sword main": lambda state: True,
            "factory machine catwalk -> Boss Fight": lambda state:
                self.helpers["darkroom2"](state) and RuleUtils.has_megasword(self.player, state),
            "factory machine generator -> Boss Fight": lambda state:
                self.helpers["darkroom2"](state) and RuleUtils.has_megasword(self.player, state),
            "2crab tree exit <-> 2crab tile":  self.helpers["tree"],
            # "coffee shop outside <-> coffee shop inside": lambda state: True,
            "quicksand left tree <-> quicksand main":  self.helpers["tree"],
                # technically an option to not have glove and water boatguy but
                # that adds weird issues so i'll just leave it as out of logic
            "quicksand right tree <-> quicksand main":  self.helpers["tree"],
            "boattree box <-> boattree main":  self.helpers["box"],
            "camera river south -> camera river north": lambda state:
                self.helpers["sword"](state) and state.has("ItemThrow", self.player),
            "camera river north -> camera river south": self.helpers["sword"],
            "camera house tree <-> camera house outside":  self.helpers["tree"],
            # "camera house outside <-> camera house inside": lambda state: True,
            "3crab trees <-> 3crab main":  self.helpers["tree"],
            "throwcheck tile -> throwcheck box": lambda state:
                self.helpers["sword"](state)
                and state.has("ItemGrinder", self.player),
            "throwcheck box -> throwcheck tile":  self.helpers["box"],
                # could be a oneway with coffee but i'll think about that later
            "arena tree north <-> arena tile":  self.helpers["tree"],
            "arena tree west <-> arena tile":  self.helpers["tree"],
            "bridge left <-> bridge right": lambda state:
                state.has("bridge on", self.player),  # need to confirm this works
            "factory loading lower main -> factory loading lower shortcut": lambda state:
                self.helpers["sword"](state)
                and state.has("ItemGrinder", self.player),
            "factory loading lower shortcut -> factory loading lower main": lambda state:
                self.helpers["sword"](state)
                and state.has("ItemGrinder", self.player),
                # or state.has_all({"ItemSwim", "ItemCoffee"}, self.player),
                # another entrance that could have one-way logic
            "mine entrance bombs -> mine entrance pipe": lambda state:
                self.helpers["sword"](state)
                and self.helpers["darkroom3"](state)
                and state.has("ItemThrow", self.player),
            "mine entrance pipe -> mine entrance bombs": lambda state:
                self.helpers["darkroom3"](state)
                and state.has("bombs exploded", self.player),
                # this needs to be a one-way
            "mine main -> mine main box": lambda state:
                self.helpers["sword"](state)
                and state.has("ItemGrinder", self.player),
            "mine main box -> mine main":  self.helpers["box"],
            "sewer main right north <-> sewer main":  self.helpers["darkroom2"],
            "sewer main left <-> sewer main": lambda state:
                self.helpers["darkroom2"](state)
                and self.helpers["swim"](state),
            "sewer bat arena -> sewer bat gate": lambda state:
                self.helpers["sword"](state)
                and self.helpers["darkroom3"](state),
                # this needs to be a one-way as the bats respawn
            "grinder south": lambda state:
                self.helpers["darkroom1"](state)
                and self.helpers["swim"](state),
            "grinder east": lambda state:
                self.helpers["darkroom1"](state)  # maybe 2
                and self.helpers["swim"](state),
            "factory machine generator <-> factory machine catwalk": lambda state:
                state.has("generator smashed", self.player),
            "miner chest pipe entrance <-> miner chest tile": lambda state:
                self.helpers["darkroom3"](state)
                and self.helpers["swim"](state),

            # unrandomized doors
            "lighthouse inside <-> lighthouse": lambda state: 
                state.has("ItemKey", self.player),
            "lighthouse <-> lighthouse lookout": lambda state: False,
                # obscure: you can swim and grab it from beneath
            # "lighthouse inside <-> lighthouse lookout": lambda state: True,
            "coffee shop pot stairs <-> sewer main right":  self.helpers["darkroom2"],  # maybe 3
            # "dog house inside <-> dog house west": lambda state: True,
            # "glove outside <-> glove inside": lambda state: True,
            "boattree main <-> waterfall cave":  self.helpers["swim"],
            # "hotel outside <-> hotel reception": lambda state: True,
            # "hotel outside <-> hotel backroom": lambda state: True,
            # "hotel reception <-> hotel room": lambda state: True,
            # "mine entrance right <-> mine entrance pipe": lambda state: True,
            # "factory loading upper <-> factory snakehall": lambda state: True,
            # "shoe shop inside <-> shoe shop outside": lambda state: True,
            # "desert RV main <-> RV house": lambda state: True,
            # "island house <-> Overworld": lambda state: True,
            "island house <-> island teleporter": lambda state:
                self.helpers["basement"](state) and self.helpers["darkroom1"](state),
            "island teleporter east":  self.helpers["darkroom1"],
            # "tent room main <-> underground house": lambda state: True,
            # "factory mega entrance <-> factory central": lambda state: True,
            "factory mega entrance <-> megasword upper": lambda state:
                state.has("generator smashed", self.player) and self.helpers["darkroom1"](state),
            "factory central south <-> factory central": lambda state:
                state.has("generator smashed", self.player),
            "dog house basement <-> hotel room": lambda state: False,
            "dog house basement <-> shoe shop downstairs": lambda state: False,
            # "temple coin test south <-> temple coin test north": lambda state: False,
            # TODO add complex logic to check if all spawns are reachable
            "temple coin test north": lambda state: False,
            "temple coin test south": lambda state: False,
            # TODO add complex logic to check if all spawns are reachable

            # # only swims
            "lighthouse water upper west":  self.helpers["swim"],
            "lighthouse water upper north":  self.helpers["swim"],
            "lighthouse water upper east":  self.helpers["swim"],
            "lighthouse water lower west":  self.helpers["swim"],
            "lighthouse water lower south":  self.helpers["swim"],
            "lighthouse water lower east":  self.helpers["swim"],
            "boat water south":  self.helpers["swim"],
            "boat water east":  self.helpers["swim"],
            "boat water north":  self.helpers["swim"],
            "boat water west":  self.helpers["swim"],
            "sword east <-> sword water":  self.helpers["swim"],
            "2crab land north river":  self.helpers["swim"],
            "2crab water east":  self.helpers["swim"],
            "2crab water south":  self.helpers["swim"],
            "2crab water west":  self.helpers["swim"],
            "dolphin water east":  self.helpers["swim"],
            "dolphin water south":  self.helpers["swim"],
            "dolphin water west":  self.helpers["swim"],
            "desert beach water south":  self.helpers["swim"],
            "desert beach water west":  self.helpers["swim"],
            "coffee shop water north":  self.helpers["swim"],
            "coffee shop water west":  self.helpers["swim"],
            "coffee shop water south":  self.helpers["swim"],
            "coffee shop upper beach":  self.helpers["swim"],

            "above lighthouse water north":  self.helpers["swim"],
            "above lighthouse water east upper":  self.helpers["swim"],
            "above lighthouse water east lower":  self.helpers["swim"],
            "above lighthouse water south":  self.helpers["swim"],
            "above lighthouse water west":  self.helpers["swim"],

            "dog house west <-> dog house east":  self.helpers["swim"],
            "dog house river north":  self.helpers["swim"],
            "dog house river south":  self.helpers["swim"],

            "boattree river south":  self.helpers["swim"],
            "3crab north water north":  self.helpers["swim"],
            "3crab north water west":  self.helpers["swim"],
            "3crab south water west":  self.helpers["swim"],
            "3crab south water south":  self.helpers["swim"],
            "sewer island water north":  self.helpers["swim"],
            # "sewer island water east":  lambda state: False,
            # TODO: check sword requirement (including one-way)
            "sewer island water south":  self.helpers["swim"],
            "sewer island water west":  self.helpers["swim"],
            "throwcheck water south":  self.helpers["swim"],
            "throwcheck water west":  self.helpers["swim"],
            "bridge switch left <-> bridge switch right":  lambda state: False,
            # "bridge switch water":  lambda state: False,
            # "bridge water north":  lambda state: False,
            # "bridge water south":  lambda state: False,
            # "mine entrance river north":  lambda state: False,
            # "mine entrance river south":  lambda state: False,
            # "poison river corner north":  lambda state: False,
            # "poison river corner south":  lambda state: False,

            "temple octopus north": lambda state:
                self.helpers["swim"](state)
                and self.helpers["darkroom3"](state),

            # # darkroom only
            "submarine east":  self.helpers["darkroom1"],
            "submarine west":  self.helpers["darkroom1"],
            "teleporter maze west":  self.helpers["darkroom1"],
            "mine main north":  self.helpers["darkroom1"],
            "mine main west upper": self.helpers["darkroom1"], # so that regions don't have to be added to enforce darkroom rules on mine main north and mine main west lower
            "mine main west lower":  self.helpers["darkroom1"],
            "mine main box": self.helpers["darkroom1"], # so that regions don't have to be added to enforce darkroom rules on mine main north and mine main west lower
            "factory switch test west":  self.helpers["darkroom1"],
            "factory switch test south":  self.helpers["darkroom1"],
            "temple outside <-> temple main":  self.helpers["darkroom1"],
            "dog house basement <-> island teleporter":  lambda state: False,

            "snake east <-> boattree east":  self.helpers["darkroom2"],
            "snake east <-> boattree main":  self.helpers["darkroom2"],
            "snake east path":  self.helpers["darkroom2"],
            "sewer island <-> sewer upper":  self.helpers["darkroom2"],
            "mine entrance left <-> mine entrance path":  self.helpers["darkroom2"],
            "tent room pipe I right":  self.helpers["darkroom2"],
            "tent room pipe I left":  self.helpers["darkroom2"],
            "tent room main right":  self.helpers["darkroom2"], # changed from 1 to 2 since you'd always travel across
            "tent room main left":  self.helpers["darkroom2"],

            "tent room pipe O":  self.helpers["darkroom3"],
            "miner chest pipe L south":  self.helpers["darkroom3"],
            "miner chest pipe L west":  self.helpers["darkroom3"],
            "trophy pipe hall right":  self.helpers["darkroom3"],
            "trophy pipe hall left":  self.helpers["darkroom3"],
            "trophy maze lower main north right":  self.helpers["darkroom3"],
            "trophy maze lower main north left":  self.helpers["darkroom3"],
            "trophy maze lower main east right":  self.helpers["darkroom3"],
            "trophy maze lower main east left":  self.helpers["darkroom3"],
            "trophy maze lower hall left":  self.helpers["darkroom3"],
            "trophy maze lower hall right":  self.helpers["darkroom3"],
            "trophy maze upper main right":  self.helpers["darkroom3"],
            "trophy maze upper main left":  self.helpers["darkroom3"],
            "trophy maze upper hall south":  self.helpers["darkroom3"],
            "trophy maze upper hall west":  self.helpers["darkroom3"],

            # # sword
            "sword east <-> sword west": self.helpers["sword"],
            "dolphin bushes":  self.helpers["sword"],
            "dog house bushes <-> dog house west":  self.helpers["sword"],
            "coffee shop outside <-> coffee shop pot stairs":  self.helpers["sword"],
            "plant bushes <-> plant tile":  self.helpers["sword"],
            "shoe shop shortcut <-> shoe shop outside":  self.helpers["sword"],
            "factory cooler west <-> factory cooler tile":  self.helpers["sword"],

            "temple main east <-> temple main":  self.helpers["wateringcan"],
            "temple firebat test east": lambda state:
                self.helpers["wateringcan"](state)
                and self.helpers["darkroom2"](state),
            "temple firebat test west": lambda state:
                self.helpers["wateringcan"](state)
                and self.helpers["darkroom2"](state),

            "dog house inside <-> dog house basement":  self.helpers["basement"],
            "shoe shop inside <-> shoe shop downstairs":  self.helpers["basement"],

            "factory reception east <-> factory reception tile":  self.helpers["presspass"],
        }

        self.location_rules = {
            # Dog House
            "Dog House - ItemCoffee": lambda state:
                self.helpers["sword"](state)
                and state.has_all({
                    "2 crab access",
                    "3 crab access",
                    }, self.player),
            # "Dog House - ItemFlashLight": lambda state: True,
            "Dog House - ItemKey": lambda state:
                self.helpers["sword"](state) and self.helpers["box"](state),
                # need to clear the plants by the boxes even with coffee
            # "Dog House - ItemWateringCan": lambda state: True,
            "Dog house - ItemBoat":  self.helpers["tree"],
            "Dog House - ItemBasement": lambda state:
                self.helpers["tree"](state)
                and state.has_all({
                    "ItemBoat",
                    "boatguy watered",
                    "ItemGlove",
                    }, self.player),
            # "Dog House - ItemPressPass": lambda state: True,
            "Dog House - House Pot Coin":  self.helpers["sword"],
            "Dog House - Sewer Island Coin":  self.helpers["chest"],
            "Dog House - Sewer Coin": lambda state:
                self.helpers["chest"](state)
                and self.helpers["darkroom2"](state)
                and self.helpers["swim"](state),
            "Dog House - Land is Great Coin":  self.helpers["chest"],
            "Dog House - Hidden Snake Coin": lambda state:
                self.helpers["chest"](state) and self.helpers["darkroom3"](state),
            "Dog House - Waterfall Coin": lambda state:
                self.helpers["chest"](state) and self.helpers["darkroom1"](state),
            "Dog House - Treasure Island Coin": lambda state:
                self.helpers["chest"](state)
                and self.helpers["swim"](state),
            "Dog House - Plant Heart":  self.helpers["wateringcan"],
            "Dog House - Bull Heart":  self.helpers["sword"],
            "Dog House - Boat Tentacle": lambda state:
                self.helpers["sword"](state)
                and state.has_all({
                    "ItemBoat",
                    "boatguy watered",
                    "ItemGlove",
                    }, self.player),
            "Dog House - Treasure Island Tentacle": lambda state:
                self.helpers["sword"](state) and self.helpers["swim"](state),
            "Dog House - Sword Toss Tentacle": lambda state:
                self.helpers["sword"](state)
                and state.has_all({"ItemCoffee", "ItemThrow"}, self.player),
            "Dog House - Sewer Tentacle": lambda state:
                self.helpers["sword"](state) and self.helpers["darkroom3"](state)
                and self.helpers["swim"](state),

            # Desert RV
            "Desert RV - ItemThrow":  self.helpers["sword"],
            "Desert RV - ItemShoes": lambda state:
                state.has("Coin", self.player, 7),
            "Desert RV - ItemGlove":  self.helpers["darkroom1"],
            "Desert RV - ItemTurboInk": lambda state:
                self.helpers["darkroom2"](state) and state.has("Tentacle", self.player, 8),
            "Desert RV - Temple Coin": lambda state:
                self.helpers["sword"](state) and self.helpers["darkroom2"](state),
                # this may change if i connect the other temple puzzles
            "Desert RV - Fire Bat Coin": lambda state:
                self.helpers["chest"](state) and self.helpers["darkroom2"](state),
                # this may change if i connect the other temple puzzles
            "Desert RV - Truck Supplies Coin": lambda state:
                self.helpers["sword"](state) and self.helpers["chest"](state),
            "Desert RV - Broken Truck":  self.helpers["chest"],
            "Desert RV - Quicksand Coin": lambda state:
                self.helpers["sword"](state) and self.helpers["darkroom2"](state),
                # vanilla does require sword because the wateringcan
                # drops while drowning in quicksand
            "Desert RV - Dumpster":  self.helpers["sword"],
            "Desert RV - Temple Heart": lambda state:
                self.helpers["darkroom3"](state)
                and state.has("ItemShoes", self.player),
            "Desert RV - Shop Heart": lambda state:
                state.has("Coin", self.player, 19),
            "Desert RV - Octopus Tentacle": lambda state:
                self.helpers["sword"](state)
                and self.helpers["darkroom3"](state)
                and self.helpers["swim"](state),
            "Desert RV - Beach Tentacle":  self.helpers["sword"],

            # Hotel Room
            "Hotel Room - ItemSwim": lambda state:
                state.has_all({
                    "swimmer saved",
                    "hostage saved",
                    "wallet saved",
                    "ninja saved",
                    "bridge saved",
                    "hidden saved",
                    }, self.player),
                # praying i can make this work
            "Hotel Room - ItemGrinder": lambda state:
                self.helpers["darkroom2"](state)
                and state.has_all({"ItemSwim", "ItemCoffee"}, self.player),
            "Hotel Room - Shrub Arena Coin":  self.helpers["sword"],
            "Hotel Room - Miner's Chest Coin": lambda state:
                self.helpers["chest"](state) and self.helpers["darkroom3"](state),
            # "Factory Main - Inside Truck": lambda state:  True,
            # "Hotel Room - Queue": lambda state: True,
            "Hotel Room - Hotel Backroom Coin": lambda state:
                self.helpers["sword"](state) and self.helpers["box"](state),
            "Factory Main - Drill Coin":  self.helpers["sword"],
            "Hotel Room - Crow Heart":  self.helpers["box"],
            "Hotel Room - Dog Heart": lambda state:
                (self.helpers["tree"](state)
                    and (state.has_all({
                            "teleporter switch1",
                            "teleporter switch4",
                            "teleporter switch6",
                        }, self.player)
                        or state.has_all({
                            "ItemSwim",
                            "ItemShoes"
                            }, self.player))),
                # TODO - untouched until i figure out a way to logic this
            "Factory Main - Cooler Tentacle":  self.helpers["sword"],

            # Island Shack
            "Island Shack - Teleporter Tentacle": lambda state:
                self.helpers["sword"](state)
                and self.helpers["darkroom1"](state)
                and state.has("ItemCoffee", self.player)
                and self.helpers["swim"](state),

            # Underground Tent
            "Underground Tent - ItemTrophy":  self.helpers["darkroom1"],
            "Dog House - Dolphin Heart":  self.helpers["wateringcan"],

            # Undefined
            "Factory Main - ItemMegaSword": lambda state:
                self.helpers["sword"](state)
                and state.has_all({
                    "ItemWateringCan",
                    "left machine",
                    "right machine",
                    "drill smacked",  # game quirk
                    }, self.player),

            # events
            "generator smashed":  self.helpers["sword"],
            "drill smacked":  self.helpers["sword"],
            # "swimmer saved": lambda state:
            #     True,
            "hostage saved":  self.helpers["sword"],
            "wallet saved": lambda state:
                state.has("ItemCoffee", self.player),
            "ninja saved":  self.helpers["tree"],
            "bridge on":  self.helpers["sword"],
            "bridge saved": lambda state:
                state.has("bridge on", self.player),
            "hidden saved":  self.helpers["box"],
            "teleporter switch1": lambda state:
                self.helpers["sword"](state) and self.helpers["darkroom3"](state),
            "teleporter switch4":  self.helpers["sword"],
            "teleporter switch6":  self.helpers["sword"],
            "boatguy watered":  self.helpers["wateringcan"],
            "left machine": lambda state:
                self.helpers["darkroom1"](state)
                and state.has_all({"ItemSwim", "ItemCoffee"}, self.player),
            "right machine": lambda state:
                self.helpers["darkroom1"](state)
                and self.helpers["sword"],
        }

        obscure = {
            "Hotel Room - Dog Heart": self.helpers["tree"],
                # TODO - untouched until i figure out a way to logic this
            "Factory Main - Cooler Tentacle":  self.helpers["sword"],

            # Island Shack
            "Island Shack - Teleporter Tentacle": lambda state:
                self.helpers["sword"](state)
                and self.helpers["darkroom1"](state)
                and self.helpers["swim"](state),
            
            # Flashlight from Below
            "lighthouse <-> lighthouse lookout": self.helpers["swim"],
        }

        def apply_rules(optional_rules):
            for key, rule in optional_rules.items():
                if key in self.region_rules:
                    self.region_rules[key] = rule
                else:
                    self.location_rules[key] = rule

        if self.world.options.obscure:
            apply_rules(obscure)

    def rev(self, e_name: str) -> (str, str):
        e_list = e_name.split(" -> ")
        if len(e_list) == 2:
            return f"{e_list[1]} <-> {e_list[0]}", f"{e_list[0]} <-> {e_list[1]}"
        else:
            return "", ""

    def set_Minit_rules(self) -> None:
        multiworld = self.world.multiworld
        for region in multiworld.get_regions(self.player):
            for entrance in region.exits:
                if entrance.name in self.region_rules:
                    set_rule(entrance, self.region_rules[entrance.name])
                else:
                    left_name, right_name = self.rev(entrance.name)
                    if left_name in self.region_rules:
                        set_rule(
                            entrance,
                            self.region_rules[left_name]
                            )
                    elif right_name in self.region_rules:
                        set_rule(
                            entrance,
                            self.region_rules[right_name]
                            )
            for location in region.locations:
                if location.name in self.location_rules:
                    set_rule(location, self.location_rules[location.name])
