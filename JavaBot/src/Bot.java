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
        choices.add(new Coordinate(0, 0));
        List<Coordinate> result = new ArrayList<>();
        for (Coordinate choice : choices){
            if (state.getBoard().on_board(choice) && state.getBoard().getTile(pos.add(choice)) == Tile.EMPTY)
                result.add(choice);
        }
        return result;
    }
    
}
