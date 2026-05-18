import random
import itertools

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
UNO_COLORS = ['Red', 'Yellow', 'Green', 'Blue']
UNO_RANKS = [str(n) for n in range(0, 10)] + ['Skip', 'Reverse', 'Draw Two']
DIFFICULTIES = ['easy', 'medium', 'hard']


def prompt_int(message, default=None, minimum=None, maximum=None):
    while True:
        value = input(f'{message} ').strip()
        if not value and default is not None:
            return default
        if value.isdigit():
            number = int(value)
            if (minimum is None or number >= minimum) and (maximum is None or number <= maximum):
                return number
        print('Enter a valid number.')


def prompt_choice(message, choices, default=None):
    choices_display = '/'.join(choices)
    while True:
        value = input(f'{message} ({choices_display}) ').strip().lower()
        if not value and default is not None:
            return default
        if value in choices:
            return value
        print('Invalid choice.')


def prompt_yes_no(message, default='y'):
    answer = prompt_choice(message, ['y', 'n'], default)
    return answer == 'y'


class Card:
    def __init__(self, suit, rank, color=None, is_uno=False):
        self.suit = suit
        self.rank = rank
        self.color = color
        self.is_uno = is_uno

    def __str__(self):
        if self.is_uno:
            return f'{self.color} {self.rank}'
        return f'{self.rank}{self.suit}'

    def __repr__(self):
        return str(self)

    @property
    def value(self):
        if self.rank in RANKS:
            return RANKS.index(self.rank) + 2
        if self.rank.isdigit():
            return int(self.rank)
        return 10

    def matches(self, other):
        if self.is_uno and other.is_uno:
            return self.color == other.color or self.rank == other.rank or self.rank == 'Wild' or self.rank == 'Wild Draw Four'
        if self.is_uno or other.is_uno:
            return False
        return self.suit == other.suit or self.rank == other.rank


class Deck:
    def __init__(self, game_type='standard'):
        self.cards = self.build(game_type)
        self.shuffle()

    def build(self, game_type):
        if game_type == 'uno':
            cards = []
            for color in UNO_COLORS:
                cards.append(Card(None, '0', color=color, is_uno=True))
                for rank in UNO_RANKS[1:]:
                    cards.extend([Card(None, rank, color=color, is_uno=True) for _ in range(2)])
            cards.extend([Card(None, 'Wild', color=None, is_uno=True) for _ in range(4)])
            cards.extend([Card(None, 'Wild Draw Four', color=None, is_uno=True) for _ in range(4)])
            return cards
        return [Card(suit, rank) for suit in SUITS for rank in RANKS]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self, count=1):
        drawn = []
        for _ in range(count):
            if self.cards:
                drawn.append(self.cards.pop())
        return drawn if count != 1 else (drawn[0] if drawn else None)

    def remaining(self):
        return len(self.cards)

    def add(self, cards):
        if isinstance(cards, list):
            self.cards.extend(cards)
        elif cards:
            self.cards.append(cards)


class Player:
    def __init__(self, name, is_ai=False, difficulty='easy'):
        self.name = name
        self.is_ai = is_ai
        self.difficulty = difficulty
        self.hand = []
        self.score = 0

    def draw(self, deck, count=1):
        cards = deck.draw(count)
        if not cards:
            return []
        if isinstance(cards, list):
            self.hand.extend(cards)
        else:
            self.hand.append(cards)
        return cards

    def remove(self, card):
        if card in self.hand:
            self.hand.remove(card)
            return card
        return None

    def show_hand(self):
        return ', '.join(f'{idx + 1}:{card}' for idx, card in enumerate(self.hand))

    def choose_card(self, prompt, valid=None):
        valid_cards = valid or self.hand
        if self.is_ai:
            return self.ai_choose(valid_cards)
        print(f"{self.name}'s hand: {self.show_hand()}")
        while True:
            choice = input(f'{prompt} ').strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(valid_cards):
                    return valid_cards[idx]
            print('Invalid selection.')

    def ai_choose(self, valid_cards):
        if self.difficulty == 'easy':
            return random.choice(valid_cards)
        if self.difficulty == 'medium':
            return max(valid_cards, key=lambda card: card.value)
        if self.difficulty == 'hard':
            low_value = min(card.value for card in valid_cards)
            return random.choice([card for card in valid_cards if card.value == low_value])
        return random.choice(valid_cards)

    def hand_value(self):
        total = 0
        aces = 0
        for card in self.hand:
            if card.rank == 'A':
                aces += 1
                total += 11
            elif card.rank in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card.rank)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def best_blackjack_action(self):
        total = self.hand_value()
        if self.difficulty == 'easy':
            return 'hit' if total < 16 else 'stand'
        if self.difficulty == 'medium':
            return 'hit' if total < 17 else 'stand'
        return 'hit' if total < 18 else 'stand'


