/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 *
 * @author nick
 */
public class GameState {
    
    private Board board;
    private List<Bomb> bombs;
    private List<Player> players;
    private String you;
    private boolean playing;

    public GameState() {
        board = new Board();
        
        bombs = new ArrayList<>();
        players = new ArrayList<>();
        for (int i = 0; i < 4; i++)
            players.add(new Player("p" + (i+1), new Coordinate(0, 0), 0, "none"));
        you = "p0";
        playing = false;
    }
    
    private GameState(Board board, List<Bomb> bombs, List<Player> players, String you, boolean playing){
        this.board = board;
        this.bombs = new ArrayList<>(bombs);
        this.players = players;
        for (int i = 0; i < 4; i++)
            players.add(new Player("p" + (i+1), new Coordinate(0, 0), 0, "none"));
        this.you = you;
        this.playing = playing;
    }
    
    public void setTile(Coordinate c, Tile t){
        this.board.setTile(c, t);
    }


    public Board getBoard() {
        return board.copy();
    }

    public List<Bomb> getBombs(){
        return bombs;
    }


    public List<Player> getPlayers(){
        return players;
    }

    public Player getPlayer(String pID){
        for (Player player : players){
            if (player.getpID().equals(pID))
                return player;
        }
        return null;
    }

    public void setYou(String you){
        this.you = you;
    }

    public void startPlaying(){
        playing = true;
    }

    public String getYou() {
        return you;
    }

    public boolean isPlaying() {
        return playing;
    }

    public GameState copy(){
        return new GameState(getBoard(), getBombs(), getPlayers(), getYou(), isPlaying());
    }
    
}
