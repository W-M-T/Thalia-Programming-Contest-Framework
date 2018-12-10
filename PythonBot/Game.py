from enum import Enum


class Tile(Enum):
    Water = 0
    Mountain = 1
    Tree = 2
    Empty = 3

    @property
    def unbreakable(self):
        return self == Tile.Water or self == Tile.Mountain


class Board:

    def __init__(self, dims):
        self.dims = dims
        self.board = [[Tile.Empty for _ in range(dims[0])] for _ in
                      range(dims[1])]
        self.bombs = []  # Lijst van dicts met pos en timer
        self.players = {}  # dict van pIDs naar pos en lives

    def on_board(self, coord):
        return 0 <= coord[0] < self.dims[0] and 0 <= coord[1] < self.dims[1]

    def get(self, coord):
        return self.board[coord[0]][coord[1]]

    def set(self, coord, val):
        self.board[coord[0]][coord[1]] = val

    def is_valid_move(self, coord):
        return self.get(coord) == Tile.Empty and self.on_board(coord)

    def gameover(self):
        pass

    def livePlayerCount(self):
        return len(list(filter(lambda x: x is not None, self.players)))