class CardGame:
    def __init__(self, players):
        self.players = players
        self.deck = Deck()

    def run(self):
        raise NotImplementedError()

    def long_game_setting(self):
        return prompt_int('Enter number of rounds or target score (default 20):', default=20, minimum=1)

    def choose_opponent(self, current):
        opponents = [player for player in self.players if player is not current]
        return random.choice(opponents) if current.is_ai else self.choose_from_list('Choose opponent:', opponents)

    def choose_from_list(self, message, options):
        print(message)
        for index, option in enumerate(options, start=1):
            print(f'{index}. {option.name}')
        while True:
            choice = input('Choice: ').strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            print('Invalid choice.')

    def display_scores(self):
        print('Scores:', ', '.join(f'{p.name}={p.score}' for p in self.players))


class BlackjackGame(CardGame):
    def run(self):
        print('=== Blackjack ===')
        target = self.long_game_setting()
        dealer = self.players[-1]
        while all(player.score < target for player in self.players[:-1]):
            self.deck = Deck()
            for player in self.players:
                player.hand = []
                player.draw(self.deck, 2)
            print(f"Dealer shows {dealer.hand[0]}")
            for player in self.players[:-1]:
                while player.hand_value() < 21:
                    print(f"{player.name}'s hand: {player.show_hand()} ({player.hand_value()})")
                    action = player.best_blackjack_action() if player.is_ai else prompt_choice('Hit or stand?', ['hit', 'stand'])
                    if action == 'hit':
                        player.draw(self.deck)
                        continue
                    break
            while dealer.hand_value() < 17:
                dealer.draw(self.deck)
            print(f"Dealer total: {dealer.hand_value()}")
            for player in self.players[:-1]:
                result = self.compare(player, dealer)
                print(f'{player.name} {result}')
                if result == 'wins':
                    player.score += 1
            self.display_scores()
        print('Blackjack session complete.')

    def compare(self, player, dealer):
        player_total = player.hand_value()
        dealer_total = dealer.hand_value()
        if player_total > 21:
            return 'busts and loses'
        if dealer_total > 21 or player_total > dealer_total:
            return 'wins'
        if player_total == dealer_total:
            return 'pushes'
        return 'loses'


class WarGame(CardGame):
    def run(self):
        print('=== War ===')
        rounds = self.long_game_setting()
        self.deck = Deck()
        while self.deck.remaining() >= len(self.players) and all(player.score < rounds for player in self.players):
            plays = {}
            for player in self.players:
                card = player.draw(self.deck)[0]
                plays[player] = card
                print(f'{player.name} plays {card}')
            winner = max(self.players, key=lambda p: plays[p].value)
            winner.score += 1
            print(f'{winner.name} wins this round with {plays[winner]}')
        self.display_scores()
        print('War game complete.')


class GoFishGame(CardGame):
    def run(self):
        print('=== Go Fish ===')
        rounds = self.long_game_setting()
        self.deck = Deck()
        for player in self.players:
            player.hand = []
            player.draw(self.deck, 5)
        for r in range(rounds):
            print(f'-- Round {r + 1} --')
            for player in self.players:
                if not player.hand:
                    player.draw(self.deck, 5)
                target = self.choose_opponent(player)
                rank = self.choose_rank(player)
                print(f'{player.name} asks {target.name} for rank {rank}')
                matches = [card for card in target.hand if card.rank == rank]
                if matches:
                    for card in matches:
                        target.remove(card)
                        player.hand.append(card)
                    print(f'{target.name} gives {len(matches)} card(s).')
                else:
                    print('Go Fish!')
                    player.draw(self.deck)
                player.score += self.remove_books(player)
            self.display_scores()
        print('Go Fish complete.')

    def choose_rank(self, player):
        ranks = sorted({card.rank for card in player.hand})
        return random.choice(ranks) if player.is_ai else self.choose_from_list('Choose a rank to ask for:', [Card('', rank) for rank in ranks]).rank

    def remove_books(self, player):
        ranks = [card.rank for card in player.hand]
        books = 0
        for rank in set(ranks):
            if ranks.count(rank) >= 4:
                books += 1
                player.hand = [card for card in player.hand if card.rank != rank]
        return books


