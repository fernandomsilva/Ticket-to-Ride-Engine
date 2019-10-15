import networkx as nx
import Queue
import collections
import random
import pickle

class PathAgent:
	def __init__(self):
		pass

	def decide(self, game, pnum):
		possible_moves = game.get_possible_moves(pnum)
		
		if len(possible_moves) == 0:
			f1 = open('disaster' + '.go', 'wb')
			pickle.dump(game, f1)
			f1.close()
			return None

		if possible_moves[0].function == 'chooseDestinationCards':
			for m in possible_moves:
				#if len(m.args[1]) == 3:
				if len(m.args[1]) == game.destination_deck_draw_rules[0]:
					#print 'd'
					return m
	
		p_queue = Queue.PriorityQueue()

		list_of_destinations = self.destinations_not_complete(game.players[pnum].hand_destination_cards, game.player_graph(pnum))

		free_connections_graph = self.free_routes_graph(game.board.graph, game.number_of_players)
		player_edges = game.player_graph(pnum).edges()
		
		joint_graph = free_connections_graph
		for edge in player_edges:
			joint_graph.add_edge(edge[0], edge[1], weight=0, color='none')
		
		#print joint_graph.edges()
		
		paths_to_take = []

		country_reference = {"FRANCE": ['FRANCEA', 'FRANCEB', 'FRANCEC', 'FRANCED'], "ITALIA": ['ITALIAA', 'ITALIAB', 'ITALIAC', 'ITALIAD', 'ITALIAE'], "OSTERREICH": ['OSTERREICHA', 'OSTERREICHB','OSTERREICHC'], "DEUTSCHLAND": ['DEUTSCHLANDA', 'DEUTSCHLANDB', 'DEUTSCHLANDC', 'DEUTSCHLANDD', 'DEUTSCHLANDE']}

		for destination in list_of_destinations:
			#if destination['city1'] in joint_graph and destination['city2'] in joint_graph:
			#	print 'YES: ' + destination['city1'] + " : " + destination['city2']
			#else:
			#	print 'NO : ' + destination['city1'] + " : " + destination['city2']

			city1, city2 = destination['city1'], destination['city2']
			temp = []
			try:
				if destination['type'] == "city":
					if city1 in joint_graph.nodes():
						for country in city2:
							for d in country_reference[country]:
								if d in joint_graph.nodes():
									if nx.has_path(joint_graph, city1, d):
										temp = nx.shortest_path(joint_graph, city1, d)
										destination['points'] = destination['points'][destination['city2'].index(country2)]
										break

				elif destination['type'] == "country":
					for d1 in country_reference[city1]:
						if d1 in joint_graph.nodes():
							for country2 in city2:
								for d2 in country_reference[country2]:
									if d2 in joint_graph.nodes():
										if nx.has_path(joint_graph, d1, d2):
											temp = nx.shortest_path(joint_graph, d1, d2)
											destination['points'] = destination['points'][destination['city2'].index(country2)]
											break
			except:
				try:
					temp = nx.shortest_path(joint_graph, destination['city1'], destination['city2'])
				except:
					continue

			for i in range(0, len(temp)-1):
				if (temp[i], temp[i+1]) not in player_edges and (temp[i+1], temp[i]) not in player_edges:
					if (temp[i], temp[i+1]) not in paths_to_take and (temp[i+1], temp[i]) not in paths_to_take:
						weight = 0
						try:
							weight = game.board.graph[temp[i]][temp[i+1]][0]['weight']
						except:
							weight = game.board.graph[temp[i]][temp[i+1]][0]['weight']

						if weight < game.players[pnum].number_of_trains:
							if isinstance(destination['points'], int):
								paths_to_take.append(((-1) * (game.point_table[weight] + 2 * destination['points']), temp[i], temp[i+1]))
							else:
								#print destination
								paths_to_take.append(((-1) * (game.point_table[weight] + 2 * destination['points'][destination['city2'].index(temp[i+1])]), temp[i], temp[i+1]))


		free_connections_graph = self.free_routes_graph(game.board.graph, game.number_of_players)

		if len(paths_to_take) == 0:
			for node1 in free_connections_graph:
				for node2 in free_connections_graph[node1]:
					for key in free_connections_graph[node1][node2]:
						if game.board.graph[node1][node2][key]['weight'] < game.players[pnum].number_of_trains:
							paths_to_take.append((game.point_table[game.board.graph[node1][node2][key]['weight']], node1, node2))

		for path in paths_to_take:
			p_queue.put(path)

		#if not p_queue.empty():
		first_max_color = None
		while not p_queue.empty():
			move = p_queue.get()
			#print move
			color = []
			try:
				#edges = game.board.graph[move[1]][move[2]]
				edges = free_connections_graph[move[1]][move[2]]
				for key in edges:
					color.append(free_connections_graph[move[1]][move[2]][key]['color'])
			except:
				#edges = game.board.graph[move[2]][move[1]]
				edges = free_connections_graph[move[2]][move[1]]
				for key in edges:
					color.append(free_connections_graph[move[2]][move[1]][key]['color'])

			
			if "GRAY" in color:
				#print "GG"
				color = ["RED", "ORANGE", "BLUE", "PINK", "WHITE", "YELLOW", "BLACK", "GREEN"]

			color_count = collections.Counter(game.players[pnum].hand)
			max_count = 0
			max_color = color[0]

			#print "cc: " + str(color_count)
				
			for c in color:
				if c.lower() in color_count:
					if color_count[c.lower()] > max_count:
						max_count = color_count[c.lower()]
						max_color = c
			
			#print "1: " + max_color
			
			if first_max_color == None:
				first_max_color = max_color

			moves_available = []
			for m in possible_moves:
				if m.function == 'claimRoute':
					if (m.args[0] == move[1] and m.args[1] == move[2]) or (m.args[0] == move[2] and m.args[1] == move[1]):
						moves_available.append(m)
			
			if len(moves_available) > 0:
				#print "if"
				return_move = None
				for m in moves_available:
					#print m.function
					#print m.args
					if m.args[2] == max_color:
						return_move = m
						break
				
				#print "return_move: " + return_move.function + " : " + str(return_move.args)
				#print max_color
				#print return_move.function
				#print return_move.args
				#print 'a'
				return return_move

		if len(game.train_deck.deck) > 0:
			top_draw = None
			for m in possible_moves:

				if m.function == 'drawTrainCard':
					#print m.function
					#print m.args
					if m.args == first_max_color:
						return m
					elif m.args == 'top':
						top_draw = m
			#print 'b'
			#print top_draw.function
			#print top_draw.args
			return top_draw

