import pygame
from pygame.locals import*
#import key names
from pygame.key import *
import os
import platform
import random
import sys
import math
from kezmenu import KezMenu
if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
pygame.init()
screen = None
endMenu = None
_debug = True
selected = None
clock = pygame.time.Clock()
def init():
    #create screen
    global screen
    if(_debug):
        screen = pygame.display.set_mode((600, 820))
    else:
        screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

def option(x):
    global selected
    selected = x
    print "selected",x
    
def endMenu():
    global selected
    global endMenu
    global clock
    global screen
    selected = None
    endMenu = KezMenu(["Play Again", lambda: option(1)],
                      ["Quit", lambda: option(2)])
    endMenu.color = (255,255,255)
    endMenu.focus_color = (0,255,0)
    endMenu.enableEffect('enlarge-font-on-focus', font = None, size = 16, enlarge_factor = 2.)
    while True:
        time_passed = clock.tick() / 1000.
        events = pygame.event.get()
        endMenu.update(events,time_passed)
        screen.fill((0,0,0,0))
        endMenu.draw(screen)
        pygame.display.update()
        if selected is not None:
            break
        for x in events:
            if x.type == KEYDOWN:
                if x.dict["key"] == K_ESCAPE:
                    pygame.display.quit()
                    return
    pygame.display.quit()
        
init()
endMenu()