class MemoryGame(CardGame):
    def run(self):
        print('=== Memory Matching ===')
        cards = [Card(suit, rank) for suit in SUITS for rank in RANKS[:4]]
        board = cards + [Card(card.suit, card.rank) for card in cards]
        random.shuffle(board)
        visible = [False] * len(board)
        scores = {player: 0 for player in self.players}
        turn = 0
        while not all(visible):
            player = self.players[turn % len(self.players)]
            print(f"{player.name}'s turn.")
            first = self.choose_index(player, board, visible, 'first')
            visible[first] = True
            second = self.choose_index(player, board, visible, 'second', exclude=first)
            visible[second] = True
            print(f'Revealed {board[first]} and {board[second]}')
            if board[first].rank == board[second].rank and board[first].suit == board[second].suit:
                scores[player] += 1
                print('Match!')
            else:
                visible[first] = visible[second] = False
            turn += 1
        print('Final points:', ', '.join(f'{p.name}={scores[p]}' for p in self.players))
        print('Memory Matching complete.')

    def choose_index(self, player, board, visible, label, exclude=None):
        options = [idx for idx, shown in enumerate(visible) if not shown and idx != exclude]
        if player.is_ai:
            return random.choice(options)
        while True:
            print('Board:', ' '.join(f'[{i}]' + (str(board[i]) if visible[i] else 'XX') for i in range(len(board))))
            idx = prompt_int(f'Pick the {label} card index', minimum=0, maximum=len(board) - 1)
            if idx in options:
                return idx
            print('Invalid choice.')


class CrazyEightsGame(CardGame):
    def run(self):
        print('=== Crazy Eights ===')
        self.deck = Deck()
        for player in self.players:
            player.hand = []
            player.draw(self.deck, 5)
        top_card = self.deck.draw()
        current = 0
        while True:
            player = self.players[current]
            valid = [card for card in player.hand if card.matches(top_card) or card.rank == '8']
            print(f'Top card: {top_card}')
            if not valid:
                print(f'{player.name} draws a card.')
                player.draw(self.deck)
            else:
                card = player.choose_card('Choose card to play:', valid)
                player.remove(card)
                if card.rank == '8':
                    suit = random.choice(SUITS) if player.is_ai else prompt_choice('Choose new suit (♠ ♥ ♦ ♣):', ['♠', '♥', '♦', '♣'])
                    top_card = Card(suit, '8')
                else:
                    top_card = card
                print(f'{player.name} plays {card}.')
                if not player.hand:
                    print(f'{player.name} wins Crazy Eights!')
                    player.score += 1
                    break
            current = (current + 1) % len(self.players)
        self.display_scores()


class RummyGame(CardGame):
    def run(self):
        print('=== Rummy ===')
        rounds = self.long_game_setting()
        self.deck = Deck()
        for player in self.players:
            player.hand = []
            player.draw(self.deck, 7)
        for round_number in range(1, rounds + 1):
            print(f'-- Round {round_number} --')
            for player in self.players:
                self.play_turn(player)
            self.display_scores()
        print('Rummy complete.')

    def play_turn(self, player):
        player.draw(self.deck)
        if player.is_ai:
            card = self.ai_discard(player)
        else:
            card = player.choose_card('Choose a card number to discard:')
        player.remove(card)
        player.score += self.evaluate_melds(player)

    def ai_discard(self, player):
        counts = {rank: sum(1 for card in player.hand if card.rank == rank) for rank in RANKS}
        low_rank = min(player.hand, key=lambda c: counts[c.rank]).rank
        for card in player.hand:
            if card.rank == low_rank:
                return card
        return player.hand[0]

    def evaluate_melds(self, player):
        ranks = [card.rank for card in player.hand]
        score = 0
        for rank in set(ranks):
            if ranks.count(rank) >= 3:
                score += 2
        return score


