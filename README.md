# Thalia-Programming-Contest-Framework

## Battleship rules

This version of the game consists of 3 phases.
- Placing 4 islands on your opponent's board: they won't be able to place ships won't on those positions.
- Placing your own ships.
The ships have the following properties:

| Type | Length | Amount |
|------|--------|--------|
| CARRIER | 5 | 1
| BATTLESHIP | 4 | 2
| CRUISER | 3 | 3
| DESTROYER | 2 | 4
- Shooting eachothers boards.


## How to get started:
We advise you to base your bot on one of these provided starter bots:

- Java starter bot: [here](https://github.com/kliyer-ai/StarterBot)
- Python starter bot: see the exampleBot directory

You can run your bot by running the ```ClientRunner.py``` script in the framework directory.

In this directory you will also find a config file. By changing it you can configure:
- The name of your team
- Whether to enable the clientside visualiser (sudo apt-get install python3-tk)
- Whether to write the bot stderr to a file (you can use this to debug your bot)
- Where to connect to the server (you probably won't need to change this)
- What command to run to run your bot.


If you have any questions, you can approach Ward, Nick or Yannick.

Have fun!
