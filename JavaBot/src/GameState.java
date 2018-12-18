
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class GameState {
    
    private Board board;
    private List<Bomb> bombs;
    private List<Player> players;
    private List<Integer> waterRounds;
    private String you;
    private int round;
    private boolean playing;
    private boolean gameover;
    private boolean won;

    public GameState() {
        board = new Board();
        
        bombs = new ArrayList<>();
        players = new ArrayList<>();
        for (int i = 0; i < 4; i++)
            players.add(new Player("p" + (i+1), new Coordinate(0, 0), 0, "none"));
        waterRounds = new ArrayList<>();
        you = "p0";
        round = 0;
        playing = false;
        gameover = false;
        won = false;
    }
    
    private GameState(Board board, List<Bomb> bombs, List<Player> players, List<Integer> waterRounds, String you, int round, boolean playing, boolean gameover, boolean won){
        this.board = board;
        this.bombs = new ArrayList<>(bombs);
        this.players = players;
        for (int i = 0; i < 4; i++)
            players.add(new Player("p" + (i+1), new Coordinate(0, 0), 0, "none"));
        this.waterRounds = waterRounds;
        this.you = you;
        this.round = round;
        this.playing = playing;
        this.gameover = gameover;
        this.won = won;
    }

    public boolean hasBomb(Coordinate c){
        for (Bomb bomb : bombs) {
            if (bomb.getPos().equals(c)) {
                return true;
            }
        }
        return false;
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

    public void gameOver(boolean won){
        this.won = won;
        gameover = true;
    }

    public boolean isGameover(){
        return gameover;
    }

    public boolean didWin(){
        return won;
    }

    public void setYou(String you){
        this.you = you;
    }

    public void nextRound(){
        round++;
    }

    public int getRound(){
        return round;
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

    public List<Integer> getWaterRounds() {
        return waterRounds;
    }

    public int getNextWaterRound(){
        int soonest = Integer.MAX_VALUE;
        for (int waterRound : waterRounds){
            if (waterRound > round && waterRound < soonest)
                soonest = waterRound;
        }

        return soonest;
    }

    public void setWaterRounds(List<Integer> waterRounds) {
        this.waterRounds = waterRounds;
    }

    public GameState copy(){
        return new GameState(getBoard(), getBombs(), getPlayers(), getWaterRounds(), getYou(), getRound(), isPlaying(), isGameover(), didWin());
    }
    
}
