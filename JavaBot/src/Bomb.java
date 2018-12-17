public class Bomb {
    private Coordinate pos;
    private int timer;

    public Bomb(Coordinate pos, int timer) {
        this.pos = pos;
        this.timer = timer;
    }

    public Coordinate getPos() {
        return pos;
    }

    public void setPos(Coordinate pos) {
        this.pos = pos;
    }

    public int getTimer() {
        return timer;
    }

    public void setTimer(int timer) {
        this.timer = timer;
    }
}
