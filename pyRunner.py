import pygame
from pygame.locals import*
#import key names
from pygame.key import *
import os
import platform
import random
import sys
import math
from menu import *
if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
pygame.init()

###OPTIMIZATION DOTO
# check collision
# use render groups and only update needed
# hardware accel on fullscreen?
# use surface.fill for drawing filled rects
# surface.convert on all surfaces
##CHANGELOG 0.6:
#David:
#-level design code
#-fixed lag problem
#-added progress bar for inv
#-fixed crashes
#Brian:
#-shield and invisibility cubes
##CHANGELOG 0.7:
#David:
#-fixed significant bug where program would slow down when many cubes
#were picked up in a row. was an error in pygame.sprite.GroupSingle class
##CHANGELOG 0.8: 
#Brian:
#-added in turrets,gun and bullets
##CHANGELOG 0.9:
#David:
#-inserted modified and improved levling code
#-created endMenu
#Brian:
#-fixed error in gun programming, now reloads

##VARS
##VARS DEFINED IN init()
screen = None
##VARS DEFINED IN gameInit()
mainLevelManager = None
gunner = None
background = None
clock = None
keepGoing = False
runner1 = None
max_height = None
min_height = None
rungroup = None
blockMinHeight = None
blockMaxHeight = None
#GROUPS
blockGroup = None
cubeGroup = None
invGroup = None
shieldGroup = None
turretGroup = None
gunGroup = None
effectsGroup = None
bulletGroup = None
gunnerGroup = None
ammoInd = None
shieldsInd = None
speedInd = None
score = None
frame_count = None
displayFrame = None
target_rate = None
invInd = None
gameMode = None

class runner(pygame.sprite.Sprite):
    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(os.path.join(\
            "Resources","runner.bmp"))
        self.image = self.image.convert()
        self.rect = self.image.get_rect()
        self.rect.centerx = 70
        if not _debug:
            self.rect.centerx = 120
        self.rect.centery = screen.get_rect().centery
        self.dy = 4
        self.flash = False #are we flashing (invunrable after collision)
        self.shield = 3 #how much is left in our shield
        self.count = 0 #this is the count for the flashing
        self.visible = True #do we want to be visible (next update)
        self.isvisible = True #are we actually visible
        self.flashRate = 8 #number of frames it will take to toggle the flash
        self.inv = False
        self.gun = 0
        self.last_shot = 10
        self.shots = 0
        self.invCount = 800
        self.ammo = 0
    def hit(self):
        if not self.inv:
            if not self.flash: #if not already flasshing from a collision
                self.shield -= 1
                if not self.shield == 0:
                    
                    debug("play")
                    self.flash = True #start flashing
                    self.count = 96 #for 96 frames
                    effectsGroup.add(fadeEffect((255,0,0)))
                    mainLevelManager.fallback(400)
    def update(self):
        #set our own dy to scroller.dx minus 2
        self.dy = scroller.dx - 2
        key = pygame.key.get_pressed()
        #key up and down events
        if key[K_UP]:
            self.rect.centery += -self.dy
        if key[K_DOWN]:
            self.rect.centery += self.dy
        if key[K_SPACE]:
            if self.gun > 1:
                debug("reload")
                self.shots = 0
                self.gun = 1
                self.ammo = 10
            elif self.gun == 1:
                debug(self.gun)
                if self.shots > 9:
                    self.shots = 0
                    self.gun = 0
                    self.ammo = 0
                else:
                    self.last_shot +=1
                    if self.last_shot >= 10:
                        self.shots +=1
                        gunnerGroup.add(gun(self.rect.centery,self.rect.centerx))
                        self.last_shot = 0
                        debug("gunnerGroup" + str(gunnerGroup))
                        self.ammo -= 1
        #clip to our max and min heights created when we make borders
        if self.rect.top < max_height+1:
            self.rect.top = max_height+1
        if self.rect.bottom > min_height-1:
            self.rect.bottom = min_height-1
        if self.flash:
            self.count -= 1
            self.flashRate -= 1
            if self.flashRate == 0: #if the flash rate is 0 we toggle visiblity
                if self.visible: 
                    self.visible = False
                else:
                    self.visible = True
                self.flashRate = 8
        if self.visible != self.isvisible: #if the wanted visible is different
            self.image.set_alpha(255*self.visible)
            self.isvisible = self.visible
        if self.count == 0:
            self.flash = False #stop flashing when we are finished
        if self.inv:
            self.invCount -= 1
        if self.invCount == 0:
            self.inv = False
            self.invCount = 800
        if self.shield == 0:
            self.kill()
    def invinc(self):
        self.inv = True
        if self.invCount < 700:
            self.invCount = 800
     
#super class for all scrolling objects
class scroller(pygame.sprite.Sprite):
    dx = 6
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
    def update(self):
        self.rect.centerx -= self.dx
