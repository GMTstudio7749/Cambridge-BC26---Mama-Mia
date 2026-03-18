import random
from cambc import Controller, Direction, EntityType, Environment, Position
import sys
from movement import BugNav

class Robot:
	def __init__(self):
		self.DIRS = [
			Direction.NORTH,
			Direction.NORTHEAST,
			Direction.EAST,
			Direction.SOUTHEAST,
			Direction.SOUTH,
			Direction.SOUTHWEST,
			Direction.WEST,
			Direction.NORTHWEST
		]
		self.turnCount = 0

		self.bug_nav = BugNav()
		self.core_pos = None

	def GET_core_pos(self, ct):
		nearby_entities = ct.get_nearby_entities()
		for eid in nearby_entities:
			if ct.get_entity_type(eid) == EntityType.CORE:
				self.core_pos = ct.get_position(eid)
				break
		if self.core_pos is None:
			self.core_pos = ct.get_position()

	def TURN(self, ct):
		self.turnCount += 1
		if(self.turnCount == 1):
			self.bug_nav.SETUP(ct)
			self.GET_core_pos(ct)

		self.bug_nav.SENSE_nearby(ct)
		self.RUN(ct)

	def RUN(self, ct):
		pass

	
	#define global function and variable in this file