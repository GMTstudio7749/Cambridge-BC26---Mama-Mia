import random
from cambc import Controller, Direction, EntityType, Environment, Position

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
		self.lastBridgePos = None
		self.lastMovedLocation = None
		self.currentBridge = []
		self.bridgeConnection = []
		self.lastOrigin = None

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

		self.bridgeConnection =  [[0 for _ in range(ct.get_map_height())] for _ in range(ct.get_map_width())]
		for pos in ct.get_nearby_tiles():
			if(not self.onTheMap(ct, pos)):
				continue
			buildingId = ct.get_tile_building_id(pos)
			if(buildingId is None or ct.get_team(buildingId) != ct.get_team()): continue
			if(ct.get_entity_type(buildingId) != EntityType.BRIDGE): continue
			targetPos = ct.get_bridge_target(buildingId)
			self.bridgeConnection[targetPos.x][targetPos.y] += 1

	def canMove(self, ct, loc):

		if(not self.onTheMap(ct, loc)): return False
		return self.mapInfos[loc.x][loc.y] == EntityType.CORE or self.mapInfos[loc.x][loc.y] == EntityType.ROAD or self.mapInfos[loc.x][loc.y] == Environment.EMPTY  or self.mapInfos[loc.x][loc.y] == EntityType.CONVEYOR or self.mapInfos[loc.x][loc.y] == EntityType.BRIDGE

	def canMoveBridge(self, ct, loc):
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

	def tileScore(self, ct, loc, ignoreEmpty):
		return self.tileScoreBool(ct, loc, ignoreEmpty, False)

	def tileScoreBool(self, ct, loc, ignoreEmpty, checkAllyBehind):
		if(not self.onTheMap(ct, loc)):
			return -99999
		emptyPenalty = 0 if ignoreEmpty else 3
		score = 0
		info = self.mapInfos[loc.x][loc.y]
		if(self.tooCloseToDanger(ct, loc)):
			score -= 20
		# if(mapData.enemyDefenseTowers.size != 0):
		# 	for enemyTower in mapData.enemyDefenseTowers.getArray():
		# 		if(enemyTower.location.distance_squared_to(loc) <= enemyTower.type.action_radius_squared):
		# 			score -= 10000
		# 			break

		if(info == EntityType.CORE or info == EntityType.CONVEYOR  or info == EntityType.ROAD):
			score -= self.getAdjacentAllies(ct, loc)
			return score
		# allyBehind = False
		# if(checkAllyBehind):
		# 	dirToTile  = get_location().direction_to(loc)
		# 	loc1 = loc.add(dirToTile)
		# 	loc2 = loc.add(dirToTile.rotate_left())
		# 	loc3 = loc.add(dirToTile.rotate_right())

		# 	allyBehind = (on_the_map(loc1) and mapData.getMapInfo(loc1).get_paint().is_ally() or
		# 		(on_the_map(loc2) and mapData.getMapInfo(loc2).get_paint().is_ally()) or
		# 		(on_the_map(loc3) and mapData.getMapInfo(loc3).get_paint().is_ally()))
		if(info == Environment.EMPTY):
			score -= 0
		if(info == Environment.ORE_AXIONITE or info == Environment.ORE_TITANIUM):
			score -= 2
			# if(not allyBehind): score -= 2
		# allyBehind = False
		return score


	def tileScoreBridge(self, ct, loc, target, ignoreEmpty):
		return self.tileScoreBridgeBool(ct, loc, target, ignoreEmpty, False)

	def tileScoreBridgeBool(self, ct, loc, target, ignoreEmpty, checkAllyBehind):
		if(not self.onTheMap(ct, loc)):
			return -99999
		emptyPenalty = 0 if ignoreEmpty else 3
		score = 0
		info = self.mapInfos[loc.x][loc.y]
		if(self.tooCloseToDanger(ct, loc)):
			score -= 20
		# if(mapData.enemyDefenseTowers.size != 0):
		# 	for enemyTower in mapData.enemyDefenseTowers.getArray():
		# 		if(enemyTower.location.distance_squared_to(loc) <= enemyTower.type.action_radius_squared):
		# 			score -= 10000
		# 			break
		if(ct.get_team(ct.get_tile_building_id(loc)) != None and ct.get_team(ct.get_tile_building_id(loc))  != ct.get_team()):
			score -= 10
		else:
			if(info == EntityType.BRIDGE):
				if(self.bridgeConnection[loc.x][loc.y] < 4):
					score += 8
				else:
					score -= 4

				if(self.lastBridgePos == loc):
					score -= 40
			if(info == EntityType.ROAD):
				score += 4
		if(info == EntityType.CORE or info == EntityType.CONVEYOR  or info == EntityType.ROAD) and ct.get_team(ct.get_tile_building_id(loc)) == ct.get_team():
			score -= self.getAdjacentAllies(ct, loc)
			return score
		# allyBehind = False
		# if(checkAllyBehind):
		# 	dirToTile  = get_location().direction_to(loc)
		# 	loc1 = loc.add(dirToTile)
		# 	loc2 = loc.add(dirToTile.rotate_left())
		# 	loc3 = loc.add(dirToTile.rotate_right())

		# 	allyBehind = (on_the_map(loc1) and mapData.getMapInfo(loc1).get_paint().is_ally() or
		# 		(on_the_map(loc2) and mapData.getMapInfo(loc2).get_paint().is_ally()) or
		# 		(on_the_map(loc3) and mapData.getMapInfo(loc3).get_paint().is_ally()))


		# if(info == Environment.EMPTY):
			# score -= 3

		if(info == Environment.WALL):
			score -= 50


		if(info == Environment.ORE_AXIONITE or info == Environment.ORE_TITANIUM):
			score -= 2
			# if(not allyBehind): score -= 2
		# allyBehind = False
		return score

	def toCardinal(self, dir, prefer_right=True):
		if dir in (
			Direction.NORTH,
			Direction.EAST,
			Direction.SOUTH,
			Direction.WEST
		):
			return dir

		return dir.rotate_right() if prefer_right else dir.rotate_left()

	def calcBestDirBridge(self, ct, currentLoc, target, lastLoc):
		dirToTarget = currentLoc.direction_to(target)
		bestDir = None
		bestScore = -9999


		pos1 = currentLoc.add(dirToTarget)
		pos2 = currentLoc.add(dirToTarget.rotate_left())
		pos3 = currentLoc.add(dirToTarget.rotate_right())
		dist1 = ct.get_position().distance_squared(pos1)
		dist2 = ct.get_position().distance_squared(pos2)
		dist3 = ct.get_position().distance_squared(pos3)
		score1 = self.tileScoreBridge(ct, pos1, target, False)
		score2 = self.tileScoreBridge(ct, pos2, target, False)
		score3 = self.tileScoreBridge(ct, pos3, target, False)

		# mn = min([dist1, dist2, dist3])
		# if(mn == dist1):
		# 	score1 += 2
		# if(mn == dist2):
		# 	score2 += 2
		# if(mn == dist3):
		# 	score3 += 2
		desire = currentLoc.direction_to(target)
		if(dirToTarget != desire):
			score1 += 1
		if(dirToTarget.rotate_left() != desire):
			score2 += 1
		if(dirToTarget.rotate_right() != desire):
			score3 += 1


		# if(self.dir_order.index(dirToTarget) % 2 == 0 and ct.get_position().distance_squared(loc) > 50):
			# if(ct.get_current_round()%4 < 2):
				# score2 += 1
		# 	else:
		# 		score3 += 1


		if(self.canMoveBridge(ct, currentLoc.add(dirToTarget)) and score1 > bestScore and not currentLoc.add(dirToTarget) == lastLoc):
			bestDir = dirToTarget
			bestScore = score1
		if(self.canMoveBridge(ct, currentLoc.add(dirToTarget.rotate_left())) and score2 > bestScore and not currentLoc.add(dirToTarget.rotate_left()) == lastLoc):
			bestDir = dirToTarget.rotate_left()
			bestScore = score2
		if(self.canMoveBridge(ct, currentLoc.add(dirToTarget.rotate_right())) and score3 > bestScore and not currentLoc.add(dirToTarget.rotate_right()) == lastLoc):
			bestDir = dirToTarget.rotate_right()
			bestScore = score3
		return [bestDir, bestScore, dirToTarget]

	def MOVE_to_target_conveyor(self, ct, loc: Position):
		# THIS HERE THIS IS IMPORTANT
		# EXPLORE USING CONVEYOR + BRIDGE only, no road
		ct.draw_indicator_line(ct.get_position(), loc, 255, 0, 0)

		if(ct.get_move_cooldown() != 0 or ct.get_action_cooldown() != 0): return

		self.lastLocation = self.currentLocation
		self.currentLocation = ct.get_position()

		if(self.lastTargetLocation == None or self.lastTargetLocation != loc):
			self.lastBridgePos = loc

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
			ignoreEmpty = ct.get_entity_type() == EntityType.BUILDER_BOT
			score1 = self.tileScore(ct, ct.get_position().add(dirToTarget), ignoreEmpty)
			score2 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_left()), ignoreEmpty)
			score3 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_right()), ignoreEmpty)


			if(dirToTarget == self.toCardinal(dirToTarget)):
				score1 += 1
			if(dirToTarget.rotate_left() == self.toCardinal(dirToTarget.rotate_left())):
				score2 += 1
			if(dirToTarget.rotate_right() == self.toCardinal(dirToTarget.rotate_right())):
				score3 += 1
			# if(self.dir_order.index(dirToTarget) % 2 == 0 and ct.get_position().distance_squared(loc) > 50):
			# 	if(ct.get_current_round()%4 < 2):
			# 		score2 += 1
			# 	else:
			# 		score3 += 1
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
				if(self.toCardinal(bestDir) == bestDir):
					if(ct.can_build_conveyor(ct.get_position().add(bestDir), self.toCardinal(bestDir).opposite())):
						ct.build_conveyor(ct.get_position().add(bestDir),  self.toCardinal(bestDir).opposite())
				else:
					if(ct.can_build_bridge(ct.get_position().add(bestDir), ct.get_position().add(bestDir.opposite()))):
						ct.build_bridge(ct.get_position().add(bestDir), ct.get_position())
				if(ct.can_move(bestDir)):
					ct.move(bestDir)
					return
			self.bugStack[self.bugStackIndex] = (dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right())
			self.bugStackIndex += 1;
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
					# if(ct.can_build_road(ct.get_position().add(dir))):
					# 	ct.build_road(ct.get_position().add(dir))
					if(self.toCardinal(dir) == dir):
						if(ct.can_build_conveyor(ct.get_position().add(dir), self.toCardinal(dir).opposite())):
							ct.build_conveyor(ct.get_position().add(dir),  self.toCardinal(dir).opposite())
					else:
						if(ct.can_build_bridge(ct.get_position().add(dir), ct.get_position().add(dir.opposite()))):
							ct.build_bridge(ct.get_position().add(dir), ct.get_position())

					# if(ct.can_build_conveyor(ct.get_position().add(dir), self.toCardinal(dir).opposite())):
						# ct.build_conveyor(ct.get_position().add(dir),  self.toCardinal(dir).opposite())

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
					# if(ct.can_build_road(ct.get_position().add(dir))):
						# ct.build_road(ct.get_position().add(dir))
					if(self.toCardinal(dir) == dir):
						if(ct.can_build_conveyor(ct.get_position().add(dir), self.toCardinal(dir).opposite())):
							ct.build_conveyor(ct.get_position().add(dir),  self.toCardinal(dir).opposite())
					else:
						if(ct.can_build_bridge(ct.get_position().add(dir), ct.get_position().add(dir.opposite()))):
							ct.build_bridge(ct.get_position().add(dir), ct.get_position())
							
					if(ct.can_move(dir)):
						ct.move(dir)
						return
				dir = dir.rotate_left()


	def MOVE_to_target(self, ct, loc: Position, zigzag: bool):
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
			ignoreEmpty = ct.get_entity_type() == EntityType.BUILDER_BOT
			score1 = self.tileScore(ct, ct.get_position().add(dirToTarget), ignoreEmpty)
			score2 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_left()), ignoreEmpty)
			score3 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_right()), ignoreEmpty)

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
			self.bugStack[self.bugStackIndex] = (dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right())
			self.bugStackIndex += 1;
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


	def MOVE_to_target_with_bridge(self, ct,origin: Position, loc: Position):
		# MOVE to a pos with bridges connected



		ct.draw_indicator_line(ct.get_position(), loc, 255, 0, 0)

		ti = ct.get_global_resources()[0]
		if(ct.get_bridge_cost()[0] > ti):
			return

		self.lastLocation = self.currentLocation

		self.currentLocation = ct.get_position()
		if(self.lastBridgePos == None or (self.lastTargetLocation is not None and self.lastTargetLocation != loc) or (self.lastOrigin is not None and self.lastOrigin != origin)):
			self.lastBridgePos = origin
			self.lastOrigin = origin
		if(self.lastTargetLocation == None or self.lastTargetLocation.distance_squared(loc) > 8 or self.bugStackIndex >= self.MAX_STACK_SIZE-10):
			self.bugStack = [None] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0
			self.lastTargetLocation = loc
			self.lastLocation = ct.get_position()
			self.currentBridge = []
		if(self.lastBridgePos is not None):
			self.currentBridge.append(self.lastBridgePos)

		if(self.lastTargetLocation != None and self.lastTargetLocation.distance_squared(loc) <= 8):
			self.lastTargetLocation = loc

		while (
			self.bugStackIndex != 0 and
			(
				(
					self.canMoveBridge(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 1])) and
					not self.tooCloseToDanger(ct, ct.get_position().add(self.bugStack[self.bugStackIndex - 1]))
				)
				or
				(
					self.bugStackIndex > 1 and
					self.canMoveBridge(ct, ct.get_position().add( self.bugStack[self.bugStackIndex - 2])) and
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
			bestDir, bestScore, dirToTarget = self.calcBestDirBridge(ct, ct.get_position(), loc, self.lastLocation)

			if(bestDir is not None and bestScore > -20):
				if(ct.can_build_road(ct.get_position().add(bestDir))):
					ct.build_road(ct.get_position().add(bestDir))
					return
				currentLoc = ct.get_position()


				bestNextLoc = ct.get_position().add(bestDir)
				bestNextDir, bestNextScore, nextDirToTarget = self.calcBestDirBridge( ct, ct.get_position().add(bestDir), loc, ct.get_position())



				bestNextNextLoc = None
				bestNextNextDir, bestNextNextScore, nextNextLoc = [None, None, None]

				if(bestNextDir is not None):
					bestNextNextLoc = ct.get_position().add(bestDir).add(bestNextDir)
					bestNextNextDir, bestNextNextScore, nextNextLoc =  self.calcBestDirBridge( ct, ct.get_position().add(bestDir).add(bestNextDir), loc, ct.get_position().add(bestDir))
				nextPos =  ct.get_position().add(bestDir)
				nextBuilderBotId = ct.get_tile_builder_bot_id(nextPos)

				if(nextBuilderBotId is not None ):
					return


				if ct.get_position().distance_squared(loc) > 2 and ct.is_in_vision(self.lastBridgePos) and (( self.lastLocation == self.lastBridgePos) or self.currentLocation == self.lastBridgePos or bestNextLoc.distance_squared(self.lastBridgePos) > 2) :
					print("THIS DOES RUn")

					builded = False

					bid1 = ct.get_tile_building_id(self.lastBridgePos)
					if(bid1 is not None and ct.get_entity_type(bid1) == EntityType.BRIDGE):
						self.lastBridgePos = ct.get_bridge_target(bid1)	
						if(ct.can_move(ct.get_position().direction_to(self.lastBridgePos))):
							ct.move(ct.get_position().direction_to(self.lastBridgePos))
						return

					if(bid1 is not None and ct.get_entity_type(bid1) == EntityType.ROAD and ct.can_destroy(self.lastBridgePos)):
						ct.destroy(self.lastBridgePos)



					if(not builded and bestNextNextDir is not None and bestNextNextScore > -20):
						if(self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos)):

							nextNextNextPos =  ct.get_position().add(bestDir).add(bestNextDir).add(bestNextNextDir)
							nextNextNextBuildingId = ct.get_tile_building_id(nextNextNextPos)

							if((nextNextNextBuildingId is not None and ct.get_team(nextNextNextBuildingId) == ct.get_team() and ct.get_entity_type(nextNextNextBuildingId) == EntityType.BRIDGE ) and ct.can_build_bridge(self.lastBridgePos, nextNextNextPos) and nextNextNextPos not in self.currentBridge):
								print("THIS IS IMPORTANT")
								print("THIS RUn 1 1")

								ct.build_bridge(self.lastBridgePos, nextNextNextPos)
								self.lastBridgePos = nextNextNextPos
								builded = True			

					if(not builded and bestNextLoc is not None and bestNextScore > -20):
						if(self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos) ):
							nextNextPos =  ct.get_position().add(bestDir).add(bestNextDir)
							nextNextBuildingId = ct.get_tile_building_id(nextNextPos)

							if((nextNextBuildingId is not None and  ct.get_team(nextNextBuildingId) == ct.get_team() and ct.get_entity_type(nextNextBuildingId) == EntityType.BRIDGE ) and ct.can_build_bridge(self.lastBridgePos, nextNextPos)  and nextNextPos not in self.currentBridge):
								print("THIS RUn 2 1")
								ct.build_bridge(self.lastBridgePos, nextNextPos)
								self.lastBridgePos = nextNextPos
								builded = True



					if(not builded and self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos)):
						nextPos =  ct.get_position().add(bestDir)
						nextBuildingId = ct.get_tile_building_id(nextPos)

						if(( nextBuildingId is not None and ct.get_team(nextBuildingId) == ct.get_team() and ct.get_entity_type(nextBuildingId) == EntityType.BRIDGE) and ct.can_build_bridge(self.lastBridgePos, nextPos)  and nextPos not in self.currentBridge):
							print("THIS RUn 3 1")
							ct.build_bridge(self.lastBridgePos, nextPos)
							self.lastBridgePos = nextPos
							builded = True




					if(not builded and bestNextNextDir is not None and bestNextNextScore > -20):
						ct.draw_indicator_line(ct.get_position().add(bestDir).add(bestNextDir).add(bestNextNextDir), self.lastBridgePos, 0, 255, 0)
						if(self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos)):
							nextNextNextPos =  ct.get_position().add(bestDir).add(bestNextDir).add(bestNextNextDir)
							nextNextNextBuildingId = ct.get_tile_building_id(nextNextNextPos)

							if((nextNextNextBuildingId is None or ct.get_team(nextNextNextBuildingId) == ct.get_team()) and ct.can_build_bridge(self.lastBridgePos, nextNextNextPos)  and nextNextNextPos not in self.currentBridge):
								print("THIS IS IMPORTANT")
								print("THIS RUn 1")

								ct.build_bridge(self.lastBridgePos, nextNextNextPos)
								self.lastBridgePos = nextNextNextPos
								builded = True

					if(not builded and bestNextLoc is not None and bestNextScore > -20):

						if(self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos) ):
							nextNextPos =  ct.get_position().add(bestDir).add(bestNextDir)
							nextNextBuildingId = ct.get_tile_building_id(nextNextPos)

							if((nextNextBuildingId is None  or ct.get_team(nextNextBuildingId) == ct.get_team()) and ct.can_build_bridge(self.lastBridgePos, nextNextPos)  and nextNextPos not in self.currentBridge):
								print("THIS RUn 2")
								ct.build_bridge(self.lastBridgePos, nextNextPos)
								self.lastBridgePos = nextNextPos
								builded = True

					if(not builded and currentLoc is not None):

						if(self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos)):

							nextPos =  ct.get_position().add(bestDir)
							nextBuildingId = ct.get_tile_building_id(nextPos)

							if((nextBuildingId is None or ct.get_team(nextBuildingId) == ct.get_team()) and ct.can_build_bridge(self.lastBridgePos, nextPos) and  nextPos not in self.currentBridge):
								print("THIS RUn 3")
								ct.build_bridge(self.lastBridgePos, nextPos)
								self.lastBridgePos = nextPos
								builded = True

					if(builded and ct.can_move(bestDir)):
						ct.move(bestDir)
					if(builded or ct.get_action_cooldown() == 1):
						return

				else:
					if(ct.can_move(bestDir)):
						ct.move(bestDir)
						return

			self.bugStack[self.bugStackIndex] = (dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right())
			self.bugStackIndex += 1;
		if(self.RIGHT):
			print("RIGHTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_right()
			for i in range(8):
				if(not self.canMoveBridge(ct, ct.get_position().add(dir)) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [None] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					if(not self.canMoveBridge(ct, ct.get_position().add(dir))):
						continue

					if(ct.can_build_road(ct.get_position().add(dir))):
						ct.build_road(ct.get_position().add(dir))
						if(ct.get_position().distance_squared(self.lastBridgePos) < 10):
							return

					if(ct.can_move(dir) and self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos) and self.lastBridgePos.distance_squared(ct.get_position().add(dir).add(dir)) >= 5):
						ct.draw_indicator_line(self.lastBridgePos, ct.get_position().add(dir).add(dir), 255, 0, 255)
						bid1 = ct.get_tile_building_id(self.lastBridgePos)
						bid2 = ct.get_tile_building_id(ct.get_position().add(dir))

						if(bid1 is not None and ct.get_entity_type(bid1) == EntityType.BRIDGE):
							self.lastBridgePos = ct.get_bridge_target(bid1)
						if(bid1 is not None and ct.get_entity_type(bid1) == EntityType.ROAD and ct.can_destroy(self.lastBridgePos)):
							ct.destroy(self.lastBridgePos)
						nextNextPos =  ct.get_position().add(dir).add(dir)
						if(self.onTheMap(ct, nextNextPos)):
							nextNextBuildingId = ct.get_tile_building_id(nextNextPos)
						else:
							nextBuildingId = None
						nextPos = ct.get_position().add(dir)
						nextBuildingId = ct.get_tile_building_id(nextPos)
						builded = False

						if(not builded and self.onTheMap(ct, nextPos) and (nextBuildingId is not None and  ct.get_team(nextBuildingId) == ct.get_team() and ct.get_entity_type(nextBuildingId) == EntityType.BRIDGE ) and  self.canMove(ct, nextPos) and ct.can_build_conveyor(ct.get_position(), dir))  and nextPos not in self.currentBridge:
							ct.build_conveyor(self.lastBridgePos, dir)
							self.lastBridgePos =  nextPos
							builded = True
						if(not builded and self.onTheMap(ct, nextNextPos) and (nextNextBuildingId is not None and  ct.get_team(nextNextBuildingId) == ct.get_team() and ct.get_entity_type(nextNextBuildingId) == EntityType.BRIDGE ) and  self.canMove(ct, nextNextPos) and ct.can_build_bridge(self.lastBridgePos, nextNextPos) and  nextNextPos not in self.currentBridge ):
							ct.build_bridge(self.lastBridgePos, nextNextPos)
							self.lastBridgePos =  nextNextPos
							builded = True
						if(not builded and self.onTheMap(ct, nextPos) and (nextBuildingId is not None and  ct.get_team(nextBuildingId) == ct.get_team() and ct.get_entity_type(nextBuildingId) == EntityType.BRIDGE ) and  self.canMove(ct, nextPos) and ct.can_build_bridge(self.lastBridgePos, nextPos))  and nextPos not in self.currentBridge:
							ct.build_bridge(self.lastBridgePos, nextPos)
							self.lastBridgePos =  nextPos
							builded = True
						if(not builded and self.onTheMap(ct, nextNextPos) and (nextNextBuildingId == None or  ct.get_team(nextNextBuildingId) == ct.get_team() ) and  self.canMove(ct, nextNextPos) and ct.can_build_bridge(self.lastBridgePos, nextNextPos) and nextNextPos not in self.currentBridge):
							ct.build_bridge(self.lastBridgePos, nextNextPos)
							self.lastBridgePos =  nextNextPos
							builded = True
						if(not builded and (nextBuildingId == None or  ct.get_team(nextBuildingId) == ct.get_team() ) and ct.can_build_bridge(self.lastBridgePos, nextPos)) and nextPos not in self.currentBridge:
							ct.build_bridge(self.lastBridgePos, nextPos)
							self.lastBridgePos =  nextPos
							builded = True

						if(builded and ct.can_move(dir)):
							print("THIS MOVED")
							ct.move(dir)
						if(builded or ct.get_action_cooldown() != 0):
							return

					if(ct.can_move(dir)):
						print("THIS MOVED")
						ct.move(dir)
						return
				dir = dir.rotate_right()
		else:
			print("LEFTING")

			dir = self.bugStack[self.bugStackIndex-1].rotate_left()
			for i in range(8):
				if(not self.canMoveBridge(ct, ct.get_position().add(dir)) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [None] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					if(not self.canMoveBridge(ct, ct.get_position().add(dir))):
						continue

					if(ct.can_build_road(ct.get_position().add(dir))):
						ct.build_road(ct.get_position().add(dir))
						if(ct.get_position().distance_squared(self.lastBridgePos) < 10):
							return

					if(ct.can_move(dir) and self.lastBridgePos is not None and ct.is_in_vision(self.lastBridgePos) and self.lastBridgePos.distance_squared(ct.get_position().add(dir).add(dir)) >= 5):
						ct.draw_indicator_line(self.lastBridgePos, ct.get_position().add(dir).add(dir), 255, 0, 255)
						bid1 = ct.get_tile_building_id(self.lastBridgePos)
						bid2 = ct.get_tile_building_id(ct.get_position().add(dir))

						if(bid1 is not None and ct.get_entity_type(bid1) == EntityType.BRIDGE):
							self.lastBridgePos = ct.get_bridge_target(bid1)
						if(bid1 is not None and ct.get_entity_type(bid1) == EntityType.ROAD and ct.can_destroy(self.lastBridgePos)):
							ct.destroy(self.lastBridgePos)
						nextNextPos =  ct.get_position().add(dir).add(dir)
						if(self.onTheMap(ct, nextNextPos)):
							nextNextBuildingId = ct.get_tile_building_id(nextNextPos)
						else:
							nextBuildingId = None
						nextPos = ct.get_position().add(dir)
						nextBuildingId = ct.get_tile_building_id(nextPos)
						builded = False


						if(not builded and self.onTheMap(ct, nextPos) and (nextBuildingId is not None and  ct.get_team(nextBuildingId) == ct.get_team() and ct.get_entity_type(nextBuildingId) == EntityType.BRIDGE ) and  self.canMove(ct, nextPos)  and ct.can_build_conveyor(ct.get_position(), dir))  and nextPos not in self.currentBridge:
							ct.build_conveyor(self.lastBridgePos, dir)
							self.lastBridgePos =  nextPos
							builded = True
						if(not builded and self.onTheMap(ct, nextNextPos) and (nextNextBuildingId is not None and  ct.get_team(nextNextBuildingId) == ct.get_team() and ct.get_entity_type(nextNextBuildingId) == EntityType.BRIDGE ) and  self.canMove(ct, nextNextPos) and ct.can_build_bridge(self.lastBridgePos, nextNextPos) and  nextNextPos not in self.currentBridge ):
							ct.build_bridge(self.lastBridgePos, nextNextPos)
							self.lastBridgePos =  nextNextPos
							builded = True
						if(not builded and self.onTheMap(ct, nextPos) and (nextBuildingId is not None and  ct.get_team(nextBuildingId) == ct.get_team() and ct.get_entity_type(nextBuildingId) == EntityType.BRIDGE ) and  self.canMove(ct, nextPos) and ct.can_build_bridge(self.lastBridgePos, nextPos)) and nextPos not in self.currentBridge:
							ct.build_bridge(self.lastBridgePos, nextPos)
							self.lastBridgePos =  nextPos
							builded = True
						if(not builded and self.onTheMap(ct, nextNextPos) and (nextNextBuildingId == None or  ct.get_team(nextNextBuildingId) == ct.get_team() ) and  self.canMove(ct, nextNextPos) and ct.can_build_bridge(self.lastBridgePos, nextNextPos) and nextNextPos not in self.currentBridge):
							ct.build_bridge(self.lastBridgePos, nextNextPos)
							self.lastBridgePos =  nextNextPos
							builded = True
						if(not builded and (nextBuildingId == None or  ct.get_team(nextBuildingId) == ct.get_team() ) and ct.can_build_bridge(self.lastBridgePos, nextPos)) and nextPos not in self.currentBridge:
							ct.build_bridge(self.lastBridgePos, nextPos)
							self.lastBridgePos =  nextPos
							builded = True

						if(builded and ct.can_move(dir)):
							print("THIS MOVED")
							ct.move(dir)
						if(builded or ct.get_action_cooldown() != 0):
							return

					if(ct.can_move(dir)):
						print("THIS MOVED")
						ct.move(dir)
						return
				dir = dir.rotate_left()
