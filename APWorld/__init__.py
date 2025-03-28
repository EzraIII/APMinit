from worlds.AutoWorld import World, WebWorld
from BaseClasses import (
    Region,
    Location,
    Item,
    ItemClassification,
    # Entrance,
    Tutorial,
)
from settings import (
    Group,
    FilePath,
)
from .Items import (
    MinitItem,
    # MinitItemData,
    item_table,
    item_frequencies,
    item_groups,
)
from .Locations import location_table
from .Regions import region_table
from .ERData import (
    er_regions,
    er_entrances,
    minit_target_group_lookup,
    er_static_connections,
    door_names,
)
from .Options import MinitGameOptions
# from worlds.generic.Rules import add_rule, set_rule, forbid_item
from .Rules import MinitRules
from .ER_Rules import ER_MinitRules
from . import RuleUtils
from typing import Dict, Any, List, TextIO, Tuple, Optional
from worlds.LauncherComponents import (
    Component,
    components,
    Type,
    launch_subprocess,
)
from Utils import visualize_regions

try:
    from entrance_rando import randomize_entrances
    from BaseClasses import EntranceType
    er_loaded = True
except ModuleNotFoundError:
    er_loaded = False
#TODO - save mod specific values like location_sent etc.


# high prio
# TODO - find more places exceptions need to be handled
# TODO - confirm each sword does correct effects per sword
# - (pushback, damage, etc.)
# TODO - figure out how to add tests and test for
# - confirm a sword or swim is in the first two checks
# - confirm prog balancing settings (min/loc/items) work
# - confirm the options are working as intended (when added)

# misc game mod TODOs
# TODO - pull all required game mods out and reapply to clean up patch file

# add options
# TODO - add puzzleless to de-prio longer/confusing puzzles
# TODO - add random start locations

# known low prio
# TODO - clean up game mod logging to necessities
# TODO - clean up item/location names

# deathlink testing
# deaths during pause seem to dissapear
# saw a death as i respawned once but no idea what the cause
# seemingly had another
# - Unable to find any instance for object index '0' name 'Player'
# - at gml_Object_apConnection_Other_62
# error when recieving a deathlink after dying, but unknown why
# - (because that should be handled)
# potential sync issue when sending items and dying (deathlink)
#  where item_sent is flagged by ap never hears

# bug reports
# hotel backroom coin is accessible without breaking the pot
# - confirmed, no idea how to fix
# fanfares sometimes clip you into walls without a way out
# - confirmed, not that worried because you always can respawn
# generation breaks sometimes, unknown cause

# ideas to explore
# make teleporter a item/location
# make residents item/location
# make boss fight require the left/right machines
# - to be stopped (and thus swim + coffee + darkroom by default)
# set item_sent flags on connect / full sync


class MinitSettings(Group):
    class RomFile(FilePath):
        """Path to Minit Vanilla data file"""
        description = "Minit Vanilla File"
        md5s = [
            "cd676b395dc2a25df10a569c17226dde", #steam
            "1432716643381ced3ad0195078e8e314", #epic
            # "6263766b38038911efff98423822890e", #itch.io, does not work
            ]
        # the hashes for vanilla to be verified by the /patch command
        required = True

    rom_file: RomFile = RomFile("")


class MinitWebWorld(WebWorld):
    theme = "ice"
    setup = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Minit randomizer for AP",
        "English",
        "docs/setup_en.md",
        "setup/en",
        ["qwint"]
    )

    tutorials = [setup]


def launch_client(*args):
    try:
        from worlds.LauncherComponents import launch as launch_component
        from .MinitClient import launch
        launch_component(launch, name="MinitClient", args=args)
    except ImportError:
        launch_if_needed(*args)


# TODO remove eventually once 0.6.0 is old enough
def launch_if_needed(*args):
    import sys
    from .MinitClient import launch
    if not sys.stdout or "--nogui" not in sys.argv:
        launch_subprocess(launch, name="MinitClient", args=args)
    else:
        launch(*args)


components.append(Component(
    "Minit Client",
    func=launch_client,
    component_type=Type.CLIENT,
    supports_uri=True,
    game_name="Minit"
    ))


# class MinitItem(Item):
#     game = "Minit"
# in items.py and already imported

