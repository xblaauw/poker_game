import random
from treys import Deck, Card, Evaluator, PLOEvaluator
import pandas as pd
import numpy as np
from joblib import Parallel, delayed
from time import sleep

random.seed = 1

class Player:
    all_in = False
    folded = False
    eval = Evaluator()
    def __init__(self, name):
        self.name = name

    def get_action(self, options, table):
        return random.choice(options)

    def get_raise(self, table):
        raise_amount = 4
        total = table.max_bet - self.bet + raise_amount
        _max = self.stack-1
        amount = min(total, _max)
        return amount

    def active(self):
        return not (self.folded or self.all_in)

    def get_hand_score(self, board=[]):
        if len(board) >= 3:
            self.hand_score = self.eval.evaluate(hand=self.hand, board=board)
            return self.hand_score
        else:
            return 4000


class Table:
    eval = Evaluator()
    rounds = ['preflop', 'flop', 'turn', 'river']
    round = 0
    played_hands_n = 0
    action_history = []
    board = []
    bust_players = []

    def __init__(self, sblind, bblind, start_stack, players):
        self.players = players
        self.sblind = sblind
        self.bblind = bblind
        self.start_stack = start_stack

        self.max_bet = 0
        for idx, p in enumerate(self.players):
            p.stack = self.start_stack
            p.idx = idx

    def player_stack_to_bet(self, player, amount):
        player.stack -= amount
        player.bet += amount
        self.pot += amount

    def rotate_roles(self): self.players.append(self.players.pop(0))

    def reindex_players(self):
        for idx, p in enumerate(self.players):
            p.idx = idx

    def play_multiple_hands(self, n_hands=1000):
        i = 0
        while True:
            # move busted players to self.bust_players
            bust_players_idx = []
            for p in self.players:
                if p.stack <= 0:
                    bust_players_idx.append(p.idx)
                    self.bust_players.append(self.players.pop(p.idx))
                    self.reindex_players()
            n_players = len(self.players)
            if (n_players <= 1) or (i > n_hands):
                break
            else:
                self.play_hand()
            i += 1
        print('winner all hands', [p.idx for p in self.players])

    def prep_table(self):
        # reset table parameters to starting position
        self.pot = 0 # shouldn't be necessary
        self.board, self.flop, self.turn, self.river = [], [], [], []
        self.max_bet = 0
        self.deck = Deck()

        # reset player parameters to starting position and deal cards
        for player in self.players:
            player.bet = 0
            player.all_in = False
            player.folded = False
            player.hand = self.deck.draw(2)

        # set small and big blind
        self.player_stack_to_bet(self.players[0], self.sblind)
        self.player_stack_to_bet(self.players[1], self.bblind)

        # the button is the small blind in heads up poker and the 3rd player with 3+ players
        self.max_bet = bblind
        if len(self.players) > 2:
            self.next_player_idx = 2
        else:
            self.next_player_idx = 0

    def play_hand(self):

        self.prep_table()

        if len(self.players) > 1:

            self.betting_round()
            self.next_player_idx = 0
            self.round = 1

            if not self.all_players_inactive():
                self.flop = self.deck.draw(3)
                self.board += self.flop
                self.betting_round()
                self.next_player_idx = 0
                self.round = 2

                if not self.all_players_inactive():
                    self.turn = self.deck.draw(1)
                    self.board += self.turn
                    self.betting_round()
                    self.next_player_idx = 0
                    self.round = 3

                    if not self.all_players_inactive():
                        self.river = self.deck.draw(1)
                        self.board += self.river
                        self.betting_round()
                        self.next_player_idx = 0
                        self.round = 4

            if len(self.flop) < 3:
                self.flop = self.deck.draw(3)
                self.board += self.flop
            if len(self.turn) < 1:
                self.turn = self.deck.draw(1)
                self.board += self.turn
            if len(self.river) < 1:
                self.river = self.deck.draw(1)
                self.board += self.river

            self.distribute_pot()
            self.rotate_roles()
            self.reindex_players()
            self.played_hands_n += 1
        else:
            pass

    def get_next_player_idx(self):
        next_idx = self.next_player_idx + 1
        if next_idx >= len(self.players):
            return 0
        else:
            return next_idx

    def get_unfolded_players_idx(self):
        unfolded_players_idx = []
        for p in self.players:
            if not p.folded:
                unfolded_players_idx.append(p.idx)
        return unfolded_players_idx

    def distribute_pot(self):
        df = pd.DataFrame(
            data={
                'names': [p.name for p in self.players],
                'bets': [p.bet for p in self.players],
                'scores': [p.get_hand_score(self.board) for p in self.players],
                'folded': [p.folded for p in self.players]
                },
            index=[p.idx for p in self.players])

        unfolded_players = df.loc[~df['folded']]
        valid_bets = unfolded_players['bets'].sort_values().unique()
        main_pot_max_bet = valid_bets.min()
        main_pot = sum([min(main_pot_max_bet, p.bet) for p in self.players])
        main_pot_winners = unfolded_players.loc[unfolded_players['scores'] == unfolded_players['scores'].min()]
        n_main_pot_winners = len(main_pot_winners)
        for winner_idx in main_pot_winners.index:
            self.players[winner_idx].stack += main_pot / n_main_pot_winners


        if len(valid_bets) > 1:
            sub_pots = pd.Series(valid_bets, index=valid_bets).diff().dropna()
            for valid_bet, sub_pot_bet in sub_pots.iteritems():
                sub_pot_participants_idx = []
                for p in self.players:
                    if p.bet >= valid_bet: # then you are part of this sub_pot
                        sub_pot_participants_idx.append(p.idx)

                sub_pot_participants = df.loc[sub_pot_participants_idx]
                total_sub_pot = len(sub_pot_participants) * sub_pot_bet
                sub_pot_winners = sub_pot_participants.loc[sub_pot_participants['scores'] == sub_pot_participants['scores'].min()]
                n_sub_pot_winners = len(sub_pot_winners)
                for winner_idx in sub_pot_winners.index:
                    self.players[winner_idx].stack += total_sub_pot / n_sub_pot_winners

    def get_n_active_players(self):
        return len(self.players) - sum([(p.all_in or p.folded) for p in self.players])

    def all_players_inactive(self):
        return sum([(p.all_in or p.folded) for p in self.players]) == len(self.players)

    def betting_round(self):
        betting_round_iter = 0
        self.last_to_raise_player_idx = None
        while True:
            betting_round_iter_limit = betting_round_iter > 20
            last_remaining = len(self.players) < 2
            all_players_inactive = self.all_players_inactive()
            if any([last_remaining, all_players_inactive, betting_round_iter_limit]):
                break
            player = self.players[self.next_player_idx]
            all_players_same_bet = all(player.bet == p.bet if not (p.folded) else True for p in self.players)
            last_to_raise = player.idx == self.last_to_raise_player_idx
            active_players = self.get_n_active_players()
            if betting_round_iter >= active_players:
                if any([last_to_raise, all_players_same_bet]):
                    break

            if player.active():
                options = self.get_player_options(player)
                action = player.get_action(options, self)
                transaction = self.do_action(player, action)
            else:
                options = ['pass']
                action = options[0]
                transaction = 0

            self.player_stack_to_bet(player, transaction)
            if player.stack < 1:
                player.all_in = True

            # print(player.idx, betting_round_iter, self.max_bet, transaction, action, options, player.folded, player.all_in, player.stack, player.bet)
            self.action_history.append(self.record_action(betting_round_iter, active_players, player, action, options, transaction))
            self.max_bet = self.get_max_bet()
            self.next_player_idx = self.get_next_player_idx()
            betting_round_iter += 1

    def record_action(self, betting_round_iter, active_players, player, action, options, transaction):
        out = {
            'played_hands_n': self.played_hands_n,
            'n_players': len(self.players),
            'hand_active_players': active_players,
            'round': self.round,
            'betting_round_iter': betting_round_iter,
            'table_max_bet': self.max_bet,
            'table_pot': self.pot,
            'player_name': player.name,
            'player_idx': player.idx,
            'action': action,
            'options': set(options),
            'transaction': transaction,
            'player_stack': player.stack,
            'player_bet': player.bet,
            'player_folded': player.folded,
            'player_all_in': player.all_in,
            'player_hand': player.hand,
            'table_last_to_raise_player_idx': self.last_to_raise_player_idx,
            'all_money': sum([p.stack for p in self.players]) + self.pot,
            'bust_player_money': sum([p.stack for p in self.bust_players])
        }
        return pd.Series(out)

    def get_action_history(self):
        df = pd.DataFrame(self.action_history)
        # df = df.loc[df['action'] != 'pass']
        return df

    def get_max_bet(self):
        bets = [p.bet for p in self.players]
        return max(bets)

    def do_action(self, player, action):
        if action == 'fold':
            player.folded = True
            transaction = 0
        elif action == 'check':
            transaction = 0
        elif action == 'call':
            transaction = self.max_bet - player.bet
        elif action == 'raise':
            self.last_to_raise_player_idx = player.idx
            transaction = player.get_raise(self)
        elif action == 'all_in':
            self.last_to_raise_player_idx = player.idx
            player.all_in = True
            transaction = player.stack
        return transaction

    def get_other_players_idx(self, player_idx):
        others_idx = []
        for p in self.players:
            if p.idx != player_idx:
                others_idx.append(p.idx)
        return others_idx

    def get_largest_other_stack(self, player_idx):
        others_idx = self.get_other_players_idx(player_idx)
        stacks = []
        for p_idx in others_idx:
            other = self.players[p_idx]
            stacks.append(other.stack)
        return max(stacks)

    def get_player_options(self, player):
        options = ['fold']
        largest_other_stack = self.get_largest_other_stack(player.idx)
        if player.stack > 0 and player.stack < largest_other_stack:
            options.append('all_in')
        if player.bet == self.max_bet:
            for _ in range(200):
                options.append('check')
        elif player.bet < self.max_bet and player.stack + player.bet > self.max_bet:
            for _ in range(200):
                options.append('call')
        if player.stack > self.max_bet:
            for _ in range(50):
                options.append('raise')
        return options



# todo: bluffai proberen https://github.com/bluffai/bluffai/tree/main/src/bluffai
if __name__ == '__main__':
    start_stack = 1000
    sblind = 2
    bblind = 4

    table = Table(
        sblind=sblind,
        bblind=bblind,
        start_stack=start_stack,
        players=[Player('A'), Player('B'), Player('C'), Player('D')]
    )
    table.play_multiple_hands(n_hands = 500)
    ah = table.get_action_history()

    print('pot', table.pot)
    print(sum([p.stack for p in table.players]))
    print([p.bet for p in table.players])
    # print(ah.to_string())
    # print(ah['round'].value_counts())
    # print(ah['round'].value_counts()>=4)
