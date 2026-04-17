import random
from cambc import Direction, EntityType, Environment, Position
from utils import *
		
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
		self.bugStack: list[Direction] = [] * self.MAX_STACK_SIZE
		self.stuckTurns = 0
		self.jiggleRight = False
		self.dir_order = [Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST, Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST, Direction.CENTRE]
		self.RIGHT = random.randint(0, 1)

		self.originConnect = None
		self.lastConnect: Position = Position(-1, -1)

		self.currentConnections = []

		self.dangerous_tiles = set()
		self.lastSafeFuzzyLoc = None

		self.prevPositions = []
		self.prevPosIndex = 0


	def SETUP(self, ct):
		# run this in turn 1 pls
		self.mapInfos =  [[None for _ in range(ct.get_map_height())] for _ in range(ct.get_map_width())]

	def SENSE_nearby(self, ct):
		#run this first every turn for the bugnav to see the environment
		self.dangerous_tiles = set()

		for pos in ct.get_nearby_tiles():
			if(not self.onTheMap(ct, pos)):
				continue
			if( ct.get_tile_env(pos) == Environment.WALL):
				self.mapInfos[pos.x][pos.y] = Environment.WALL
			elif(not ct.is_tile_empty(pos)):
				bid = ct.get_tile_building_id(pos)
				bteam = ct.get_team(bid)
				btype = ct.get_entity_type(bid)
				if(btype == EntityType.CORE and bteam != ct.get_team()):
					self.mapInfos[pos.x][pos.y] = "ECORE"
				elif(btype == EntityType.BARRIER and bteam != ct.get_team()):
					self.mapInfos[pos.x][pos.y] = "EBarrier"
				else:
					self.mapInfos[pos.x][pos.y] = ct.get_entity_type(bid)
				if(btype in TURRET_TYPE and bteam != ct.get_team()):
					if(btype == EntityType.LAUNCHER):
						for dir in Dirs :
							i = pos.add(dir)
							self.dangerous_tiles.add(i)
					else:
						for i in ct.get_attackable_tiles_from(pos, ct.get_direction(bid), btype):
							self.dangerous_tiles.add(i)

			else:
				self.mapInfos[pos.x][pos.y] = Environment.EMPTY
				if(ct.get_tile_env(pos) == Environment.ORE_TITANIUM ):
					self.mapInfos[pos.x][pos.y] = Environment.ORE_TITANIUM 
				if(ct.get_tile_env(pos) == Environment.ORE_AXIONITE):
					self.mapInfos[pos.x][pos.y] = Environment.ORE_AXIONITE
	

	def canMove(self, ct, loc):

		if(not self.onTheMap(ct, loc)): return False
		if(ct.is_in_vision(loc)):
			bid =  ct.get_tile_builder_bot_id(loc)
			if(bid != None and bid != ct.get_id()):
				return False
		return self.mapInfos[loc.x][loc.y] in ORE_ENV or  self.mapInfos[loc.x][loc.y] == EntityType.MARKER or self.mapInfos[loc.x][loc.y] == EntityType.CORE or self.mapInfos[loc.x][loc.y] == EntityType.ROAD or self.mapInfos[loc.x][loc.y] == Environment.EMPTY  or self.mapInfos[loc.x][loc.y] == EntityType.CONVEYOR or self.mapInfos[loc.x][loc.y] == EntityType.BRIDGE


	def tooCloseToDanger(self, ct, loc):
		out = loc in self.dangerous_tiles

		return out

	def onTheMap(self, ct, loc):
		return (0 <= loc.x and loc.x < ct.get_map_width()) and (0 <= loc.y and loc.y < ct.get_map_height())

	def reachableFrom(self, ct, loc, target):
		if(not self.onTheMap(ct, target)):
			return False
		targetInfo = self.mapInfos[target.x][target.y]

		if(targetInfo != None and (targetInfo in TURRET_TYPE or targetInfo == Environment.WALL or targetInfo == "EBarrier" or targetInfo == EntityType.BARRIER or targetInfo == EntityType.HARVESTER or targetInfo == "ECORE")):
			return False
		checkLoc = loc
		while(not checkLoc == target):
			# ct.draw_indicator_line(loc, target, 255, 255, 255)
			info = self.mapInfos[checkLoc.x][checkLoc.y]
			if(not self.onTheMap(ct, checkLoc) or (info != None and (self.mapInfos[checkLoc.x][checkLoc.y] in TURRET_TYPE or info == EntityType.HARVESTER or info == "ECORE" or  info == Environment.WALL or info == "EBarrier" or info == EntityType.BARRIER))):
				return False
			checkLoc = checkLoc.add(checkLoc.direction_to(target))
		return True

	def getAdjacentAllies(self, ct, loc):
		return 0

	def tileScore(self, ct, loc, target, allyScore, enemyScore, emptyScore, dangerousScore):
		return self.tileScoreBool(ct, loc, target, allyScore, enemyScore, emptyScore, dangerousScore,False)

	def tileScoreBool(self, ct, loc, target, allyScore, enemyScore, emptyScore, dangerousScore ,checkAllyBehind):
		if(not self.onTheMap(ct, loc)):
			return -99999
		score = 0
		info = self.mapInfos[loc.x][loc.y]
		print(dangerousScore)
		if(self.tooCloseToDanger(ct, loc)):
			print("DANGER")
			if(loc.distance_squared(target) > 2):
				score += dangerousScore
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
				if(info == EntityType.CORE):
					return -99999

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
		if(info == EntityType.BARRIER):
			score -= 10
		if(info == Environment.EMPTY):
			score += emptyScore
		if(info == Environment.ORE_AXIONITE or info == Environment.ORE_TITANIUM):
			score += emptyScore
			# score += emptyScore
			# if(not allyBehind): score -= 2
		# allyBehind = False
		return score

	def tileScoreConveyor(self, ct, currentLoc, loc, target, allyScore, enemyScore, emptyScore):
		return self.tileScoreConveyorBool(ct, currentLoc,loc, target, allyScore, enemyScore, emptyScore, False)

	def tileScoreConveyorBool(self, ct, currentLoc, loc, target, allyScore, enemyScore, emptyScore, checkAllyBehind):
		if(not self.onTheMap(ct, loc)):
			return -99999
		if(not ct.is_in_vision(loc)):
			# print(ct.get_current_round(), ct.get_id())
			return -99999
		if(currentLoc.distance_squared(loc) > 9):
			return -99999
		
		
		score = 0

		if(loc.distance_squared(target) <= 2):
			score += 3
		info = self.mapInfos[loc.x][loc.y]
		bid = ct.get_tile_building_id(loc)
		bteam = ct.get_team(bid)
		if(self.tooCloseToDanger(ct, loc)):
			score -= 2


		if(info == EntityType.CONVEYOR or info == EntityType.BRIDGE):
			if(ct.get_team(bid)  == ct.get_team()):
				score += allyScore
			else:
				score += enemyScore
			if(info == EntityType.CONVEYOR):
				conveyorDir = ct.get_direction(bid)
				conveyorTarget = loc.add(conveyorDir)
				if(currentLoc == conveyorTarget):
					return -50
			return score
		if(bteam != ct.get_team()):
			score += enemyScore
			return score
		if(info == EntityType.ROAD or info == EntityType.CORE):
			score += emptyScore
			return score


		if(info == EntityType.BARRIER or info == Environment.WALL):
			return -99999

		if(info == Environment.EMPTY):
			score += emptyScore
		if(info == Environment.ORE_AXIONITE or info == Environment.ORE_TITANIUM):
			score -= 50
			# score += emptyScore
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

	def safeFuzzyMove(self, ct, dir):
		for d in self.fuzzyDirs(dir):
			if(ct.can_move(d) and not self.tooCloseToDanger(ct, ct.get_position().add(d))):
				ct.move(d)
				return
		self.fuzzyMove(ct, dir)



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


	def MOVE_to_target(self, ct, loc: Position, zigzag: bool, allyScore=0, enemyScore=0, emptyScore=-2, dangerousScore=-30):
		# THIS HERE, EXPLORE USING ROAD ONLY, NO CONVEYOR BUILD

		# ct.draw_indicator_line(ct.get_position(), loc, 255, 0, 0)

		if(not ct.get_move_cooldown() == 0): return

		self.lastLocation = self.currentLocation
		self.currentLocation = ct.get_position()


		if(self.lastTargetLocation == None or self.lastTargetLocation.distance_squared(loc) > 8 or self.bugStackIndex >= self.MAX_STACK_SIZE-10):
			self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
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
			# print("REACHED SMT")
			self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0

		if(self.bugStackIndex == 0):
			dirToTarget = ct.get_position().direction_to(loc)
			bestDir = None
			bestScore = -9999
			score1 = self.tileScore(ct, ct.get_position().add(dirToTarget), loc, allyScore, enemyScore, emptyScore, dangerousScore)
			score2 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_left()), loc, allyScore, enemyScore, emptyScore, dangerousScore)
			score3 = self.tileScore(ct, ct.get_position().add(dirToTarget.rotate_right()),  loc,allyScore, enemyScore, emptyScore, dangerousScore)



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
				print("CANMOVE")
				nextPos = ct.get_position().add(bestDir)

				bid = ct.get_tile_building_id(nextPos)
				bteam = ct.get_team(bid)
				btype = ct.get_entity_type(bid)

				if(btype == EntityType.MARKER):
					if(ct.can_destroy(nextPos)):
						ct.destroy(nextPos)

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
				# print("FUZZY MOVIGN")
				self.fuzzyMove(ct, dirToTarget.opposite())
				return
			self.bugStack[self.bugStackIndex] = dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right()
			self.bugStackIndex += 1

		if(self.RIGHT):
			print("RIGHTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_right()
			for i in range(8):
				if(not self.canMove(ct, ct.get_position().add(dir))  or self.tooCloseToDanger(ct, ct.get_position().add(dir))):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
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
			print("LEFTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_left()
			for _ in range(8):
				if(not self.canMove(ct, ct.get_position().add(dir)) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
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
		bestPos = None

		dir1 = dirToTarget
		dir2 = dirToTarget.rotate_left()
		dir3 = dirToTarget.rotate_right()
		pos1 = cur_pos.add(dir1)
		pos2 = cur_pos.add(dir2)
		pos3 = cur_pos.add(dir3)
		pos4 = cur_pos.add(dir1).add(dir1)
		pos5 = cur_pos.add(dir2).add(dir2)
		pos6 = cur_pos.add(dir3).add(dir3)
		pos7 = cur_pos.add(dir1).add(dir1).add(dir1)
		pos8 = cur_pos.add(dir2).add(dir2).add(dir2)
		pos9 = cur_pos.add(dir3).add(dir3).add(dir3)
		pos10 = cur_pos.add(dir1).add(dir2)
		pos11 = cur_pos.add(dir1).add(dir3)
		pos12 = cur_pos.add(dir2).add(dir1)
		pos13 = cur_pos.add(dir2).add(dir3)
		pos14 = cur_pos.add(dir3).add(dir1)
		pos15 = cur_pos.add(dir3).add(dir2)

		# ct.draw_indicator_line(cur_pos, pos1, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos2, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos3, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos4, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos5, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos6, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos7, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos8, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos9, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos10, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos11, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos12, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos13, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos14, 255, 255, 255)
		# ct.draw_indicator_line(cur_pos, pos15, 255, 255, 255)




		score1 = self.tileScoreConveyor(ct, cur_pos, pos1, loc,  allyScore, enemyScore, emptyScore)
		score2 = self.tileScoreConveyor(ct, cur_pos, pos2, loc,  allyScore, enemyScore, emptyScore)
		score3 = self.tileScoreConveyor(ct, cur_pos, pos3, loc,  allyScore, enemyScore, emptyScore)
		score4 = self.tileScoreConveyor(ct, cur_pos, pos4, loc,  allyScore, enemyScore, emptyScore)
		score5 = self.tileScoreConveyor(ct, cur_pos, pos5, loc, allyScore, enemyScore, emptyScore)
		score6 = self.tileScoreConveyor(ct, cur_pos, pos6, loc, allyScore, enemyScore, emptyScore)
		score7 = self.tileScoreConveyor(ct, cur_pos, pos7, loc, allyScore, enemyScore, emptyScore)
		score8 = self.tileScoreConveyor(ct, cur_pos, pos8, loc, allyScore, enemyScore, emptyScore)
		score9 = self.tileScoreConveyor(ct, cur_pos, pos9, loc, allyScore, enemyScore, emptyScore)
		score10 = self.tileScoreConveyor(ct, cur_pos, pos10, loc, allyScore, enemyScore, emptyScore)
		score11 = self.tileScoreConveyor(ct, cur_pos, pos11, loc,allyScore, enemyScore, emptyScore)
		score12 = self.tileScoreConveyor(ct, cur_pos, pos12, loc,allyScore, enemyScore, emptyScore)
		score13 = self.tileScoreConveyor(ct, cur_pos, pos13, loc,allyScore, enemyScore, emptyScore)
		score14 = self.tileScoreConveyor(ct, cur_pos, pos14, loc,allyScore, enemyScore, emptyScore)
		score15 = self.tileScoreConveyor(ct, cur_pos, pos15, loc,allyScore, enemyScore, emptyScore)


		if(dir1 == self.toCardinal(dir1)):
			score1 += 6
		else:

			score1 -= 3
		if(dir2 == self.toCardinal(dir2)):
			score2 += 6
		else:
			score2 -= 3
		if(dir3 == self.toCardinal(dir3)):
			score3 += 6
		else:
			score3 -= 3
		score4 -= 2
		score5 -= 2
		score6 -= 2
		score7 -= 1
		score8 -= 1
		score9 -= 1
		score10 -= 2
		score11 -= 2
		score12 -= 2
		score13 -= 2
		score14 -= 2
		score15 -= 2



		# print("SCORE: ", score1, score2, score3)
		# ct.draw_indicator_line(pos1, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos2, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos3, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos4, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos5, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos6, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos7, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos8, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos9, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos10, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos11, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos12, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos13, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos14, cur_pos, 255, 255, 255)
		# ct.draw_indicator_line(pos15, cur_pos, 255, 255, 255)




		if(self.canMove(ct, pos1) and score1 > bestScore and not pos1 == self.lastLocation):
			bestDir = dir1
			bestPos = pos1
			bestScore = score1
		if(self.canMove(ct, pos2) and score2 > bestScore and not pos2 == self.lastLocation):
			bestDir = dir2
			bestPos = pos2
			bestScore = score2
		if(self.canMove(ct, pos3) and score3 > bestScore and not pos3 == self.lastLocation):
			bestDir = dir3
			bestPos = pos3
			bestScore = score3
		if(self.canMove(ct, pos4) and score4 > bestScore and not pos4 == self.lastConnect):
			bestDir = dir1
			bestPos = pos4 
			bestScore = score4
		if(self.canMove(ct, pos5) and score5 > bestScore and not pos5 == self.lastConnect):
			bestDir = dir2
			bestPos = pos5 
			bestScore = score5
		if(self.canMove(ct, pos6) and score6 > bestScore and not pos6 == self.lastConnect):
			bestDir = dir3
			bestPos = pos6
			bestScore = score6
		if(self.canMove(ct, pos7) and score7 > bestScore and not pos7 == self.lastConnect):
			bestDir = dir1
			bestPos = pos7
			bestScore = score6
		if(self.canMove(ct, pos8) and score8 > bestScore and not pos8 == self.lastConnect):
			bestDir = dir2
			bestPos = pos8
			bestScore = score8
		if(self.canMove(ct, pos9) and score9 > bestScore and not pos9 == self.lastConnect):
			bestDir = dir3
			bestPos = pos9
			bestScore = score9
		if(self.canMove(ct, pos10) and score10 > bestScore and not pos10 == self.lastConnect):
			bestDir = dir1
			bestPos = pos10
			bestScore = score10
		if(self.canMove(ct, pos11) and score11 > bestScore and not pos11 == self.lastConnect):
			bestDir = dir1
			bestPos = pos11
			bestScore = score11
		if(self.canMove(ct, pos12) and score12 > bestScore and not pos12 == self.lastConnect):
			bestDir = dir2
			bestPos = pos12
			bestScore = score12
		if(self.canMove(ct, pos13) and score13 > bestScore and not pos13 == self.lastConnect):
			bestDir = dir2
			bestPos = pos13
			bestScore = score13
		if(self.canMove(ct, pos14) and score14 > bestScore and not pos14 == self.lastConnect):
			bestDir = dir3
			bestPos = pos14
			bestScore = score14
		if(self.canMove(ct, pos15) and score15 > bestScore and not pos15 == self.lastConnect):
			bestDir = dir3
			bestPos = pos15
			bestScore = score15
		
		return bestDir, bestPos, bestScore, dirToTarget

	def tryBuildConveyor(self, ct, pos, dir, save=True):
		bid = ct.get_tile_building_id(pos)
		btype = ct.get_entity_type(bid)
		bteam = ct.get_team(bid)

		nextPos = pos.add(dir)
		if(not self.onTheMap(ct, nextPos) or not ct.is_in_vision(nextPos)):
			return False
		nextBid = ct.get_tile_building_id(nextPos)
		nextBtype = ct.get_entity_type(nextBid)
		nextBteam = ct.get_team(nextBid)

		if(pos.add(dir) in self.currentConnections):
			return False



		if(nextBid is not None and nextBteam != ct.get_team()) or not self.canMove(ct, nextPos):
			return False

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
				# print("SO BAD")
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
			# ct.draw_indicator_line(self.lastLocation, self.currentConnections[-2], 100, 100, 150)
			# print(self.lastTargetLocation.direction_to(self.currentConnections[-2]))
			pass

		if(not self.onTheMap(ct, loc) or not ct.is_in_vision(loc)):
			return False

		nextBid = ct.get_tile_building_id(loc)
		nextBtype = ct.get_entity_type(nextBid)
		nextBteam = ct.get_team(nextBid)

		# ct.draw_indicator_line(loc, ct.get_position(), 255, 100, 255)
		if(not self.canMove(ct, loc)):
			return False

		if(nextBteam != ct.get_team()):
			return False
		x = loc.x
		y = loc.y
		if(self.mapInfos[x][y] == Environment.WALL or self.mapInfos[x][y] == Environment.ORE_AXIONITE or self.mapInfos[x][y] == Environment.ORE_TITANIUM):
			# print("THIS IS BAD")

			return False
		if(self.mapInfos[x][y] == Environment.EMPTY):
			return True
		if(nextBtype == EntityType.CORE):
			return True
		if(nextBtype == EntityType.CONVEYOR):
			# ct.draw_indicator_line(Position(0, 0), loc.add(ct.get_direction(nextBid)), 25, 105, 225)
			# ct.draw_indicator_line(Position(0, 0), loc, 25, 105, 225)
			if(ct.get_direction(nextBid) == dir.opposite()):
				# print(loc, ct.get_direction(nextBid), dir.opposite())
				return False
		if(nextBtype == EntityType.BRIDGE):
			if(ct.get_bridge_target(nextBid) == ct.get_position()):
				return False
		# print(loc)
		return True

	def tryDirWithConveyor(self, ct, dir):
		# print(dir)
		nextPos = ct.get_position().add(dir)
		# ct.draw_indicator_line(ct.get_position(), nextPos, 255, 255, 255)
		if(dir == self.toCardinal(dir)):
			self.tryBuildConveyor(ct, self.lastConnect, dir)
		else:
			if(ct.get_global_resources()[0] < ct.get_bridge_cost()[0]):
				return
			if(self.canMoveDirWithConveyor(ct, self.lastConnect.add(dir).add(dir), dir)):
				self.tryBuildBridge(ct, self.lastConnect, nextPos.add(dir).add(dir))
			self.tryBuildBridge(ct, self.lastConnect, nextPos.add(dir))
		self.tryBuildRoad(ct, nextPos)


	def MOVE_to_target_with_conveyor(self, ct, origin: Position, loc: Position, dist=2):
		# THIS HERE, EXPLORE USING CONVEYOR + ROAD, dont care about allyScore, enemyScore and emptyScore
		
		# ct.draw_indicator_line(ct.get_position(), loc, 255, 255, 0)
		

		if(not ct.get_move_cooldown() == 0): return

		print("IM MOVING ")

		if(self.originConnect == None or self.originConnect != origin):
			self.originConnect = origin
			self.lastConnect = origin
			self.currentConnections = []
			# print("RESETED CONENCTIONS")




		self.lastLocation = self.currentLocation
		self.currentLocation = ct.get_position()

		if(loc.distance_squared(self.lastConnect) <= dist):
			return "STUCK"


		if(ct.get_global_resources()[0] < ct.get_conveyor_cost()[0]):
			if(ct.get_position() != self.lastConnect):
				self.MOVE_to_target(ct, self.lastConnect, False, 0, 0, 0)
			return

		if(ct.get_position().distance_squared(self.lastConnect) > 2 or (len(self.currentConnections) > 0 and self.currentConnections[-1] == self.lastConnect)): # LAST TIME 2
			self.MOVE_to_target(ct, self.lastConnect, False, 0, 0, 0)
		

		if(ct.get_position().distance_squared(self.lastConnect) > 2):
			return

		if(self.lastTargetLocation == None or self.lastTargetLocation.distance_squared(loc) > 8 or self.bugStackIndex >= self.MAX_STACK_SIZE-10):
			# print("BUGSTACK ", self.bugStackIndex)
			self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0
			self.lastTargetLocation = loc
			self.lastLocation = ct.get_position()
			# print("RESETED CONENCTIONS2")




		

		
		if(self.lastTargetLocation != None and self.lastTargetLocation.distance_squared(loc) <= 8):
			self.lastTargetLocation = loc


		if(self.lastConnect != None):
			pass
			# ct.draw_indicator_line(self.lastConnect, Position(0, 0), 255, 255, 100)

		if(self.lastConnect not in self.currentConnections and self.lastConnect != Position(-1, -1)):
			self.currentConnections.append(self.lastConnect)
		# print(self.currentConnections)
		# thứ duy nhất hắn có thể làm, cũng là điều duy nhất hắn muốn làm chính là kiên trì đến cùng
		
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
			self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
			self.bugStackIndex = 0
		
		bid = ct.get_tile_building_id(self.lastConnect)
		btype = ct.get_entity_type(bid)
		bteam = ct.get_team(bid)
		if(bid != None):
			if(bteam != ct.get_team()):
				# print(self.currentConnections)
				# if(len(self.currentConnections) > 3 ):
				# 	moveDir = ct.get_position().direction_to(self.lastConnect)
				# 	if(ct.can_move(moveDir)):
				# 		ct.move(moveDir)
				# 	if(ct.is_tile_passable(self.lastConnect)):
				# 		if(ct.can_fire(self.lastConnect)):
				# 			ct.fire(self.lastConnect)
				# 		return
					# self.lastConnect = self.currentLocation[::-2]
				# else:
				# if(ct.is_tile_passable(self.lastConnect)):
				# 	return
				# else:
				# 	if(len(self.currentConnections) > 3 ):
				# 		self.lastConnect = self.currentConnections[-2]
				# 	else:
				# print(self.currentConnections)
				# return "STUCK"
				# print(self.currentConnections)
				# if(len(self.currentConnections) > 2):
				# 	self.lastConnect = self.currentConnections[-2]
				# 	self.currentConnections.pop()
				# else:
				return "STUCK"
				
					
			if(btype == EntityType.CONVEYOR):
				conveyorDir = ct.get_direction(bid)
				nextPos = self.lastConnect.add(conveyorDir)
				bid = ct.get_tile_building_id(nextPos)
				btype = ct.get_entity_type(bid)
				bteam = ct.get_team(bid)
				if(bid != None and bteam != ct.get_team()):
					if(ct.can_destroy(self.lastConnect)):
						ct.destroy(self.lastConnect)
				else:
					self.lastConnect = nextPos
				
			elif(btype == EntityType.BRIDGE):
				nextPos =  ct.get_bridge_target(bid)
				bid = ct.get_tile_building_id(nextPos)
				btype = ct.get_entity_type(bid)
				bteam = ct.get_team(bid)
				if(bid != None and bteam != ct.get_team()):
					if(ct.can_destroy(self.lastConnect)):
						ct.destroy(self.lastConnect)
				else:
					self.lastConnect = nextPos
			elif(btype == EntityType.ROAD):
				pass
			else:
				return "STUCK"


		if(self.bugStackIndex == 0):
			if(self.lastConnect.distance_squared(loc) > 30):
				allyScore = -1
			else:
				allyScore = -3
			bestDir, bestPos, bestScore, dirToTarget = self.calcBestDirConveyor(ct, self.lastConnect, loc, allyScore, -25, 1)
			
			# ct.draw_indicator_line(Position(0, 0), bestPos, 255, 255, 255)
			if(bestPos is not None and bestScore > -20):
				if(self.lastConnect.distance_squared(bestPos) == 1):
					self.tryBuildConveyor(ct, self.lastConnect, bestDir)
				else:
					self.tryBuildBridge(ct, self.lastConnect, bestPos)

				if(ct.can_build_road(ct.get_position().add(bestDir))):
					ct.build_road(ct.get_position().add(bestDir))

				if(bestPos.distance_squared(self.lastConnect) < ct.get_position().distance_squared(self.lastConnect)):
					if(ct.can_move(bestDir)):
						ct.move(bestDir)
						return
				if(ct.get_action_cooldown() > 0 or ct.get_global_resources()[0] < ct.get_bridge_cost()[0]):
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
			# print("LEFTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_right()
			for i in range(8):
				if(not self.canMoveDirWithConveyor(ct, ct.get_position().add(dir), dir) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					self.tryDirWithConveyor(ct, dir)
					bestPos = ct.get_position().add(dir)
					if(bestPos.distance_squared(self.lastConnect) < ct.get_position().distance_squared(self.lastConnect)):
						if(ct.can_move(dir)):
							ct.move(dir)
							return
					if(ct.get_action_cooldown() > 0 or ct.get_global_resources()[0] < ct.get_bridge_cost()[0]):
						return
				dir = dir.rotate_right()
		else:
			# print("RIGHTING")
			dir = self.bugStack[self.bugStackIndex-1].rotate_left()
			for i in range(8):
				if(not self.canMoveDirWithConveyor(ct, ct.get_position().add(dir), dir) or self.tooCloseToDanger(ct, ct.get_position().add(dir)) ):
					if(not self.onTheMap(ct, ct.get_position().add(dir))):
						self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
						self.bugStackIndex = 0
						self.RIGHT = not self.RIGHT
						break
					self.bugStack[self.bugStackIndex] = dir
					self.bugStackIndex += 1

				else:
					self.tryDirWithConveyor(ct, dir)
					bestPos = ct.get_position().add(dir)
					if(bestPos.distance_squared(self.lastConnect) < ct.get_position().distance_squared(self.lastConnect)):
						if(ct.can_move(dir)):
							ct.move(dir)
							return
					if(ct.get_action_cooldown() > 0 or ct.get_global_resources()[0] < ct.get_bridge_cost()[0]):
						return
				dir = dir.rotate_left()
		if(ct.get_action_cooldown() == 0):
			return "STUCK"
		
	def trymoveIntoRangeBool(self, ct, targetLoc, dist, avoidDanger):
		bestDir = Direction.CENTRE
		bestDirScore = self.tileScore(ct, ct.get_position(),targetLoc, 0, 0, 1, -30) if ct.get_position().distance_squared(targetLoc) <= dist else -9999

		for dir in self.fuzzyDirs(ct.get_position().direction_to(targetLoc)):
			if(ct.get_position().add(dir).distance_squared(targetLoc) <= dist  and self.canMove(ct, ct.get_position().add(dir)) and ct.can_move(dir)):
				score = self.tileScore(ct, ct.get_position().add(dir),targetLoc, 0, 0, 1,-30)
				if(score > bestDirScore):
					bestDir = dir
					bestDirScore = score
		print("BESTDIR: ",bestDir)
		if(bestDir != Direction.CENTRE and ( not avoidDanger or bestDirScore > -20) and bestDirScore > -100):
			ct.move(bestDir)
			return True
		
		return ct.get_position().distance_squared(targetLoc) <= dist

	def safeFuzzyMoveLocBool(self, ct, loc):
		if(self.lastSafeFuzzyLoc is None or self.lastSafeFuzzyLoc.distance_squared(loc) > 4):
			self.prevPositions = [None] * 8
			self.prevPosIndex = 0
		self.lastSafeFuzzyLoc = loc

		return self.safeFuzzyMoveDirBool(ct, ct.get_position().direction_to(loc))
	
	def isPreviousLocation(self, loc, previous):
		for prevLoc in previous:
			if(prevLoc is not None and prevLoc == loc):
				return True
		return False

	def safeFuzzyMoveDirBool(self, ct, dir):
		bestDirection = None
		bestDirScore = -1000
		loc = None
		score = 0
		deviation = -1
		for d in self.fuzzyDirs(dir):
			deviation += 1

			loc = ct.get_position().add(d)
			if(not self.canMove(ct, loc) or self.isPreviousLocation(loc, self.prevPositions)):
				continue
			score = self.tileScoreBool(ct, loc, Position(-1, -1), 0, 0, 1, -30, False) - deviation / 2

			if(score > bestDirScore):
				bestDirection = d
				bestDirScore = score
		if(bestDirection is not None):
			if(ct.can_build_road(ct.get_position().add(bestDirection))):
				ct.build_road(ct.get_position().add(bestDirection))
			if(ct.can_move(bestDirection)):
				ct.move(bestDirection)
				self.prevPositions[self.prevPosIndex] = ct.get_position()
				self.prevPosIndex = (self.prevPosIndex + 1) % len(self.prevPositions)
				return True
		self.prevPositions[self.prevPosIndex] = ct.get_position()
		self.prevPosIndex = (self.prevPosIndex + 1) % len(self.prevPositions)

		return False
