import random

from cambc import Controller, Direction, EntityType, Environment, Position
from core import Core
from builder import Builder


class Player:
	def __init__(self):
		self.robot = None

	def run(self, ct):
		if(self.robot == None):
			etype = ct.get_entity_type()
			if(etype == EntityType.CORE):
				self.robot = Core()
			elif(etype == EntityType.BUILDER_BOT):
				self.robot = Builder()

		if(self.robot):
			self.robot.TURN(ct)