screen = None
class turret(scroller):
    def __init__(self,y):
        self.image = pygame.Surface((55,32))
        self.angle = random.randint(-45,45)
        self.top = random.randint(0,1)
        global top
        top = self.top
        self.rect = self.image.get_rect()
        debug(str(self.rect.centerx))
        scroller.__init__(self)
        self.count = 0
        self.x = self.rect.centerx
        if self.top == 1:
            self.rect.top = max_height+1
            self.image.blit(pygame.transform.rotate(gunner,self.angle),(self.rect.centerx-15,-15,0,0))
        else:
            self.rect.bottom = min_height-1
            self.angle += 180
            self.image.blit(pygame.transform.rotate(gunner,self.angle),(self.rect.centerx-15,0,0,0))
        self.rect.right = pygame.display.get_surface().get_width()
        debug(str(self.angle))
    def y(self): #y accessor
        return self.y
    def update(self):
        scroller.update(self)
        self.count += 1
        if self.count == 25:
            bulletGroup.add(bullet(self.rect.centerx,self.rect.centery,self.angle))
            debug(str(bulletGroup))
            self.count = 0
        if self.rect.right < 0: #same code to delete self if off screen as block
            self.kill()
            del self
class bullet(scroller):
    def __init__(self,x,y,angle):
        self.image = pygame.Surface((10,10))
        pygame.draw.circle(self.image, (255,145,35), (5,5), 5)
        self.color = ((255,145,35))
        self.angle = angle
        scroller.__init__(self)
        self.y = y+5
        self.x = x+8 
        self.mag = 15
        self.rect = self.image.get_rect()
        self.rect.centery = self.y
        self.rect.centerx = self.x
        pygame.draw.rect(self.image, self.color,self.rect,3)
        self._dy = math.cos(math.radians(self.angle))*self.mag
        self._dx = math.sin(math.radians(self.angle))*self.mag
    def update(self):
        scroller.update(self)
        self.rect.centery += self._dy
        self.rect.centerx += self._dx
        if top == 1:
            if self.rect.centery > min_height:
                self.kill()
                del self
        if top == 0:
            if self.rect.centery < max_height:
                self.kill()
                del self
#class that displays color and then fades out
class fadeEffect(pygame.sprite.Sprite):
    def __init__(self,color):
        pygame.sprite.Sprite.__init__(self)
        #create a surface matching the display size
        self.image = pygame.Surface(pygame.display.get_surface().get_size())
        #fill
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.alpha = 96 #match this with the flash count of the runner
    def update(self):
        self.image.set_alpha(self.alpha)
        #update alpha and decrease every frame
        self.alpha -= 1
        if self.alpha == 0:
            self.kill()
    def kill(self):
        debug("KILLED ME")
        pygame.sprite.Sprite.kill(self)
class block(scroller):
    def __init__(self, y):
        scroller.__init__(self)
        self.image = pygame.Surface((20, 90))
        self.rect = self.image.get_rect()
        self.y = y
        pygame.draw.rect(self.image, (28,55,183), self.rect)
        self.rect.right = pygame.display.get_surface().get_width()
        self.rect.centery = y
        #make sure the block is on the screen
        #debug("block with center y of {0:n}".format(self.rect.centery))
    def update(self):
        scroller.update(self)
        if self.rect.right < 0:
            self.kill()
            del self
    def y(self):
        return self.y
    def __str__(self):
        return "block: ",self.y
class cube(scroller):
    def __init__(self,y):
        scroller.__init__(self)
        self.image = pygame.Surface((20,20))
        self.rect = self.image.get_rect()
        pygame.draw.rect(self.image, self.color,self.rect,3)
        self.y = y
        self.rect.right = pygame.display.get_surface().get_width()
        self.rect.centery = self.y
    def update(self):
        scroller.update(self)
        if self.rect.right < 0: #same code to delete self if off screen as block
            self.kill()
            del self
    def y(self): #y accessor
        return self.y
    def hit(self):
        effectsGroup.add(fadeEffect(self.color))
class scoreCube(cube):
    scoreProbabilites = [500,500,500,500,1000,1000,2000] #define probablility list for scores
    def __init__(self,y):
        #choose a random score
        self.score = random.choice(self.scoreProbabilites)
        #define the image options
        self.colors = {500: (0,0,255),1000:(0,255,0),2000:(255,0,255)}
        #choose a image corresponding with the score 
        self.color = self.colors[self.score]
        #debug("scoreCube with y: "+str(y))
        cube.__init__(self,y) #call the initializer after these two commands
    def score(self): #score accessor
        return self.score
class gunCube(cube):
    def __init__(self,y):
        self.color=(255,0,0)
        cube.__init__(self,y)
    def hit(self):
        rungroup.sprite.gun += 1
        debug(str(rungroup.sprite.gun))

class invCube(cube):
    def __init__(self,y):
        self.color = (255,255,255)
        cube.__init__(self,y)

class shieldCube(cube):
    def __init__(self,y):
        self.color = (0,128,255)
        cube.__init__(self,y)
class gun(scroller):
    def __init__(self,y,x):
        self.image = pygame.Surface((10,10))
        self.color = (255,100,0)
        self.y = y
        self.x = x
        pygame.draw.circle(self.image, self.color, (5,5), 5)
        self.rect = self.image.get_rect()
        self.rect.centerx = self.x
        self.rect.centery = self.y
        scroller.__init__(self)
        self._dx = 15
        pygame.draw.rect(self.image, self.color,self.rect,3)
        self.shots = 10
    def update(self):
        scroller.update(self)
        self.rect.centerx += self._dx
        if self.rect.centerx > pygame.display.get_surface().get_width():
            self.kill()
            del self
