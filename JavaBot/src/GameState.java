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
    private Player[] players;
    private int you;
    private boolean playing;

    public GameState() {
        board = new Board();
        
        bombs = new ArrayList<>();
        players = new Player[4];
        for (int i = 0; i < 4; i++){
            players[i] = new Player(i, new Coordinate(0, 0), 0, "p" + i);
        }
        you = 0;
        playing = false;
    }
    
    private GameState(Board board, List<Bomb> bombs, Player[] players, int you, boolean playing){
        this.board = board;
        this.bombs = new ArrayList<>(bombs);
        this.players = new Player[4];
        for (int i = 0; i < 4; i++){
            this.players[i] = players[i].copy();
        }
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

    public Player[] getPlayers(){
        return players;
    }

    public Player getPlayer(int i){
        return players[i];
    }

    public void setYou(int you){
        this.you = you;
    }

    public void startPlaying(){
        playing = true;
    }

    public int getYou() {
        return you;
    }

    public boolean isPlaying() {
        return playing;
    }

    public GameState copy(){
        return new GameState(getBoard(), getBombs(), getPlayers(), getYou(), isPlaying());
    }
    
}
