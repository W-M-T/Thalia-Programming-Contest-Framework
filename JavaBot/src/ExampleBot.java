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
        List<Coordinate> choices = getLegalDirs(state);
        int m = random.nextInt() % choices.size();
        boolean b = random.nextInt() % 2 == 0;

        return new Move(choices.get(m), b);
    }
}