class ammoIndicator():
    def __init__(self):
        self.ammoNumber = 0 #define storage of shields
        self.cubeTemplate = pygame.image.load(os.path.join("Resources",\
                                                           "bulletInd.gif"))
        self.cubeTemplate = self.cubeTemplate.convert()
        self.surface = None #location to store our surface
        self.displayedAmmo = 0#number of shields displayed
        self.font = pygame.font.Font(None,18)
        self.fontSurface = self.font.render("Ammo: ",True,(255,255,255))
    def getSurface(self): #prepare and output a surface with the shields
        if self.surface and self.displayedAmmo == self.ammoNumber:
            return self.surface #if we don't need to make a surface return the
        #old one
        elif not self.surface: #make a surface if we need one
            self.surface = pygame.Surface(((155+self.fontSurface.get_width()),10))
            self.surface.fill((0,0,0)) #fill with the bg color
        self.surface.fill((0,0,0))
        count = self.fontSurface.get_width() + 5
        self.surface.blit(self.fontSurface,(0,0))
        for x in range(self.ammoNumber): #build surface
            self.surface.blit(self.cubeTemplate,(count,0))
            count += 15
        self.displayedAmmo = self.ammoNumber #we are displaying the number
        return self.surface
    def setAmmo(self,ammo):
        self.ammoNumber = ammo        
#class to layout and return a surface containing the shields indicator
class shieldIndicator():
    def __init__(self):
        self.shieldNumber = 0 #define storage of shields
        self.cubeTemplate = pygame.image.load(os.path.join("Resources",\
                                                           "blue square.bmp"))
        self.cubeTemplate = self.cubeTemplate.convert()
        self.surface = None #location to store our surface
        self.displayedShields = 0#number of shields displayed
        self.font = pygame.font.Font(None,18)
        self.fontSurface = self.font.render("Shields: ",True,(255,255,255))
    def getSurface(self): #prepare and output a surface with the shields
        if self.surface and self.displayedShields == self.shieldNumber:
            return self.surface #if we don't need to make a surface return the
        #old one
        elif not self.surface: #make a surface if we need one
            self.surface = pygame.Surface(((105+self.fontSurface.get_width()),10))
            self.surface.fill((0,0,0)) #fill with the bg color
        self.surface.fill((0,0,0))
        count = self.fontSurface.get_width() + 5
        self.surface.blit(self.fontSurface,(0,0))
        for x in range(self.shieldNumber): #build surface
            self.surface.blit(self.cubeTemplate,(count,0))
            count += 35
        self.displayedShields = self.shieldNumber #we are displaying the number
        return self.surface
    def setShield(self,shield):
        self.shieldNumber = shield

#class to layout and create the bar
class progressIndicator():
    def __init__(self,color,label):
        self.percent = 0 #define storage of percent
        self.surface = None #location to store our surface
        self.displayedPercent = 0#number of percentage displayed
        self.label = label
        self.font = pygame.font.Font(None,18)
        self.fontSurface = self.font.render(self.label,True,(255,255,255))
        self.color = color
    def getSurface(self): #prepare and output a surface with the shields
        if self.surface and self.percent == self.displayedPercent:
            return self.surface #if we don't need to make a surface return the
        #old one
        elif not self.surface: #make a surface if we need one
            self.surface = pygame.Surface(((105+self.fontSurface.get_width()),15))
        self.surface.fill((0,0,0))
        self.surface.blit(self.fontSurface,(0,0))
        box = pygame.rect.Rect((self.fontSurface.get_width()+5,0,100,10))
        boxFill = box.move(1,1)
        boxFill.width = ((self.percent/100.0)*99)-1
        boxFill.height -= 1
        pygame.draw.rect(self.surface,self.color,box,1)
        if self.percent != 0:
            pygame.draw.rect(self.surface,self.color,boxFill)
        self.displayedPercent = self.percent #we are displaying the number
        return self.surface
    def setPercentage(self,percent):
        self.percent = percent
        debug(str(self.percent))

#The pygame GroupSingle has a error in its code such that when a sprite is added to the group, the other sprites will cause some form of memory leak instead
#of being properly disposed of. This class emulates the behavior of the GroupSingle's add method but functions properly.
class WorkingSingle(pygame.sprite.Group):
    def add(self,*sprites):
        if self.sprites():
            self.sprites()[0].kill()
        try:
            spriteAdd = sprites[0]
        except IndexError:
            spriteAdd = ()
        pygame.sprite.Group.add(self,spriteAdd)

