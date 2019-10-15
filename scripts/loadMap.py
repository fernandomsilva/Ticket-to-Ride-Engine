import networkx as nx
import re

def loadgraphfromfile(filename):
	file = open(filename, 'r')
	line = file.readline()

	G = nx.MultiGraph()

	while len(line.strip()) > 0:
		G.add_node(line.strip())
		line = file.readline()

	line = file.readline()
	while len(line.strip()) > 0:
		num = re.search('[+-]?\d+(?:\.\d+)?', line).group(0)
		index = re.search('[+-]?\d+(?:\.\d+)?', line).start()
		index_after_num = re.search('[+-]?\d+(?:\.\d+)?', line).start() + len(num) - 1
		index_space = line[index_after_num+2:].index(' ')
		color = line[index_after_num+2:index_after_num+2+index_space]
		#print line[index+2:index+2+index_space]]
		node1 = line[:index].strip() if (line[:index].strip())[-1] != ' ' else line[:index-1].strip()
		node2 = line[index_after_num+2+index_space:].strip() if (line[index_after_num+2+index_space:].strip())[-1] != ' ' else (line[index_after_num+2+index_space:].strip())[:-1]
		if num[0] == '+':
			G.add_edge(node1, node2, weight=float(num[2:]), color=color, mountain=int(num[1]))
		else:
			G.add_edge(node1, node2, weight=float(num), color=color, mountain=int(0))
		line = file.readline()

	for e in G.edges():
		for me in G[e[0]][e[1]]:
			G[e[0]][e[1]][me]['owner'] = -1
			num = G[e[0]][e[1]][me]['weight']

			if num < 0:
				G[e[0]][e[1]][me]['underground'] = True
			else:
				G[e[0]][e[1]][me]['underground'] = False
			if (num % 1) > 0.0:
				G[e[0]][e[1]][me]['ferries'] = int((num % 1) * 10.0)
			else:
				G[e[0]][e[1]][me]['ferries'] = 0

	for e in G.edges():
		for me in G[e[0]][e[1]]:
			G[e[0]][e[1]][me]['weight'] = int(abs(G[e[0]][e[1]][me]['weight']))

	return G
