import random
from cambc import Controller, Direction, EntityType, Environment, Position
from utils import *

class Explore:
	def __init__(self):
		self.MAP_WIDTH = -1
		self.MAP_HEIGHT = -1

		self.setup = False
		self.Explore_Dir = Direction.CENTRE
		self.Explore_Target = Position(-1, -1)
		self.Explore_Turn = -1

		self.bugnav = BugNav()
	
	def EXPLORE_setup(self, ct: Controller, spawn_pos: Position, core_pos: Position):
		"""Setup explore move function infos and const, along with bugnav"""
		self.bugnav.SETUP(ct)
		self.MAP_WIDTH = ct.get_map_width()
		self.MAP_HEIGHT = ct.get_map_height()

		sx, sy = spawn_pos.x, spawn_pos.y
		cx, cy = core_pos.x, core_pos.y
		if sx < cx and sy < cy:
			self.Explore_Dir = Direction.NORTHWEST
		elif sx < cx and sy > cy:
			self.Explore_Dir = Direction.SOUTHWEST
		elif sx > cx and sy < cy:
			self.Explore_Dir = Direction.NORTHEAST
		else:
			self.Explore_Dir = Direction.SOUTHEAST

	def IS_in_map(self, x: int, y: int):
		"""Check if two int x, y is located in map"""
		if x < 0 or x >= self.MAP_WIDTH or y < 0 or y >= self.MAP_HEIGHT:
			return False
		return True

	def GET_next_bounce_dir(self, dir: Direction, edge_pos: Position):
		"""Get the next bounce dir depends on current dir and edge pos"""
		if dir not in Diagonal_Dirs:
			return random.choice(Diagonal_Dirs)
		
		bounce_dir = dir.opposite()
		for _ in range(4):
			bounce_dir = bounce_dir.rotate_right().rotate_right()
			
			dx, dy = bounce_dir.delta()
			nx, ny = edge_pos.x + dx, edge_pos.y + dy
			if not self.IS_in_map(nx, ny): continue
			return bounce_dir

		return random.choice(Diagonal_Dirs)	
	
	def GET_next_explore_target(self, ct: Controller, dir: Direction):
		"""Get the next explore target, depends on dir and position\n
		if dir = Direction.CENTRE -> just random a diagonal dir"""
		X, Y = self.Explore_Target.x, self.Explore_Target.y
		if X < 0 or Y < 0:
			X, Y = ct.get_position().x, ct.get_position().y

		if dir == Direction.CENTRE:
			dir = random.choice(Diagonal_Dirs)
		elif not dir in Diagonal_Dirs:
			dir = dir.rotate_right()
		
		dx, dy = dir.delta()
		while self.IS_in_map(X + dx, Y + dy):
			X += dx
			Y += dy

		return Position(X, Y)

	def MOVE_explore(self, ct: Controller, range_squared: int, max_turn: int):
		"""Explore movement function, reset max_turn rounds\n
		Move to an accepted range within the explore target"""
		if self.Explore_Target == Position(-1, -1):
			self.Explore_Target = self.GET_next_explore_target(ct, self.Explore_Dir)
			self.Explore_Turn = max_turn

		my_pos = ct.get_position()
		cur_dis = my_pos.distance_squared(self.Explore_Target)
		if cur_dis <= range_squared or self.Explore_Turn < 1:
			self.Explore_Turn = max_turn
			self.Explore_Dir = self.GET_next_bounce_dir(self.Explore_Dir, self.Explore_Target)
			self.Explore_Target = self.GET_next_explore_target(ct, self.Explore_Dir)

		if ct.get_move_cooldown() == 0:
			self.Explore_Turn = self.Explore_Turn - 1
			self.bugnav.SENSE_nearby(ct)
			self.bugnav.MOVE_to_target(ct, self.Explore_Target, False)
			
		ct.draw_indicator_dot(self.Explore_Target, 100, 100, 255)

		
