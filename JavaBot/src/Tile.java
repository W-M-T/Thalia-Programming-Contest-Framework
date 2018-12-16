/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/**
 *
 * @author nick
 */
public enum Tile {
    WATER, MOUNTAIN, TREE, EMPTY;

    boolean unbreakable() {
        return this == WATER || this == MOUNTAIN;
    }
}
