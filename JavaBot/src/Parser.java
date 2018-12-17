/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

import java.util.Arrays;
import java.util.Scanner;

/**
 *
 * @author nick
 */
public class Parser {
    
    private GameHandler handler;
    private Scanner input;

    public Parser(GameHandler handler) {
        this.handler = handler;
        input = new Scanner(System.in);
    }
    
    public void run(){
        boolean done = false;        
        String[] commands;
        
        while(!done){
            String in = input.nextLine();
            in = in.replace(", ", ",");
            commands = in.split(" ");
            
            switch(commands[0]){
                case "CONFIG":
                    parseConfig(commands);
                    break;
                case "START":
                    parseStart(commands);
                    break;
                case "REQUEST":
                    parseRequest(commands);
                    break;
                case "UPDATE":
                    parseUpdate(commands);
                    break;
                default:
                    System.out.println("Unknown command");
                    done = true;
            }
        }
    }

    private void parseConfig(String[] commands){
        handler.handleConfig(commands[1], commands);
    }

    private void parseStart(String[] commands){
        if (commands[1].equals("GAME"))
            handler.startGame();
        else
            System.out.println("Undefined Request");
    }

    private void parseRequest(String[] commands){
        if (commands[1].equals("MOVE"))
                handler.performAction();
        else
            System.out.println("Undefined Request");
    }

    private void parseUpdate(String[] commands){
            handler.handleUpdate(commands[1], commands);
    }
}
