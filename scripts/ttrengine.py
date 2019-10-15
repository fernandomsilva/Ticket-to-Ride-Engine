import multiprocessing as mp
import collections
import random
import bisect
import networkx as nx
import itertools
import random
import copy
import Queue
import pickle
import time
import copy_reg
import types
import operator
import re

import collections
import random
import bisect
import networkx as nx
import itertools
import random
import copy
import Queue
import pickle
import time
import copy_reg
import types

def _pickle_method(m):
	if m.im_self is None:
		return getattr, (m.im_class, m.im_func.func_name)
	else:
		return getattr, (m.im_self, m.im_func.func_name)

copy_reg.pickle(types.MethodType, _pickle_method)

class LogMove:
	def __init__(self, pnum, move, args):
		self.pnum = pnum
		self.move = move
		self.args = []
		if 'TrainCard' in move:
			self.args.append(args)
		else:
			for arg in args:
				if type(arg) == list and type(arg[0]) != str:
					for subarg in arg:
						self.args.append(str(subarg))
				else:
					self.args.append(arg)

	def __getstate__(self): return self.__dict__
	def __setstate__(self, d): self.__dict__.update(d)

class GameHandler:
	def __init__(self, game, agents, filename):
		self.game = game
		self.agents = agents
		self.filename = filename
		self.turn_count = 0
		self.last_player = None
		self.total_move_count = []
		self.first_player = -1
		self.total_relative_edges_left = []

	def play(self, runnum, save=False):
		movelog = []
		start = time.time()
		for i in range(0, self.game.number_of_players):
			#print(i)
			move = self.agents[i].decide(self.game.copy(), i)
			movelog.append(LogMove(i, move.function, move.args))
			#print("rn: " + str(runnum))
			#print(move.function)
			#print(move.args)
			self.game.make_move(move.function, move.args)
		
		#print (self.game.players_choosing_destination_cards)
		self.first_player = self.game.current_player

		while self.game.game_over == False:
			#print("Current Player: " + str(self.game.current_player) + ", " + str(self.game.players[self.game.current_player].number_of_trains)) + ', ' + str(self.game.players[self.game.current_player].points)
			if self.last_player != self.game.current_player:
				self.total_move_count.append(len(self.game.get_possible_moves(self.game.current_player)))
				self.last_player = self.game.current_player
				if self.game.current_player == self.first_player:
					self.total_relative_edges_left.append(numberOfRelativeEdges(self.game.board.graph))
			move = self.agents[self.game.current_player].decide(self.game, self.game.current_player)
			try:
				movelog.append(LogMove(self.game.current_player, move.function, move.args))
			except:
				#print 'NO MORE MOVES!!!'
				f1 = open('disaster' + '.go', 'wb')
				pickle.dump(self.game, f1)
				f1.close()
				return
			#print(move.function)
			#print self.game.players[self.game.current_player].hand
			self.game.make_move(move.function, move.args)
			self.turn_count += 1


		#for i in range(0, self.game.number_of_players):
		#	print("Player " + str(i+1) + ": " + str(self.game.players[i].points))

		if save:
			f1 = open(self.filename + str(runnum) + '.go', 'wb')
			f2 = open(self.filename + str(runnum) + '.ml', 'wb')
			pickle.dump(self.game, f1)
			pickle.dump(movelog, f2)
			f1.close()
			f2.close()

		#print "Total game length: " + str(time.time() - start)

def numberOfRelativeEdges(graph, multi_edges=True):
	total_relative_edges_left = 0
	visited = []
	for city1 in graph:
		for city2 in graph[city1]:
			if (city2, city1) not in visited:
				if multi_edges:
					taken = True
				else:
					taken = False
				for edge_index in graph[city1][city2]:
					edge = graph[city1][city2][edge_index]
					if edge['owner'] == -1 and multi_edges:
						taken = False
					elif edge['owner'] != -1 and not multi_edges:
						taken = True
				if not taken:
					total_relative_edges_left += 1

				visited.append((city1, city2))

	return total_relative_edges_left


#returns the train deck (a list of strings)
#number_of_color_cards => an integer that defines the number of each of the non-wild cards in the deck
#number_of_wildcards => an integer that defines the number of wild cards in the deck
#default values (following the rulebook) should be 12 color cards and 14 wilds
def make_train_deck(number_of_color_cards, number_of_wildcards):
	cards = {"red": number_of_color_cards, "orange": number_of_color_cards, "blue": number_of_color_cards, "pink": number_of_color_cards, "white": number_of_color_cards, "yellow": number_of_color_cards, "black": number_of_color_cards, "green": number_of_color_cards, "wild": number_of_wildcards}
	return cards

def randomCard(cards):
	keys = cards.keys()
	total = 0
	temp = []
	
	for x in keys:
		total += cards[x]
		temp.append(total)
	
	seed = random.random() * total
	index = bisect.bisect(temp, seed)
	
	return keys[index]

def emptyCardDict():
	return {"red": 0, "orange": 0, "blue": 0, "pink": 0, "white": 0, "yellow": 0, "black": 0, "green": 0, "wild": 0}

#returns a dict that relates the number of trains on a route to how many points that is worth
# 1 train route is worth 1 point
# 2 train route is worth 2 points
# 3 train route is worth 4 points
def point_table():
	#if board == "europe":
	#	return {1:1, 2:2, 3:4, 4:7, 5:10, 6:15, 8:21}

	#return {1:1, 2:2, 3:4, 4:7, 5:10, 6:15}
	return {1:1, 2:2, 3:4, 4:7, 5:10, 6:15, 8:21, 9:27}

def comparePlayerKey(p1):
	return p1.points

#class to encapsulate the destination cards
#dest1 and dest2 => strings for the two destinations
#points => integer for how many points the player wins by completing that conection
class DestinationCard:
	def __init__(self, dest1, dest2, points):
		self.destinations = [dest1, dest2]
		self.points = points
	
	def __str__(self):
		return str(self.destinations) + " " + str(self.points)

