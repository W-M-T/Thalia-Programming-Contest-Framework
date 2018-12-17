import java.util.ArrayList;
import java.util.List;

public abstract class Bot {
    
    public abstract void initialize();

    public abstract Move nextMove(GameState state);

    public List<Coordinate> getLegalDirs(GameState state){
        Coordinate pos = state.getPlayer(state.getYou()).getPos();
        List<Coordinate> choices = new ArrayList<>();
        choices.add(new Coordinate(-1, 0));
        choices.add(new Coordinate(1, 0));
        choices.add(new Coordinate(0, -1));
        choices.add(new Coordinate(0, 1));
        for (Coordinate choice : choices){
            if (choice.getX() < 0 || choice.getX() >= Board.FIELD_SIZE ||
                    choice.getY() < 0 || choice.getY() >= Board.FIELD_SIZE ||
                    state.getBoard().getTile(pos.add(choice)) != Tile.EMPTY
            )
                choices.remove(choice);
        }
        return choices;
    }
    
}
