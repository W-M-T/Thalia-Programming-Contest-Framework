import java.awt.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;


public class Board {
        
    public static final int FIELD_SIZE = 15;

    private Tile[][] board;

    public Board() {
        board = new Tile[FIELD_SIZE][FIELD_SIZE];

        for(Tile[] row : board)
            Arrays.fill(row, Tile.EMPTY);

    }

    private Board(Tile[][] board) {

        Tile[][] copy = new Tile[FIELD_SIZE][FIELD_SIZE];
        for (int y = 0; y < FIELD_SIZE; y++){
            for (int x = 0; x < FIELD_SIZE; x++){
                copy[x][y] = board[x][y];
            }
        }
        this.board = copy;
    }

    boolean on_board(int x, int y) {
        return x >= 0 && x < FIELD_SIZE && y >= 0 && y < FIELD_SIZE;
    }

    Tile getTile(Coordinate c) {
        return board[c.getX()][c.getY()];
    }

    void setTile(Coordinate c, Tile val) {
        board[c.getX()][c.getY()] = val;
    }

    @Override
    public String toString() {
        StringBuilder s = new StringBuilder();
        for (Tile[] row : board){
            for (Tile tile : row){
                s.append(tile).append(", ");
            }
            s.append('\n');
        }
        return s.toString();
    }

    public Board copy(){
        return new Board(board);
    }
}