class UnoGame(CardGame):
    def run(self):
        print('=== Uno-Style Game ===')
        self.deck = Deck(game_type='uno')
        for player in self.players:
            player.hand = []
            player.draw(self.deck, 7)
        pile = [self.deck.draw()]
        current = 0
        direction = 1
        while True:
            player = self.players[current]
            top = pile[-1]
            valid = [card for card in player.hand if card.matches(top)]
            print(f'Top pile card: {top}')
            if not valid:
                print(f'{player.name} draws a card.')
                player.draw(self.deck)
            else:
                card = player.choose_card('Choose a card to play:', valid)
                player.remove(card)
                pile.append(card)
                print(f'{player.name} plays {card}')
                if card.rank == 'Reverse':
                    direction *= -1
                elif card.rank == 'Skip':
                    current = (current + direction) % len(self.players)
                elif card.rank == 'Draw Two':
                    next_player = self.players[(current + direction) % len(self.players)]
                    next_player.draw(self.deck, 2)
                elif card.rank == 'Wild Draw Four':
                    next_player = self.players[(current + direction) % len(self.players)]
                    next_player.draw(self.deck, 4)
                if card.rank in ('Wild', 'Wild Draw Four') and not player.is_ai:
                    color = prompt_choice('Choose a new color:', [c.lower() for c in UNO_COLORS])
                    card.color = color.capitalize()
            if not player.hand:
                print(f'{player.name} wins Uno!')
                player.score += 1
                break
            current = (current + direction) % len(self.players)
        self.display_scores()


def best_hand_value(cards):
    sorted_cards = sorted(cards, key=lambda c: c.value, reverse=True)
    ranks = [c.rank for c in sorted_cards]
    flush = len({c.suit for c in cards}) == 1
    values = [c.value for c in sorted_cards]
    straight = all(values[i] - 1 == values[i + 1] for i in range(len(values) - 1))
    counts = {rank: ranks.count(rank) for rank in ranks}
    if straight and flush:
        rank = 8
    elif 4 in counts.values():
        rank = 7
    elif sorted(counts.values()) == [2, 3]:
        rank = 6
    elif flush:
        rank = 5
    elif straight:
        rank = 4
    elif 3 in counts.values():
        rank = 3
    elif list(counts.values()).count(2) == 2:
        rank = 2
    elif 2 in counts.values():
        rank = 1
    else:
        rank = 0
    return rank, values


class PokerGame(CardGame):
    def run(self):
        print('=== Poker (5-Card Draw) ===')
        self.deck = Deck()
        for player in self.players:
            player.hand = []
            player.draw(self.deck, 5)
        for player in self.players:
            if player.is_ai:
                self.ai_discard_and_draw(player)
            else:
                print(f"{player.name}'s hand: {player.show_hand()}")
                if prompt_yes_no('Discard cards before showdown? (y/n)', default='n'):
                    discards = prompt_int('How many cards to discard?', default=0, minimum=0, maximum=3)
                    for _ in range(discards):
                        card = player.choose_card('Choose card to discard:')
                        player.remove(card)
                    player.draw(self.deck, discards)
        results = []
        for player in self.players:
            rank = best_hand_value(player.hand)
            results.append((rank, player))
            print(f"{player.name}: {player.show_hand()} -> {rank[0]}")
        winner = max(results)[1]
        print(f'{winner.name} wins Poker!')
        winner.score += 1
        self.display_scores()

    def ai_discard_and_draw(self, player):
        keep = sorted(player.hand, key=lambda c: c.value, reverse=True)[:3]
        player.hand = keep
        player.draw(self.deck, 5 - len(keep))


class TexasHoldemGame(CardGame):
    def run(self):
        print('=== Texas Hold’em ===')
        self.deck = Deck()
        community = []
        for player in self.players:
            player.hand = []
            player.draw(self.deck, 2)
            print(f'{player.name} has {player.hand[0]}, {player.hand[1]}')
        community.extend(self.deck.draw(3))
        community.append(self.deck.draw())
        community.append(self.deck.draw())
        print('Community cards:', ', '.join(str(card) for card in community))
        best = None
        for player in self.players:
            combos = itertools.combinations(player.hand + community, 5)
            player_best = max((best_hand_value(list(combo)) for combo in combos), default=(0, []))
            print(f'{player.name} best hand rank {player_best[0]}')
            if best is None or player_best > best[0]:
                best = (player_best, player)
        if best:
            print(f'{best[1].name} wins Texas Hold’em!')
            best[1].score += 1
        self.display_scores()


