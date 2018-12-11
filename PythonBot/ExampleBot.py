#!/usr/bin/python3
import random

from PythonBot.Bot import *


class ExampleBot(Bot):
    def __init__(self):
        super().__init__()

    def initialise(self):
        pass  # You can delete this function if you don't it

    def do_move(self):
        return {"dir": random.choice(self.get_valid_dirs()),
                "bomb": random.random() > 0.1}


if __name__ == "__main__":
    ExampleBot().run()