class BugNav:
	def __init__(self):
		self.DIRECTIONS = [
			Direction.NORTH,
			Direction.NORTHEAST,
			Direction.EAST,
			Direction.SOUTHEAST,
			Direction.SOUTH,
			Direction.SOUTHWEST,
			Direction.WEST,
			Direction.NORTHWEST
		]

		self.mapInfos = []

		self.lastLocation = None
		self.currentLocation = None
		self.lastTargetLocation = None
		self.bugStackIndex = 0
		self.MAX_STACK_SIZE = 100
		self.bugStack = [None] * self.MAX_STACK_SIZE
		self.stuckTurns = 0
		self.jiggleRight = False
		self.dir_order = [Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST, Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST, Direction.CENTRE]
		self.RIGHT = random.randint(0, 1)

		self.originConnect = None
		self.lastConnect = None

		self.currentConnections = []

	def SETUP(self, ct):
		# run this in turn 1 pls
		self.mapInfos =  [[None for _ in range(ct.get_map_height())] for _ in range(ct.get_map_width())]

	def SENSE_nearby(self, ct):
		#run this first every turn for the bugnav to see the environment
		for pos in ct.get_nearby_tiles():
			if(not self.onTheMap(ct, pos)):
				continue
			if( ct.get_tile_env(pos) == Environment.WALL):
				self.mapInfos[pos.x][pos.y] = Environment.WALL
			elif(not ct.is_tile_empty(pos)):
				bid = ct.get_tile_building_id(pos)
				self.mapInfos[pos.x][pos.y] = ct.get_entity_type(bid)
			else:
				self.mapInfos[pos.x][pos.y] = Environment.EMPTY
				if(ct.get_tile_env(pos) == Environment.ORE_TITANIUM ):
					self.mapInfos[pos.x][pos.y] = Environment.ORE_TITANIUM 
				if(ct.get_tile_env(pos) == Environment.ORE_AXIONITE):
					self.mapInfos[pos.x][pos.y] = Environment.ORE_AXIONITE

	def canMove(self, ct, loc):

		if(not self.onTheMap(ct, loc)): return False
		return self.mapInfos[loc.x][loc.y] == EntityType.CORE or self.mapInfos[loc.x][loc.y] == EntityType.ROAD or self.mapInfos[loc.x][loc.y] == Environment.EMPTY  or self.mapInfos[loc.x][loc.y] == EntityType.CONVEYOR or self.mapInfos[loc.x][loc.y] == EntityType.BRIDGE


	def tooCloseToDanger(self, ct, loc):
		return False

	def onTheMap(self, ct, loc):
		return (0 <= loc.x and loc.x < ct.get_map_width()) and (0 <= loc.y and loc.y < ct.get_map_height())

	def reachableFrom(self, ct, loc, target):
		targetInfo = self.mapInfos[target.x][target.y]
		if(targetInfo == None or targetInfo == Environment.WALL or targetInfo == EntityType.BARRIER):
			return False
		checkLoc = loc
		while(not checkLoc == target):
			info = self.mapInfos[checkLoc.x][checkLoc.y]
			if(not self.onTheMap(ct, checkLoc) or (info == None or self.mapInfos[checkLoc.x][checkLoc.y] == Environment.WALL or self.mapInfos[checkLoc.x][checkLoc.y] == EntityType.BARRIER)):
				return False
			checkLoc = checkLoc.add(checkLoc.direction_to(target))
		return True

	def getAdjacentAllies(self, ct, loc):
		return 0

	def tileScore(self, ct, loc, allyScore, enemyScore, emptyScore):
		return self.tileScoreBool(ct, loc, allyScore, enemyScore, emptyScore, False)

	def tileScoreBool(self, ct, loc, allyScore, enemyScore, emptyScore, checkAllyBehind):
		if(not self.onTheMap(ct, loc)):
			return -99999
		score = 0
		info = self.mapInfos[loc.x][loc.y]
		if(self.tooCloseToDanger(ct, loc)):
			score -= 20
		# if(mapData.enemyDefenseTowers.size != 0):
		# 	for enemyTower in mapData.enemyDefenseTowers.getArray():
		# 		if(enemyTower.location.distance_squared_to(loc) <= enemyTower.type.action_radius_squared):
		# 			score -= 10000
					# break

		if(info == EntityType.CORE or info == EntityType.CONVEYOR  or info == EntityType.ROAD):
			if(ct.get_team(ct.get_tile_building_id(loc))  == ct.get_team()):
				score += allyScore
			else:
				score += enemyScore

			return score


		# allyBehind = False
		# if(checkAllyBehind):
		# 	dirToTile  = ct.get_position().direction_to(loc)
		# 	loc1 = loc.add(dirToTile)
		# 	loc2 = loc.add(dirToTile.rotate_left())
		# 	loc3 = loc.add(dirToTile.rotate_right())

		# 	allyBehind = (self.onTheMap(loc1) and mapData.getMapInfo(loc1).get_paint().is_ally() or
		# 		(self.onTheMap(loc2) and mapData.getMapInfo(loc2).get_paint().is_ally()) or
		# 		(self.onTheMap(loc3) and mapData.getMapInfo(loc3).get_paint().is_ally()))
		if(info == Environment.EMPTY):
			score += emptyScore
		if(info == Environment.ORE_AXIONITE or info == Environment.ORE_TITANIUM):
			score -= 20
			# if(not allyBehind): score -= 2
		# allyBehind = False
		return score

	def toCardinal(self, dir):
		dx, dy = dir.delta()
		
		if dx == 0:
			return Direction.SOUTH if dy > 0 else Direction.NORTH
		if dy == 0:
			return Direction.EAST if dx > 0 else Direction.WEST

		# diagonal → choose dominant axis
		if abs(dx) > abs(dy):
			return Direction.EAST if dx > 0 else Direction.WEST
		else:
			return Direction.SOUTH if dy > 0 else Direction.NORTH

	def fuzzyMove(self,ct, dir):
		for d in self.fuzzyDirs(dir):
			if(ct.can_move(d)):
				ct.move(d)
				return

	def fuzzyDirs(self, dir):
		if(not self.RIGHT):
			return [
				dir,
				dir.rotate_left(),
				dir.rotate_right(),
				dir.rotate_left().rotate_left(),
				dir.rotate_right().rotate_right(),
				dir.rotate_left().rotate_left().rotate_left(),
				dir.rotate_right().rotate_right().rotate_right()
			]
		else:
			return [
				dir,
				dir.rotate_right(),
				dir.rotate_left(),
				dir.rotate_right().rotate_right(),
				dir.rotate_left().rotate_left(),
				dir.rotate_right().rotate_right().rotate_right(),
				dir.rotate_left().rotate_left().rotate_left()
			]


	def MOVE_to_target(self, ct, loc: Position, zigzag: bool, allyScore=0, enemyScore=0, emptyScore=-2):
		# THIS HERE, EXPLORE USING ROAD ONLY, NO CONVEYOR BUILD

		ct.draw_indicator_line(ct.get_position(), loc, 255, 0, 0)

		if(not ct.get_move_cooldown() == 0): return

		self.lastLocation = self.currentLocation
		self.currentLocation = ct.get_position()


		if(self.lastTargetLocation == None or self.lastTargetLocation.distance_squared(loc) > 8 or self.bugStackIndex >= self.MAX_STACK_SIZE-10):
			self.bugStack = [None] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0
			self.lastTargetLocation = loc
			self.lastLocation = ct.get_position()
		if(self.lastTargetLocation != None and self.lastTargetLocation.distance_squared(loc) <= 8):
			self.lastTargetLocation = loc

		while (
			self.bugStackIndex != 0 and
			(
				(
					self.canMove(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 1])) and
					not self.tooCloseToDanger(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 1]))
				)
				or
				(
					self.bugStackIndex > 1 and
					self.canMove(ct, ct.get_position().add( self.bugStack[self.bugStackIndex - 2])) and
					not self.tooCloseToDanger(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 2])) and
					not (
						self.lastLocation is not None and
						ct.get_position().add(self.bugStack[self.bugStackIndex - 2]) == self.lastLocation
					)
				)
			)
		):
			self.bugStackIndex -= 1

		if(self.reachableFrom(ct, ct.get_position(), loc)):
			self.bugStack = [None] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0

		if(self.bugStackIndex == 0):
			dirToTarget = ct.get_position().direction_to(loc)
			bestDir = None
			bestScore = -9999
			score1 = self.tileScore(ct, ct.get_position().add(dirToTarget),  allyScore, enemyScore, emptyScore)
			score2 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_left()), allyScore, enemyScore, emptyScore)
			score3 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_right()),  allyScore, enemyScore, emptyScore)

			if(zigzag):
				if(self.dir_order.index(dirToTarget) % 2 == 0 and ct.get_position().distance_squared(loc) > 50):
					if(ct.get_current_round()%4 < 2):
						score2 += 1
					else:
						score3 += 1
			if(self.canMove(ct, ct.get_position().add(dirToTarget)) and score1 > bestScore and not ct.get_position().add(dirToTarget) == self.lastLocation):
				bestDir = dirToTarget
				bestScore = score1
			if(self.canMove(ct, ct.get_position().add(dirToTarget.rotate_left())) and score2 > bestScore and not ct.get_position().add(dirToTarget.rotate_left()) == self.lastLocation):
				bestDir = dirToTarget.rotate_left()
				bestScore = score2
			if(self.canMove(ct, ct.get_position().add(dirToTarget.rotate_right())) and score3 > bestScore and not ct.get_position().add(dirToTarget.rotate_right()) == self.lastLocation):
				bestDir = dirToTarget.rotate_right()
				bestScore = score3



			if(bestDir is not None and bestScore > -20):
				if(ct.can_build_road(ct.get_position().add(bestDir))):
					ct.build_road(ct.get_position().add(bestDir))

				if(ct.can_move(bestDir)):
					ct.move(bestDir)
					return

			locCheck = ct.get_position().add(dirToTarget)
			checkFrontRobot = self.onTheMap(ct, locCheck) and ct.get_tile_builder_bot_id(locCheck) != None
			locCheck = ct.get_position().add(dirToTarget.rotate_left())
			checkLeftRobot = self.onTheMap(ct, locCheck) and  ct.get_tile_builder_bot_id(locCheck) != None
			locCheck = ct.get_position().add(dirToTarget.rotate_right())
			checkRightRobot = self.onTheMap(ct, locCheck) and  ct.get_tile_builder_bot_id(locCheck) != None
			if(checkFrontRobot and checkLeftRobot and checkRightRobot):
				print("FUZZY MOVIGN")
				self.fuzzyMove(ct, dirToTarget.opposite())
				return
			self.bugStack[self.bugStackIndex] = dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right()
			self.bugStackIndex += 1

		if(self.RIGHT):
			dir = self.bugStack[self.bugStackIndex-1].rotate_right()
			for i in range(8):
				if(not self.canMove(ct, ct.get_position().add(dir)) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [None] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					if(not self.canMove(ct, ct.get_position().add(dir))):
						continue
					if(ct.can_build_road(ct.get_position().add(dir))):
						ct.build_road(ct.get_position().add(dir))

					if(ct.can_move(dir)):
						ct.move(dir)
						return
				dir = dir.rotate_right()
		else:
			dir = self.bugStack[self.bugStackIndex-1].rotate_left()
			for i in range(8):
				if(not self.canMove(ct, ct.get_position().add(dir)) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [None] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					if(not self.canMove(ct, ct.get_position().add(dir))):
						continue
					if(ct.can_build_road(ct.get_position().add(dir))):
						ct.build_road(ct.get_position().add(dir))

					if(ct.can_move(dir)):
						ct.move(dir)
						return
				dir = dir.rotate_left()


	def calcBestDirConveyor(self, ct, cur_pos, loc, allyScore, enemyScore, emptyScore):
		dirToTarget = cur_pos.direction_to(loc)
		bestDir = None
		bestScore = -9999

		if(cur_pos.distance_squared(loc) < 30):
			allyScore -= 5
			emptyScore += 5

		dir1 = dirToTarget
		dir2 = dirToTarget.rotate_left()
		dir3 = dirToTarget.rotate_right()
		score1 = self.tileScore(ct, cur_pos.add(dir1),  allyScore, enemyScore, emptyScore)
		score2 = self.tileScore(ct, cur_pos.add(dir2), allyScore, enemyScore, emptyScore)
		score3 = self.tileScore(ct, cur_pos.add(dir3),  allyScore, enemyScore, emptyScore)
		if(dir1 == self.toCardinal(dir1)):
			score1 += 4
		if(dir2 == self.toCardinal(dir2)):
			score2 += 4
		if(dir3 == self.toCardinal(dir3)):
			score3 += 4

		if(cur_pos.add(dir1).distance_squared(loc) <= 2):
			score1 += 10
		if(cur_pos.add(dir2).distance_squared(loc) <= 2):
			score2 += 10
		if(cur_pos.add(dir3).distance_squared(loc) <= 2):
			score3 += 10

		ct.draw_indicator_line(cur_pos.add(dir1), cur_pos, 255, 255, 255)
		ct.draw_indicator_line(cur_pos.add(dir2), cur_pos, 255, 255, 255)
		ct.draw_indicator_line(cur_pos.add(dir3), cur_pos, 255, 255, 255)


		if(self.canMove(ct, cur_pos.add(dirToTarget)) and score1 > bestScore and not cur_pos.add(dirToTarget) == self.lastLocation):
			bestDir = dirToTarget
			bestScore = score1
		if(self.canMove(ct, cur_pos.add(dirToTarget.rotate_left())) and score2 > bestScore and not cur_pos.add(dirToTarget.rotate_left()) == self.lastLocation):
			bestDir = dirToTarget.rotate_left()
			bestScore = score2
		if(self.canMove(ct, cur_pos.add(dirToTarget.rotate_right())) and score3 > bestScore and not cur_pos.add(dirToTarget.rotate_right()) == self.lastLocation):
			bestDir = dirToTarget.rotate_right()
			bestScore = score3
		return bestDir, bestScore, dirToTarget

	def tryBuildConveyor(self, ct, pos, dir, save=True):
		bid = ct.get_tile_building_id(pos)
		btype = ct.get_entity_type(bid)
		bteam = ct.get_team(bid)

		nextPos = pos.add(dir)
		nextBid = ct.get_tile_building_id(nextPos)
		nextBtype = ct.get_entity_type(nextBid)
		nextBteam = ct.get_team(nextBid)

		if(pos.add(dir) in self.currentConnections):
			return False



		if(nextBid is not None and nextBteam != ct.get_team()) or not self.canMove(ct, nextPos):
			print("THIS?")
			return

		if(bid is None):
			if(ct.can_build_conveyor(pos, dir)):
				ct.build_conveyor(pos, dir)
				if(save):
					self.lastConnect = pos.add(dir)
			return True
		elif(bteam != ct.get_team()):
			return False
		elif(btype == EntityType.ROAD):
			if(ct.can_destroy(pos)):
				ct.destroy(pos)
				print("SO BAD")
				if(ct.can_build_conveyor(pos, dir)):
					ct.build_conveyor(pos, dir)
					if(save):
						self.lastConnect = pos.add(dir)
			return True

	def tryBuildBridge(self, ct, pos, nextPos):
		bid = ct.get_tile_building_id(pos)
		btype = ct.get_entity_type(bid)
		bteam = ct.get_team(bid)


		if(nextPos in self.currentConnections):
			return False

		if(not self.onTheMap(ct, nextPos) or not ct.is_in_vision(nextPos)):
			return False
		nextBid = ct.get_tile_building_id(nextPos)
		nextBtype = ct.get_entity_type(nextBid)
		nextBteam = ct.get_team(nextBid)
		if(nextBid is not None and nextBteam != ct.get_team()) or not self.canMove(ct, nextPos):
			return
			
		if(bid is None):
			if(ct.can_build_bridge(pos, nextPos)):
				ct.build_bridge(pos, nextPos)
				self.lastConnect = nextPos

			return True
		elif(bteam != ct.get_team()):
			return False
		elif(btype == EntityType.ROAD):
			if(ct.can_destroy(pos)):
				ct.destroy(pos)
				if(ct.can_build_bridge(pos, nextPos)):
					ct.build_bridge(pos, nextPos)
					self.lastConnect = nextPos
			return True

	def tryBuildRoad(self, ct, pos):
		if(ct.can_build_road(pos)):
			ct.build_road(pos)

	def canMoveDirWithConveyor(self, ct, loc, dir):
		if(not self.onTheMap(ct, loc)): return False
		if(loc in self.currentConnections):
			return False
		if(self.lastTargetLocation is not None and len(self.currentConnections) > 2 and self.lastTargetLocation.direction_to(self.currentConnections[-2]) == dir):
			return False
		if(self.lastTargetLocation is not None and len(self.currentConnections) > 2):
			ct.draw_indicator_line(self.lastLocation, self.currentConnections[-2], 100, 100, 150)
			# print(self.lastTargetLocation.direction_to(self.currentConnections[-2]))

		if(not self.onTheMap(ct, loc) or not ct.is_in_vision(loc)):
			return False

		nextBid = ct.get_tile_building_id(loc)
		nextBtype = ct.get_entity_type(nextBid)
		nextBteam = ct.get_team(nextBid)

		ct.draw_indicator_line(loc, ct.get_position(), 255, 100, 255)
		if(not self.canMove(ct, loc)):
			return False

		if(nextBteam != ct.get_team()):
			return False
		x = loc.x
		y = loc.y
		if(self.mapInfos[x][y] == Environment.WALL or self.mapInfos[x][y] == Environment.ORE_AXIONITE or self.mapInfos[x][y] == Environment.ORE_TITANIUM):
			print("THIS IS BAD")

			return False
		if(self.mapInfos[x][y] == Environment.EMPTY):
			return True
		if(nextBtype == EntityType.CORE):
			return True
		if(nextBtype == EntityType.CONVEYOR):
			ct.draw_indicator_line(Position(0, 0), loc.add(ct.get_direction(nextBid)), 25, 105, 225)
			ct.draw_indicator_line(Position(0, 0), loc, 25, 105, 225)
			if(ct.get_direction(nextBid) == dir.opposite()):
				print(loc, ct.get_direction(nextBid), dir.opposite())
				return False
		if(nextBtype == EntityType.BRIDGE):
			if(ct.get_bridge_target(nextBid) == ct.get_position()):
				return False
		print(loc)
		return True

	def tryDirWithConveyor(self, ct, dir):
		print(dir)
		nextPos = ct.get_position().add(dir)
		ct.draw_indicator_line(ct.get_position(), nextPos, 255, 255, 255)
		if(dir == self.toCardinal(dir)):
			self.tryBuildConveyor(ct, self.lastConnect, dir)
		else:
			if(ct.get_global_resources()[0] < ct.get_bridge_cost()[0]):
				return
			if(self.canMoveDirWithConveyor(ct, self.lastConnect.add(dir).add(dir), dir)):
				self.tryBuildBridge(ct, self.lastConnect, nextPos.add(dir).add(dir))
			self.tryBuildBridge(ct, self.lastConnect, nextPos.add(dir))
		self.tryBuildRoad(ct, nextPos)


	def MOVE_to_target_with_conveyor(self, ct, origin: Position, loc: Position,allyScore=2, enemyScore=-10, emptyScore=0):
		# THIS HERE, EXPLORE USING CONVEYOR + ROAD, dont care about allyScore, enemyScore and emptyScore

		ct.draw_indicator_line(ct.get_position(), loc, 255, 0, 0)


		if(not ct.get_move_cooldown() == 0): return
		if(ct.get_global_resources()[0] < ct.get_conveyor_cost()[0]):
			return


		if(self.originConnect == None or self.originConnect != origin):
			self.originConnect = origin
			self.lastConnect = origin
			self.currentConnections = []
			print("RESETED CONENCTIONS")


		self.lastLocation = self.currentLocation
		self.currentLocation = ct.get_position()

		if(self.lastTargetLocation == None or self.lastTargetLocation.distance_squared(loc) > 8 or self.bugStackIndex >= self.MAX_STACK_SIZE-10):
			print("BUGSTACK ", self.bugStackIndex)
			self.bugStack = [None] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0
			self.lastTargetLocation = loc
			self.lastLocation = ct.get_position()
			print("RESETED CONENCTIONS2")

		if(self.lastTargetLocation != None and self.lastTargetLocation.distance_squared(loc) <= 8):
			self.lastTargetLocation = loc


		if(self.lastConnect != None):
			ct.draw_indicator_line(self.lastConnect, Position(0, 0), 255, 255, 100)

		if(ct.get_position().distance_squared(self.lastConnect) > 0):
			self.MOVE_to_target(ct, self.lastConnect, False, 0, 0, 0)
			return

		if(self.lastConnect not in self.currentConnections):
			self.currentConnections.append(self.lastConnect)
		print(self.currentConnections)

		while (
			self.bugStackIndex != 0 and
			(
				(
					self.canMove(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 1])) and
					not self.tooCloseToDanger(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 1]))
				)
				or
				(
					self.bugStackIndex > 1 and
					self.canMove(ct, ct.get_position().add( self.bugStack[self.bugStackIndex - 2])) and
					not self.tooCloseToDanger(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 2])) and
					not (
						self.lastLocation is not None and
						ct.get_position().add(self.bugStack[self.bugStackIndex - 2]) == self.lastLocation
					)
				)
			)
		):
			self.bugStackIndex -= 1

		if(self.reachableFrom(ct, ct.get_position(), loc)):
			self.bugStack = [None] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0

		if(self.bugStackIndex == 0):


			bestDir, bestScore, dirToTarget = self.calcBestDirConveyor(ct, ct.get_position(), loc, allyScore, enemyScore, emptyScore)

			if(bestDir is not None and bestScore > -20):
				nextPos = ct.get_position().add(bestDir)

				# if(ct.get_position() == origin):
					# self.lastConnect = ct.get_position().add(bestDir)

				bid = ct.get_tile_building_id(self.lastConnect)
				btype = ct.get_entity_type(bid)
				bteam = ct.get_team(bid)

				if(bid != None):
					if(bteam == ct.get_team()):
						if(btype == EntityType.CONVEYOR):
							self.lastConnect = self.lastConnect.add(ct.get_direction(bid))
						if(btype == EntityType.BRIDGE):
							self.lastConnect = ct.get_bridge_target(bid)

				bestDir2, bestScore2, dirToTarget2 = self.calcBestDirConveyor(ct, ct.get_position().add(bestDir), loc, allyScore, enemyScore, emptyScore)
				builded = False
				
				
				if(bestDir == self.toCardinal(bestDir)):
					if(ct.get_position() == self.lastConnect):
						builded = builded or self.tryBuildConveyor(ct, self.lastConnect, bestDir)
				else:
					if(ct.get_global_resources()[0] < ct.get_bridge_cost()[0]):
						return
					if(bestDir2 is not None and bestScore2 > -20):
						bestDir3, bestScore3, dirToTarget3 = self.calcBestDirConveyor(ct, nextPos.add(bestDir2), loc, allyScore, enemyScore, emptyScore)
						if(bestDir3 is not None and bestScore3 > -20):

							nextPos2 = nextPos.add(bestDir2)
							builded = builded or self.tryBuildBridge(ct, self.lastConnect, nextPos2.add(bestDir3))
						builded = builded or self.tryBuildBridge(ct, self.lastConnect, nextPos.add(bestDir2))
					builded = builded or self.tryBuildBridge(ct, self.lastConnect, nextPos)

				if(ct.can_build_road(ct.get_position().add(bestDir))):
					ct.build_road(ct.get_position().add(bestDir))

				if(nextPos.distance_squared(self.lastConnect) < ct.get_position().distance_squared(self.lastConnect)):
					if(ct.can_move(bestDir)):
						ct.move(bestDir)
					return
				if(ct.get_action_cooldown() > 0):
					return

			locCheck = ct.get_position().add(dirToTarget)
			checkFrontRobot = self.onTheMap(ct, locCheck) and ct.get_tile_builder_bot_id(locCheck) != None
			locCheck = ct.get_position().add(dirToTarget.rotate_left())
			checkLeftRobot = self.onTheMap(ct, locCheck) and  ct.get_tile_builder_bot_id(locCheck) != None
			locCheck = ct.get_position().add(dirToTarget.rotate_right())
			checkRightRobot = self.onTheMap(ct, locCheck) and  ct.get_tile_builder_bot_id(locCheck) != None
			if(checkFrontRobot and checkLeftRobot and checkRightRobot):
				self.fuzzyMove(ct, dirToTarget.opposite())
				return
			self.bugStack[self.bugStackIndex] = dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right()
			self.bugStackIndex += 1

		if(self.RIGHT):
			print("LEFTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_right()
			for i in range(8):
				if(not self.canMoveDirWithConveyor(ct, ct.get_position().add(dir), dir) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [None] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					if(not self.canMove(ct, ct.get_position().add(dir))):
						continue
					self.tryDirWithConveyor(ct, dir)
					if(ct.get_position().add(dir).distance_squared(self.lastConnect) < ct.get_position().distance_squared(self.lastConnect)):
						if(ct.can_move(dir)):
							ct.move(dir)
						return
				dir = dir.rotate_right()
		else:
			print("RIGHTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_left()
			for i in range(8):
				if(not self.canMoveDirWithConveyor(ct, ct.get_position().add(dir), dir) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [None] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					if(not self.canMove(ct, ct.get_position().add(dir))):
						continue
					self.tryDirWithConveyor(ct, dir)
					if(ct.get_position().add(dir).distance_squared(self.lastConnect) < ct.get_position().distance_squared(self.lastConnect)):
						if(ct.can_move(dir)):
							ct.move(dir)
				dir = dir.rotate_left()
		if(ct.get_action_cooldown() == 0):
			return "STUCK"