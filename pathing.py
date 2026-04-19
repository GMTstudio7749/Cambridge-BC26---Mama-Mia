import random
from cambc import Controller, Direction, EntityType, Environment, Position
from utils import *
from collections import deque

class Pathing:
    def __init__(self):
        self.myLoc = Position(-1, -1)
        self.clockwise = False
        self.shouldGuessRotation = True
        self.bestBugDist = 100000000
        self.shouldBug = False
        self.doneSimulating = False
        self.currentTarget = None
        self.pathLength = 0
        self.currentBugPosition = None
        self.currentBugDirection = None 


        self.lastLocation = None
        self.currentLocation = None

        self.MAX_STACK_SIZE = 100
        self.bugStack: list[Direction] = [] * self.MAX_STACK_SIZE
        self.RIGHT = random.randint(0, 1)


    def bfsToBugTarget(self, ct, start, goal, canMove, tooCloseToDanger):
        if start == goal:
            return None 

        DIRECTIONS = [
            Direction.NORTH, Direction.NORTHEAST, Direction.EAST,
            Direction.SOUTHEAST, Direction.SOUTH, Direction.SOUTHWEST,
            Direction.WEST, Direction.NORTHWEST
        ]

        queue = deque()
        queue.append(start)

        visited = set()
        visited.add((start.x, start.y))

        parent = {} 

        while queue:
            cur = queue.popleft()

            for d in DIRECTIONS:
                nxt = cur.add(d)

                if (nxt.x, nxt.y) in visited:
                    continue
                if not self.onTheMap(ct, nxt) or not ct.is_in_vision(nxt):
                    continue
                if not canMove(ct, nxt):
                    continue
                if tooCloseToDanger(ct, nxt):
                    continue

                visited.add((nxt.x, nxt.y))
                parent[(nxt.x, nxt.y)] = (cur, d)

                if nxt == goal:
                    step = nxt
                    while parent[(step.x, step.y)][0] != start:
                        step = parent[(step.x, step.y)][0]
                    return parent[(step.x, step.y)][1]

                queue.append(nxt)

        bestDir = None
        bestDist = start.distance_squared(goal)

        for d in DIRECTIONS:
            nxt = start.add(d)

            if not self.onTheMap(ct, nxt):
                continue
            if not canMove(ct, nxt):
                continue
            if tooCloseToDanger(ct, nxt):
                continue

            dist = nxt.distance_squared(goal)

            if dist < bestDist:
                bestDist = dist
                bestDir = d

        return bestDir

    def bugLoop(self, ct, target, canMove, canMoveLoc, tooCloseToDanger, reachableFrom, tileScore):
        for _ in range(10):
            if self.doneSimulating or self.currentBugPosition == target:
                return
            self.bug(ct, canMoveLoc, tooCloseToDanger, reachableFrom, tileScore)


    def pathTo(self, ct, target, canMove, checkCanMove, canMoveLoc, tooCloseToDanger, reachableFrom, tileScore):
        if( ct.get_move_cooldown() > 0):
            return
        self.myLoc = ct.get_position()
        if(self.myLoc == target):
            return 
        if(self.myLoc.distance_squared(target) <= 2):
            if(checkCanMove(ct, self.myLoc.direction_to(target))):
                return self.myLoc.direction_to(target)
            return 

        if(self.currentTarget == None or not self.currentTarget == target):
            self.resetPathing(ct, target)
        
        self.doneSimulating = self.currentBugPosition == target
        
        self.bugLoop(ct, target, checkCanMove, canMoveLoc, tooCloseToDanger, reachableFrom, tileScore)
        # ct.draw_indicator_line(self.currentBugPosition, self.myLoc, 255, 0, 255)

        return self.bfsToBugTarget(ct, ct.get_position(), self.currentBugPosition, canMove, tooCloseToDanger)
        


    def onTheMap(self, ct, pos):
        if(pos.x < 0 or pos.x >= ct.get_map_width() or pos.y < 0 or pos.y >= ct.get_map_height()):
            return False
        return True

    def bug(self, ct, canMove, tooCloseToDanger, reachableFrom, tileScore):
        if(not ct.get_move_cooldown() == 0): return


        self.lastLocation = self.currentLocation
        self.currentLocation = self.currentBugPosition
        dirToTarget = self.currentLocation.direction_to(self.currentTarget)
        bestDir = None
        bestScore = -9999
        if(self.currentLocation.add(self.bugStack[self.bugStackIndex - 1]).distance_squared(self.myLoc) >= 20 or self.currentLocation.add( self.bugStack[self.bugStackIndex - 2]).distance_squared(self.myLoc) >= 20 or  self.currentLocation.add(dirToTarget).distance_squared(self.myLoc) >= 20 or self.currentLocation.add(dirToTarget.rotate_left()).distance_squared(self.myLoc) >= 20 or self.currentLocation.add(dirToTarget.rotate_right()).distance_squared(self.myLoc) >= 20):
            self.doneSimulating = True
            return
        for i in Dirs:
            if(self.currentLocation.add(i).distance_squared(self.myLoc) >= 20):
                self.doneSimulating = True
                return
            
        while (
            self.bugStackIndex != 0 and
            (
                (
                    canMove(ct, self.currentLocation.add(self.bugStack[self.bugStackIndex - 1])) and
                    not tooCloseToDanger(ct, self.currentLocation.add(self.bugStack[self.bugStackIndex - 1]))
                )
                or
                (
                    self.bugStackIndex > 1 and
                    canMove(ct, self.currentLocation.add( self.bugStack[self.bugStackIndex - 2])) and
                    not tooCloseToDanger(ct, self.currentLocation.add(self.bugStack[self.bugStackIndex - 2])) and
                    not (
                        self.lastLocation is not None and
                        self.currentLocation.add(self.bugStack[self.bugStackIndex - 2]) == self.lastLocation
                    )
                )
            )
        ):
            self.bugStackIndex -= 1
            print("GG")

        if(reachableFrom(ct, self.currentLocation, self.currentTarget)):
            self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
            self.bugStackIndex = 0
            print("REACHABLE")

        if(self.bugStackIndex == 0):
            print("EZ")


            score1 = tileScore(ct, self.currentLocation.add(dirToTarget), self.currentTarget, 0, 0, -2, -30)
            score2 = tileScore(ct, self.currentLocation.add(dirToTarget.rotate_left()), self.currentTarget, 0, 0, -2, -30)
            score3 = tileScore(ct, self.currentLocation.add(dirToTarget.rotate_right()),  self.currentTarget,0, 0, -2, -30)



            # if(zigzag):
            #     if(self.dir_order.index(dirToTarget) % 2 == 0 and self.currentLocation.distance_squared(loc) > 50):
            #         if(ct.get_current_round()%4 < 2):
            #             score2 += 1
            #         else:
            #             score3 += 1
            if(canMove(ct, self.currentLocation.add(dirToTarget)) and score1 > bestScore and not self.currentLocation.add(dirToTarget) == self.lastLocation):
                bestDir = dirToTarget
                bestScore = score1
            if(canMove(ct, self.currentLocation.add(dirToTarget.rotate_left())) and score2 > bestScore and not self.currentLocation.add(dirToTarget.rotate_left()) == self.lastLocation):
                bestDir = dirToTarget.rotate_left()
                bestScore = score2
            if(canMove(ct, self.currentLocation.add(dirToTarget.rotate_right())) and score3 > bestScore and not self.currentLocation.add(dirToTarget.rotate_right()) == self.lastLocation):
                bestDir = dirToTarget.rotate_right()
                bestScore = score3

            


            if(bestDir is not None and bestScore > -20):
                # print("CANMOVE")
                nextPos = self.currentLocation.add(bestDir)
                if(nextPos.distance_squared(self.myLoc) <= 20):
                    self.currentBugPosition = nextPos
                    self.currentBugDirection = bestDir
                    # ct.draw_indicator_line(ct.get_position(), nextPos, 255, 255, 255)
                    return
                else:
                    self.doneSimulating = True
                    return
                

            self.bugStack[self.bugStackIndex] = dirToTarget.rotate_left() if self.RIGHT else dirToTarget.rotate_right()
            self.bugStackIndex += 1


        if(self.RIGHT):
            dir = self.bugStack[self.bugStackIndex-1].rotate_right()
            for i in range(8):
                if(self.currentLocation.add(dir).distance_squared(self.myLoc) > 20):
                    self.doneSimulating = True
                    return
                if(not canMove(ct, self.currentLocation.add(dir))  or tooCloseToDanger(ct, self.currentLocation.add(dir))):
                    if(not self.onTheMap(ct, self.currentLocation.add(dir))):
                        self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
                        self.bugStackIndex = 0
                        self.RIGHT = not self.RIGHT
                        break
                    self.bugStack[self.bugStackIndex] = dir
                    self.bugStackIndex += 1

                else:
                    if(self.currentLocation.add(dir).distance_squared(self.myLoc) <= 20):
                        self.currentBugPosition = self.currentLocation.add(dir)
                        self.currentBugDirection = dir
                        # ct.draw_indicator_line(ct.get_position(), self.currentBugPosition, 255, 255, 255)
                    else:
                        self.doneSimulating = True
                        return
                    return
                dir = dir.rotate_right()
        else:
            dir = self.bugStack[self.bugStackIndex-1].rotate_left()
            for _ in range(8):
                if(self.currentLocation.add(dir).distance_squared(self.myLoc) > 20):
                    self.doneSimulating = True
                    return
            
                if(not canMove(ct, self.currentLocation.add(dir)) or tooCloseToDanger(ct, self.currentLocation.add(dir)) ):
                    if(not self.onTheMap(ct, self.currentLocation.add(dir))):
                        self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
                        self.bugStackIndex = 0
                        self.RIGHT = not self.RIGHT
                        break
                    self.bugStack[self.bugStackIndex] = dir
                    self.bugStackIndex += 1

                else:
                    if(self.currentLocation.add(dir).distance_squared(self.myLoc) <= 20):
                        self.currentBugPosition = self.currentLocation.add(dir)
                        self.currentBugDirection = dir
                        # ct.draw_indicator_line(ct.get_position(), self.currentBugPosition, 255, 255, 255)
                    else:
                        self.doneSimulating = True
                        return
                    return
                dir = dir.rotate_left()

    def resetPathing(self, ct, target):
        self.bestBugDist = 100000000;
        self.shouldBug = False;
        self.currentTarget = target;
        self.currentBugDirection = None;
        self.currentBugPosition = ct.get_position();
        self.pathLength = 0;

        print("RESETED")
        self.bugStack = [Direction.CENTRE] * self.MAX_STACK_SIZE
        self.bugStackIndex = 0
        self.lastTargetLocation = target
        self.lastLocation = ct.get_position()