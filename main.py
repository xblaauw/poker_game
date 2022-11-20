import random
from treys import Deck, Card, Evaluator, PLOEvaluator
import pandas as pd
import numpy as np
from joblib import Parallel, delayed


def format_cards_str(cards):
    return '    '.join([Card.int_to_pretty_str(c).replace('[', '').replace(']','') for c in cards])

class Player:
    hand: list[int] = []
    pretty_hand: str = None
    score: int = None
    class_: str = None

    def __init__(self):
        pass

e = Evaluator()
n_p = 5

# def job(e, n_p):
d = Deck()

flop = d.draw(3)
turn = d.draw(1)
river = d.draw(1)
board = flop+turn+river

players = []
for n in range(n_p):
    player = Player()
    player.n = n
    player.hand = d.draw(2)
    player.pretty_hand = format_cards_str(player.hand)
    players.append(player)



# e.hand_summary(board, [player.hand for player in players])

    # return out

data = Parallel(n_jobs=-1)(delayed(job)(e, n_p) for _ in range(50000))
df = pd.DataFrame(data)
df['winner_score'] = df[['p1_score', 'p2_score']].min(axis=1)
df['winner'] = df[['p1_score', 'p2_score']].idxmin(axis=1).map({'p1_score': 'p1', 'p2_score': 'p2'})

df.describe()
df[['p1_score', 'p2_score']].idxmin()

t = pd.read_csv('winchances_url_https://caniwin.com/texasholdem/preflop/heads-up.php_.csv'.replace('/', '_'), index_col=0)
t['c1'] = t['Name'].str[0]
t['c2'] = t['Name'].str[1]
t['s'] = t['Name'].str[2]

card_order = ['A', 'K', 'Q', 'J', 'T'] + list(str(x) for x in range(9,1,-1))
m_o = t.loc[t['s']=='o'][['c1','c2','Win %']].set_index(['c1','c2']).squeeze().unstack('c2')
m_s = t.loc[t['s']=='s'][['c1','c2','Win %']].set_index(['c1','c2']).squeeze().unstack('c2').T
m = m_o.fillna(m_s)
m = m.loc[card_order, card_order]
mv = m.values
mv_masked = m.clip(50).replace(50, 0).values
m_masked = m.copy()
m_masked[:] = mv_masked