class SolitaireGame(CardGame):
    def run(self):
        print('=== Solitaire ===')
        self.deck = Deck()
        tableau = [self.deck.draw(i + 1) for i in range(7)]
        foundations = {suit: [] for suit in SUITS}
        stock = self.deck.cards
        self.deck.cards = []
        waste = []
        while True:
            print('\nFoundations:', ' '.join(f'{suit}:{len(stack)}' for suit, stack in foundations.items()))
            print('Waste:', waste[-1] if waste else 'Empty')
            for index, pile in enumerate(tableau, start=1):
                top = pile[-1] if pile else 'Empty'
                print(f'T{index}: {top}')
            command = input('Enter command (draw, move W T#, move T# F#, move T# T#, quit): ').strip().lower()
            if command == 'quit':
                break
            if command == 'draw':
                if stock:
                    waste.append(stock.pop())
                else:
                    stock = waste[::-1]
                    waste.clear()
                    print('Recycled waste into stock.')
                continue
            parts = command.split()
            if len(parts) == 3 and parts[0] == 'move':
                source = parts[1].upper()
                dest = parts[2].upper()
                card = None
                if source == 'W' and waste:
                    card = waste[-1]
                elif source.startswith('T'):
                    idx = int(source[1:]) - 1
                    if tableau[idx]:
                        card = tableau[idx][-1]
                if not card:
                    print('Invalid source.')
                    continue
                if dest.startswith('F'):
                    suit = card.suit
                    if suit and ((not foundations[suit] and card.rank == 'A') or (foundations[suit] and RANKS.index(card.rank) == RANKS.index(foundations[suit][-1].rank) + 1)):
                        foundations[suit].append(card)
                        if source == 'W':
                            waste.pop()
                        else:
                            tableau[idx].pop()
                        print(f'Moved {card} to foundation {suit}.')
                    else:
                        print('Cannot move to foundation.')
                elif dest.startswith('T'):
                    dest_idx = int(dest[1:]) - 1
                    if not tableau[dest_idx] or card.value == tableau[dest_idx][-1].value - 1:
                        if source == 'W':
                            waste.pop()
                        else:
                            tableau[idx].pop()
                        tableau[dest_idx].append(card)
                        print(f'Moved {card} to tableau {dest_idx + 1}.')
                    else:
                        print('Cannot move to tableau.')
                else:
                    print('Invalid destination.')
            else:
                print('Invalid command.')
            if all(len(stack) == 13 for stack in foundations.values()):
                print('Solitaire complete! You won!')
                break
        print('Solitaire session ended.')


def setup_players():
    players = []
    total = prompt_int('Enter total number of players (2-6):', default=2, minimum=2, maximum=6)
    human = prompt_int('How many human players?', default=1, minimum=1, maximum=total)
    for i in range(human):
        name = input(f'Enter name for player {i + 1}: ').strip() or f'Player{i + 1}'
        players.append(Player(name, is_ai=False))
    for j in range(total - human):
        name = f'AI{j + 1}'
        difficulty = prompt_choice(f'Select difficulty for {name}:', DIFFICULTIES, default='easy')
        players.append(Player(name, is_ai=True, difficulty=difficulty))
    if prompt_yes_no('Add dealer as AI for Blackjack? (y/n)', default='n') and total >= 2:
        players.append(Player('Dealer', is_ai=True, difficulty='medium'))
    return players


def main():
    games = {
        '1': ('Blackjack', BlackjackGame),
        '2': ('War', WarGame),
        '3': ('Go Fish', GoFishGame),
        '4': ('Memory Matching', MemoryGame),
        '5': ('Crazy Eights', CrazyEightsGame),
        '6': ('Rummy', RummyGame),
        '7': ('Uno-style', UnoGame),
        '8': ('Poker (5-Card Draw)', PokerGame),
        '9': ('Texas Hold’em', TexasHoldemGame),
        '10': ('Solitaire', SolitaireGame),
    }
    while True:
        print('\n=== Card Games Hub ===')
        for key, (name, _) in games.items():
            print(f'{key}. {name}')
        print('Q. Quit')
        choice = input('Select a game: ').strip().lower()
        if choice == 'q':
            break
        if choice not in games:
            print('Invalid selection.')
            continue
        game_name, game_cls = games[choice]
        print(f'You selected {game_name}.')
        players = setup_players() if game_name != 'Solitaire' else [Player('You', is_ai=False)]
        game = game_cls(players)
        game.run()
        if not prompt_yes_no('Play another game? (y/n)', default='y'):
            break


if __name__ == '__main__':
    main()
