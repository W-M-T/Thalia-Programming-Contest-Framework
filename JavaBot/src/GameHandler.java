/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

import java.util.List;

/**
 *
 * @author nick
 */
public class GameHandler {

    private GameState state;
    private Bot bot;
    
    
    public GameHandler(Bot bot){
        state = new GameState();
        this.bot = bot;
    }

    public void performAction(){
        Move move = bot.nextMove(state);

        StringBuilder response = new StringBuilder();
        response.append(move.bomb ? "BOMBWALK " : "WALK ");
        if (move.direction.getX() < 0)
            response.append("LEFT");
        else if (move.direction.getX() > 0)
            response.append("RIGHT");
        else if (move.direction.getY() < 0)
            response.append("UP");
        else if (move.direction.getY() > 0)
            response.append("DOWN");

        System.out.println(response.toString());
    }

    public void handleConfig(String type, String[] params){
        switch (type) {
            case "TILE":
                Coordinate coordinate = Coordinate.parseCoordinate(params[2]);
                Tile tile;
                switch (params[3]) {
                    case "WATER": tile = Tile.WATER; break;
                    case "TREE": tile = Tile.TREE; break;
                    case "MOUNTAIN": tile = Tile.MOUNTAIN; break;
                    default: tile = Tile.EMPTY;
                }
                state.setTile(coordinate, tile);
                break;
            case "PLAYER":
                Player player = state.getPlayer(Integer.parseInt(params[3]));
                switch (params[2]){
                    case "PLACE": player.setPos(Coordinate.parseCoordinate(params[4])); break;
                    case "LIVES": player.setLives(Integer.parseInt(params[4])); break;
                    default: player.setName(params[4]);
                }
                break;
            case "YOU":
                state.setYou(Integer.parseInt(params[3]));
        }
    }

    public void startGame(){
        state.startPlaying();
    }

    public void handleUpdate(String type, String[] params){
        switch (type){
            case "PLAYER":
                if (params[2].equals("LOC"))
                    state.getPlayer(Integer.parseInt(params[3])).setPos(Coordinate.parseCoordinate(params[4]));
                else if (params[2].equals("STATUS")){
                    Player player = state.getPlayer(Integer.parseInt(params[3]));
                    if (params[4].equals("DEAD"))
                        player.kill();
                    else if (params[4].equals("HIT")){
                        player.hit();
                    }
                }
                break;
            case "BOMB":
                if (params[2].equals("PLACED"))
                    state.getBombs().add(new Bomb(Coordinate.parseCoordinate(params[3]), 7));
                else if (params[2].equals("EXPLODED")){
                    List<Bomb> bombs = state.getBombs();
                    for (Bomb bomb: bombs){
                        if (bomb.getPos().equals(Coordinate.parseCoordinate(params[3])))
                            bombs.remove(bomb);
                    }
                }
                break;
            case "TILE":
                if (params[2].equals("GONE"))
                    state.getBoard().setTile(Coordinate.parseCoordinate(params[3]), Tile.EMPTY);
                break;
        }
    }
       
}
