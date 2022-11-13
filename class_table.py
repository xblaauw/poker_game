import random
import pandas as pd
from poker import Card, Hand, Range, Rank, Combo
from copy import copy, deepcopy


class Table:
    buyin = 100
    smallblind = 1
    bigblind = 2
    players = []
    deck = []
    pot = 0
    effective_stack = None
    action_history = []
    table_history = []
    last_to_raise = None
    iteration = 0
    community_cards = []
    player_ids = []
    previous_player_id = 0
    table_history = []
    table_actions_history = []
    round = 0


    def __init__(self, buyin, smallblind, bigblind, players):
        self.smallblind = smallblind
        self.bigblind = bigblind

        self.players = players
        for ID, player in enumerate(players):
            player.bank = buyin
            player.id = ID
        self.player_ids = [player.id for player in players]

    def refresh_deck(self):
        self.deck = list(Card)
        random.shuffle(self.deck)

    def deal(self):
        for player in self.players:
            player.hand = [self.deck.pop() for _ in range(2)]

    def get_player_options(self, player):
        options = ['fold', 'raise']
        if player.folded:
            return ['folded']
        elif player.stack < self.effective_stack:
            options += ['call']*5
        elif player.stack == self.effective_stack:
            options.append('check')
        return options

    def player_bank_to_stack(self, player, action):
        if action == 'raise':
            amount = self.effective_stack - player.stack + player.get_raise_amount(self)
        elif action == 'call':
            amount = self.effective_stack - player.stack
        elif action == 'smallblind':
            amount = self.smallblind
        elif action == 'bigblind':
            amount = self.bigblind
        else:
            amount = 0
        player.bank -= amount
        player.stack += amount
        self.pot += amount
        return amount

    def get_player_by_id(self, player_id):
        for i in range(len(self.players)):
            if self.players[i].id == player_id:
                return self.players[i]

    def get_next_participant_id(self):
        prev_player_idx = self.player_ids.index(self.previous_player_id)
        if prev_player_idx == len(self.player_ids)-1:
            return self.player_ids[0]
        else:
            return self.player_ids[prev_player_idx + 1]

    def play_hand(self):
        self.refresh_deck()
        self.deal()

        self.betting_round()
        self.br1 = self.get_table_history()
        if self.get_n_unfolded_players() > 1:
            self.flop()
            self.round += 1
            self.betting_round()
            self.br2 = self.get_table_history()
            if self.get_n_unfolded_players() > 1:
                self.turn()
                self.round += 1
                self.betting_round()
                self.br3 = self.get_table_history()
                if self.get_n_unfolded_players() > 1:
                    self.river()
                    self.round += 1
                    self.betting_round()
                    self.br4 = self.get_table_history()
        # winning_player_id = self.get_winner_id()
        # self.distribute_winnings(winning_player_id=winning_player_id)

        # self.pot = 0

    def get_winner_id(self):
        hands = [player.hand for player in self.players]

    def set_effective_stack(self):
        stacks = []
        for player in self.players:
            if not player.folded:
                stacks.append(player.stack)
        self.effective_stack = max(stacks)

    def get_n_unfolded_players(self): return sum([not player.folded for player in self.players])

    def betting_round(self):
        # next player is player with index = 0
        self.previous_player_id = self.players[-1].id
        self.last_to_raise = 999999
        self.first_pass_players = len(self.players)
        while True:

            if self.iteration == 0: # small blind
                player_id = self.player_ids[0]
                player = self.get_player_by_id(player_id)
                action = 'smallblind'
            elif self.iteration == 1: # big blind
                player_id = self.player_ids[1]
                player = self.get_player_by_id(player_id)
                action = 'bigblind'
                self.last_to_raise = player.id
            else: # every other iteration after the big blind
                player_id = self.get_next_participant_id()
                player = self.get_player_by_id(player_id)

                # todo: end iteration function
                last_remaining = self.check_last_remaining(player)
                last_to_raise = player.id == self.last_to_raise
                if last_remaining or (last_to_raise and self.first_pass_players <= 0):
                    break

                options = self.get_player_options(player)
                action = player.evaluate_options(options, table=self)

                if action == 'raise':
                    self.last_to_raise = player.id
                elif action == 'fold':
                    player.folded = True
                elif action == 'folded':
                    pass

            bank_to_stack = self.player_bank_to_stack(player, action)
            self.set_effective_stack()
            self.pot = sum([player.stack for player in self.players])
            self.record_step(player=player, action=action, bank_to_stack=bank_to_stack)

            self.previous_player_id = player.id
            self.first_pass_players -= 1
            print('it: ', self.iteration)
            self.iteration += 1

    def check_last_remaining(self, player):
        others_folded = []
        for p in self.players:
            if p.id != player.id:
                others_folded.append(p.folded)
        return all(others_folded)

    def flop(self): self.community_cards.append([self.deck.pop() for _ in range(3)])

    def turn(self): self.community_cards.append([self.deck.pop() for _ in range(1)])

    def river(self): self.community_cards.append([self.deck.pop() for _ in range(1)])

    def get_table_history(self): return pd.DataFrame(self.table_actions_history).set_index('iteration')

    def record_step(self, player, action, bank_to_stack):
        tablestate = pd.Series({
            'iteration': self.iteration,
            'current_player_id': player.id,
            'current_player_name': player.name,
            # 'player_hand': player.hand,
            'action': action,
            'effective_stack': self.effective_stack,
            'bank_to_stack': bank_to_stack,
            'prev_player_id': self.previous_player_id,
            'pot': self.pot,
            'round': self.round,
            'first_pass_players': self.first_pass_players
        })
        player_states = []
        for player in self.players:
            player_state = pd.Series({
                'bank': player.bank,
                'stack': player.stack,
            }).add_suffix('_player_'+str(player.id))
            player_states.append(player_state)
        tablestate = pd.concat([tablestate, pd.concat(player_states)])
        self.table_actions_history.append(tablestate)
        self.table_history.append(copy(self))



