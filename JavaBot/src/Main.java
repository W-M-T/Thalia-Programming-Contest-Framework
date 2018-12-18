
public class Main {
    public static void main(String[] args) {
        // Change to your bot
        Bot yourBot = new ExampleBot();
        GameHandler handler = new GameHandler(yourBot);
        Parser p = new Parser(handler);
        p.run();
    }
    
}
