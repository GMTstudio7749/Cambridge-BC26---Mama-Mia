from cambc import Controller, EntityType
from core import Core
from builder import Builder
from utils import *

class Player:
	def __init__(self):
		self.builder_ctrl = Builder()
		self.core_ctrl = Core()

	def run(self, ct: Controller):
		my_type = ct.get_entity_type()
		
		if(my_type == EntityType.CORE):
			self.core_ctrl.CORE_run(ct)
		elif(my_type == EntityType.BUILDER_BOT):
			self.builder_ctrl.BUILDER_run(ct)