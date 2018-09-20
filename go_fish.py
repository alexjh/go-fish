#!/usr/bin/env python

import random
from pprint import pprint
from collections import namedtuple, Counter


def shuffle_cards(state):
    return Shuffle()


def deal_card(state, player):
    return Fish(player)


def move_human(state):
    print("Player:")
    pprint(sorted(state.players[state.player].hand))
    pprint(sorted(state.players[state.player].found))

    request = input("Enter card to request: <Player> <Card>, ? for help ")
    target, card = request.split()

    return Ask(int(card), state.player, int(target))


def move_cpu(state):
    # AJH Better intelligence for choosing card
    request = random.choice(state.players[state.player].hand)[0]
    victim = random.choice(
        [index for index, player in enumerate(state.players) if index != state.player]
    )
    print("%d says: %d do you have a %d" % (state.player, victim, request))
    return Ask(request, state.player, victim)


def main():
    players = int(input("Enter number of players: "))

    states = (
        GameState(get_cards(), get_players(players), random.randint(0, players - 1)),
    )


    # AJH Deal with initial matches?
    # If they have a match, can a player ask for a card?
    # Will multiple matches be recorded on their next turn?

    # Deck is in intial state, so start playing until the game is done
    while not states[-1].is_finished:
        if states[-1].needs_dealing:
            for i in range(get_dealt_cards(players)):
                for index, player in enumerate(states[-1].players):
                    deal = deal_card(states[-1], index)
                    states = deal.apply(states)

        if states[-1].player == 0:
            move = move_human(states[-1])
        else:
            move = move_cpu(states[-1])
        states = move.apply(states)

        if not states[-1].players[states[-1].player].received:
            print("-> Go fish")
            move = Fish(states[-1].player)
            states = move.apply(states)

        if states[-1].has_match:
            move = Found(states[-1].player)
            states = move.apply(states)

            print(
                "Asked for {0}, found {1}".format(
                    states[-1].players[states[-1].player].asked,
                    states[-1].players[states[-1].player].found[-1],
                )
            )

        print(
            "{0} asked for {1}, got {2}".format(
                states[-1].player,
                states[-1].players[states[-1].player].asked,
                states[-1].players[states[-1].player].received,
            )
        )

        if states[-1].players[states[-1].player].received:
            if (
                states[-1].players[states[-1].player].asked
                != states[-1].players[states[-1].player].received[0][0]
            ):
                move = Next()
                states = move.apply(states)
        else:
            move = Next()
            states = move.apply(states)

    pprint(states[-1])

    print("Winner: ")
    pprint(find_winner(states))


def find_winner(states):
    """

    Find the players with the highest counts of cards. Note that there can be
    multiple winners.

    >>> states = (GameState((), (PlayerState(), PlayerState()), 0),)
    >>> find_winner(states)
    [0, 1]
    >>> states = (GameState((), (PlayerState(found=(1,2)), PlayerState(found=(1,2))), 0),)
    >>> find_winner(states)
    [0, 1]
    >>> states = (GameState((), (PlayerState(), PlayerState(found=(1,2))), 0),)
    >>> find_winner(states)
    [1]
    """

    winners = []
    count = 0
    for index, player in enumerate(states[-1].players):
        if len(player.found) == count:
            winners.append(index)
        if len(player.found) > count:
            winners = [index]
            count = len(player.found)

    return winners


class Shuffle(namedtuple("_Shuffle", "")):
    def apply(self, game_states):
        return game_states + (game_states[-1].shuffle(),)


class Fish(namedtuple("_Fish", "player")):
    def apply(self, game_states):
        if not game_states[-1].deck:
            return game_states

        return game_states + (game_states[-1].fish(self.player),)


class Next(namedtuple("_Next", "")):
    def apply(self, game_states):
        return game_states + (game_states[-1].next_player(),)


class Found(namedtuple("_Found", "player")):
    def apply(self, game_states):
        return game_states + (game_states[-1].found(self.player),)


class Ask(namedtuple("_Ask", "card player target")):
    def apply(self, game_states):
        if self.player == self.target:
            return game_states

        found_cards = tuple(
            [
                card
                for card in game_states[-1].players[self.target].hand
                if card[0] == self.card
            ]
        )

        if not found_cards:
            return game_states + (game_states[-1].didnt_find(self.card),)

        return game_states + (
            game_states[-1].move_cards(self.target, self.player, found_cards),
        )


