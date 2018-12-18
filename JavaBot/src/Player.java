import java.util.ArrayList;
import java.util.List;

public class Player {
    private String pID;
    private Coordinate pos;
    private int lives;
    private String name;
    private boolean alive;

    public Player(String pID, Coordinate pos, int lives, String name) {
        this.pID = pID;
        this.pos = pos;
        this.lives = lives;
        this.name = name;
        alive = true;
    }

    public List<Coordinate> getLegalDirs(GameState state){
        List<Coordinate> choices = new ArrayList<>();
        choices.add(new Coordinate(-1, 0));
        choices.add(new Coordinate(1, 0));
        choices.add(new Coordinate(0, -1));
        choices.add(new Coordinate(0, 1));
        choices.add(new Coordinate(0, 0));
        List<Coordinate> result = new ArrayList<>();
        for (Coordinate choice : choices){
            if (state.getBoard().on_board(pos.add(choice)) && state.getBoard().getTile(pos.add(choice)) == Tile.EMPTY && !state.hasBomb(pos.add(choice)))
                result.add(choice);
        }
        return result;
    }

    public void kill() {
        alive = false;
    }

    public void hit(){
        lives--;
    }

    public String getpID() {
        return pID;
    }

    public void setpID(String pID) {
        this.pID = pID;
    }

    public Coordinate getPos() {
        return pos;
    }

    public void setPos(Coordinate pos) {
        this.pos = pos;
    }

    public int getLives() {
        return lives;
    }

    public void setLives(int lives) {
        this.lives = lives;
    }

    public String getName() {
        return name;
    }

    public boolean isAlive() {
        return alive;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Player copy(){
        return new Player(pID, pos.copy(), lives, name);
    }
}
