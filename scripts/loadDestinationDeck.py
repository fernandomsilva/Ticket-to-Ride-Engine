import re

class DestinationCard:
	def __init__(self, dest1, dest2, points):
		self.destinations = [dest1, dest2]
		self.points = points
	
	def __getstate__(self): return self.__dict__
	def __setstate__(self, d): self.__dict__.update(d)

	def __str__(self):
		return str(self.destinations) + " " + str(self.points)

class DestinationCountryCard(DestinationCard):
	def setType(self, ctype):
		self.type = ctype

	def __str__(self):
		return str(self.destinations) + " " + str(self.points) + " " + self.type

#class DestinationCityCountryCard(DestinationCard):
#	def setType():
#		self.type = 'city'

def loaddestinationdeckfromfile(filename):
	file = open(filename, 'r')

	deck = []

	line = file.readline()
	while len(line.strip()) > 0:
		index = re.search('\d', line).start()
		index_space = line[index:].index(' ')

		deck.append(DestinationCard(line[:index-1], line[index+index_space+1:].strip(), int(line[index:index+index_space])))

		line = file.readline()

	return deck

def loadcountrydestinationdeck(filename, ctype):
	file = open(filename, 'r')

	deck = []

	line = file.readline()
	while len(line.strip()) > 0:
		index = re.search('\d', line)

		dest1 = line[:index.start()-1]
		dests2 = []
		points = []

		while index:
			index_space = line[index.start():].index(' ')
			#index_space2 = line[index_space:].index(' ')
			temp_index = re.search('\d', line[index.start()+index_space:])

			points.append(int(line[index.start():index.start()+index_space]))

			if temp_index:
				temp_abs_index = temp_index.start() + index.start() + index_space
				dests2.append(line[index.start()+index_space+1:temp_abs_index-1].strip())
			else:
				dests2.append(line[index.start()+index_space+1:].strip())

			line = line[temp_abs_index:]
			index = re.search('\d', line)

		obj = DestinationCountryCard(dest1, dests2, points)
		obj.setType(ctype)
		deck.append(obj)

		line = file.readline()

	return deck

def destinationdeckdict(dest_list, board="usa"):
	result = {}

	if board == "europe" or board == "asia":
		for dest in dest_list[6:]:
			result[dest] = 1
	
		result['long_routes'] = dest_list[:6]
	else:
		for dest in dest_list:
			result[dest] = 1

	return result

def loadswitzerlanddestinationdeck(dest_filename, country_country_dest_filename, city_country_dest_filename):
	dest_deck = loaddestinationdeckfromfile(dest_filename)
	country_deck = loadcountrydestinationdeck(country_country_dest_filename, 'country')
	city_deck = loadcountrydestinationdeck(city_country_dest_filename, 'city')

	return destinationdeckdict(dest_deck + country_deck + city_deck)