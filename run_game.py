from class_table import Table
# from class_gamestate import Gamestate
from class_player import Player
from poker import Card, Hand, Range, Rank, Combo
import pandas as pd


if __name__ == '__main__':
    player1 = Player(name='p1')
    player2 = Player(name='p2')
    player3 = Player(name='p3')
    player4 = Player(name='p4')
    player5 = Player(name='p5')
    players = [player1, player2, player3, player4, player5]

    table = Table(buyin=1000, smallblind=2, bigblind=4, players=players)

    table.play_hand()
    br1 = table.br1
    br2 = table.br2
    br3 = table.br3
    br4 = table.br4