#special group class to manage rezzing of objects that are randomly created, objects in the group must have a initialalizer of (self,y)
class randomRezGroup(pygame.sprite.RenderUpdates):
    def __init__(self,templateClass,maxRezHeight,minRezHeight,maxInRow=3,minDistance=75,minRowDistance=100,\
                 maxRowDistance=200,active=True):
        pygame.sprite.RenderUpdates.__init__(self)
        #initialize this
        self.nextRowPosition = 0
        #this signals the draw method to create its first row
        self.lastRowPosition = -1
        #assign some instance variables
        self.templateClass = templateClass
        self.minDistance = minDistance
        self.minRowDistance = minRowDistance
        self.maxRowDistance = maxRowDistance
        self.maxRezHeight = maxRezHeight
        self.minRezHeight = minRezHeight
        self.maxInRow = maxInRow
        self.active = active
        debug("self.templateClass "+str(self.templateClass)+"\nself.minDistance "+str(self.minDistance)+"\nself.minRowDistance "+str(self.minRowDistance)+\
              "\nself.maxRowDistance "+str(self.maxRowDistance)+"\nself.maxRezHeight "+str(self.maxRezHeight)+"\nself.minRezHeight "+str(self.minRezHeight)+\
              "\nself.maxInRow "+str(self.maxInRow))
    def update(self):
        #override draw method to handle drawing of new rows if needed
        if (self.lastRowPosition == -1 or self.lastRowPosition >=self.nextRowPosition) and self.active: 
            #choose random locations for blocks based on maxBlockInRow
            spritesInRow = []
            for x in range(random.randint(1,self.maxInRow)):
                #randomly choose how many blocks to create
                #randomly select block positions and add to group
                spritesInRow.append(self.templateClass(random.randint(\
                                                    self.maxRezHeight,\
                                                      self.minRezHeight)))
                
            self.add(spritesInRow)
            #check for minBlockDistance compliance
            orderedSprites = sorted(spritesInRow,key=self.templateClass.y)
            #go through ordered sprites and check for distance compliance
            i = -1 #counter variable
            for x in orderedSprites:
                if i >= 0: #ignore first one
                    topSprite = orderedSprites[i].rect.bottom #list is ordered
                    #in top to bottom order by position, this is the higher up
                    #one. we get its bottom x position
                    bottomSprite = x.rect.top #get the top position of the lower
                    #sprite
                    #debug("topSprite: {0:n}\nbottomSprite: {1:n}".format(\
                        #topSprite,bottomSprite))
                    if (bottomSprite - topSprite) < self.minDistance: #check
                        #for correct distance and if nessecary delete the sprite
                        x.kill()
                        #debug("sprite distance kill")
                i += 1
            #randomly choose our next row position
            self.nextRowPosition = random.randint(self.minRowDistance,\
                                             self.maxRowDistance)
            #track our just created last row
            self.lastRowPosition = 0
        #last row position increases by scroller.dx every frame
        self.lastRowPosition += scroller.dx
        return pygame.sprite.RenderUpdates.update(self)

#class to manage leveling
class levelManager(object):
    def __init__(self):
        #instance variables
        self.currentLevel = 1
        self.frameCount = 0
        self.framesTillNext = 0
        self.levelList = []
        self.activeLevel = None
        self.maxSpeed = 0
        self.minSpeed = 0
        self.speedInd = None
    def add(self,level): #add a level to the levels list
        self.levelList.append(level)
        level.number = len(self.levelList)-1
        if level.speed > self.maxSpeed: #maxSpeed of level assignment 
            self.maxSpeed = level.speed
        if self.minSpeed == 0:
            self.minSpeed = level.speed
        if level.speed < self.minSpeed:
            self.minSpeed = level.speed
        debug("maxSpeed: "+str(self.maxSpeed)+"\nminSpeed: "+str(self.minSpeed))
    def setLevel(self, levelNum): #set the level to the levelNum level in the
        #list and make it active, also set the framesTillNext to next level
        try:
            self.activeLevel = self.levelList[levelNum-1]
            self.currentLevel = levelNum
        except IndexError:
            debug("no more levels, fellback to current")
        self.activeLevel.makeActive()
        self.framesTillNext = self.activeLevel.length
        debug("scroller.dx:"+str(scroller.dx))
        if self.speedInd:
            if len(self.levelList) == 1:
                self.speedInd.setPercentage(100)
            else:
                self.speedInd.setPercentage(((self.activeLevel.speed-self.minSpeed)/float(self.maxSpeed-self.minSpeed))*100)
    def frame(self):#called every frame
        self.frameCount += 1
        self.framesTillNext -= 1
        if self.framesTillNext == 0:
            debug("advanced to level: " + str(self.currentLevel+1))
            self.setLevel(self.currentLevel+1) #if there are no frames left
            #go to the next level
    def setIndicator(self,indicator):
        self.speedInd = indicator
    def fallback(self, time): #fallback to a level for a specified time
        if not self.currentLevel == 1:
            self.setLevel(self.currentLevel-1)
            self.framesTillNext = time

#special class which describes a level and its attributes
#can also set the level if given the appropriate objects via enableLevel'
##LEVEL IS INITIALIZED AS SO:
##    attributes is a dictionary containing keys which are the groups to set,the
##    value must be a list which contains values in order for the randomRezGroup
##    (which is the key)
##    values are as so:
##        -maxInRow
##        -minDistanceBetweenRow
##        -maxDistanceBetweenRow
##        -maxDistanceBetweenBlocks
##        -also takes a speed attribute
##        -active
class level(object):
    def __init__(self,attributes,speed,length):
        #assign instance variables
        self.attributes = attributes
        self.speed = speed
        self.number = 0 #empty variable which will store our level number
        self.length = length
        #assigned by manager
    def makeActive(self):
        for key in self.attributes: #go through keys in dictionary and assign
            #values
            values = self.attributes[key]
            key.minDistance = values[3]
            key.minRowDistance = values[1]
            key.maxRowDistance = values[2]
            key.maxInRow = values[0]
            key.active = values[4]
        scroller.dx = self.speed #set speed

            
#debug function
_debug = True
_die = True
def debug(printstring):
    if _debug:
        print printstring

def init():
    #create screen
    global screen
    global clock
    if(_debug):
        screen = pygame.display.set_mode((600, 820))
    else:
        screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    # Ignore mouse motion (greatly reduces resources when not needed)
    pygame.event.set_blocked(pygame.MOUSEMOTION)
    clock = pygame.time.Clock()
