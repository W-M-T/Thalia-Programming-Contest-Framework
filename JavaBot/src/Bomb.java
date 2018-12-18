public class Bomb {
    private Coordinate pos;
    private int timer;
    private boolean isPrimed;

    public Bomb(Coordinate pos, int timer) {
        this.pos = pos;
        this.timer = timer;
        isPrimed = false;
    }

    public Coordinate getPos() {
        return pos;
    }

    public void setPrimed(){
        isPrimed = true;
    }

    public boolean isPrimed() {
        return isPrimed;
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
