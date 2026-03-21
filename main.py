from cambc import Controller, EntityType
from core import Core
from builder import Builder
import random


class Player:
	def __init__(self):
		self.core_ctrl = Core()
		self.builder_ctrl = Builder()
		self.setup = False

	def run(self, ct: Controller):
		my_type = ct.get_entity_type()
		
		if my_type == EntityType.CORE:
			if not self.setup:
				self.core_ctrl.CORE_setup(ct)
				self.setup = True
			self.core_ctrl.CORE_run(ct)
		elif my_type == EntityType.BUILDER_BOT:
			if not self.setup:
				self.builder_ctrl.BUILDER_setup(ct)
				self.setup = True
			self.builder_ctrl.BUILDER_run(ct)
