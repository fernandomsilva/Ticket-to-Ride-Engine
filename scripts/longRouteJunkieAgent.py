import networkx as nx
import operator
import random

class LongRouteJunkieAgent:
	def __init__(self):
		self.current_objective_route = None
		self.current_objective_color = None
		self.players_previous_points = -1

	def decide(self, game, pnum):
		possible_moves = game.get_possible_moves(pnum)
		
		if possible_moves[0].function == 'chooseDestinationCards':
			self.players_previous_points = -1
			#list_of_destinations = []

			return self.chooseDestinations(possible_moves, game, pnum, 3)

		claim_route_moves = []
		draw_train_card_moves = []
		
		for move in possible_moves:
			#if move.function == 'drawDestinationCards':
			#	move_draw_dest = move
			if move.function == 'claimRoute': 
				claim_route_moves.append(move)
			elif move.function == 'drawTrainCard':
				draw_train_card_moves.append(move)

		total_current_points = 0
		for i in range(0, len(game.players)):
			total_current_points += game.players[i].points

		if self.players_previous_points < total_current_points:
			x = self.generate_game_plan(game, pnum)
			self.current_objective_route = [x[0], x[1]]
			self.current_objective_color = x[2]
			self.players_previous_points = total_current_points

		if self.current_objective_color != None:
			#if self.current_objective_color == 'drawDestination':
			#	self.players_previous_points = -1
			#	return move_draw_dest
			
			for move in claim_route_moves:
				#print self.current_objective_route
				#print move.args
				if (move.args[0] == self.current_objective_route[0] and move.args[1] == self.current_objective_route[1]) or (move.args[1] == self.current_objective_route[0] and move.args[0] == self.current_objective_route[1]):
					return move
			
			draw_top_move = None
			draw_wild_move = None
			if self.current_objective_color.lower() != 'gray':
				for move in draw_train_card_moves:
					if move.args.lower() == self.current_objective_color.lower():
						return move
					if move.args.lower() == 'wild':
						draw_wild_move = move
					if move.args.lower() == 'top':
						draw_top_move = move			
			else:
				max_color = {x:game.players[pnum].hand[x] for x in game.players[pnum].hand if x != 'destination' and x != 'wild'}
				max_color = max(max_color.iteritems(), key=operator.itemgetter(1))

				for move in draw_train_card_moves:
					if move.args == max_color:
						return move
					if move.args.lower() == 'wild':
						draw_wild_move = move
					if move.args.lower() == 'top':
						draw_top_move = move

			if draw_wild_move != None:
				return draw_wild_move
			if draw_top_move != None:
				return draw_top_move
		
		if len(draw_train_card_moves) > 0:
			return random.choice(draw_train_card_moves)
		if len(claim_route_moves) > 0:
			return random.choice(claim_route_moves)
		
		return random.choice(possible_moves)

	def generate_game_plan(self, game, pnum):
		#shortest path between destinations - 1 destination at a time
		#connect destination edges
		#get long routes
		joint_graph = self.joint_graph(game, pnum, 3 if game.players[pnum].number_of_trains >= 3 else game.players[pnum].number_of_trains)
		city1 = None
		city2 = None
		color = None
		min_trains_threshold = 8

		list_of_destinations = self.destinations_not_completed(game, pnum, joint_graph)
		if list_of_destinations:
			#most_valuable_route = max(list_of_destinations, key='points')[0]
			most_valuable_route_index = max(xrange(len(list_of_destinations)), key=lambda index: list_of_destinations[index]['points'])
			most_valuable_route = list_of_destinations[most_valuable_route_index]
			result = self.chooseNextRouteTarget(game, pnum, joint_graph, most_valuable_route['city1'], most_valuable_route['city2'])
			if result != False:
				city1, city2, color = result
		if city1 == None:
			#min_number_of_trains = min([x.number_of_trains for x in game.players])
			#if min_number_of_trains >= min_trains_threshold and sum(game.destination_deck.deck.values()) > 0:
			#	#for move in possible_moves:
			#	#	if move.function == 'drawDestinationCards':
			#	#		return move
			#	return ['drawDestination', 'drawDestination', 'drawDestination']
			#else:
			#	result = self.chooseMaxRoute(game, pnum);
			result = self.chooseMaxRoute(game, pnum)
		
		return result			

	def calculate_value(self, cities, points, graph):
		try:
			if graph.has_path(graph, cities[0], cities[1]):
				left_to_claim = 0
				path = graph.shortest_path(graph, cities[0], cities[1])
				for s in range(0, len(path)-1):
					for t in range(s+1, len(path)):
						temp = 0
						for edge in graph[path[s]][path[t]]:
							if edge['owner'] == -1:
								temp = edge['weight']
							else:
								temp = 0
								break
						
						left_to_claim = left_to_claim + temp
						
				return [float(points), float(left_to_claim)]
			else:
				return [float(-1.0 * points), float(50)]
		except:
			return [float(-1.0 * points), float(50)]

	def chooseDestinations(self, moves, game, pnum, min_weight_edge):
		best_move = (0, None)
		least_worst_move = (0, None)
		joint_graph = self.joint_graph(game, pnum, min_weight_edge)
		
		for m in moves:
			current_move_value = 0
			number_of_trains_needed = 0			
			points = 0
			
			for dest in m.args[1]:
				temp = self.calculate_value(dest.destinations, dest.points, joint_graph)
				current_move_value += temp[0]
				number_of_trains_needed += temp[1]
				points += dest.points
			
			if number_of_trains_needed <= game.players[pnum].number_of_trains:
				total = current_move_value / number_of_trains_needed
				if total > best_move[0]:
					best_move = (total, m)
			else:
				if least_worst_move[1] == None:
					least_worst_move = (points, m)
				else:
					if least_worst_move[0] > points:
						least_worst_move = (points, m)
		
		if best_move[1] != None:
			return best_move[1]
		
		return least_worst_move[1]

	def destinations_not_completed(self, game, pnum, joint_graph):
		result = []
		graph = game.player_graph(pnum)

		destination_cards = game.players[pnum].hand_destination_cards
		for card in destination_cards:
			city1 = card.destinations[0]
			city2 = card.destinations[1]
			try:
				nx.shortest_path(graph, city1, city2)
				solved = True
			except:
				solved = False

			if not solved:
				if city1 in joint_graph.nodes() and city2 in joint_graph.nodes() and nx.has_path(joint_graph, city1, city2):
					try:
						result.append({'city1': city1, 'city2': city2, 'points': card.points, 'type': card.type})
					except:
						result.append({'city1': city1, 'city2': city2, 'points': card.points})

		return result

	def free_routes_graph(self, graph, number_of_players, min_weight_edge=0):
		G = nx.MultiGraph()

		visited_nodes = []
		
		for node1 in graph:
			for node2 in graph[node1]:
				if node2 not in visited_nodes:
					locked = False
					for edge in graph[node1][node2]:
						if number_of_players < 4:
							if graph[node1][node2][edge]['owner'] != -1:
								locked = True

					if not locked:
						for edge in graph[node1][node2]:
							if graph[node1][node2][edge]['owner'] == -1 and graph[node1][node2][edge]['weight'] >= min_weight_edge:
								G.add_edge(node1, node2, weight=graph[node1][node2][edge]['weight'], color=graph[node1][node2][edge]['color'], owner=-1)

			visited_nodes.append(node1)
		
		return G

	def joint_graph(self, game, pnum, min_weight_edge=0):
		free_connections_graph = self.free_routes_graph(game.board.graph, game.number_of_players, min_weight_edge)
		player_edges = game.player_graph(pnum).edges()
		
		joint_graph = free_connections_graph
		for edge in player_edges:
			joint_graph.add_edge(edge[0], edge[1], weight=0, color='none', owner=pnum)

		return joint_graph

	def chooseNextRouteTarget(self, game, pnum, graph, city1, city2):
		try:
			list_of_route_nodes = nx.shortest_path(graph, city1, city2)
		except:
			return False

		list_of_colors = set()
		cities = []
		for i in range(0, len(list_of_route_nodes)-1):
			cities = [list_of_route_nodes[i], list_of_route_nodes[i+1]]
			for key in graph[list_of_route_nodes[i]][list_of_route_nodes[i+1]]:
				edge = graph[list_of_route_nodes[i]][list_of_route_nodes[i+1]][key]

				if edge['owner'] != -1:
					list_of_colors = set()
					cities = []
					break

				list_of_colors.add(edge['color'].lower())

			if len(cities) != 0:
				break

		color_weight = []
		list_of_colors = list(list_of_colors)
		if 'gray' in list_of_colors:
			list_of_colors = [x for x in game.players[pnum].hand if x != 'destination']
		for color in list_of_colors:
			color_weight.append(game.players[pnum].hand[color.lower()])
			
		max_weight = color_weight.index(max(color_weight))
		desired_color = list_of_colors[max_weight]

		return [cities[0], cities[1], desired_color]
	
	def rank(self, edge, game, pnum):
		color = edge['color'].lower()
		player_colors_no_wild = {x:game.players[pnum].hand[x] for x in game.players[pnum].hand if x != 'wild' and x != 'destination'}
		number_of_wilds = game.players[pnum].hand['wild']
		max_color_value = max(player_colors_no_wild.values())
		
		if color == 'gray':
			if max_color_value >= edge['weight']:
				return 15
			if max_color_value + number_of_wilds >= edge['weight']:
				return 9
			return 10 - edge['weight'] + max_color_value

		if player_colors_no_wild[color] >= edge['weight']:
			return 10
		if player_colors_no_wild[color] + number_of_wilds >= edge['weight']:
			return 9

		return 9 - edge['weight'] + max_color_value
	
	def chooseMaxRoute(self, game, pnum):
		number_of_trains_left = game.players[pnum].number_of_trains
		max_size = 0
		list_of_edges = []
	
		free_routes_graph = self.free_routes_graph(game.board.graph, game.number_of_players)
		for city1 in free_routes_graph:
			for city2 in free_routes_graph[city1]:
				for e in free_routes_graph[city1][city2]:
					edge = free_routes_graph[city1][city2][e]
					if edge['weight'] <= number_of_trains_left:
						if edge['weight'] > max_size:
							max_size = edge['weight']
							list_of_edges = [(edge, city1, city2)]
						elif edge['weight'] == max_size:
							list_of_edges.append((edge, city1, city2))

		if len(list_of_edges) > 0:
			best_route = [self.rank(x[0], game, pnum) for x in list_of_edges]
			best_route = list_of_edges[best_route.index(max(best_route))]
		
			return [best_route[1], best_route[2], best_route[0]['color']]
		
		return [None, None, None]