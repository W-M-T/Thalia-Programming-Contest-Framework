To get started writing your Bomberman bot, you need to create a new class implementing Bot.java and implement the methods.

The method initialize() is called just before the game begins.
The method nextMove() is called each turn and should return the move you want to make based on the given GameState.

The GameState contains all essential information about the current state of the game.


To run your bot, first export it as a runnable jar file and place this jar in the same folder as ClientRunner.py.
Next, replace the line in the config file saying 'RunCommand = ./../PythonBot/ExampleBot.py' with 'RunCommand = java -jar [botname].jar'