def gameInit():
    global screen
    ##VARS DEFINED IN gameInit()
    global mainLevelManager
    global gunner
    global background
    global clock
    global keepGoing
    global runner1
    global rungroup
    global max_height
    global min_height
    global blockMinHeight
    global blockMaxHeight
    #GROUPS
    global blockGroup
    global cubeGroup
    global invGroup
    global shieldGroup
    global turretGroup
    global gunGroup
    global effectsGroup
    global bulletGroup
    global gunnerGroup
    global ammoInd
    global shieldsInd
    global speedInd
    global score
    global frame_count
    global displayFrame
    global target_rate
    global invInd
    #Globals defined in mainMenu()
    global gameMode
    ##INITIALIZATION CODE    
    mainLevelManager = levelManager()
    gunner = pygame.image.load(os.path.join(\
            "Resources","gunner.bmp"))
    gunner = gunner.convert()
    gunner.set_colorkey((0,0,0))
    background = pygame.Surface((screen.get_width(), screen.get_height()))
    pygame.draw.rect(background, (0,0,0), background.get_rect())
    #only nessecary if not fullscreen
    pygame.display.set_caption("pyRunner 2D")
    keepGoing = True
    #create our runner and a group to hold it
    runner1 = runner(screen)
    rungroup = pygame.sprite.GroupSingle(runner1)
    #calculate window borders based on size
    #create window borders
    height = screen.get_height()
    border_height = (height-800)/2.0
    #min_border_height stores minimum height for borders
    min_border_height = 70
    if border_height < min_border_height:
        #minimum border of 50px
        max_height = min_border_height
        min_height = height-min_border_height
        border_height = min_border_height
    max_height = border_height
    min_height = height - border_height
    #create our borders
    pygame.draw.rect(background, (255,255,255),\
                     pygame.rect.Rect(0,border_height, screen.get_width(), \
                                      0))
    pygame.draw.rect(background, (255,255,255),\
                     pygame.rect.Rect(0, min_height,\
                                      screen.get_width(), 0))
    #choose block border heights
    blockMinHeight = min_height - 45
    blockMaxHeight = max_height + 45
    ##INITIALIZE REZ GROUPS
    #initialize a block group of our randomRezGroup class (subclass of pygame.
    #sprite.group
    blockGroup = randomRezGroup(block,maxRezHeight=blockMaxHeight,minRezHeight=blockMinHeight)
    cubeGroup = randomRezGroup(scoreCube,maxRezHeight=blockMaxHeight,minRezHeight=blockMinHeight)
    invGroup = randomRezGroup(invCube,maxRezHeight=blockMaxHeight,minRezHeight=blockMinHeight)
    shieldGroup = randomRezGroup(shieldCube,maxRezHeight=blockMaxHeight,minRezHeight=blockMinHeight)
    turretGroup = randomRezGroup(turret,maxRezHeight = blockMaxHeight,minRezHeight=blockMinHeight)
    gunGroup = randomRezGroup(gunCube,maxRezHeight = blockMaxHeight,minRezHeight = blockMinHeight)
    effectsGroup = WorkingSingle() #group to store effects in
    bulletGroup = pygame.sprite.RenderUpdates()
    gunnerGroup = pygame.sprite.RenderUpdates()
    ##LEVEL CREATION AND DESIGN
    if gameMode == "endurance":
        mainLevelManager.add(level({blockGroup:[2,100,200,75,True],cubeGroup:[1,700,2000,300,True],\
                                    invGroup:[1,2000,5000,300,False],shieldGroup:[1,1000,3000,300,False],turretGroup:[1,1000,2000,300,False]\
                                    ,gunGroup:[1,50,50,50,False]},6,800))
        mainLevelManager.add(level({},7,800))
        mainLevelManager.add(level({blockGroup:[3,100,200,75,True]},7,1200))
        mainLevelManager.add(level({shieldGroup:[1,4000,7000,300,True]},8,800))
        mainLevelManager.add(level({gunGroup:[1,3000,7000,300,True]},8,600))
        mainLevelManager.add(level({invGroup:[1,5000,10000,300,True]},8,1200))
        mainLevelManager.add(level({turretGroup:[1,3000,5000,300,True]},8,3500))
        mainLevelManager.add(level({turretGroup:[1,2000,4000,300,True]},8,2000))
        mainLevelManager.add(level({blockGroup:[3,100,200,75,False],shieldGroup:[1,450,600,300,True]},8,1000))
        mainLevelManager.add(level({blockGroup:[3,75,200,75,True],shieldGroup:[1,4000,7000,300,True]},9,3200))
    elif gameMode == "challenge":
        mainLevelManager.add(level({blockGroup:[3,75,200,75,True],cubeGroup:[1,700,2000,300,True],\
                                    invGroup:[1,5000,10000,300,True],shieldGroup:[1,4000,7000,300,True],turretGroup:[1,2000,4000,300,True]\
                                    ,gunGroup:[1,3000,7000,300,True]},9,800))
    #create a shield indicator
    ammoInd = ammoIndicator()
    ammoInd.setAmmo(10)
    shieldsInd = shieldIndicator()
    shieldsInd.setShield(3)
    speedInd = progressIndicator((0,255,0),"Speed:   ")
    mainLevelManager.setIndicator(speedInd)
    #make first level active
    mainLevelManager.setLevel(1)
    #blit the background to the screen to start with
    screen.blit(background, (0,0))
    #create a variable to store distance
    score = 0
    #keep track of the number of frames
    frame_count = 0
    #do we want to display a framerate?
    displayFrame = False
    #target frame rate
    target_rate = 70
    #the next chosen row
    #tracking of last row
    invInd = progressIndicator((255,255,255),"")