#			else:
#				#print "else"
#				top_draw = None
#				for m in possible_moves:
#
#					if m.function == 'drawTrainCard':
#						#print m.args
#						if m.args == max_color:
#							return m
#						elif m.args == 'top':
#							top_draw = m
#				return top_draw
			
		for m in possible_moves:
			if len(game.train_deck.deck) > 0:
				if m.function == 'drawTrainCard' and m.args == 'top':
					return m
			else:
				if m.function == 'drawTrainCard' and m.args == 'wild':
					return m

		if len(possible_moves) > 0:
			return random.choice(possible_moves)
		
		#print len(game.train_deck.deck)
		#print len(game.train_deck.discard_pile)
		#for (city1, city2) in paths_to_take:
		#	try:
		#		p_queue.
		#	except:

		#print player_edges
		#print paths_to_take
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'GRAY')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'BLACK')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'BLUE')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'GREEN')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'RED')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'ORANGE')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'YELLOW')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'PINK')
		#print game.board.get_free_connection(paths_to_take[0][0], paths_to_take[0][1], 'WHITE')
		
	def destinations_not_complete(self, destination_cards, graph, switzerland=False):
		result = []
		
		country_reference = {"FRANCE": ['FRANCEA', 'FRANCEB', 'FRANCEC', 'FRANCED'], "ITALIA": ['ITALIAA', 'ITALIAB', 'ITALIAC', 'ITALIAD', 'ITALIAE'], "OSTERREICH": ['OSTERREICHA', 'OSTERREICHB','OSTERREICHC'], "DEUTSCHLAND": ['DEUTSCHLANDA', 'DEUTSCHLANDB', 'DEUTSCHLANDC', 'DEUTSCHLANDD', 'DEUTSCHLANDE']}

		for card in destination_cards:
			city1, city2 = card.destinations
			solved = False
			try:
				if card.type == "city":
					if city1 in graph.nodes():
						for country in city2:
							for d in country_reference[country]:
								if d in graph.nodes():
									if nx.has_path(graph, city1, d):
										solved = True
										break
						if solved:
							break

				elif card.type == "country":
					for d1 in country_reference[city1]:
						if d1 in graph.nodes():
							for country2 in city2:
								for d2 in country_reference[country2]:
									if d2 in graph.nodes():
										if nx.has_path(graph, d1, d2):
											solved = True
											break
							if solved:
								break
					if solved:
						break
			except:
				try:
					nx.shortest_path(graph, city1, city2)
					solved = True
				except:
					solved = False

			if not solved:
				try:
					result.append({'city1': city1, 'city2': city2, 'points': card.points, 'type': card.type})
				except:
					result.append({'city1': city1, 'city2': city2, 'points': card.points})

		return result

	def free_routes_graph(self, graph, number_of_players):
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
							if graph[node1][node2][edge]['owner'] == -1:
								G.add_edge(node1, node2, weight=graph[node1][node2][edge]['weight'], color=graph[node1][node2][edge]['color'])

			visited_nodes.append(node1)
		
		return G