#!/usr/bin/python3
import random
import sys
from Bot import *


class ExampleBot(Bot):
    def __init__(self):
        super().__init__()

    def initialise(self):
        pass  # You can delete this function if you don't use it

    def do_move(self):
        return {"dir": random.choice(self.get_valid_dirs()),
                "bomb": random.random() > 0.1}


if __name__ == "__main__":
<<<<<<< HEAD
    print("[StdErr test]", file=sys.stderr)
=======
>>>>>>> 399e31b5c4ae52fbe376c8f1548411f62f6d8ec2
    sys.stderr.flush()
    ExampleBot().run()
