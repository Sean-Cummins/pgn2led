#!/usr/bin/env python

import io
import sys
import argparse
import fileinput
from pathlib import Path

from PIL import Image
from pynput.keyboard import Key, Listener
import chess
import chess.pgn

PIECES = {
    "b": 'assets/pieces/b.png',
    "k": 'assets/pieces/k.png',
    "n": 'assets/pieces/n.png',
    "p": 'assets/pieces/p.png',
    "q": 'assets/pieces/q.png',
    "r": 'assets/pieces/r.png',
    "B": 'assets/pieces/B.png',
    "K": 'assets/pieces/K.png',
    "N": 'assets/pieces/N.png',
    "P": 'assets/pieces/P.png',
    "Q": 'assets/pieces/Q.png',
    "R": 'assets/pieces/R.png',
}

DEFAULT_COLORS = {
    "square light": "#f0d9b5", #(240, 217, 181)
    "square dark": "#b58863", #(181, 136, 99)
    "square dark lastmove": "#aba23a", #(171,162,58)
    "square light lastmove": "#ced26b", #(206,210,107)
}

LIGHT_SQUARES = ['a2','a4','a6','a8',
                'b1','b3','b5','b7',
                'c2','c4','c6','c8',
                'd1','d3','d5','d7',
                'e2','e4','e6','e8',
                'f1','f3','f5','f7',
                'g2','g4','g6','g8',
                'h1','h3','h5','h7']

DARK_SQUARES = ['a1','a3','a5','a7',
                'b2','b4','b6','b8',
                'c1','c3','c5','c7',
                'd2','d4','d6','d8',
                'e1','e3','e5','e7',
                'f2','f4','f6','f8',
                'g1','g3','g5','g7',
                'h2','h4','h6','h8']

pieces = {piece: Image.open(Path(file)) for piece, file in PIECES.items()}

def pgn2png(pgn, max_width = 128, max_height = 128, piece_width = 16, piece_height = 16, pieces = pieces, defaults = DEFAULT_COLORS):
    
    board = pgn.board()

    for move in pgn.mainline_moves():
        board.push(move) #get to current position
    
    piece_map = board.piece_map()

    if pgn.mainline_moves():
        last_move = [chess.square_name(move.from_square), chess.square_name(move.to_square)]
    else:
        last_move = []

    img = Image.new('RGB', (max_width, max_height))
    
    def is_light_square(square_name):
        if any(square==square_name for square in LIGHT_SQUARES):
            return True
        else:
            return False
    
    def is_dark_square(square_name):
        if any(square==square_name for square in DARK_SQUARES):
            return True
        else:
            return False
    
    def square_to_colour(square):
        square_name = chess.square_name(square)

        if is_light_square(square_name):
            if square_name in last_move:
                return defaults["square light lastmove"]
            else:
                return defaults["square light"]

        elif is_dark_square(square_name):
            if square_name in last_move:
                return defaults["square dark lastmove"]
            else:
                return defaults["square dark"]
        else: 
            return

    #render board and pieces
    #reversed: PIL uses (0,0) in the upper left corner, i.e A8->H1 but python-chess goes A1->H8 
    for i, x in enumerate(reversed(range(0, max_width, piece_width))):
        for j, y in enumerate(range(0, max_height, piece_height)): 
                        
            x1 = y
            y1 = y + piece_height 
            x2 = x
            y2 = x + piece_height
            
            square = chess.square(j,i)
            
            # board
            colour = square_to_colour(square)
                        
            img.paste(colour,(x1,x2, y1,y2))
                 
            # pieces
            if square in piece_map.keys(): #square has a piece                          
                get_piece = str(piece_map[square])
                img.paste(pieces[get_piece],(x1,x2), mask=pieces[get_piece])
 
    return img

def is_end_of_pgn(line):
    for result in ['*', '1/2-1/2', '1-0', '0-1']:
        if line.strip().endswith(result):
            return True
    else:
        return False

def process_pgn(lines):
    lines = io.StringIO(lines) #chess.pgn needs StringIO 
    pgn = chess.pgn.read_game(lines)
    return pgn  

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='*', default = sys.stdin, 
        help='files to read, if empty, stdin is used')
    parser.add_argument('--output', default = sys.stdout, 
        help='output file, if empty, stdout is used') 
    parser.add_argument('--broadcast', dest='broadcast', default=False, action='store_true', 
        help='toggle which pgn to follow and send to output using tab key')
    args = parser.parse_args()

    channel = 0
    pgns = []

    if args.broadcast:

        def on_press(key):
            global channel 
            if key == Key.tab:
                if pgns:
                    channel = cycle(pgns, channel)
                    img = pgn2png(pgns[channel])
                    img.save(args.output, 'PNG')

        def cycle(pgns, channel):
            if channel < len(pgns):
                channel = channel + 1
            if channel >= len(pgns):
                channel = 0
            return channel

        listener = Listener(on_press=on_press)
        listener.start()        

    try:
        lines = ''
        for line in fileinput.input(args.input):
            lines+=line.lstrip() # curl/lichess bug? randomly adding single leading space char to start of pgns throwing pgn parser
            if is_end_of_pgn(line):
                pgn = process_pgn(lines)
                if args.broadcast:
                    if any(game.headers == pgn.headers for game in pgns):#update existing
                        pgns = [pgn if pgn.headers == game.headers else game for game in pgns]
                    else:
                        pgns.append(pgn)

                    if pgn.headers == pgns[channel].headers:#ouput if match channel select
                        img = pgn2png(pgn)
                        img.save(args.output, 'PNG')  
                else:
                    img = pgn2png(pgn)
                    img.save(args.output, 'PNG')  
                lines = ''

    except KeyboardInterrupt:
        sys.stdout.flush()
        pass     
