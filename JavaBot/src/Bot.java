
public interface Bot {
    
    void initialize(GameState state);

    Move nextMove(GameState state);

}
