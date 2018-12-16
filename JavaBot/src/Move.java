public class Move {
    Coordinate direction;
    boolean bomb;

    public Move(Coordinate direction, boolean bomb) {
        this.direction = direction;
        this.bomb = bomb;
    }

    public Coordinate getDirection() {
        return direction;
    }

    public void setDirection(Coordinate direction) {
        this.direction = direction;
    }

    public boolean isBomb() {
        return bomb;
    }

    public void setBomb(boolean bomb) {
        this.bomb = bomb;
    }
}