def parse_request(request):
    """
    >>> parse_request("")
    None
    >>> parse_request(" ")
    None
    >>> parse_request("0")
    None
    >>> parse_request("K 99")
    None
    >>> parse_request("A 2")
    (1, 2)
    >>> parse_request("4 2")
    (4, 2)
    """

    card, player = request.split()

    if card is None or player is None:
        return None

    card = card.lower()

    if card == "a":
        card = 1
    elif card == "j":
        card = 11
    elif card == "q":
        card = 12
    elif card == "k":
        card = 13
    else:
        try:
            card = int(card)
        except:
            return None

    if card < 1 or card > 13:
        return None

    try:
        player = int(player)
    except:
        return None

    if player < 1:
        return None

    return card, player - 1


def get_cards():
    deck = [(card, suit) for card in range(1, 14) for suit in "cdhs"]
    random.shuffle(deck)
    return tuple(deck)


def get_players(num_players):
    return (PlayerState(),) * num_players


def get_dealt_cards(num_players):
    """

    >>> get_dealt_cards(2)
    7
    >>> get_dealt_cards(4)
    5
    """
    num_cards = 7
    if num_players > 3:
        num_cards = 5
    return num_cards


class GameState(namedtuple("_Game", ["deck", "players", "player"])):
    @property
    def has_match(self):
        if not self.players[self.player].hand:
            return False

        cards = Counter([card[0] for card in self.players[self.player].hand])

        for card, count in cards.items():
            if count == 4:
                return True

        return False

    @property
    def needs_dealing(self):
        dealt_cards = get_dealt_cards(len(self.players))

        return len(self.deck) + dealt_cards > 52

    @property
    def is_finished(self):
        if not self.deck:
            return True

        if self.needs_dealing:
            return False

        for player in self.players:
            if not player.hand:
                return True

        return False

    # TODO move this outside of gamestate
    def need_to_fish(self, last_hand):
        return self.players[self.player].hand == last_hand

    def shuffle(self):
        if not self.deck:
            return self

        deck = list(self.deck)
        random.shuffle(deck)

        return GameState(tuple(deck), self.players, self.player)

    def next_player(self):
        return GameState(
            self.deck, self.players, (self.player + 1) % len(self.players),
        )

    def fish(self, player):
        if not self.deck:
            return self

        if player == 0:
            print("Drew a {0}".format(self.deck[-1]))

        return GameState(
            self.deck[:-1],
            replace(
                self.players,
                player,
                PlayerState(
                    self.players[player].hand + (self.deck[-1],),
                    self.players[player].found,
                    (self.deck[-1],),
                    self.players[player].asked,
                ),
            ),
            self.player,
        )

    def found(self, player):
        card_count = Counter([card[0] for card in self.players[self.player].hand])

        matched_cards = [card for card, count in card_count.items() if count == 4]

        cards = tuple(
            [
                card
                for card in self.players[self.player].hand
                if card[0] in matched_cards
            ]
        )

        return GameState(
            self.deck,
            replace(
                self.players,
                player,
                PlayerState(
                    remove(self.players[player].hand, cards),
                    self.players[player].found + cards,
                    self.players[player].received,
                    self.players[player].asked,
                ),
            ),
            self.player,
        )

    def didnt_find(self, card):
        return GameState(
            self.deck,
            replace(
                self.players,
                self.player,
                PlayerState(
                    self.players[self.player].hand,
                    self.players[self.player].found,
                    tuple(),
                    card,
                ),
            ),
            self.player,
        )

    def move_cards(self, source, dest, cards):
        # TODO Block moving 4 cards?

        return GameState(
            self.deck,
            replace(
                replace(
                    self.players,
                    source,
                    PlayerState(
                        remove(self.players[source].hand, cards),
                        self.players[source].found,
                        tuple(),
                        self.players[source].asked,
                    ),
                ),
                dest,
                PlayerState(
                    self.players[dest].hand + cards,
                    self.players[dest].found,
                    cards,
                    cards[0][0],
                ),
            ),
            self.player,
        )


class PlayerState(namedtuple("_Player", ["hand", "found", "received", "asked"])):
    pass


PlayerState.__new__.__defaults__ = (tuple(), tuple(), tuple(), tuple())


def replace(tpl, idx, value):
    return tpl[:idx] + (value,) + tpl[idx + 1 :]


def remove(tpl, values):
    return tuple([card for card in tpl if card not in values])


def append(tpl, value):
    return tpl + (value,)


main()