def main():    
    global screen
    ##VARS DEFINED IN gameInit()
    global mainLevelManager
    global gunner
    global background
    global clock
    global keepGoing
    global runner1
    global rungroup
    global blockMinHeight
    global blockMaxHeight
    #GROUPS
    global blockGroup
    global cubeGroup
    global invGroup
    global shieldGroup
    global turretGroup
    global gunGroup
    global effectsGroup
    global bulletGroup
    global gunnerGroup
    global ammoInd
    global shieldsInd
    global speedInd
    global score
    global frame_count
    global displayFrame
    global target_rate
    global invInd
    #run loop
    while 1:
        #check to make sure our runner still exists
        if not rungroup.sprite:
            break
        #target_rate is the max possible frame rate
        clock.tick(target_rate)
        #check how long the user has beem playing and if they have\
        #been playing long enough make the speed faster
        ##LEVELING CODE[OLD]##
##            if frame_count == 800: #Level 2
##                scroller.dx += 1
##                debug("lvl2")
##            elif frame_count == 1200: #Level 3
##                scroller.dx += 1
##                debug("Go Faster")
##            elif frame_count == 3200:
##                scroller.dx += 1
##            elif frame_count == 6400:
##                scroller.dx += 1
        #tell the levelManager we have a new frame
        mainLevelManager.frame()
        #get events registered
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitGame()
                return
            #this is here so we can quit
            if event.type == pygame.KEYUP:
                if event.dict["key"] == K_ESCAPE:
                    pause()
                    return
                #toggle frame rate display w/ key f
                if event.dict["key"] == K_f:
                    if displayFrame:
                        displayFrame = False
                    else:
                        displayFrame = True
                if event.dict["key"] == K_p:
                    pause()
                    return
                if event.dict["key"] == K_SPACE:
                    rungroup.sprite.last_shot = 10
                else:
                    pass
        if rungroup.sprite: #if runner dies before our loop is over we don't
            #want an error
            pygame.sprite.groupcollide(gunnerGroup,blockGroup,True,True)
            pygame.sprite.groupcollide(gunnerGroup,cubeGroup,True,True)
            pygame.sprite.groupcollide(gunnerGroup,shieldGroup,True,True)
            pygame.sprite.groupcollide(gunnerGroup,invGroup,True,True)
            pygame.sprite.groupcollide(gunnerGroup,turretGroup,True,True)
            pygame.sprite.groupcollide(gunnerGroup,gunGroup,True,True)
            pygame.sprite.groupcollide(bulletGroup,blockGroup,False,True)
            pygame.sprite.groupcollide(bulletGroup,cubeGroup,False,True)
            pygame.sprite.groupcollide(bulletGroup,shieldGroup,False,True)
            pygame.sprite.groupcollide(bulletGroup,invGroup,False,True)
            pygame.sprite.groupcollide(bulletGroup,gunGroup,False,True)
            collided = pygame.sprite.spritecollide(rungroup.sprite,bulletGroup,True)
            for x in collided:
                rungroup.sprite.hit()
            #delete blocks that intercept cubes
            pygame.sprite.groupcollide(cubeGroup,blockGroup, False,True)
            collidedSprites = pygame.sprite.spritecollide(rungroup.sprite,cubeGroup,True)
            for x in collidedSprites:
                x.hit()
                score += x.score
            pygame.sprite.groupcollide(invGroup,blockGroup,True,False)
            pygame.sprite.groupcollide(invGroup,cubeGroup,False,True)
            collidedSprites = pygame.sprite.spritecollide(rungroup.sprite,invGroup,True)
            for x in collidedSprites:
                x.hit()
                rungroup.sprite.invinc()
                debug("Invincible")
            pygame.sprite.groupcollide(shieldGroup,blockGroup,True,False)
            pygame.sprite.groupcollide(shieldGroup,cubeGroup,False,True)
            collidedSprites = pygame.sprite.spritecollide(rungroup.sprite,shieldGroup,True)
            for x in collidedSprites:
                x.hit()
                if not rungroup.sprite.shield == 3:
                    rungroup.sprite.shield +=1
                debug("Shield")
            #check for colisions between runner and sprites in block group
            collidedSprites = pygame.sprite.spritecollideany(rungroup.sprite, blockGroup)
            if collidedSprites and _die:
                #reduce shields
                rungroup.sprite.hit()
            pygame.sprite.groupcollide(gunGroup,blockGroup,False,True)
            pygame.sprite.groupcollide(gunGroup,cubeGroup,False,True)
            pygame.sprite.groupcollide(gunGroup,shieldGroup,False,True)
            pygame.sprite.groupcollide(gunGroup,invGroup,False,True)
            collided = pygame.sprite.spritecollide(rungroup.sprite,gunGroup,True)
            for x in collided:
                rungroup.sprite.gun += 1
                rungroup.sprite.ammo = 10
        #increment distance
        score += 0.5
        #increment the number of frames
        frame_count += 1
        #choose distance font
        scoreFont = pygame.font.Font(None, 40)
        #get a surface with the font on it
        fontSurface = scoreFont.render("{0:n}".format(round(score)), True,\
                                          (255,255,255))
        #rect for the new font
        fontRect = pygame.rect.Rect(0,0,fontSurface.get_width()+5,\
                                    fontSurface.get_height())
        ##BEFORE DOING ANY NEW DRAWING, CLEAR ALL SPRITES
        rungroup.update()
        blockGroup.update()
        cubeGroup.update()
        effectsGroup.update()
        gunnerGroup.update()
        invGroup.update()
        gunGroup.update()
        turretGroup.update()
        shieldGroup.update()
        bulletGroup.update()
        invGroup.clear(screen,background)
        gunGroup.clear(screen,background)
        gunnerGroup.clear(screen,background)
        turretGroup.clear(screen,background)
        bulletGroup.clear(screen,background)
        shieldGroup.clear(screen,background)
        rungroup.clear(screen, background)
        blockGroup.clear(screen,background)
        cubeGroup.clear(screen, background)
        effectsGroup.clear(screen,background)
        #clear the previous font
        screen.blit(background,(0,0),fontRect)
        #draw the new font
        screen.blit(fontSurface,(0,0))
        #optional framerate display
        if displayFrame:
            frameFont = pygame.font.Font(None, 40)
            frameSurface = frameFont.render("{0:n}".format(round(\
                                                clock.get_fps())),\
                                               True, (255,255,255))
            #find the rect for the new surface
            x = 0
            y = screen.get_height()-frameSurface.get_height()
            frameRateRect = frameSurface.get_rect().move(x,y)
            frameRateRect.width += 10
            #clear previous font
            screen.blit(background, (0, y),\
                                     frameRateRect)
            #draw new font
            screen.blit(frameSurface, (0, y))
        #set the shields to appropriate value (runner's shield)
        if rungroup.sprite:
            shieldsInd.setShield(rungroup.sprite.shield)
        if rungroup.sprite:
            ammoInd.setAmmo(rungroup.sprite.ammo)
        #add in shield indicator display
        ammoIndicatorRect = fontRect
        ammoIndicatorRect.top += (fontSurface.get_height() + 15)#put 10 px below font
        ammoIndicatorRect = ammoIndicatorRect.move(200,7)
        shieldIndicatorRect = fontRect
        shieldIndicatorRect.top += (fontSurface.get_height() - 40)#put 10 px below font
        speedIndicatorRect = shieldIndicatorRect.move(0,20)
        invIndicatorRect = pygame.rect.Rect(0,0,105,15)
        dispRect = pygame.display.get_surface().get_rect()
        invIndicatorRect.centerx = dispRect.centerx
        invIndicatorRect.centery = dispRect.centery
        #draw all groups on screen
        screen.blit(background,ammoIndicatorRect, ammoIndicatorRect)
        screen.blit(background, shieldIndicatorRect,shieldIndicatorRect)
        screen.blit(background,speedIndicatorRect,speedIndicatorRect)
        if rungroup.sprite:
            if rungroup.sprite.inv:
                screen.blit(background,invIndicatorRect,invIndicatorRect)
                invInd.setPercentage((rungroup.sprite.invCount/float(800))*100)
        #check to make sure the cubes arent spawned over the blocks
        rungroup.draw(screen)
        gunGroup.draw(screen)
        gunnerGroup.draw(screen)
        turretGroup.draw(screen)
        bulletGroup.draw(screen)
        blockGroup.draw(screen)
        cubeGroup.draw(screen)
        invGroup.draw(screen)
        shieldGroup.draw(screen)
        screen.blit(ammoInd.getSurface(),ammoIndicatorRect)
        screen.blit(shieldsInd.getSurface(),shieldIndicatorRect) #blit new
        screen.blit(speedInd.getSurface(),speedIndicatorRect)
        if rungroup.sprite:
            if rungroup.sprite.inv:
                screen.blit(invInd.getSurface(),invIndicatorRect)
        effectsGroup.draw(screen)
        pygame.display.update()
    #end the game
    endMenu()

