# Thalia Programming Contest Framework

## How do I develop a bot
- Download or Clone this repo
- Choose either the Python ~~or Java Bot~~ and start you can start making your 
    own bot from that point. If you want to use your own language this is also 
    possible but more work is needed. [See below for more info](#I-want-use-my-own-language).
    
You can run your bot by running the ```ClientRunner.py``` script in the framework directory.
This script has an optional argument to use another config file.

In this directory you will also find a config file. By changing it you can configure:
- The name of your team
- Whether to enable the clientside visualiser
- Whether to write the bot stderr to a file (you can use this to debug your bot)
- Where to connect to the server (you probably won't need to change this)
- What command to run to run your bot.

The Server hosts lobbies to which the clients can connect using lobby ids.
If you use the same lobby id you will be in the same game. A lobby can have 2-4
people in it and when it is full the game starts.

The config file located in the `framework` directory has a team name and other
configuration stuff. Make sure to set this up properly with correct IP addresses.

To test we recommend to not show debug output of the `ClientRunner` and not 
show a visualiser. Also create two config files both with different names to 
see the difference between these two bots. Let these two bots join the same 
room and play a match.

## I want use my own language
You can find a copy of the protocol in the repo. And you can use the example 
bots as reference. But keep in mind that this will take a significant amount of
time and you will not have much left to develop the actual bot.

## Bomberman rules
- The map is 14x14 tiles
- A tile can be:
  - Empty, walkable
  - A tree, can be blown up
  - Mountain, can not be blown up
  - Water, same as the mountain
- The game consists of rounds till one or zero players are left
- Each round you can either walk or stand still and either place a bomb or not
- You can not walk through people or stand on the same tile, 
  you also can't stand on the tile a different player stood in the round that you made the move
- You can not walk through bombs, but you can stand on your own if you haven't moved yet
- After a bomb is placed 7 turn go past and it explodes
- A bomb explodes in the shape of an infinite +
- When an explosion hits a tree, it does not go further and the bomb disappears
- When an explosion touches an other bomb it also instantly explodes
- If there are multiple bombs on a line still only one tree dies
- Getting hit by a bomb loses one life
- If you don't have a lives left you lose and die
- Bomberman is the first battle royale and thus after the specified rounds, 
  water comes in 1 tile and everything on those tiles disappears and/or dies
- The time limit per round is 0.5 seconds

## Hints
- Work iteratively, you don't have much time
- Implementing Minimax will take significant time and probably won't be worth it
- The water is very dangerous so really watch out for that