class MinitWorld(World):
    """
    Minit is a peculiar little adventure played sixty seconds at a time.
    """

    game = "Minit"
    required_client_version = (0, 4, 4)
    options_dataclass = MinitGameOptions
    options: MinitGameOptions
    settings: MinitSettings
    web = MinitWebWorld()
    output_connections: List[Tuple[str, str]]
    spoiler_hints: Dict[str, str]

    item_name_to_id = {
        name: data.code
        for name, data
        in item_table.items()
        if data.code is not None}
    location_name_to_id = {
        name: data.code
        for name, data
        in location_table.items()
        if data.code is not None}
    locked_locations = {
        name: data
        for name, data
        in location_table.items()
        if data.locked_item}
    item_name_groups = item_groups

    def __init__(self, multiworld: "MultiWorld", player: int):
        super().__init__(multiworld, player)
        self.spoiler_hints = {}

    def generate_early(self):
        if self.options.er_option and not er_loaded:
            from Options import OptionError
            raise OptionError("Please use the Generic Entrance Rando branch for ER")

    def create_item(self, name: str) -> MinitItem:
        data = item_table[name]

        if self.options.damage_boosts and name == "HeartPiece":
            item_clas = ItemClassification.progression_skip_balancing
        elif self.options.darkrooms == "insane" and name == "ItemFlashLight":
            item_clas = ItemClassification.useful
        else:
            item_clas = data.classification
        return MinitItem(name, item_clas, data.code, self.player)

    def add_to_pool(self, name: str, count: int):
        self.multiworld.itempool.append(
            self.create_item(name))
        return count + 1

    def create_items(self):
        item_count = 0
        for item_name, item_data in item_table.items():
            if item_data.code and item_data.can_create(self):
                if item_name in item_frequencies:
                    frequency = item_frequencies[item_name]
                else:
                    frequency = 1
                for count in range(frequency):
                    item_count = self.add_to_pool(item_name, item_count)

        total_locations = len(self.multiworld.get_unfilled_locations(self.player))
        for _ in range(total_locations - item_count):
            item_count = self.add_to_pool(self.get_filler_item_name(), item_count)
        assert item_count == total_locations, f"{item_count} == {total_locations}"

    def make_bad_map(self) -> List[Tuple[str, str]]:
        """only needed for ER POC before Generic ER gets merged"""
        """only needed for ER POC before Generic ER gets merged"""
        unconnected = []
        output = []
        for entrance in er_entrances:
            if entrance.entrance_name not in door_names:
                unconnected.append(entrance.entrance_name)
        self.random.shuffle(unconnected)
        try:
            while unconnected:
                left = unconnected.pop()
                right = unconnected.pop()
                output.append((left, right))
                output.append((right, left))
        except IndexError:
            print("too many connections, leaving 1 unconnected")
        return output

    def add_regions_and_locations(self, er_on: bool):
        if er_on:
            region_list = er_regions
            entrance_list = er_static_connections
        else:
            region_list = region_table.keys()
            entrance_list = region_table
        for region_name in region_list:
            self.multiworld.regions.append(Region(
                region_name,
                self.player,
                self.multiworld))

        for loc_name, loc_data in location_table.items():
            if not loc_data.can_create(self):
                continue
            if er_on:
                loc_region = loc_data.er_region
            else:
                loc_region = loc_data.region
            region = self.multiworld.get_region(
                loc_region,
                self.player)
            new_loc = Location(
                self.player,
                loc_name,
                loc_data.code,
                region)
            if (not loc_data.show_in_spoiler):
                new_loc.show_in_spoiler = False
            region.locations.append(new_loc)
            if loc_data.locked_item:
                self.multiworld.get_location(
                    loc_name,
                    self.player
                ).place_locked_item(MinitItem(
                    name=loc_data.locked_item,
                    classification=ItemClassification.progression,
                    code=None,
                    player=self.player))

        for region_name, exit_list in entrance_list.items():
            region = self.multiworld.get_region(region_name, self.player)
            if er_on:
                for other_region_name in exit_list:
                    other_region = self.multiworld.get_region(
                        other_region_name,
                        self.player,
                        )
                    region.connect(other_region)
                    other_region.connect(region)
            else:
                region.add_exits(exit_list)
        # elif self.options.er_option == "on":
        #     # current map gen is pure random, so make regions/connections vanilla
        #     self.output_connections = self.make_bad_map()

    def create_regions(self):
        from worlds.generic.Rules import forbid_item

        er_on = bool(self.options.er_option)
        starting_entrance = ""
        early_location_list: List[Location] = []
        self.add_regions_and_locations(er_on)
        if er_on and er_loaded:
            # current code for using the Generic ER randomizer
            if True: #self.multiworld.players == 1:
                # if there is a one-player world, make at least one
                # of the early entrances into a check
                # that you can pick up for free
                free_checks = [
                    "watering can",  # deadend
                    "camera house outside south",  # deadend
                    "glove outside east",
                    "glove outside west",
                    "factory loading upper north",
                    "factory loading upper east",
                    "factory loading upper south",
                    "factory snakehall north",
                    "factory queue",  # deadend
                    "trophy room",  # deadend
                    ]  # consider removing the deadends because they could have a higher chance of killing the seed
                room_lookup = {
                    "camera house outside south": "camera house inside",
                    "glove outside east": "glove inside",
                    "glove outside west": "glove inside",
                    "factory loading upper north": "factory loading upper",
                    "factory loading upper east": "factory loading upper",
                    "factory loading upper south": "factory loading upper",
                    "factory snakehall north": "factory loading upper",
                }

                starting_entrance = self.random.choices(free_checks)[0]

                if starting_entrance in room_lookup:
                    starting_region = room_lookup[starting_entrance]
                else:
                    starting_region = starting_entrance

                early_location_list = [
                    self.multiworld.get_location(location_name, self.player)
                    for location_name, location_data in location_table.items()
                    if location_data.er_region == starting_region
                ]
                # print(f"adding {starting_entrance} to starting region to make single player ER playable")
                manual_connect_start = None
                manual_connect_end = None
                # add_manual_connect = True

            for er_entrance in er_entrances:
                region = self.multiworld.get_region(
                    er_entrance.region_name,
                    self.player)
                # entrance.is_dead_end = er_entrance[2]

                en1 = region.create_exit(er_entrance.entrance_name)
                en1.randomization_type = EntranceType.TWO_WAY
                en1.randomization_group = er_entrance.group_type
                if starting_entrance and er_entrance.entrance_name in ["dog house south", starting_entrance]:
                    if er_entrance.entrance_name == "dog house south":
                        manual_connect_start = en1
                    if er_entrance.entrance_name == starting_entrance:
                        manual_connect_end = en1
                    if manual_connect_start and manual_connect_end:
                        manual_connect_start.connect(manual_connect_end.parent_region)
                        manual_connect_end.connect(manual_connect_start.parent_region)
                        self.output_connections = [
                                                      (
                                                          manual_connect_start.name,
                                                          manual_connect_end.name
                                                      ),
                                                      (
                                                          manual_connect_end.name,
                                                          manual_connect_start.name
                                                      )
                                                  ]
                        # print(f"connecting {manual_connect_start.name} and {manual_connect_end.name}")
                        # add_manual_connect = False
                else:
                    en2 = region.create_er_target(er_entrance.entrance_name)
                    en2.randomization_type = EntranceType.TWO_WAY
                    en2.randomization_group = er_entrance.group_type

        # should never be called with the new OptionError
        # elif er_on and not er_loaded:
        #     # also only needed for ER POC before Generic ER gets merged
        #     self.add_regions_and_locations(False)
        #     self.output_connections = self.make_bad_map()
        #     for name in [
        #         "Dog House - Dolphin Heart",
        #         "Dog House - Plant Heart",
        #         "Desert RV - ItemGlove",
        #         "Hotel Room - Queue",
        #         "Dog House - ItemSword",
        #     ]:
        #         early_location_list.append(self.multiworld.get_location(name, self.player))

        else:
            self.output_connections = None
            for name in [
                "Dog House - Dolphin Heart",
                "Dog House - Plant Heart",
                "Desert RV - ItemGlove",
                "Hotel Room - Queue",
                "Dog House - ItemSword",
            ]:
                early_location_list.append(self.multiworld.get_location(name, self.player))
            # self.output_connections = [
            #     ("dog house inside door", "dog house door",),
            #     ("dog house door", "dog house inside door",),

            #     ("dog house west", "dog house east",),
            #     ("dog house east", "dog house west",),

            #     ("dog house east lower", "dog house bushes",),
            #     ("dog house bushes", "dog house east lower",),

            #     ("dog house river north", "dog house river south",),
            #     ("dog house river south", "dog house river north",),

            #     ("dog house south", "coffee shop inside",),
            #     ("coffee shop inside", "dog house south",),
            # ]
            # self.output_connections = self.make_bad_map()

        for location in early_location_list:
            forbid_item(location, "Coin", self.player)
        # forbid_item(early_location, "HeartPiece", self.player)
        # forbid_item(early_location, "Tentacle", self.player)

    def write_spoiler_header(self, spoiler_handle: TextIO) -> None:
        if self.options.er_option == "off" or not er_loaded:
            return

        spoiler_handle.write(f"Entrance Rando Location Paths:\n")
        for location, path in self.spoiler_hints.items():
            spoiler_handle.write(f"\t{location}: {path}\n")

    # copied from BaseClasses CollectionState in order to rewrite it to
    # path from all houses and grab the shortest path for hint data
    # also reference Tunic's https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/tunic/__init__.py#L307C9-L307C32
    #
    # def update_reachable_regions(self, player: int):
    #     self.stale[player] = False
    #     reachable_regions = self.reachable_regions[player]
    #     blocked_connections = self.blocked_connections[player]
    #     queue = deque(self.blocked_connections[player])
    #     start = self.multiworld.get_region("Menu", player)

    #     # init on first call - this can't be done on construction since the regions don't exist yet
    #     if start not in reachable_regions:
    #         reachable_regions.add(start)
    #         blocked_connections.update(start.exits)
    #         queue.extend(start.exits)

    #     # run BFS on all connections, and keep track of those blocked by missing items
    #     while queue:
    #         connection = queue.popleft()
    #         new_region = connection.connected_region
    #         if new_region in reachable_regions:
    #             blocked_connections.remove(connection)
    #         elif connection.can_reach(self):
    #             assert new_region, f"tried to search through an Entrance \"{connection}\" with no Region"
    #             reachable_regions.add(new_region)
    #             blocked_connections.remove(connection)
    #             blocked_connections.update(new_region.exits)
    #             queue.extend(new_region.exits)
    #             self.path[new_region] = (new_region.name, self.path.get(connection, None))

    #             # Retry connections if the new region can unblock them
    #             for new_entrance in self.multiworld.indirect_connections.get(new_region, set()):
    #                 if new_entrance in blocked_connections and new_entrance not in queue:
    #                     queue.append(new_entrance)

    def extend_hint_information(self, hint_data: Dict[int, Dict[int, str]]) -> None:
        if self.options.er_option == "off" or not er_loaded:
            return

        hint_data.update({self.player: {}})

        all_state = self.multiworld.get_all_state(True)
        # sometimes some of my regions aren't in path for some reason? and other comments stolen from Treble
        all_state.update_reachable_regions(self.player)
        paths = all_state.path
        # start = self.multiworld.get_region("dog house west", self.player)
        # start_connections = [entrance.name for entrance in start.exits]  # if entrance not in {"Home", "Shrink Down"}]
        transition_names = [er_entrance.entrance_name for er_entrance in er_entrances]  # + start_connections
        for loc in self.multiworld.get_locations(self.player):
            # if (loc.parent_region.name in {"Tower HQ", "The Shop", "Music Box", "The Craftsman's Corner"}
            #         or loc.address is None):
            path_to_loc = []
            name, connection = paths[loc.parent_region]
            while connection != ("Menu", None):
                name, connection = connection
                if name in transition_names:
                    path_to_loc.append(name)

            text = ""
            for transition in reversed(path_to_loc):
                text += f"{transition} => "
            text = text.rstrip("=> ")
            self.spoiler_hints[loc.name] = text
            if loc.address is not None:
                hint_data[self.player][loc.address] = text

    def fill_slot_data(self) -> Dict[str, Any]:
        slot_data = self.options.as_dict(
                "death_link",
                "death_amnisty_total",
            )
        slot_data["ER_connections"] = self.output_connections
        slot_data["goals"] = self.options.chosen_goal.parse_goals()

        return slot_data

    def interpret_slot_data(self, slot_data: Dict[str, Any]):
        try:
            if slot_data["ER_connections"]:
                e_dict = {entrance.name: entrance for region in self.multiworld.get_regions(self.player) for entrance in region.entrances}

                for connection in slot_data["ER_connections"]:
                    assert connection[0] in e_dict, f"entrance {connection[0]} in slot data not in world"
                    assert connection[1] in e_dict, f"entrance {connection[1]} in slot data not in world"

                    e_dict[connection[0]].connected_region = e_dict[connection[1]].parent_region
        except AssertionError:
            import logging
            logging.getLogger("Client").info(f"Tracker: ER Handling failed because of unknown entrances, confirm your AP install can support ER")

    def set_rules(self):
        if self.options.er_option == "off":
            MinitRules(self).set_Minit_rules()
        elif self.options.er_option == "on" and not er_loaded:
            MinitRules(self).set_Minit_rules()
        elif self.options.er_option == "on" and er_loaded:
            ER_MinitRules(self).set_Minit_rules()

            self.output_connections += randomize_entrances(
                    world=self,
                    coupled=True,
                    target_group_lookup=minit_target_group_lookup,
                    preserve_group_order=False
                    ).pairings
            # visualize_regions(
            #     self.multiworld.get_region("Menu", self.player),
            #     "output/regionmap.puml")

        if self.options.chosen_goal == "boss_fight":  # boss fight
            self.multiworld.completion_condition[self.player] = lambda state: \
                state.has("Boss dead", self.player)
        elif self.options.chosen_goal == "toilet_goal":  # toilet
            self.multiworld.completion_condition[self.player] = lambda state: \
                RuleUtils.has_brokensword(self.player, state) and \
                state.has("Sword Flushed", self.player)
        elif self.options.chosen_goal == "any_goal":  # any
            self.multiworld.completion_condition[self.player] = lambda state: \
                state.has("Boss dead", self.player) or \
                (RuleUtils.has_brokensword(self.player, state) and
                    state.has("Sword Flushed", self.player))
        if bool(self.options.starting_sword):
            self.multiworld.local_early_items[self.player][self.get_sword_item_name()] = 1

    def get_sword_item_name(self) -> str:
        if self.options.progressive_sword == "off":
            return "ItemSword"
        elif self.options.progressive_sword == "reverse_progressive":
            return "Reverse Progressive Sword"
        elif self.options.progressive_sword == "forward_progressive":
            return "Progressive Sword"

    def get_filler_item_name(self) -> str:
        if bool(self.options.min_hp):
            return "Coin"
        else:
            return "HeartPiece"

    # def pre_fill(self) -> None:
    #     from worlds.generic.Rules import forbid_item
    #     forbid_item(self.multiworld.get_location("Dog House - ItemSword", self.player), "Coin", self.player)
        # if self.multiworld.players == 1 and not bool(self.options.starting_sword):
        #     starting_items = ["ItemSwim", "ItemWateringCan"]
        #     if self.options.progressive_sword == "off":
        #         starting_items.append("ItemBrokenSword")
        #         starting_items.append("ItemSword")
        #         starting_items.append("ItemMegaSword")
        #     elif self.options.progressive_sword == "reverse_progressive":
        #         starting_items.append("Reverse Progressive Sword")
        #     elif self.options.progressive_sword == "forward_progressive":
        #         starting_items.append("Progressive Sword")
        #     self.random.shuffle(starting_items)
        #     self.multiworld.local_early_items[self.player][starting_items.pop()] = 1

    def collect(self, state: "CollectionState", item: "Item") -> bool:
        change = super().collect(state, item)
        if change and item.name in item_groups["swords"]:
            state.prog_items[item.player]["has_sword"] += 1
        return change

    def remove(self, state: "CollectionState", item: "Item") -> bool:
        change = super().remove(state, item)
        if change and item.name in item_groups["swords"]:
            state.prog_items[item.player]["has_sword"] -= 1
            assert state.prog_items[item.player]["has_sword"] > -1
        return change
