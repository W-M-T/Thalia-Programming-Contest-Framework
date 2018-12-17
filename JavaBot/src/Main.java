/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/**
 *
 * @author nick
 */
public class Main {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        Bot yourBot = new ExampleBot();
        GameHandler handler = new GameHandler(yourBot);
        Parser p = new Parser(handler);
        p.run();
    }
    
}