def pause():
    global selected
    global menu
    global clock
    global screen
    menu = cMenu(0, 0, 0, 10, 'vertical', 5, screen,
            [('Continue', 1, None),
            ('Quit',       2, None)])

    # Center the menu on the draw_surface (the entire screen here)
    menu.set_center(True, True)
    # Center the menu on the draw_surface (the entire screen here)
    menu.set_alignment('center', 'center')
    # Create the state variables (make them different so that the user event is
    # triggered at the start of the "while 1" loop so that the initial display
    # does not wait for user input)
    state = 0
    prev_state = 1
    # rect_list is the list of pygame.Rect's that will tell pygame where to
    # update the screen (there is no point in updating the entire screen if only
    # a small portion of it changed!)
    rect_list = []
    # The main while loop
    while 1:
        # Check if the state has changed, if it has, then post a user event to
        # the queue to force the menu to be shown at least once
        if prev_state != state:
            pygame.event.post(pygame.event.Event(EVENT_CHANGE_STATE, key = 0))
            prev_state = state
        # Get the next event
        e = pygame.event.wait()
        # Update the menu, based on which "state" we are in - When using the menu
        # in a more complex program, definitely make the states global variables
        # so that you can refer to them by a name
        if e.type == pygame.KEYDOWN or e.type == EVENT_CHANGE_STATE:
            if state == 0:
                rect_list, state = menu.update(e, state)
            elif state == 1:
                screen.blit(background,menu.contained_rect,menu.contained_rect)
                main()
                return
            else:
                debug("exit")
                quitGame()
                return
        # Quit if the user presses the exit button
        if e.type == pygame.QUIT:
            quitGame()
            return

        # Update the screen
        pygame.display.update(rect_list)
    
        
