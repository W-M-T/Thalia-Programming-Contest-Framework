#!/usr/bin/python3

import operator
from typing import List, Tuple

from Game import Board, Tile


class Bot:
    def __init__(self):
        """Initialize instance variables."""
        self.board = Board((15, 15))
        self.done = False
        self.water_round = None
        self.you = None

    def handle_config(self, config_info: List[str]):
        if config_info[0] == "WATER" and config_info[1] == "ROUND":
            self.water_round = int(config_info[2])

        elif config_info[0] == "TILE":
            coord = Bot.get_coord(config_info[1])
            self.board.set(coord, Tile[config_info[2]])

        elif config_info[0] == "PLAYER":
            p_id = int(config_info[2])

            if config_info[1] == "NAME":
                self.board.players[p_id] = {'lives': None, 'pos': None}
            elif config_info[1] == "PLACE":
                self.board.players[p_id]['pos'] = Bot.get_coord(config_info[3])
            elif config_info[1] == "LIVES":
                self.board.players[p_id]['lives'] = int(config_info[3])

        elif config_info[0] == "YOU":
            self.you = config_info[1]

    def handle_update(self, update_info: List[str]):
        if update_info[0] == "PLAYER":
            p_id = int(update_info[2])

            if update_info[1] == "LOC":
                self.board.players[p_id]['pos'] = Bot.get_coord(update_info[2])
            elif update_info[1] == "STATUS":
                if update_info[3] == "HIT":
                    self.board.players[p_id]['lives'] -= 1
                elif update_info[3] == "DEAD":
                    self.board.players[p_id]['lives'] = 0

        if update_info[0] == "BOMB":
            coord = Bot.get_coord(update_info[2])

            if update_info[1] == "PLACED":
                self.board.bombs.append({'pos': coord, 'timer': 1})

    def handle_command(self, text: str):
        """Handle the server's message."""
        tokens = text.strip().split()
        if tokens[0] == 'CONFIG':
            self.handle_config(tokens[1:])
        elif tokens[0] == 'START' and tokens[1] == "GAME":
            self.initialise()
        elif tokens[0] == 'REQUEST' and tokens[1] == "MOVE":
            self.report_move()
        elif tokens[0] == 'UPDATE':
            self.handle_update(tokens[1:])
        elif tokens[0] == "YOU":
            self.done = True

    def do_move(self):
        raise NotImplementedError("Implement this function to do a move")

    def report_move(self):
        move = self.do_move()
        dir: Tuple[int, int] = move['dir']
        bomb: bool = move['bomb']

        if max(dir) > 1 or min(dir) < -1:
            raise ValueError("one of the dims is out of range")

        if not self.board.is_valid_move(
                tuple(map(operator.add,
                          self.board.players[self.you]['pos'],
                          dir))):
            raise ValueError("This is not a valid location")

        if bomb:
            print("BOMBWALK {}".format(Bot.format_dir(dir)))
        else:
            print("WALK {}".format(Bot.format_dir(dir)))

    def initialise(self):
        pass

    def run(self):
        """Run the bot."""
        self.done = False
        while self.done != True:
            command = input()
            self.handle_command(command)

    def get_valid_dirs(self) -> List[Tuple[int, int]]:
        x, y = self.board.players[self.you]['pos']
        choices = ([(1, 0)] if x != 13 else []) \
                  + ([(0, 1)] if y != 13 else []) \
                  + ([(-1, 0)] if x != 1 else []) \
                  + ([(0, -1)] if y != 1 else [])
        choices = list(filter((lambda coord:
                               self.board.board[y + coord[1]][x + coord[0]]
                               == Tile.Empty),
                              choices))

        return choices

    @staticmethod
    def format_dir(coord: Tuple[int, int]):
        """Return a direction according to a coord"""
        dirs = {(0, 1): "UP", (0, -1): "DOWN",
                (-1, 0): "LEFT", (1, 0): "RIGHT",
                (0, 0): "STAY"}
        return dirs[coord]

    @staticmethod
    def format_coord(coord: Tuple[int, int]):
        """Return a properly formatted coordinate string."""
        return "(" + str(coord[0]) + "," + str(coord[1]) + ")"

    @staticmethod
    def get_coord(coord_str: str) -> Tuple[int, int]:
        coord_strs = coord_str.split(',')
        return int(coord_strs[0][1:]), int(coord_strs[1][:-1])


if __name__ == "__main__":
    Bot().run()