class DestinationCountryCard(DestinationCard):
	def setType(self, ctype):
		self.type = ctype

	def __str__(self):
		return str(self.destinations) + " " + str(self.points) + " " + self.type

#class to encapsulate the player
#hand => list of train cards (strings) in the player's hand
#number_of_trains => integer of how many trains the player has left (players start with 45 trains)
#points => integer of the number of points the player currently has
#choosing_destination_cards => boolean to indicate if the player is picking destination cards to keep
#drawing_train_cards => boolean to indicate that the player drew 1 train cards and needs to draw 1 more
class Player:
	def __init__(self, hand, number_of_trains, points):
		self.hand = hand
		self.hand_destination_cards = []
		self.number_of_trains = number_of_trains
		self.points = points
		self.graph = nx.Graph()
		self.choosing_destination_cards = False
		self.drawing_train_cards = False

	def copy(self):
		p = Player(self.hand.copy(), self.number_of_trains, self.points)
		#p.hand_destination_cards = copy.copy(self.hand_destination_cards)
		p.hand_destination_cards = self.hand_destination_cards[:]	
		p.choosing_destination_cards = self.choosing_destination_cards
		p.drawing_train_cards = self.drawing_train_cards
		p.graph = nx.Graph(self.graph)
		return p

	def print_destination_cards(self):
		for card in self.hand_destination_cards:
			print(card)






#Data structure to store move data
class Move:
	def __init__(self, fref, args):
		self.function = fref
		self.args = args


#class to encapsulate decks (train card deck and destination deck)
#deck => list of cards (strings for train deck, DestinationCard class for destination deck) of the deck 
class CardManager:
	def __init__(self, cardlist):
		self.deck = cardlist
		self.discard_pile = {}

	def __len__(self):
		return len(self.deck)

	def copy(self):
		#c = CardManager(copy.copy(self.deck))
		#c.discard_pile = copy.copy(self.discard_pile)
		c = CardManager(self.deck.copy())
		c.discard_pile = self.discard_pile.copy()
		return c

	#returns a randomly picked card from the list (deck)
	def draw_card(self):
		if (sum(self.deck.itervalues()) == 0):
			self.reshuffle()
		card = randomCard(self.deck)
		self.deck[card] -= 1

		return card

	#puts a card in the discard pile
	def discard(self, card):
		if type(card) == type([]) or type(card) == type({}):
			for c in card:
				if c in self.discard_pile:
					self.discard_pile[c] += 1
				else:
					self.discard_pile[c] = 1
		else:
			if card in self.discard_pile:
				self.discard_pile[card] += 1
			else:
				self.discard_pile[card] = 1

	#assumes an empty deck. Puts all cards from the discard pile back in the deck. Empties the discard_pile
	def reshuffle(self):
		#self.deck = copy.copy(self.discard_pile)
		self.deck = self.discard_pile.copy()
		self.discard_pile = {}

#class to encapsulate the Board (represented by a graph from the library networkx)
#board_graph => graph that represents the board (a graph in networkx is represented by a dictionary)
class Board:
	def __init__(self, board_graph):
		self.graph = board_graph

	def copy(self):
		#b = Board(copy.deepcopy(self.graph))
		b = Board(nx.MultiGraph(self.graph))
		return b

	#returns a route (edge) of a specific color that connect two cities
	#if color is None, return a list of all routes between the two cities
	#city1 => string of one of the cities in the route
	#city2 => string of the other city in the route
	#color => string of color of the route
	def get_connection(self, city1, city2, color=None):
		edge = None

		if city1 in self.graph:
			if city2 in self.graph[city1]:
				edge = self.graph[city1][city2]

		if city2 in self.graph:
			if city1 in self.graph[city2]:
				edge = self.graph[city2][city1]

		if edge != None:
			if color == None:
				return edge
			else:
				for opt in edge:
					if edge[opt]['color'] == color:
						return edge[opt]

		return None

	#returns a route (edge) with a specific color that has not been claimed
	#if number_of players <= 3, only 1 route can be claimed between the same two cities
	#city1 and city2 => string of the two cities that make up the route
	#color => the color of the route
	#number_of_players => the number of players in the current game
	def get_free_connection(self, city1, city2, color, number_of_players=2, special_variant=False):
		connections = self.get_connection(city1, city2)
		locked = False
		if number_of_players < 4 or (number_of_players == 3 and special_variant):
			for c in connections:
				if connections[c]['owner'] != -1:
					locked = True

		if not locked:
			for c in connections:
				if (connections[c]['color'] == color or connections[c]['color'] == "GRAY") and connections[c]['owner'] == -1:
					return connections[c]

		return None

#class that encapsulate the game itself
#board => object of the Board class (defined above)
#point_table => dictionary (use function point_table above)
#destination_deck => list of all destination cards in the game (cards should be of class DestinationCard [defined above])
#train_deck => list of all train cards in the game (use function make_train_deck above)
#player => list of all players (objects of class Player [defined above]) in the game
#current_player => index of the player in the list of players who should make the next move
#------------------------
#train_deck_face_up => list of train cards that are currently face up on the table (always has length of 5 after setup)
#players_choosing_destination_cards => boolean that is true while all players are choosing the destination cards they want at the beginning of the game (only at the beginning of the game)
#last_turn_player => index of the player who has the last turn. After it has a value > -1, the next time this player makes a move, the game will end


####################
#   MAKING MOVES   #
####################

#always use the funciton make_move(self, move, args)
#move is the reference to a move function. All possible move functions are:
#move_choose_destination_cards(self, args), move_claimRoute(self, args), move_drawDestinationCards(self, args), move_drawTrainCard(self, args)
#all of them are expecting a list as an argument. Look at their 'sister' functions to know what should be on the list, for example:
#if I wanted to claim a route, I have the function move_claimRoute and:
#claimRoute(self, city1, city2, color)
#to claim a route, you would call:
#game.make_move(game.move_claimRoute, [city1, city2, color])
#so, if the AI wants to claim the blue route between NEW YORK and BOSTON, the call should be:
#game.make_move(game.move_claimRoute, ['NEW YORK', 'BOSTON', 'blue'])
#the same concept is applied to all other move. If a move function has no parameters just pass an empty list, for example:
#game.make_move(game.move_drawDestinationCards, [])

