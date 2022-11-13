import poker
from poker import Card
import random


class Gamestate:
    states = []

    def __init__(self):
        pass

    def add_state(self, table): self.states.append(table)


class Player:
    name, money = None, 0
    hand = None
    loc = None
    stack = 0

    def __init__(self, name, buy_in):
        self.name = name
        self.money = buy_in

    def add_hand(self, hand): self.hand = hand

    def add_location(self, location): self.loc = location

    def add_to_stack(self, target_amount):
        if target_amount >= self.money:
            a = self.money
        else:
            a = target_amount
        self.money -= a
        self.stack += a
        return a

    def _raise(self, stake, amount):
        if stake > self.stack:
            a = stake-self.stack + amount
        else:
            a = amount
        a = self.add_to_stack(a)
        return a

    def _call(self, stake):
        a = stake-self.stack
        a = self.add_to_stack(a)
        return a

    def _check(self):
        return 0

    def _fold(self):
        self.stack=0
        self.hand=None
        return 0

    def get_options(self, gamestate):
        options = ['raise', 'fold']
        state = gamestate.states[-1]
        stake = state.stake

        if stake == self.stack:
            options.append('check')
        if stake > self.stack:
            options.append('call')

    def make_info(self, gamestate):
        # formatting/ parsing function to guide later decision making processes in chose_action
        return None

    def chose_action(self, options, info):
        if info is None:
            action = input(f'chose action from {options}:')
            if action == 'random':
                return action random.choice(options)
            return action

    def do_action(self, gamestate):
        options = self.get_options(gamestate)
        info = self.make_info(gamestate)
        action = self.chose_action(options, info)

        if action == 'fold':
            change_to_pot = self.fold()
            return action, change_to_pot
        elif action == 'raise':
            change_to_pot = self._raise()
        elif action == 'call':
            change_to_pot = self.call()
        else:
            change_to_pot = self.check()

        return action, change_to_pot


class Table:
    sblind = 1
    bblind = 2
    buy_in = 100
    deck = list(Card)
    random.shuffle(deck)
    players = []
    round = 0
    pot = 0
    stake = 0
    betround = 0
    gamestate = Gamestate()

    def __init__(self, sblind, bblind, buy_in):
        self.sblind = sblind
        self.bblind = bblind
        self.buy_in = buy_in

    def add_player(self, player): self.players.append(player)

    def play_round(self):
        self.assign_player_positions()
        self.deal_hands()
        self.gamestate.add_state(self)
        self.bet_round()
        self.flop()
        self.bet_round()
        self.turn()
        self.bet_round()
        self.river()
        self.bet_round()
        self.end_game()

    def assign_player_positions(self):
        # player 0 is small blind, player 1 is big blind etc
        random.shuffle(self.players)
        for i, player in enumerate(self.players):
            player.add_location(i)

    def deal_hands(self):
        for player in self.players:
            player_hand = [self.deck.pop() for _ in range(2)]
            player.add_hand(hand=player_hand)

    def add_to_pot(self, amount):
        self.pot += amount

    def bet_round(self):
        for play



table = Table(10, 20, 1000)
table.add_player(Player(name='p1', buy_in=table.buy_in))
table.add_player(Player(name='p2', buy_in=table.buy_in))
table.add_player(Player(name='p3', buy_in=table.buy_in))

table.start_game()



