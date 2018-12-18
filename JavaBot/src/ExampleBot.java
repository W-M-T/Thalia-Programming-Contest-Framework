import java.util.List;
import java.util.Random;

public class ExampleBot extends Bot{

    @Override
    public void initialize() {
        // Since there is not a lot of initialization to be done, this can probably be left empty.
    }

    @Override
    public Move nextMove(GameState state) {
        Random random = new Random();
        List<Coordinate> choices = state.getPlayer(state.getYou()).getLegalDirs(state);
        Coordinate c = choices.get(Math.abs(random.nextInt()) % choices.size());
        boolean b;
        if (c.equals(new Coordinate(0, 0)))
            b = false;
        else
            b = random.nextInt() % 2 == 0;
        return new Move(c, b);
    }
}