def endMenu():
    global selected
    global menu
    global clock
    global screen
    menu = cMenu(0, 0, 0, 10, 'vertical', 5, screen,
               [('Play Again', 1, None),
                ('Quit',       2, None)])

    # Center the menu on the draw_surface (the entire screen here)
    menu.set_center(True, True)
    # Center the menu on the draw_surface (the entire screen here)
    menu.set_alignment('center', 'center')
    # Create the state variables (make them different so that the user event is
    # triggered at the start of the "while 1" loop so that the initial display
    # does not wait for user input)
    state = 0
    prev_state = 1
    # rect_list is the list of pygame.Rect's that will tell pygame where to
    # update the screen (there is no point in updating the entire screen if only
    # a small portion of it changed!)
    rect_list = []
    font = pygame.font.Font(None, 30)
    fontSurface = font.render("Your score is: {0:n}".format(round(score)),True,(255,255,255))
    # The main while loop
    while 1:
      # Check if the state has changed, if it has, then post a user event to
      # the queue to force the menu to be shown at least once
      if prev_state != state:
         pygame.event.post(pygame.event.Event(EVENT_CHANGE_STATE, key = 0))
         prev_state = state
      # Get the next event
      e = pygame.event.wait()
      # Update the menu, based on which "state" we are in - When using the menu
      # in a more complex program, definitely make the states global variables
      # so that you can refer to them by a name
      if e.type == pygame.KEYDOWN or e.type == EVENT_CHANGE_STATE:
         if state == 0:
            rect_list, state = menu.update(e, state)
            rect_list.append(screen.blit(fontSurface,(screen.get_rect().centerx-(fontSurface.get_width()/2.), \
                             (screen.get_rect().centery)-60,0,0)))
         elif state == 1:
            debug("start game")
            state = 0
            gameInit()
            main()
            return
         else:
            debug("exit")
            quitGame()
            return

      # Quit if the user presses the exit button
      if e.type == pygame.QUIT:
         quitGame()
         return

      # Update the screen
      pygame.display.update(rect_list)

def mainMenu():
    global selected
    global menu
    global clock
    global screen
    global gameMode
    menu = cMenu(0, 0, 0, 10, 'vertical', 5, screen,
               [('Play Game', 1, None),
                ('High Scores',2,None),
                ('About',3,None),
                ('Quit',       4, None)])

    # Center the menu on the draw_surface (the entire screen here)
    menu.set_center(True, True)
    # Center the menu on the draw_surface (the entire screen here)
    menu.set_alignment('center', 'center')
    # Create the state variables (make them different so that the user event is
    # triggered at the start of the "while 1" loop so that the initial display
    # does not wait for user input)
    state = 0
    prev_state = 1
    # rect_list is the list of pygame.Rect's that will tell pygame where to
    # update the screen (there is no point in updating the entire screen if only
    # a small portion of it changed!)
    rect_list = []
    # The main while loop
    while 1:
      # Check if the state has changed, if it has, then post a user event to
      # the queue to force the menu to be shown at least once
      if prev_state != state:
         pygame.event.post(pygame.event.Event(EVENT_CHANGE_STATE, key = 0))
         prev_state = state
      # Get the next event
      e = pygame.event.wait()
      # Update the menu, based on which "state" we are in - When using the menu
      # in a more complex program, definitely make the states global variables
      # so that you can refer to them by a name
      if e.type == pygame.KEYDOWN or e.type == EVENT_CHANGE_STATE:
        if state == 0:
            rect_list, state = menu.update(e, state)
        elif state == 1:
            screen.fill((0,0,0))
            rect_list.append(screen.get_rect())
            menu = cMenu(0,0,20,10,'vertical',5,screen,
            [('Challenge',5,None),
            ('Endurance',6,None),
            ('Back',7,None)])
            menu.set_center(True, True)
            menu.set_alignment('center', 'center')
            state = 0
            prev_state = 1
        elif state == 4:
            debug("exit")
            quitGame()
            return
        elif state == 5:
            gameMode = 'challenge'
            gameInit()
            main()
            return
        elif state == 6:
            gameMode = 'endurance'
            gameInit()
            main()
            return
        elif state == 7:
            screen.fill((0,0,0))
            rect_list.append(screen.get_rect())
            menu = cMenu(0, 0, 20, 10, 'vertical', 5, screen,
                        [('Play Game', 1, None),
                         ('High Scores',2,None),
                         ('About',3,None),
                         ('Quit', 4, None)])
            # Center the menu on the draw_surface (the entire screen here)
            menu.set_center(True, True)
            # Center the menu on the draw_surface (the entire screen here)
            menu.set_alignment('center', 'center')
            state = 0
            prev_state = 1
      # Quit if the user presses the exit button
      if e.type == pygame.QUIT:
         quitGame()
         return

      # Update the screen
      pygame.display.update(rect_list)
      
def quitGame():
    pygame.display.quit()

if __name__ == "__main__":
    init()
    mainMenu()