######### REMEMBER: the first move every player makes should be to choose which destination cards they want to keep (they need to keep 2 or 3 out of the 3 they get at the setup)
class Game:
	def __init__(self, board, point_table, destination_deck, train_deck, players, current_player, variants=[3, 2, 3, 1, True, False, False, False, False, False, 4, 5, 2, 3, 2, 10, 15, 2, False]):
		self.board = board
		self.point_table = point_table
		self.destination_deck = CardManager(destination_deck)
		self.train_deck = CardManager(train_deck)
		self.train_cards_face_up = emptyCardDict()
		self.number_of_players = len(players)
		self.players = players
		self.current_player = current_player
		self.players_choosing_destination_cards = False
		self.last_turn_player = -1
		self.moves_reference = {}
		self.game_over = False
		self.destination_deck_draw_rules = variants[0:4]
		self.longest_route_variant = variants[4]
		self.globetrotter_variant = variants[5]
		self.europe_variant = variants[6]
		self.switzerland_variant = variants[7]
		self.nordic_countries_variant = variants[8]
		self.india_variant = variants[9]
		self.asia_variant = variants[18]

		self.number_of_current_draws = 0

		#TWEAKABLE
		self.number_of_train_cards_first_turn = variants[10] #4
		self.number_of_face_up_train_cards = variants[11] #5
		self.limit_of_face_up_wild_cards = variants[12] #2
		self.number_of_cards_drawn_on_underground = variants[13] #3
		self.number_of_leftover_trains_to_end_game = variants[14] #2
		self.amount_of_points_longest_route = variants[15] #10
		self.amount_of_points_globetrotter = variants[16] #15
		self.number_of_cards_draw_per_turn = variants[17] #2
    

		#Number of trains players start the game with

	def __getstate__(self): return self.__dict__
	def __setstate__(self, d): self.__dict__.update(d)

	def set_moves_reference(self):
		self.moves_reference['chooseDestinationCards'] = self.move_choose_destination_cards
		self.moves_reference['claimRoute'] = self.move_claimRoute
		self.moves_reference['drawDestinationCards'] = self.move_drawDestinationCards
		self.moves_reference['drawTrainCard'] = self.move_drawTrainCard
		
	def copy(self):
		copy_players = []
		for p in self.players:
			copy_players.append(p.copy())
		#g = Game(self.board.copy(), self.point_table, copy.copy(self.destination_deck), copy.copy(self.train_deck), copy_players, self.current_player)
		g = Game(self.board.copy(), self.point_table, {}, {}, copy_players, self.current_player, self.destination_deck_draw_rules + [self.longest_route_variant, self.globetrotter_variant, self.europe_variant, self.switzerland_variant, self.nordic_countries_variant, self.india_variant,self.number_of_train_cards_first_turn,self.number_of_face_up_train_cards, self.limit_of_face_up_wild_cards, self.number_of_cards_drawn_on_underground, self.number_of_leftover_trains_to_end_game, self.amount_of_points_longest_route, self.amount_of_points_globetrotter, self.number_of_cards_draw_per_turn, self.asia_variant])
		g.set_moves_reference()
		g.destination_deck = self.destination_deck.copy()
		g.train_deck = self.train_deck.copy()
		g.players_choosing_destination_cards = self.players_choosing_destination_cards
		g.last_turn_player = self.last_turn_player
		g.train_cards_face_up = self.train_cards_face_up.copy()
		#g.number_of_train_cards_first_turn = self.number_of_train_cards_first_turn
		#g.number_of_face_up_train_cards = self.number_of_face_up_train_cards
		#g.limit_of_face_up_wild_cards = self.limit_of_face_up_wild_cards
		#g.number_of_cards_drawn_on_underground = self.number_of_cards_drawn_on_underground
		#g.number_of_leftover_trains_to_end_game = self.number_of_leftover_trains_to_end_game
		#g.amount_of_points_longest_route = self.amount_of_points_longest_route
		#g.amount_of_points_globetrotter = self.amount_of_points_globetrotter
		#g.number_of_cards_draw_per_turn = self.number_of_cards_draw_per_turn
		#g.number_of_current_draws = self.number_of_current_draws

		return g

	#sets up the initial state of the players hands, face up cards and etc
	#remember, the first move of every player should be to choose the destination cards they want to keep
	def setup(self):
		self.set_moves_reference()

		if self.europe_variant:
			for i in range(0, self.number_of_players):
				if "destination" not in self.players[i].hand:
					self.players[i].hand["destination"] = []
				card = random.choice(self.destination_deck.deck['long_routes'])
				self.players[i].hand["destination"].append(card)
				self.destination_deck.deck['long_routes'].remove(card)

			self.destination_deck.deck['long_routes'] = 0

		for i in range (0, self.number_of_players):
			for j in range(0, self.number_of_train_cards_first_turn):
				self.players[i].hand[self.draw_card(self.train_deck)] += 1
			for j in range(0, self.destination_deck_draw_rules[0]):
				if "destination" not in self.players[i].hand:
					self.players[i].hand["destination"] = []
				self.players[i].hand["destination"].append(self.draw_card(self.destination_deck))

			self.players[i].choosing_destination_cards = True

		self.current_player = random.choice([x for x in range(0, self.number_of_players)])
		self.who_went_first = self.current_player
		self.players_choosing_destination_cards = True

		for i in range(0, self.number_of_face_up_train_cards):
			self.addFaceUpTrainCard()

	#draws a card from a deck
	#deck => the deck (list) to be drawn from
	def draw_card(self, deck):
		card = deck.draw_card()

		if deck == self.train_deck and sum(self.train_deck.deck.itervalues()) == 0:
			self.train_deck.reshuffle()

		return card

	#discards train cards to the discard pile
	#used be the function claim route
	def discard_cards(self, player_index, cards):
		for card in cards:
			self.train_deck.discard(card)
			self.players[player_index].hand[card] -= 1

	#adds a new face up train cards
	#makes sure to never have 3 wild cards face up at the same time (rulebook)
	def addFaceUpTrainCard(self):
		#print self.train_deck.deck
		#print self.train_deck.discard_pile
		
		if len(self.train_deck.deck) > 0:
			card = self.draw_card(self.train_deck)

			if card in self.train_cards_face_up:
				self.train_cards_face_up[card] += 1
			else:
				self.train_cards_face_up[card] = 1			

			if sum(self.train_cards_face_up.itervalues()) == self.number_of_face_up_train_cards:
				#card_count = collections.Counter(self.train_cards_face_up)
				card_count = self.train_cards_face_up

				if 'wild' in card_count:
					if card_count['wild'] >= self.limit_of_face_up_wild_cards + 1:
						x = sum(self.train_deck.deck.itervalues()) + sum(self.train_deck.discard_pile.itervalues())
						if x > self.number_of_face_up_train_cards:
							self.train_deck.discard(self.train_cards_face_up)
							self.train_cards_face_up = emptyCardDict()
							x = self.number_of_face_up_train_cards
							for i in range(0, x):
								try:
									self.addFaceUpTrainCard()
								except:
									print(self.train_deck.deck)
									print(self.train_deck.discard_pile)

	#passes the turn to the next player
	def next_players_turn(self):
		self.current_player = (self.current_player + 1) % self.number_of_players

	#lists all the destination cards pending the player choice of which to keep
	#player_index => index of the player
	def list_pending_destination_cards(self, player_index):
		#result = []
		#for card in self.players[player_index].hand:
		#	if type(card) != str:
		#		result.append(card)

		return self.players[player_index].hand["destination"]

	#makes the move of choosing the destination cards to keep
	def move_choose_destination_cards(self, args):
		#for card in args[1]:
			#print card
		self.choose_destination_cards(args[0], args[1])

	#chooses which destination cards to keep
	#player => index of the player choosing the cards
	#cards => list of destination cards (objects of class DestinationCard) to keep. All the other destination cards not in the list that the player currently has will be removed from the game
	#PS: Destination cards get added to the players hand of train cards until he decides which ones to keep
	def choose_destination_cards(self, player, cards):
		min_num_cards = self.destination_deck_draw_rules[1] if self.players_choosing_destination_cards else self.destination_deck_draw_rules[3]

		#print "cards:" + str(cards)
		
		if len(cards) >= min_num_cards:
			#print self.players[player].hand
			self.players[player].hand["destination"] = []
			for card in cards:
				#self.players[player].hand.remove(card)
				self.players[player].hand_destination_cards.append(card)

			self.players[player].choosing_destination_cards = False

			if self.players_choosing_destination_cards:
				for i in range(0, self.number_of_players):
					if self.players[i].choosing_destination_cards == True:
						i = i - 1
						break
				if i == self.number_of_players - 1:
					self.players_choosing_destination_cards = False

			#print (self.players[player].hand)
			#raw_input('wait')

		if min_num_cards == self.destination_deck_draw_rules[3] and len(cards) >= min_num_cards:
			self.next_players_turn()

	#tests whether the player has the cards needed to claim a route
	#player_index => index of the player
	#number_of_cards => integer of the number of cards needed to claim that route
	#color => string of the color the cards need to be to claim the route
	#returns False if the player doesn't have the cards needed
	#returns the list of cards he needs to use to claim the route
	#if the player doesn't have enough of the color, it will try to complete the requirements with wild cards
	def checkPlayerHandRequirements(self, player_index, number_of_cards, color, ferries, special_nordic_route=False):
		if sum([x for x in self.players[player_index].hand.itervalues() if isinstance(x, int)]) < number_of_cards:
			return False

		color = color.lower()

		card_count = self.players[player_index].hand
		total = 0

		if color in card_count:
			total = total + card_count[color]
		if not self.switzerland_variant and not self.nordic_countries_variant:
			if color != 'wild' and 'wild' in card_count:
				total = total + card_count['wild']
			if color not in card_count and color != 'wild':
				color = 'wild'
	
		if special_nordic_route:
			total_cards_left = sum([x for x in self.players[player_index].hand.itervalues() if isinstance(x, int)])
			total_cards_left = total_cards_left - total
			total = total + (total_cards_left/4)

		if ferries > 0 and card_count['wild'] < ferries:
			return False
		if total < number_of_cards - ferries:
			return False

		cards_to_use = []
		if ferries > 0:
			for i in range(0, ferries):
				cards_to_use.append('wild')
			number_of_cards = number_of_cards - ferries

		if len(cards_to_use) < number_of_cards:
			if color in card_count:
				x = number_of_cards if card_count[color] >= number_of_cards else card_count[color]
				for i in range(0, x):
					cards_to_use.append(color)

		if len(cards_to_use) < number_of_cards:
			if special_nordic_route:
				number_of_cards = number_of_cards - len(cards_to_use)
				number_of_cards = 4 * number_of_cards			
				length_of_original_color = len(cards_to_use)
				
				if card_count['wild'] > 0:
					x = number_of_cards if number_of_cards >= card_count['wild'] else card_count['wild']
					for i in range(0, x):
						cards_to_use.append('wild')

				while (len(cards_to_use) - length_of_original_color) < number_of_cards:
					temp_dictionary = {}
					for key in card_count:
						if isinstance(card_count[key], int):
							if key not in cards_to_use and card_count[key] > 0:
								temp_dictionary[key] = card_count[key]

					next_color = min(temp_dictionary, key=temp_dictionary.get)
					number_of_cards_left = number_of_cards - len(cards_to_use) + length_of_original_color
					x = number_of_cards_left if card_count[next_color] >= number_of_cards_left else temp_dictionary[next_color]
					for i in range(0, x):
						cards_to_use.append(next_color)
				
			else:
				x = number_of_cards - len(cards_to_use)
				for i in range(0, x):
					cards_to_use.append('wild')

		return cards_to_use

	#makes the move of claiming a route
	def move_claimRoute(self, args):
		#if len(args) == 2:
		#	return self.claimRoute(args[0], args[1])
		return self.claimRoute(args[0], args[1], args[2])		

	#claims a route of a specific color between two cities
	#city1 and city2 => strings of the two cities that form the route
	#color => string of the color of the route to claim
	#if the route is a gray route, pass color as the color you want to use to claim that route, for example:
	#if you want to claim a gray route with blue cards, pass 'blue' as the color
	def claimRoute(self, city1, city2, color):
		edge = self.board.get_free_connection(city1, city2, color, self.number_of_players, self.switzerland_variant or self.nordic_countries_variant)

		if edge != None and edge['owner'] == -1:
			route_color = edge['color'] if edge['color'] != 'GRAY' else color
			
			if color.lower() == 'wild' and (self.switzerland_variant or self.nordic_countries_variant):
				return False

			special_nordic_route = False
				
			if self.nordic_countries_variant:
				cities = [city1.lower(), city2.lower()]
				if "murmansk" in cities and "lieksa" in cities:
					special_nordic_route = True
			
			cards_needed = self.checkPlayerHandRequirements(self.current_player, edge['weight'], route_color, edge['ferries'], special_nordic_route)

			if cards_needed and self.players[self.current_player].number_of_trains >= edge['weight']:
				not_enough_cards = False
			
				if edge['underground']:
					extra_weight = 0
					y = self.number_of_cards_drawn_on_underground if (sum(self.train_deck.deck.itervalues()) + sum(self.train_deck.discard_pile.itervalues()))  >= self.number_of_cards_drawn_on_underground else (sum(self.train_deck.deck.itervalues()) +  sum(self.train_deck.discard_pile.itervalues()))
					for i in range(0, y):
						card = self.draw_card(self.train_deck)
						if card.lower() == route_color.lower() or card.lower() == "wild":
							extra_weight = extra_weight + 1
						self.train_deck.discard(card)
					
					if sum(self.train_deck.deck.itervalues()) == 0:
						self.train_deck.reshuffle()
				
					if extra_weight > 0:
						total_player_hand = self.players[self.current_player].hand[route_color.lower()]
						if route_color.lower() != "wild":
							total_player_hand += self.players[self.current_player].hand["wild"]
						
						if len(cards_needed) + extra_weight > total_player_hand:
							not_enough_cards = True
						else:
							if self.players[self.current_player].hand[route_color.lower()] >= len(cards_needed) + extra_weight:
								for i in range(0, extra_weight):
									cards_needed.append(route_color.lower())
									
								extra_weight = 0
								
							elif self.players[self.current_player].hand[route_color.lower()] > len(cards_needed):
								difference = self.players[self.current_player].hand[route_color.lower()] - len(cards_needed)
								for i in range(0, difference):
									cards_needed.append(route_color.lower())
								
								extra_weight = extra_weight - difference
							
							for i in range (0, extra_weight):
								cards_needed.append("wild")
						
				if not not_enough_cards:
					self.discard_cards(self.current_player, cards_needed)
					self.players[self.current_player].number_of_trains = self.players[self.current_player].number_of_trains - edge['weight']
					edge['owner'] = self.current_player
					self.players[self.current_player].points = self.players[self.current_player].points + self.point_table[edge['weight']]
					if edge['mountain'] != 0:
						self.players[self.current_player].number_of_trains = self.players[self.current_player].number_of_trains - edge['mountain']
						self.players[self.current_player].points = self.players[self.current_player].points + (edge['mountain'] * 2)

					self.players[self.current_player].graph.add_edge(city1, city2, weight=edge['weight'])
			else:
				return False

			if self.players[self.current_player].number_of_trains <= self.number_of_leftover_trains_to_end_game:
				self.last_turn_player = self.current_player

			self.next_players_turn()

			return True

		return False

	#makes the move of drawing new destination cards
	def move_drawDestinationCards(self, args):
		return self.drawDestinationCards()

	#draws 3 new destination cards of which the player is required to keep at least 1 (rulebook)
	#the player that does this move needs to call the choose destination cards moves right after.
	def drawDestinationCards(self):
		if sum(self.destination_deck.deck.itervalues()) == 0:
			return False

		x = self.destination_deck_draw_rules[2] if sum(self.destination_deck.deck.itervalues()) >= self.destination_deck_draw_rules[2] else sum(self.destination_deck.deck.itervalues())
		if 'destination' not in self.players[self.current_player].hand:
			self.players[self.current_player].hand['destination'] = []
		for i in range(0, x):
			self.players[self.current_player].hand['destination'].append(self.draw_card(self.destination_deck))

		self.players[self.current_player].choosing_destination_cards = True

		return True

	#makes the move of drawing new train cards
	def move_drawTrainCard(self, card):

		return self.drawTrainCard(card)

	#draws a new train card either from the ones face up on the table or from the top of the deck
	#card => string of the card to draw. If value is 'top', draws a card from the top of the deck
	#to draw from the face up cards, just pass the string of the color of the card to draw as the parameter
	def drawTrainCard(self, card):
		if sum(self.train_deck.deck.itervalues()) == 0:
			self.train_deck.reshuffle()
		if (not self.switzerland_variant) and (not self.nordic_countries_variant) and self.number_of_current_draws + 1 < self.number_of_cards_draw_per_turn and card == 'wild' and card in self.train_cards_face_up and self.train_cards_face_up[card] > 0 and self.players[self.current_player].drawing_train_cards == False:
			self.players[self.current_player].hand['wild'] += 1
			self.train_cards_face_up['wild'] -= 1
			self.number_of_current_draws += 2
			self.addFaceUpTrainCard()

			if self.number_of_current_draws == self.number_of_cards_draw_per_turn:
				self.number_of_current_draws = 0
				self.next_players_turn()

			if self.number_of_current_draws + 1 == self.number_of_cards_draw_per_turn:
				self.players[self.current_player].drawing_train_cards = True

			return True

		drawn = False
		
		if card == 'top':
			self.players[self.current_player].hand[self.draw_card(self.train_deck)] += 1
			self.number_of_current_draws += 1
			drawn = True
			
		elif card in self.train_cards_face_up and self.train_cards_face_up[card] > 0:
			self.players[self.current_player].hand[card] += 1
			self.train_cards_face_up[card] -= 1
			self.number_of_current_draws += 1
			self.addFaceUpTrainCard()
			
			drawn = True
		
		if drawn:
			if card == 'top' and sum(self.train_deck.deck.itervalues()) == 0:
				self.number_of_current_draws = 0
				self.next_players_turn()
				return True

			elif sum(self.train_deck.deck.itervalues()) == 0 and sum(self.train_cards_face_up.itervalues()) == 0:
				self.number_of_current_draws = 0
				self.next_players_turn()
				return True

			if self.players[self.current_player].drawing_train_cards:
				self.players[self.current_player].drawing_train_cards = False
				self.number_of_current_draws = 0
				self.next_players_turn()
			
			else:
				if self.number_of_current_draws + 1 == self.number_of_cards_draw_per_turn:
					self.players[self.current_player].drawing_train_cards = True
			
			return True
		
		return False
		
	#makes a move as the current player
	#read the description of how to use on the Game Class description
	def make_move(self, move, args):
		#print("args: " + str(args))
		#print(len(self.train_deck.deck))
		#print "Move made!  " + str(move)
		last_turn = False
		if self.current_player == self.last_turn_player:
			last_turn = True
		if not self.players[self.current_player].choosing_destination_cards or (self.players[self.current_player].choosing_destination_cards and move == 'chooseDestinationCards'):

			if move == 'chooseDestinationCards':
				self.move_choose_destination_cards(args)
			elif move == 'claimRoute':
				self.move_claimRoute(args)
			elif move == 'drawDestinationCards':
				self.move_drawDestinationCards(args)
			elif move == 'drawTrainCard':
				self.move_drawTrainCard(args)
			else:
				move(args)
		if last_turn:
			self.calculatePoints()
			self.game_over = True
			return sorted([x for x in self.players], key=comparePlayerKey)


	#returns a graph of all routes (edges) claimed by a player
	#player => index of the player
	def player_graph(self, player):
		#G = nx.Graph()
		#
		#for node1 in self.board.graph:
		#	for node2 in self.board.graph[node1]:
		#		for edge in self.board.graph[node1][node2]:
		#			if self.board.graph[node1][node2][edge]['owner'] == player:
		#				G.add_edge(node1, node2, weight=self.board.graph[node1][node2][edge]['weight'])
		#
		#return G
		return self.players[player].graph

	def player_plus_free_graph(self, player):
		G = nx.Graph()
		
		for node1 in self.board.graph:
			for node2 in self.board.graph[node1]:
				for edge in self.board.graph[node1][node2]:
					if self.board.graph[node1][node2][edge]['owner'] == player or self.board.graph[node1][node2][edge]['owner'] == -1:
						G.add_edge(node1, node2, weight=self.board.graph[node1][node2][edge]['weight'])
		
		return G

	#calculates the points of all players at the end of the game
	def calculatePoints(self):
		longest_route_value = None
		longest_route_player = []
		max_destination_cards_completed = 0
		globetrotter_player = []
		asia_route_value = None
		asia_route_player = []
	
		for player in self.players:
			#print "This player has " + str(player.points) + " points from building routes"
			player_graph = self.player_graph(self.players.index(player))
		
			number_of_destinations_completed = 0

			for destination in player.hand_destination_cards:
				try:
					if destination.type != '':
						coutrynodes = ['FRANCEA', 'FRANCEB', 'FRANCEC', 'FRANCED', 'ITALIAA', 'ITALIAB', 'ITALIAC', 'ITALIAD', 'ITALIAE', 'OSTERREICHA', 'OSTERREICHB','OSTERREICHC', 'DEUTSCHLANDA', 'DEUTSCHLANDB', 'DEUTSCHLANDC', 'DEUTSCHLANDD', 'DEUTSCHLANDE']
						pnodes = player_graph.nodes()
						available_nodes = {'FRANCE': [], 'ITALIA': [], 'OSTERREICH': [], 'DEUTSCHLAND': []}
						for node in coutrynodes:
							if node in pnodes:
								if 'FRANCE' in node:
									available_nodes['FRANCE'].append(node)
								if 'ITALIA' in node:
									available_nodes['ITALIA'].append(node)
								if 'DEUTSCHLAND' in node:
									available_nodes['DEUTSCHLAND'].append(node)
								if 'OSTERREICH' in node:
									available_nodes['OSTERREICH'].append(node)

						max_points = 0
						if destination.type == 'city':
							if destination.destinations[0] in player_graph.nodes():
								for key in available_nodes:
									for country in available_nodes[key]:
										if nx.has_path(player_graph, destination.destinations[0], country):
											total = destination.points[destination.destinations[1].index(key)]
											if total > max_points:
												max_points = total
											break
									if max_points == max(destination.points):
										break
						elif destination.type == 'country':
							for start in available_nodes[destination.destinations[0]]:
								for key in available_nodes:
									if key == destination.destinations[0]:
										break
	
									for country in available_nodes[key]:
										if nx.has_path(player_graph, start, country):
											total = destination.points[destination.destinations[1].index(key)]
											if total > max_points:
												max_points = total
											break
									if max_points == max(destination.points):
										break

						if max_points > 0:
							player.points = player.points + max_points
							number_of_destinations_completed += 1
						else:
							player.points = player.points - min(destination.points)
				except:
					try:
						mandala = 0
						if nx.has_path(player_graph, destination.destinations[0], destination.destinations[1]):
							#print "Finished " + str(destination.destinations) + "!  +" + str(destination.points)
							player.points = player.points + destination.points
							number_of_destinations_completed += 1
							if self.india_variant:
								copy_graph = nx.Graph(player_graph)
								path = nx.shortest_path(player_graph, destination.destinations[0], destination.destinations[1])
								for i in range(0, len(path)-1):
									copy_graph.remove_edge(path[i], path[i+1])
								if nx.has_path(copy_graph, destination.destinations[0], destination.destinations[1]):
									mandala += 1
						else:
							#print "Did not finish " + str(destination.destinations) + "!  -" + str(destination.points)
							player.points = player.points - destination.points
					except:
						#print "Did not finish " + str(destination.destinations) + "!  -" + str(destination.points)
						player.points = player.points - destination.points

			#print "Player " + str(self.players.index(player)) + " M: " + str(mandala)
			if self.india_variant and mandala > 0:
				if mandala == 1:
					player.points = player.points + 5
				elif mandala == 2:
					player.points = player.points + 10
				elif mandala == 3:
					player.points = player.points + 20
				elif mandala == 4:
					player.points = player.points + 30
				else:
					player.points = player.points + 40
			if self.globetrotter_variant:
				if number_of_destinations_completed > max_destination_cards_completed:
					globetrotter_player = []
				if number_of_destinations_completed >= max_destination_cards_completed:
					max_destination_cards_completed = number_of_destinations_completed
					globetrotter_player.append(self.players.index(player))

			if self.longest_route_variant:
				temparr = [self.findMaxWeightSumForNode(player_graph, v, []) for v in player_graph.nodes()]
				temp = 0
				if len(temparr) > 0:
					temp = max(temparr)
				
				if longest_route_value == None or temp >= longest_route_value:
					if temp > longest_route_value:
						longest_route_player = [self.players.index(player)]
					else:
						longest_route_player.append(self.players.index(player))

					longest_route_value = temp
                    
			if self.asia_variant:
				temparr = [self.findMaxNodesVistiedForNode(player_graph, v, []) for v in player_graph.nodes()]
				aux = [len(x) for x in temparr]
				temparr = aux
				temp = 0
				if len(temparr) > 0:
					temp = max(temparr)
				
				if asia_route_value == None or temp >= asia_route_value:
					if temp > asia_route_value:
						asia_route_player = [self.players.index(player)]
					else:
						asia_route_player.append(self.players.index(player))

					asia_route_value = temp

		if self.globetrotter_variant:
			for player in globetrotter_player:
				self.players[player].points = self.players[player].points + self.amount_of_points_globetrotter

		if self.longest_route_variant:
			for player in longest_route_player:
				self.players[player].points = self.players[player].points + self.amount_of_points_longest_route

		if self.asia_variant:
			for player in asia_route_player:
				self.players[player].points = self.players[player].points + 10

	def returnCurrentPoints(self, player):
		player_graph = self.player_graph(self.players.index(player))
		for destination in player.hand_destination_cards:
			try:
				if nx.has_path(player_graph, destination.destinations[0], destination.destinations[1]):
					player.points = player.points + destination.points
				else:
					player.points = player.points - destination.points
			except:
				player.points = player.points - destination.points

	#calculates the longest route of a player
	#G => the graph from which to calculate (use a graph return by the function player_graph above)
	#source => the node from which to start
	#list_of_visited_edges => the list of the edges visited already
	#the function calculates the longest route in the calculatePoints function above by recursively calling this function updating the list of visited edges, for every node in the graph
	def findMaxWeightSumForNode(self, G, source, list_of_visited_edges):
		temp_edges = [e for e in G.edges() if e not in list_of_visited_edges and source in e]
		if len(temp_edges) == 0:
			return 0
		else:
			result = []
			result.extend([(self.findMaxWeightSumForNode(G, x, list_of_visited_edges+[(x,y)]) + G[x][y]['weight']) for (x,y) in temp_edges if source == y])
			result.extend([(self.findMaxWeightSumForNode(G, y, list_of_visited_edges+[(x,y)]) + G[y][x]['weight']) for (x,y) in temp_edges if source == x])
			return max(result)

	def findMaxNodesVistiedForNode(self, G, source, list_of_visited_edges):
		temp_edges = [e for e in G.edges() if e not in list_of_visited_edges and source in e]
		if len(temp_edges) == 0:
			return set()
		else:
			result = []
			result.extend([(self.findMaxNodesVistiedForNode(G, x, list_of_visited_edges+[(x,y)]).union([x, y])) for (x,y) in temp_edges if source == y])
			result.extend([(self.findMaxNodesVistiedForNode(G, y, list_of_visited_edges+[(x,y)]).union([x, y])) for (x,y) in temp_edges if source == x])
			l = [len(x) for x in result]
			return result[l.index(max(l))]

	def get_possible_moves(self, player_index):
		pmoves = []
		if self.players_choosing_destination_cards == True:
			dest_card_set = self.list_pending_destination_cards(player_index)
			for x in range(self.destination_deck_draw_rules[1], len(dest_card_set) + 1):
				comb = itertools.combinations(dest_card_set, x)
				for cardset in comb:
					pmoves.append(Move('chooseDestinationCards', [player_index, list(cardset)]))
					#pmoves.append(Move(self.move_choose_destination_cards, [player_index, list(cardset)]))
		elif self.players[player_index].choosing_destination_cards == True:
			dest_card_set = self.list_pending_destination_cards(player_index)
			for x in range(self.destination_deck_draw_rules[3], len(dest_card_set) + 1):
				comb = itertools.combinations(dest_card_set, x)
				for cardset in comb:
					pmoves.append(Move('chooseDestinationCards', [player_index, list(cardset)]))
					#pmoves.append(Move(self.move_choose_destination_cards, [player_index, list(cardset)]))
		elif self.players[player_index].drawing_train_cards == True and sum(self.train_deck.deck.itervalues()) > 0:
			pmoves.append(Move('drawTrainCard', 'top'))
			for card in set(self.train_cards_face_up):
				if (self.switzerland_variant or self.nordic_countries_variant) and self.train_cards_face_up[card] > 0:
					pmoves.append(Move('drawTrainCard', card))
				else:
					if card != 'wild' and self.train_cards_face_up[card] > 0:
						pmoves.append(Move('drawTrainCard', card))
				#pmoves.append(Move(self.move_drawTrainCard, card))				
		else:
			colors = ["RED", "ORANGE", "BLUE", "PINK", "WHITE", "YELLOW", "BLACK", "GREEN"]
			edges = self.board.graph.edges()
			#for city1 in self.board.graph:
			#	for city2 in self.board.graph:
			visited = []
			for (city1, city2) in edges:
				if (city1, city2) not in visited:
					visited.append((city1, city2))

					special_nordic_route = False				
					if self.nordic_countries_variant:
						cities = [city1.lower(), city2.lower()]
						if "murmansk" in cities and "lieksa" in cities:
							special_nordic_route = True
	
					for color in colors:
						edge = self.board.get_free_connection(city1, city2, color, self.number_of_players, self.switzerland_variant or self.nordic_countries_variant)

						if edge != None:
							if self.checkPlayerHandRequirements(player_index, edge['weight'], color, edge['ferries'], special_nordic_route) != False:
								if self.players[player_index].number_of_trains >= edge['weight'] + edge['mountain']:
									pmoves.append(Move('claimRoute', [city1, city2, color]))
								#pmoves.append(Move(self.move_claimRoute, [city1, city2, color]))
			if sum(self.destination_deck.deck.itervalues()) > 0:
				pmoves.append(Move('drawDestinationCards',[]))
				#pmoves.append(Move(self.move_drawDestinationCards,[]))
			if sum(self.train_deck.deck.itervalues()) > 0:
				pmoves.append(Move('drawTrainCard', 'top'))
				#pmoves.append(Move(self.move_drawTrainCard, 'top'))
			if sum(self.train_cards_face_up.itervalues()) > 0:
				for card in set(self.train_cards_face_up):
					if self.train_cards_face_up[card] > 0:
						pmoves.append(Move('drawTrainCard', card))
					#pmoves.append(Move(self.move_drawTrainCard, card))
		return pmoves

	def printScoring(self, pnum):
		longest_route_player = []
	
		player = self.players[pnum]
		player_graph = self.player_graph(pnum)
	
		for destination in player.hand_destination_cards:
			try:
				if destination.type != '':
					coutrynodes = ['FRANCEA', 'FRANCEB', 'FRANCEC', 'FRANCED', 'ITALIAA', 'ITALIAB', 'ITALIAC', 'ITALIAD', 'ITALIAE', 'OSTERREICHA', 'OSTERREICHB','OSTERREICHC', 'DEUTSCHLANDA', 'DEUTSCHLANDB', 'DEUTSCHLANDC', 'DEUTSCHLANDD', 'DEUTSCHLANDE']
					pnodes = player_graph.nodes()
					available_nodes = {'FRANCE': [], 'ITALIA': [], 'OSTERREICH': [], 'DEUTSCHLAND': []}
					for node in coutrynodes:
						if node in pnodes:
							if 'FRANCE' in node:
								available_nodes['FRANCE'].append(node)
							if 'ITALIA' in node:
								available_nodes['ITALIA'].append(node)
							if 'DEUTSCHLAND' in node:
								available_nodes['DEUTSCHLAND'].append(node)
							if 'OSTERREICH' in node:
								available_nodes['OSTERREICH'].append(node)

					scored = False
					if destination.type == 'city':
						if destination.destinations[0] in player_graph.nodes():
							for key in available_nodes:
								for country in available_nodes[key]:
									if nx.has_path(player_graph, destination.destinations[0], country):
										print(str(destination.destinations) + ' was completed! +' + str(destination.points))
										scored = True
										break
					elif destination.type == 'country':
						for start in available_nodes[destination.destinations[0]]:
							for key in available_nodes:
								if key == destination.destinations[0]:
									break

								for country in available_nodes[key]:
									if nx.has_path(player_graph, start, country):
										print(str(destination.destinations) + ' was completed! +' + str(destination.points))
										scored = True
										break

					if not scored:
						print(str(destination.destinations) + ' was not completed! -' + str(destination.points))
			except:
				try:
					if nx.has_path(player_graph, destination.destinations[0], destination.destinations[1]):
						print(str(destination.destinations) + ' was completed! +' + str(destination.points))
					else:
						print(str(destination.destinations) + ' was not completed! -' + str(destination.points))
				except:
					print(str(destination.destinations) + ' was not completed! -' + str(destination.points))

		visited = []
		for node1 in self.board.graph:
			for node2 in self.board.graph[node1]:
				for edge in self.board.graph[node1][node2]:
					if self.board.graph[node1][node2][edge]['owner'] == pnum:
						visited.append((node1, node2))
						if not (node2, node1) in visited:
							print(node1 + ", " + node2 + ": +" + str(self.point_table[self.board.graph[node1][node2][edge]['weight']]))
		
	def getDCardScore(self, pnum):
		rscore = 0
		player = self.players[pnum]
		player_graph = self.player_graph(pnum)
		
		for destination in player.hand_destination_cards:
			try:
				if nx.has_path(player_graph, destination.destinations[0], destination.destinations[1]):
					#print "Finished " + str(destination.destinations) + "!  +" + str(destination.points)
					rscore = rscore + destination.points
				else:
					#print "Did not finish " + str(destination.destinations) + "!  -" + str(destination.points)
					rscore = rscore - destination.points
			except:
				#print "Did not finish " + str(destination.destinations) + "!  -" + str(destination.points)
				rscore = rscore - destination.points
		return rscore

	def getUnclaimedRoutes(self):
		colors = ["RED", "ORANGE", "BLUE", "PINK", "WHITE", "YELLOW", "BLACK", "GREEN"]
		edges = self.board.graph.edges()
		#for city1 in self.board.graph:
		#	for city2 in self.board.graph:
		unclaimed = set()
		visited = []
		for (city1, city2) in edges:
			if (city1, city2) not in visited:
				visited.append((city1, city2))

				for color in colors:
					edge = self.board.get_free_connection(city1, city2, color, self.number_of_players, self.switzerland_variant or self.nordic_countries_variant)

					if edge != None:
						unclaimed.add((city1, city2))
		return unclaimed
    
	def winner(self):
		points_list = [x.points for x in self.players]     
		max_points = max(points_list)
		winners = [i for i in range(0, len(self.players)) if self.players[i].points == max_points]
		
		return winners