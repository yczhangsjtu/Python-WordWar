import pyglet
from webcolors import name_to_rgb
from collections import namedtuple
from os.path import dirname, splitext, realpath, isfile, join, basename
from os import listdir
from socket import gethostname
from time import strftime, gmtime, clock
from datetime import datetime
from hashlib import md5
from random import seed, randint
import string
import codecs
import math
import re

################################################################################
###########GLOBAL CONSTANTS#####################################################
sync = False # Determine if the movements of the computer players are
             # synchronized
winw = 1300
winh = 715
colors = ["Red","Yellow","White","Green","Orange","Blue","Black","HotPink",\
          "GreenYellow","Purple","Olive","Cyan","DarkBlue","Goldenrod","Brown",\
          "Gray"]
menuButtonLabels = ["START","LOAD","QUIT"]
mainMenuButtonLabels = ["SAVE","LOAD","QUIT"]
controlButtonLabels = ["SET OUT","RECRUIT","SELECT ALL","UNSELECT ALL","CANCEL"]
nbuts = len(menuButtonLabels)
bh = winh / 10 #height of each button
bw = winw / 4
x0 = (winw - bw)/2
y0 = (winh - bh * nbuts)/2
citySize = 45
# Word Block size
wbh = winh / 35
wbw = winw / 8
# Recruit Panel size
rpw = winw
rph = winh / 30
rpx = (winw-rpw)/2
rpy = (winh-rph*2)/2
# Distance threshold
thresdst = 150 # Threshold distance for two cities being seen as neighbor
CURRENT_DIR = dirname(realpath(__file__))
NEWGAME_FILE = "new.txt"
DICT_FILE = "eword.txt"
SAVE_DIR = join(CURRENT_DIR,"save")
IMG_DIR = "img"
SOUND_DIR= "sound"
# Constants for the battle field
soldierSpeed = 3
soldierSize = 30
soldierWidth = 30
soldierHeight = 50
waitTime = 5.0
################################################################################
############CLASS MYBUTTON######################################################
def name_to_rgba(colorname):
    rgb = name_to_rgb(colorname)
    rgba = (rgb[0],rgb[1],rgb[2],255)
    return rgba

class mybutton():
    def __init__(self,X,Y,w,h,shape,color,text,txtcolor):
        self.x = X
        self.y = Y
        self.w = w
        self.h = h
        self.shape = shape
        self.color = color
        self.text = text
        self.txtcolor = txtcolor
        self.label = pyglet.text.Label(self.text,font_name='Arial',\
            font_size = min(self.w,self.h)/2,color=name_to_rgba(self.txtcolor),\
            x=self.x+self.w/2,y=self.y+self.h/2,\
            anchor_x='center',anchor_y='center',bold=True)

    def draw(self):
        if self.shape == "r":
            drawrectangle(self.x,self.y,self.x+self.w,self.y+self.h,\
                          name_to_rgb('black'), name_to_rgb(self.color))
        elif self.shape == "i":
            if self.color != None:
                pyglet.sprite.Sprite(self.color,x=self.x,y=self.y).draw()
        self.label.color=name_to_rgba(self.txtcolor)
        self.label.draw()

    # Return if the point x, y hit this button
    def click(self,x,y):
        return x >= self.x and x <= self.x+self.w\
            and y >= self.y and y <= self.y+self.h

class city():
    def __init__(self):
        self.shape = mybutton(0,0,citySize,citySize,"r",colors[0],"","Black")
        self.words = []
        self.c = 0
        # Buffer is used to temporily store the words selected to leave the
        # city
        self.buff = []

    def addWord(self,word):
        self.words.append(word)
    
    def draw(self):
        rank = len(self.words) / 20
        if rank >= len(cityImages): rank = len(cityImages)-1
        pyglet.sprite.Sprite(cityImages[rank],\
            x=self.shape.x,y=self.shape.y).draw()

    def drawflag(self):
        drawrectangle(self.shape.x,self.shape.y+citySize*4/5,\
                      self.shape.x+citySize/5,self.shape.y+citySize,\
                      name_to_rgb("Black"),\
                      name_to_rgb(self.shape.color))
        

class wordblock():
    def __init__(self,x,y,word):
        self.shape = mybutton(x,y,wbw,wbh,"i",wordblockImage[0],"","White")
        self.selected = False
        self.movedover = False
        self.word = word
        self.label = pyglet.text.Label(word,font_name='Arial',\
            font_size = min(wbw,wbh)/2,color=name_to_rgba("Black"),\
            x=x+wbw/2,y=y+wbh/2,anchor_x='center',anchor_y='center',bold=True)
    
    def draw(self):
        if self.movedover:
            self.shape.color = wordblockImage[2]
        elif self.selected:
            self.shape.color = wordblockImage[1]
        else:
            self.shape.color = None
        self.shape.draw()
        if self.movedover:
            self.label.draw()

class soldier():
    def __init__(self,word,color,s):
        self.word = word
        self.color = color
        self.pos = [0,0]
        self.targ = None
        self.state = "walk"
        self.imgIndex = 0
        self.walkImages = walkImages[s]
        self.fightImages = fightImages[s]
        self.dieImages = dieImages[randint(0,1)][s]
        self.over = False
    
    def moveon(self):
        if self.state == "walk":
            if self.targ:
                x,y,tx,ty = self.pos[0],self.pos[1],self.targ[0],self.targ[1]
                if (x-tx)*(x-tx)+(y-ty)*(y-ty) <= soldierSpeed*soldierSpeed:
                    self.pos[0] = self.targ[0]
                    self.pos[1] = self.targ[1]
                    self.imgIndex = 0
                else:
                    dist = math.sqrt((x-tx)*(x-tx)+(y-ty)*(y-ty))
                    dx = int((tx-x)/dist*soldierSpeed)
                    dy = int((ty-y)/dist*soldierSpeed)
                    self.pos[0] += dx
                    self.pos[1] += dy
                    self.imgIndex = (self.imgIndex+1)%len(self.walkImages)
        elif self.state == "fight":
            self.imgIndex = (self.imgIndex+1)%len(self.fightImages)
        elif self.state == "die":
            if self.imgIndex < len(self.dieImages) - 1:
                self.imgIndex += 1
            else:
                self.over = True

    def walk(self):
        self.state = "walk"
        self.imgIndex = 0
    
    def fight(self):
        self.state = "fight"
        self.imgIndex = 0
    
    def die(self):
        self.state = "die"
        self.imgIndex = 0

    def setTarget(self,targ):
        self.targ = targ
    
    def draw(self):
        s = soldierSize
        x,y= self.pos[0],self.pos[1]
        if self.state != "die":
            drawrectangle(x,y+soldierHeight+5,x+soldierWidth,y+soldierHeight,\
                          name_to_rgb("Black"),name_to_rgb(colors[self.color]))
        indx = 0
        if self.color == yourColor: indx = 1
        if self.state == "walk":
            pyglet.sprite.Sprite(self.walkImages[self.imgIndex],x=x,y=y).draw()
        elif self.state == "fight":
            pyglet.sprite.Sprite(self.fightImages[self.imgIndex],x=x,y=y).draw()
            if self.imgIndex == len(self.fightImages) - 1:
                hitSounds[randint(0,len(hitSounds)-1)].play()
        elif self.state == "die":
            pyglet.sprite.Sprite(self.dieImages[self.imgIndex],x=x,y=y).draw()
    
    def setpos(self,x,y):
        self.pos = [x,y]

class fightPair():
    def __init__(self, sdr1, sdr2):
        self.soldier1 = sdr1
        self.soldier2 = sdr2
        self.answerIndex = randint(0,3)
        self.options = []
        x,y = 0,winh
        self.x = x
        self.y = y
        mode = randint(0,1)
        if mode is 0: # E-to-C mode
            self.question = sdr2.word
            self.answer = wordDict[sdr2.word]
        else: # C-to-E mode
            self.question = wordDict[sdr2.word]
            self.answer = sdr2.word
        for i in range(4):
            if i is self.answerIndex:
                # This is the correct option
                if mode is 0:
                    self.options.append(wordDict[sdr2.word])
                else:
                    self.options.append(sdr2.word)
            else:
                # This is a wrong answer, generate a random word
                while True:
                    index = randint(0,len(wordList)-1)
                    if wordList[index] is not sdr2.word: break
                w = wordList[index]
                if mode is 0:
                    self.options.append(wordDict[w])
                else:
                    self.options.append(w)
        w,h = answerbw, answerbh
        self.buttons = [mybutton(x,y-(i+2)*h,w,h,"r","Yellow",self.options[i],\
                        "Black")\
                         for i in range(4)]

    def draw(self):
        x,y = self.x, self.y
        w,h = answerbw, answerbh 
        drawrectangle(x,y,x+w,y-h,name_to_rgb("Black"),name_to_rgb("Yellow"))
        pyglet.text.Label(self.question,anchor_x="left",anchor_y="bottom",\
                          x=x,y=y-h,font_name="Arial",font_size=h/2,\
                          color=(0,0,0,255)).draw()
        for b in self.buttons: b.draw()

    def click(self,x,y):
        for b in self.buttons:
            if b.click(x,y):
                if b.text is self.answer:
                    return "correct"
                else:
                    return "wrong"
        return None
        
################################################################################
###########GLOBAL OBJECTS#######################################################
window = pyglet.window.Window()
window.set_size(winw,winh)
################################################################################
###########SOUNDS###############################################################

def getSound(filename):
    return pyglet.media.load(join(SOUND_DIR,filename),streaming=False)

backgroundMusics = [getSound("BackMusic%d.mp3"%i) for i in range(2)]
hitSounds = [getSound("Hit%d.mp3"%i) for i in range(8)]

bgmp1 = pyglet.media.Player() 
bgmp1.queue(backgroundMusics[0])
bgmp2 = pyglet.media.Player() 
bgmp2.queue(backgroundMusics[1])
bgmp1.eos_action = bgmp1.EOS_LOOP
bgmp2.eos_action = bgmp2.EOS_LOOP
################################################################################
###########IMAGES###############################################################
def getPhotoImage(filename,w,h):
    img = pyglet.resource.image(join(IMG_DIR,filename))
    img.width = w
    img.height = h
    return img

cityImages = [getPhotoImage("city%d.gif"%i,\
                            citySize*(i+15)/15,citySize*(i+15)/15)\
                            for i in range(5)]
groundImage = getPhotoImage("ground.jpeg",winw,winh)
buttonImages = [getPhotoImage("button%d.gif"%i,bw,bh)\
                for i in range(3)]
wordblockImage = [getPhotoImage("wordblock%d.gif"%i,wbw,wbh) for i in range(3)]
documentButtonImages = [getPhotoImage("button%d.gif"%i,winw,bh)\
                        for i in range(3,5)]
arrowImages = [getPhotoImage("arrow%d.gif"%i,30,30)\
                for i in range(2)]
fireImages = [getPhotoImage("fire%d.gif"%i,citySize,citySize) for i in range(3)]
fireImages.extend([getPhotoImage("fire%d.gif"%i,citySize/2,citySize/2)
                   for i in range(3)])
SOLDIER_PATHS = [join(IMG_DIR,"soldier%d"%i) for i in range(2)]
WALK_PATHS = [join(p,"walk") for p in SOLDIER_PATHS]
FIGHT_PATHS= [join(p,"fight") for p in SOLDIER_PATHS]
DIE_PATHS= [[join(p,"die%i"%i) for p in SOLDIER_PATHS] for i in range(2)]
def getWalkImage(filename,i):
    img = pyglet.resource.image(join(WALK_PATHS[i],filename))
    img.width = soldierWidth
    img.height = soldierHeight
    return img
def getFightImage(filename,i):
    img = pyglet.resource.image(join(FIGHT_PATHS[i],filename))
    img.width = soldierWidth
    img.height = soldierHeight
    return img
def getDieImage(filename,i,j):
    img = pyglet.resource.image(join(DIE_PATHS[i][j],filename))
    img.width = soldierWidth
    img.height = soldierHeight
    return img 
    
walkImages = [[getWalkImage("%d.png"%i,j) \
               for i in range(len(listdir(WALK_PATHS[j])))]\
               for j in range(len(WALK_PATHS))]
fightImages = [[getFightImage("%d.png"%i,j) \
                for i in range(len(listdir(FIGHT_PATHS[j])))]\
                for j in range(len(FIGHT_PATHS))]
dieImages = [[[getDieImage("%d.png"%i,k,j) \
               for i in range(len(listdir(DIE_PATHS[k][j])))]\
               for j in range(len(DIE_PATHS[k]))] for k in range(2)]
################################################################################
###########STATE VARIABLES######################################################
gameStarted = False
currentCanvas = "menu"
showControlPanel = False
showRecruitPanel = False
showMainMenu = False
selectTargetCity = False
documentMode = ""
saveName = ""
recruitWord = ""
recruitAnswer = ""
message = ""
messagelife = 0
messages = []
marks = []
hangon = False
youAreAttacked = False
# Word List
deadWords = []
tmpDeadWords = []
# City List
cities = []
citySelect = None
srccity = None
dstcity = None
# Dictionary
wordDict = {}
wordList = []
# Game info
yourColor = 0
# Buttons
documentbuttons = []
menubuttons = []
menubuttons.append(mybutton(x0,y0+2*bh,bw,bh,"i",buttonImages[0],\
                   menuButtonLabels[0],"Black"))
menubuttons.append(mybutton(x0,y0+bh,  bw,bh,"i",buttonImages[0],\
                   menuButtonLabels[1],"Black"))
menubuttons.append(mybutton(x0,y0,     bw,bh,"i",buttonImages[0],\
                   menuButtonLabels[2],"Black"))
controlbuttons = []
ctrbw,ctrbh = winw/4, winh/12
controlbuttons.append(mybutton(0,y0+4*ctrbh,ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[0],"Black"))
controlbuttons.append(mybutton(0,y0+3*ctrbh,ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[1],"Black"))
controlbuttons.append(mybutton(0,y0+2*ctrbh,ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[2],"Black"))
controlbuttons.append(mybutton(0,y0+ctrbh,  ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[3],"Black"))
controlbuttons.append(mybutton(0,y0,        ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[4],"Black"))
mainMenuButtons = []
mainMenuButtons.append(mybutton(x0,y0+2*bh,bw,bh,"i",buttonImages[0],\
                       mainMenuButtonLabels[0],"Black"))
mainMenuButtons.append(mybutton(x0,y0+bh,  bw,bh,"i",buttonImages[0],\
                       mainMenuButtonLabels[1],"Black"))
mainMenuButtons.append(mybutton(x0,y0,     bw,bh,"i",buttonImages[0],\
                       mainMenuButtonLabels[2],"Black"))

savebutton = mybutton(winw-bw,0,bw,bh,"i",buttonImages[2],"Save","Black")
# Word Blocks
wordblocks = []
wordblockx0 = winw
wordblocky0 = winh
wordblockx1 = 0
wordblocky1 = 0
# For the battle field
attackers = []
defenders = []
yourTroop = []
enemyTroop = []
fightPairs = []
fx,fy = 10,7

answerbw = winw
answerbh = 20
# Get infomation of a city from the string read from the file
# Example
# city56.x = 123 would return {'index':56, 'cmd':'x', 'val':'123'}
# city56.addWord = hello would return {'index':56,'cmd':'addWord','val':'hello'}
# if the string is not correctly formatted, return None
CityInfo = namedtuple('CityInfo', 'stype index cmd val')
def getCityInfo(line):
    results = re.match(r'([a-zA-Z]+)(\d+)\.([a-zA-Z]+)\s*=\s*(\w+)',line)
    if(results==None): return None
    if(results.lastindex != 4): return None
    index = int(results.group(2))
    return CityInfo( stype = results.group(1), index = int(results.group(2)),\
                     cmd = results.group(3), val = results.group(4) )

def readCityInfo(infofile):
    global cities, yourColor, deadWords
    # Read information of cities
    fcity = open(infofile, "r")
    cities = []
    deadWords = []
    while True:
        s = fcity.readline()
        if s == "": break
        info = getCityInfo(s)
        if info is None: continue
        if info.stype == "city":
            if info.index < 0: continue
            while info.index >= len(cities):
                cities.append(city())
            if(info.cmd == "x"):
                cities[info.index].shape.x = int(info.val)
            elif(info.cmd == "y"):
                cities[info.index].shape.y = int(info.val)
            elif(info.cmd == "color"):
                if info.val == "yourColor":
                    yourColor = cities[info.index].c
                else:
                    cities[info.index].c = int(info.val)
                    cities[info.index].shape.color = colors[int(info.val)]
            elif(info.cmd == "addWord"):
                if info.val in wordDict:
                    cities[info.index].addWord(info.val)
        elif info.stype == "deadWords":
            if info.cmd == "addWord":
                deadWords.append(info.val)

    fcity.close()

def saveCityInfo(infofile):
    fcity = open(infofile, "w")
    yourColorSpecified = False
    for i in range(len(cities)):
        c = cities[i]
        fcity.write("city%d.x = %d\n"%(i,c.shape.x))
        fcity.write("city%d.y = %d\n"%(i,c.shape.y))
        fcity.write("city%d.color = %d\n"%(i,c.c))
        if yourColor == c.c and not yourColorSpecified:
            fcity.write("city%d.color = yourColor\n"% i)
            yourColorSpecified = True
        for w in c.words:
            fcity.write("city%d.addWord = %s\n"%(i,w))
    for w in deadWords:
        fcity.write("deadWords0.addWord = %s\n"%w)
    fcity.close()

def readDict():
    fdict = codecs.open(DICT_FILE,"r","utf-8")
    while True:
        s = fdict.readline()
        if(s == ""): break
        s = s.replace("\r","")
        s = s.replace("\n","")
        if(s.isalpha):
            m = fdict.readline()
            if(m == ""): break
            m = m.replace("\r","")
            m = m.replace("\n","")
            wordDict[s] = m
            wordList.append(s)
    fdict.close()

def init():
    readDict()
    seed()

def start():
    global gameStarted
    if(not gameStarted):
        startNewGame()
        drawselect()
    else:
        continueGame()

def continueGame():
    global currentCanvas
    currentCanvas = "main"

def startNewGame():
    global currentCanvas
    readCityInfo(NEWGAME_FILE)
    currentCanvas = "select"

def document(mode):
    global documentbuttons, currentCanvas, documentMode, saveName
    SAVE_FILES = [join(SAVE_DIR, fname) for fname in listdir(SAVE_DIR) \
                  if isfile(join(SAVE_DIR, fname)) and \
                  splitext(basename(fname))[1]==".sav"]
    documentbuttons = [mybutton(0,winh-(i+1)*bh,winw,bh,"i",\
                       documentButtonImages[0],\
                       splitext(basename(SAVE_FILES[i]))[0],"Black")\
                       for i in range(len(SAVE_FILES))]
    currentCanvas = "document"
    documentMode = mode
    saveName = ""
    drawdoc()

def quit():
    saveCityInfo(join(SAVE_DIR,"autosave.sav"))
    pyglet.app.exit()

def control(cmd, ct):
    global showControlPanel, wordblocks, selectTargetCity
    global srccity, currentCanvas, showRecruitPanel, recruitWord
    global wordblockx0, wordblockx1, wordblocky0, wordblocky1
    if cmd == "CANCEL":
        showControlPanel = False
        bgmp1.play()
        wordblocks = []
        wordblockx0 = winw
        wordblocky0 = winh
        wordblockx1 = 0
        wordblocky1 = 0
    elif cmd == "SELECT ALL":
        if ct and ct.c == yourColor:
            for w in wordblocks:
                w.selected = True
    elif cmd == "UNSELECT ALL":
        if ct and ct.c == yourColor:
            for w in wordblocks:
                w.selected = False
    elif cmd == "SET OUT":
        if ct and ct.c == yourColor:
            ct.words = []
            ct.buff = []
            for b in wordblocks:
                if b.selected:
                    ct.buff.append(b.word)
                else:
                    ct.words.append(b.word)
            if len(ct.buff) is not 0:
                bgmp1.play()
                srccity = ct
                selectTargetCity = True
                currentCanvas = "select"
                drawselect()
                citySelect = None
                showControlPanel = False
                wordblocks = []
                wordblockx0 = winw
                wordblocky0 = winh
                wordblockx1 = 0
                wordblocky1 = 0
    elif cmd == "RECRUIT":
        bgmp1.play()
        if len(deadWords) <= 0: return
        if ct and ct.c == yourColor:
            showControlPanel = False
            wordblocks = []
            wordblockx0 = winw
            wordblocky0 = winh
            wordblockx1 = 0
            wordblocky1 = 0
            word = deadWords[randint(0,len(deadWords)-1)]
            showRecruitPanel = True
            recruitWord = word
            recruitAnswer = ""

def areNeighbors(city1, city2):
    x1, y1 = city1.shape.x, city1.shape.y
    x2, y2 = city2.shape.x, city2.shape.y
    return (x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)<thresdst*thresdst

# Sum of the digits of a string s(as hex numbers)
def hexsum(s):
    sm = 0
    for c in s:
        sm += int(c,16)
    return sm

def popPair(dt):
    if len(fightPairs) > 0:
        F = fightPairs[0]
        S = randint(0,1)
        if S == 0:
            F.soldier1.walk()
            F.soldier2.die()
        else:
            F.soldier1.die()
            F.soldier2.walk()
        fightPairs.remove(F)
    if len(fightPairs) > 0:
        pyglet.clock.schedule_once(popPair,dt);

# control soldier by ai
def ai(s,targets):
    mindist,targ = None,None
    for e in targets:
        if e.state != "walk": continue
        x,y = s.pos[0], s.pos[1]
        ex,ey = e.pos[0], e.pos[1]
        dist = (ex-x)*(ex-x)+(ey-y)*(ey-y)
        if mindist is None:
            mindist = dist
            targ = e
        if mindist > dist:
            mindist = dist
            targ = e
    if targ is not None:
        s.setTarget(targ.pos)
        return s.moveon()
    else:
        return None

def battlemoveon(dt):
    global srccity, dstcity, attackers, defenders, currentCanvas
    global yourTroop, enemyTroop 
    if not currentCanvas == "battle": return
    # Check the victory of both sides
    gameOver = False
    if len(attackers) is 0: # The attackers fail
        gameOver = True
        dstcity.words = [d.word for d in defenders]
        dstcity.buff = []
        srccity.buff = []
    elif len(defenders) is 0: # The attackers succeed
        gameOver = True
        dstcity.words = [a.word for a in attackers]
        dstcity.buff = []
        srccity.buff = []
        dstcity.c = srccity.c
        dstcity.shape.color = colors[dstcity.c]
    if gameOver:
        attackers = []
        defenders = []
        currentCanvas = "main"
        bgmp2.pause()
        srccity = None
        dstcity = None
        return
    # Movement of your troop(follow the flag)
    for s in yourTroop:
        if s.over:
            deadWords.append(s.word)
            tmpDeadWords.append(s)
            yourTroop.remove(s)
        elif s.state == "walk":
            ai(s,enemyTroop)
        elif s.state == "fight" or s.state == "die":
            s.moveon()

    # Movement of the enemy troop
    for s in enemyTroop:
        if s.over:
            deadWords.append(s.word)
            tmpDeadWords.append(s)
            enemyTroop.remove(s)
        elif s.state=="walk":
            ai(s,yourTroop) # Enemies are controled by AI
        elif s.state=="fight" or s.state == "die":
            s.moveon()
    # Check the meeting of a pair of enemies
    for yt in yourTroop:
        for et in enemyTroop:
            if yt.state != "walk" or et.state != "walk": continue
            x1,y1,x2,y2 = yt.pos[0],yt.pos[1],et.pos[0],et.pos[1]
            dx,dy = x1-x2, y1-y2
            if dx*dx+dy*dy <= soldierSize*soldierSize/4:
                if len(fightPairs)==0:
                    pyglet.clock.schedule_once(popPair,waitTime)
                fightPairs.append(fightPair(yt,et))
                et.pos[0] = yt.pos[0]+soldierSize/2
                et.pos[1] = yt.pos[1]
                yt.fight()
                et.fight()

Message = namedtuple("Message","text loc")

def removeMessage(dt):
    global messages
    while True:
        nodelete = True
        for m in messages:
            if m[1] <= 0:
                messages.remove(m)
                nodelete = False
                break
        if nodelete:
            break

def putMessage(msg,location=None):
    global message, messages, messagelife
    # location is None means this is a message generated by the player
    if location is None:
        message = msg
        messagelife = 5.0
    else: # else, this is from others
        m = [Message(text=msg,loc=location),3.0]
        messages.append(m)

def removeMark(dt):
    global marks
    while True:
        nodelete = True
        for m in marks:
            if m.life <= 0:
                marks.remove(m)
                nodelete = False
                break
        if nodelete:
            break
    

markData = namedtuple("markData","Type Img index life")
def putMark(tp,data):
    if not currentCanvas == "main": return
    global marks
    img = None
    if tp == "arrow" or tp == "attack":
        x0,y0,x1,y1 = data[0],data[1],data[2],data[3]
        # Sin value of the arrow
        cs = (x1-x0)/math.sqrt((x1-x0)*(x1-x0)+(y1-y0)*(y1-y0))
        ag = math.acos(cs)
        if y1 > y0: ag = 2*math.pi-ag
        sz = int(math.sqrt((y1-y0)*(y1-y0)+(x1-x0)*(x1-x0)))-citySize
        if sz < 0: sz = 15
        indx = 1
        if tp == "attack": indx = 0
        arrowImages[indx].width = sz
        arrowImages[indx].height = 15
        spt = pyglet.sprite.Sprite(arrowImages[indx])
        spt.x = (x0+x1)/2
        spt.y = (y0+y1)/2
        spt.rotation = ag*180/math.pi
        img = [spt]
        mt = markData(Type = tp, Img=img, index = 0, life = 1.0)
        marks.append(mt)
    elif tp == "fire":
        x0,y0 = data[0],data[1]
        img = [pyglet.sprite.Sprite(f,x=x0,y=y0) for f in fireImages]
        mt = markData(Type = tp, Img=img, index=0, life = 1.0)
        marks.append(mt)


NeighborInfo = namedtuple("NeighborInfo","Neighbors Alliance Enemies")
# The array of neighbors of a city
def neighbors(c):
    ns = []
    al = []
    en = []
    x,y = c.shape.x,c.shape.y
    for n in cities:
        x1,y1 = n.shape.x,n.shape.y
        if (x-x1)*(x-x1)+(y-y1)*(y-y1) < thresdst*thresdst and n is not c:
            ns.append(n)
            if n.c == c.c: al.append(n)
            else: en.append(n)
    return NeighborInfo(Neighbors=ns, Alliance=al, Enemies=en)

# Return an array of cities with color c
def citiesWithColor(c):
    return [ct for ct in cities if ct.c==c]
# On entering main scene, this function is executed repeatedly, controlling
# the enemies
def mainfunc(dt):
    global attackers, defenders, srccity, dstcity, flag, currentCanvas, hangon
    global youAreAttacked, showRecruitPanel, yourTroop, enemyTroop
    if currentCanvas == "main" and not hangon and not showRecruitPanel\
       and not showControlPanel and not showMainMenu:
        # Keep an array for all the colors to record whether the contry has 
        # taken actions
        moved = False # Used only in nonsynchronized mode
        for cl in range(len(colors)):
            if not sync:
                if moved: break
                else:
                    cl = randint(0,len(colors)-1)
                    moved = True
            if cl == yourColor: continue
            cts = citiesWithColor(cl)
            if len(cts) == 0: continue
            c = cts[randint(0,len(cts)-1)]
            # Recruit
            if len(deadWords) > 0 and not showRecruitPanel:
                r = randint(0,4) # recruit with specific probability
                if r == 0:
                    c.words.append(deadWords.pop(randint(0,len(deadWords)-1)))
                    putMessage("Recruited %s"%c.words[-1], \
                               [c.shape.x,c.shape.y])
                    continue
            # Move Troop
            # Pick one of it's neighbors, if it's of the same color, move
            # with a probability p, where p = n/(m+n), where m and n are
            # number of enemy neighbors of the two cities respectively.
            # If it's an enemy, launch a war with probability
            # p = m/30(m+n) where m is the number of soldiers(words) of
            # this city and n is that of enemies
            if len(c.words) > 1:
                ns = neighbors(c)
                # It has neighrbos
                if(len(ns.Neighbors)>0):
                    nb = ns.Neighbors[randint(0,len(ns.Neighbors)-1)]
                    if nb in ns.Alliance:
                        m = len(ns.Enemies)
                        n = len(neighbors(nb).Enemies)
                        if m == 0 and n == 0:
                            m = 1
                            n = 1
                        p = randint(1,m+n)
                        # move with probability n/(m+n)
                        if p <= n:
                            # Move one word to the destination
                            i = randint(0,len(c.words)-1)
                            nb.words.append(c.words.pop(i))
                            x0 = c.shape.x+citySize/2
                            x1 = nb.shape.x+citySize/2
                            y0 = c.shape.y+citySize/2
                            y1 = nb.shape.y+citySize/2
                            putMark("arrow",[x0,y0,x1,y1])
                            continue
                    elif nb in ns.Enemies:
                        m = len(c.words)
                        n = len(nb.words)
                        p = randint(1,30*(m+n))
                        if p <= m:
                            # launch a war
                            srccity,dstcity = c,nb
                            # Move some of the words in the city out for war
                            nsoldiers = randint(0,len(srccity.words))
                            while len(srccity.words) > 1 and nsoldiers > 0:
                                srccity.buff.append(srccity.words.pop(0))
                                nsoldiers -= 1
                            if len(srccity.buff) == 0: # No army to move out
                                srccity,dstcity = None,None
                                continue
                            attackers = [soldier(w,srccity.c,1)
                                         for w in srccity.buff]
                            defenders = [soldier(w,dstcity.c,0)
                                         for w in dstcity.words]
                            # If it's war between computers, each win with
                            # probability m/(m+n) or n/(m+n) respectively
                            # where m and n are the number of soldiers
                            # the winner lose half of the soldiers and the
                            # loser die out
                            # If the target city has no defence, just take
                            # it no matter whether it's yours or computer's
                            if not nb.c == yourColor or n == 0:
                                p = randint(1,m+n)
                                if p <= m: # Attacker win
                                    nb.c = c.c
                                    nb.shape.color = colors[nb.c]
                                    nb.words = [s.word for s in attackers]
                                    deadWords.extend([s.word for s in defenders])
                                else: # Defender win
                                    deadWords.extend([s.word for s in attackers])

                                nb.buff = []
                                c.buff = []
                                attackers = []
                                defenders = []
                                srccity, dstcity = None, None
                                x0 = c.shape.x+citySize/2
                                x1 = nb.shape.x+citySize/2
                                y0 = c.shape.y+citySize/2
                                y1 = nb.shape.y+citySize/2
                                putMark("attack",[x0,y0,x1,y1])
                                putMark("fire",[x1,y1])
                            # Or the computer is attacking you, enter battle
                            # field
                            else:
                                for s in attackers:
                                # Attackers originally distribute in the below
                                # half of the battle field
                                    s.setpos(randint(0,winw),\
                                             randint(winh*3/4,winh))
                                for s in defenders:
                                    s.setpos(randint(0,winw),\
                                             randint(0,winh/4))
                                flag = [winw/2,winh/2]
                                yourTroop = defenders
                                enemyTroop = attackers
                                hangon = True
                                youAreAttacked = True
                                putMessage("Your are being attacked!")
                                x0 = c.shape.x+citySize/2
                                x1 = nb.shape.x+citySize/2
                                y0 = c.shape.y+citySize/2
                                y1 = nb.shape.y+citySize/2
                                putMark("attack",[x0,y0,x1,y1])
                                putMark("fire",[x1,y1])
                                break

# Control the move of animations
# markData = namedtuple("markData","Type Img index life")
def animate(dt):
    global marks, message, messages, messagelife
    if currentCanvas == "main":
        for i in range(len(marks)):
            m = markData( Type = marks[i].Type,\
                          Img = marks[i].Img, life = marks[i].life - dt,\
                          index = (marks[i].index+1)%len(marks[i].Img))
            marks[i] = m
    if currentCanvas == "main" or currentCanvas == "battle":
        if messagelife <=0:
            message = ""
        else:
            messagelife -= dt
        for i in range(len(messages)):
            if messages[i][1] > 0:
                messages[i][1] -= dt
        

################################################################################
################EVENT HANDLE FUNCTIONS##########################################

def menuButtonClick(command):
    if(command == "START"):
        start()
    elif(command == "LOAD"):
        document("load")
    elif(command == "QUIT"):
        quit()

def menuLeftClick(x,y):
    for i in range(nbuts):
        if(menubuttons[i].click(x,y)):
            menuButtonClick(menubuttons[i].text) # Pass the text of the button
    
def documentMouseMove(x,y):
    for b in documentbuttons:
        if(b.click(x,y)):
            b.color = documentButtonImages[1]
        else:
            b.color = documentButtonImages[0]

def documentLeftClick(x,y):
    global currentCanvas, gameStarted, showControlPanel, showMainMenu, saveName
    global srccity, dstcity
    if documentMode == "load":
        for b in documentbuttons:
            if b.click(x,y):
                readCityInfo(join(SAVE_DIR,b.text+".sav"))
                currentCanvas = "main"
                gameStarted = True
                showControlPanel = False
                showMainMenu = False
                srccity,dstcity = None,None
    elif documentMode == "save":
        for b in documentbuttons:
            if b.click(x,y):
                saveName = b.text
        if savebutton.click(x,y):
            saveCityInfo(join(SAVE_DIR,saveName+".sav"))
            currentCanvas = "main"

def documentRightClick(x,y):
    global currentCanvas
    if gameStarted:
        currentCanvas = "main"
    else:
        """
        cv_document.pack_forget()
        cv_menu.pack()
        """
        currentCanvas = "menu"

def keyPress(char):
    global saveName, recruitAnswer
    if currentCanvas == "document" and documentMode == "save":
        if char.isalpha():
            saveName += event.char
    elif currentCanvas == "main":
        if showRecruitPanel:
            if char.isalpha():
                recruitAnswer += char
    elif currentCanvas == "battle":
        pass

def backSpacePress():
    global saveName, recruitAnswer
    if currentCanvas == "document" and documentMode == "save":
        saveName = saveName[:-1]
    elif currentCanvas == "main":
        if showRecruitPanel:
            recruitAnswer = recruitAnswer[:-1]

def returnPress():
    global saveName, currentCanvas, showRecruitPanel, recruitWord, recruitAnswer
    global citySelect
    if currentCanvas == "document" and documentMode == "save":
        saveCityInfo(join(SAVE_DIR,saveName+".sav"))
        currentCanvas = "main"
    elif currentCanvas == "main":
        if showRecruitPanel:
            if recruitAnswer == recruitWord:
                putMessage("Correct!")
                if citySelect and citySelect.c == yourColor:
                    citySelect.words.append(recruitWord)
                    deadWords.remove(recruitWord)
                    if len(deadWords) > 0:
                        word = deadWords[randint(0,len(deadWords)-1)]
                        recruitWord = word
                        recruitAnswer = ""
                    else:
                        showRecruitPanel = False
                        recruitWord = ""
                        recruitAnswer = ""
                        citySelect = None
            else:
                putMessage("Wrong, the answer is %s"%recruitWord)
                showRecruitPanel = False
                recruitWord = ""
                recruitAnswer = ""
                citySelect = None

def selectLeftClick(x,y):
    global currentCanvas, yourColor, selectTargetCity, dstcity, gameStarted
    global attackers, defenders, yourTroop, enemyTroop, tmpDeadWords
    # selectTargetCity is set to True when the player is moving troop from one
    # city to another. It is False when start a new game and choose your own
    # color
    if not selectTargetCity:
        if(citySelect != None):
            gameStarted = True
            yourColor = citySelect.c
            currentCanvas = "main"
    else:
        if(citySelect != None):
            # The target city should be within a threshold distance
            if areNeighbors(citySelect,srccity) and citySelect != srccity:
                newscene = None
                dstcity = citySelect
                if dstcity.c is srccity.c: # The destination is your own city
                    for w in srccity.buff:
                        dstcity.words.append(w)
                    srccity.buff = []
                    newscene = "main"
                else: # The destination belongs to an enemy
                    if len(dstcity.words) is 0: # This is an empty city
                        for w in srccity.buff:
                            dstcity.words.append(w)
                        srccity.buff = []
                        dstcity.c = srccity.c
                        newscene = "main"
                    else: # There would be a battle
                        attackers=[soldier(w,srccity.c,0) for w in srccity.buff]
                        defenders=[soldier(w,dstcity.c,1) for w in dstcity.words]
                        for s in attackers:
                            # Attackers originally distribute in the below
                            # half of the battle field
                            s.setpos(randint(0,winw),\
                                     randint(winh*3/4,winh))
                        for s in defenders:
                            s.setpos(randint(0,winw),\
                                     randint(0,winh/4))
                        newscene = "battle"
                        yourTroop = attackers
                        enemyTroop = defenders
                if newscene == "main":
                    currentCanvas = "main"
                else:
                    tmpDeadWords = []
                    currentCanvas = "battle"
                    bgmp2.play()
                    bgmp1.pause()

def selectRightClick(x,y):
    global currentCanvas,srccity
    if not selectTargetCity:
        currentCanvas = "menu"
        drawmenu()
    else:
        currentCanvas = "main"
        for c in srccity.buff:
            srccity.words.append(c)
        srccity.buff = []
        srccity = None

def selectMouseMove(x,y):
    global citySelect
    citySelect = None
    for c in cities:
        if(c.shape.click(x,y)):
            citySelect = c

def mainLeftClick(x,y):
    global showControlPanel,wordblocks,showMainMenu,currentCanvas
    global youAreAttacked, hangon, srccity, dstcity, tmpDeadWords
    global wordblockx0, wordblockx1, wordblocky0, wordblocky1
    if hangon:
        if youAreAttacked:
            tmpDeadWords = []
            currentCanvas = "battle"
            bgmp2.play()
            bgmp1.pause()
        hangon = False
        youAreAttacked = False
    elif showControlPanel:
        # If the control panel is visible while no city is selected
        # just turn off the control panel
        if not citySelect:
            showControlPanel = False
            return
        for b in controlbuttons:
            if(b.click(x,y)):
                control(b.text, citySelect)
            if citySelect.c is yourColor:
                # If this city is yours, the words would be shown
                # Click on them to select or unselect
                for w in wordblocks:
                    if w.shape.click(x,y):
                        w.selected = not w.selected
    elif showMainMenu:
        for b in mainMenuButtons:
            if b.click(x,y):
                if b.text == "SAVE":
                    document("save")
                elif b.text == "LOAD":
                    document("load")
                elif b.text == "QUIT":
                    quit()
    elif showRecruitPanel:
        pass
    else:
        if citySelect:
            #bgmp1.pause()
            showControlPanel = True
            for b in controlbuttons:
                if not b.text == "CANCEL" and citySelect.c is not yourColor:
                    b.txtcolor = "Gray"
                else:
                    b.txtcolor = "Black"
            else:
                # The city is yours, and the words in it would be shown
                # The words would be arranged in a matrix, whose size is
                # determined by the number of words, n
                n = len(citySelect.words)
                if n == 0: return
                # Number of columns and number of rows
                nc = int(math.ceil(math.sqrt(n/5.0)))
                nr = nc * 5
                # Left-Down corner of this matrix
                x0,y0 = ctrbw,winh/2-nr*wbh/2
                # Add the word blocks into the array
                for i in range(n):
                    x,y = x0+int(wbw*math.floor(i/nr)),y0+int(wbh*(i%nr))
                    wordblocks.append(wordblock(x,y,citySelect.words[i]))
                    if x < wordblockx0: wordblockx0 = x
                    if y < wordblocky0: wordblocky0 = y
                    if x+wbw > wordblockx1: wordblockx1 = x+wbw
                    if y+wbh > wordblocky1: wordblocky1 = y+wbh

def mainRightClick(x,y):
    global showMainMenu, showControlPanel, citySelect, srccity, wordblocks
    global showRecruitPanel, hangon, youAreAttacked
    global wordblockx0, wordblockx1, wordblocky0, wordblocky1
    if hangon: return
    if not showControlPanel and not showRecruitPanel:
        showMainMenu = not showMainMenu
    if(showControlPanel):
        showControlPanel = False
        citySelect = None
        srccity = None
        wordblocks = []
        wordblockx0 = winw
        wordblocky0 = winh
        wordblockx1 = 0
        wordblocky1 = 0
    if showRecruitPanel:
        showRecruitPanel = False
        recruitWord = ""
        recruitAnswer = ""
    bgmp1.play()

def mainMouseMove(x,y):
    global citySelect, controlButtonSelect, showMainMenu, wordblocks
    # If control panel is visible, just if any button is selected
    if showControlPanel:
        controlButtonSelect = None
        for b in controlbuttons:
            if b.click(x,y):
                controlButtonSelect = b
                b.color = buttonImages[2]
            else:
                b.color = buttonImages[1]
        if citySelect is not None and citySelect.c is yourColor:
            # In this case, the word panel is shown
            # Move the mouse over a word, the background is changed
            # and the Chinese meaning is shown
            for w in wordblocks:
                if w.shape.click(x,y):
                    w.movedover = True
                else:
                    w.movedover = False
    elif showMainMenu:
        pass
    elif showRecruitPanel:
        pass
    else:
        citySelect = None
        for c in cities:
            if(c.shape.click(x,y)):
                citySelect = c
                break

def mainMouseLeftMove(x,y):
    global showControlPanel, wordblocks 
    if showControlPanel:
        # If the control panel is visible while no city is selected
        # just turn off the control panel
        if not citySelect:
            showControlPanel = False
            return
        if citySelect.c is yourColor:
            # If this city is yours, the words would be shown
            # Click on them to select or unselect
            for w in wordblocks:
                if w.shape.click(x,y):
                    w.selected = True
                    w.movedover = True
                else:
                    w.movedover = False

def battleLeftClick(x,y):
    global currentCanvas, fightPairs, deadWords
    F,S = None, None
    if len(fightPairs) > 0:
        F = fightPairs[0]
        S = F.click(x,y)
    if F is not None:
        if S == "correct":
            F.soldier1.walk()
            F.soldier2.die()
            fightPairs.remove(F)
            msg = S + "    " + F.soldier2.word + " " + wordDict[F.soldier2.word]
            putMessage(msg)
            pyglet.clock.unschedule(popPair)
            if len(fightPairs) > 0:
                pyglet.clock.schedule_once(popPair,waitTime)
        elif S == "wrong":
            F.soldier1.die()
            F.soldier2.walk()
            fightPairs.remove(F)
            msg = S + "    " + F.soldier2.word + " " + wordDict[F.soldier2.word]
            putMessage(msg)
            pyglet.clock.unschedule(popPair)
            if len(fightPairs) > 0:
                pyglet.clock.schedule_once(popPair,waitTime)
################################################################################
############DRAWING FUNCTIONS###################################################

def drawrectangle(x0,y0,x1,y1,outline,fill):
    if outline:
        r,g,b=outline[0],outline[1],outline[2]
        pyglet.graphics.draw(4,pyglet.gl.GL_LINE_LOOP,\
            ('v2i',(x0,y0,x1,y0,x1,y1,x0,y1)),\
            ('c3B',(r,g,b,r,g,b,r,g,b,r,g,b))\
        )
    if fill:
        r,g,b=fill[0],fill[1],fill[2]
        pyglet.graphics.draw(4,pyglet.gl.GL_QUADS,\
            ('v2i',(x0,y0,x1,y0,x1,y1,x0,y1)),\
            ('c3B',(r,g,b,r,g,b,r,g,b,r,g,b))\
        )

def drawmenu():
    if(currentCanvas != "menu"): return
    pyglet.sprite.Sprite(groundImage,x=0,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=0,y=winh/2).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=winh/2).draw()
    for b in menubuttons: 
        b.draw()

def drawselect():
    global citySelect
    if(currentCanvas != "select"): return
    pyglet.sprite.Sprite(groundImage,x=0,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=0,y=winh/2).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=winh/2).draw()
    for c in cities:
        c.draw()
    for c in cities:
        c.drawflag()
    pyglet.text.Label("Select a city.",anchor_x="left",anchor_y="bottom",\
                      x=0,y=winh-20,color=(255,255,255,255),font_name="Arial",\
                      font_size=15).draw()
    if citySelect:
        x,y,w = citySelect.shape.x, citySelect.shape.y, citySize
        W = w * 6/5
        x -= (W-w)/2
        y -= (W-w)/2
        drawrectangle(x,y,x+W,y+W,[0,0,0],None)
    # If it is in selectTargetCity mode, highlight the neighbors of the source
    # city by thick outlines
    if selectTargetCity:
        """
        cv_selectCity.delete('target')
        """
        for c in cities:
            if areNeighbors(c,srccity) and c is not srccity:
                x,y,w = c.shape.x, c.shape.y, citySize
                W = w * 6/5
                x -= (W-w)/2
                y -= (W-w)/2
                drawrectangle(x,y,x+W,y+W,name_to_rgb('red'),None)

def drawmain():
    global citySelect,showControlPanel
    global wordblockx0, wordblockx1, wordblocky0, wordblocky1
    if(currentCanvas != "main"): return
    pyglet.sprite.Sprite(groundImage,x=0,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=0,y=winh/2).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=winh/2).draw()
    for c in cities:
        c.draw()
    for c in cities:
        c.drawflag()
    if(citySelect != None):
        x = citySelect.shape.x
        y = citySelect.shape.y
        w = citySize
        W = w * 6/5
        x -= (W-w)/2
        y -= (W-w)/2
        drawrectangle(x,y,x+W,y+W,[0,0,0],None)
    
    # Messages
    if not message == "":
        x,y = 0,0
        drawrectangle(x,y,winw,wbh,name_to_rgb('black'),name_to_rgb('Orange'))
        pyglet.text.Label(message,anchor_x="left",anchor_y="bottom",\
                          font_name="Arial",font_size=wbh/2,x=x,y=y,\
                          color=(0,0,0,255)).draw()
    for m in messages:
        pyglet.text.Label(m[0].text,anchor_x="center",anchor_y="center",\
                          font_name="Arial",font_size=wbh/2,\
                          x=m[0].loc[0],y=m[0].loc[1],\
                          color=(255,255,255,255)).draw()
    # Marks
    for m in marks:
        if m.Type  == "arrow" or m.Type == "attack" or m.Type=="fire":
            i = m.index
            m.Img[i].draw()

    # City info panel
    if(citySelect):
        x,y,w,h = 0,winh,winw/4,winh/20
        if(citySelect.shape.x < winw/2): x = winw - w
        if(citySelect.c == yourColor):
            relation = "Yourself"
        else:
            relation = "Enemy"
        infos = ["Relation: "+ relation,\
                 "Color: "+str(citySelect.shape.color),\
                 "Number Of Words: "+str(len(citySelect.words))]
        for i in range(len(infos)):
            drawrectangle(x,y-i*h,x+w,y-(i+1)*h,\
                          name_to_rgb('black'),name_to_rgb('yellow'))
            pyglet.text.Label(infos[i],anchor_x="left",anchor_y="top",\
                              font_name="Arial",font_size=h/2,\
                              x=x,y=y-i*h, color=(0,0,0,255)).draw()
    # Control panel
    if showControlPanel:
        for b in controlbuttons:
            b.draw()
        # Word panel
        if citySelect.c == yourColor:
            # Draw the back rectangle
            drawrectangle(wordblockx0,wordblocky0,wordblockx1,wordblocky1,\
                          name_to_rgb("Black"),name_to_rgb("Yellow"))
            blockMovedOver = None
            for w in wordblocks:
                w.draw()
                if w.movedover:
                    blockMovedOver = w
            # If moved over by mouse, show the Chinese meaning
            if blockMovedOver is not None:
                bx,by = 0,0
                drawrectangle(bx,by,winw,wbh,name_to_rgb('black'),\
                              name_to_rgb('Orange'))
                pyglet.text.Label(wordDict[blockMovedOver.word],\
                                  anchor_x="left",anchor_y="bottom",\
                                  font_name="Arial",font_size=wbh/2,\
                                  x=bx,y=by,color=(0,0,0,255)).draw()

    # Recruit Panel
    if showRecruitPanel:
        drawrectangle(rpx,rpy,rpx+rpw,rpy+rph*2,name_to_rgb('black'),\
                      name_to_rgb('Orange'))
        pyglet.text.Label(wordDict[recruitWord],\
                          anchor_x="left",anchor_y="bottom",\
                          font_name="Arial",font_size=rph/2,\
                          x=rpx,y=rpy+rph,color=(0,0,0,255)).draw()
        pyglet.text.Label(recruitAnswer,anchor_x="left",anchor_y="bottom",\
                          font_name="Arial",font_size=rph/2,\
                          x=rpx,y=rpy,color=(0,0,0,255)).draw()
    
    # Menu
    if showMainMenu:
        for b in mainMenuButtons:
            b.draw()

def drawdoc():
    if currentCanvas != "document": return
    pyglet.sprite.Sprite(groundImage,x=0,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=0,y=winh/2).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=winh/2).draw()
    for b in documentbuttons:
        b.draw()
    if documentMode == "save":
        pyglet.sprite.Sprite(documentButtonImages[0],x=0,y=0).draw()
        pyglet.text.Label(saveName, anchor_x="left",anchor_y="bottom",\
                          font_name="Arial",font_size=bh/2, x=0, y=0).draw()
        savebutton.draw()
        
def drawbattle():
    if currentCanvas != "battle": return
    pyglet.sprite.Sprite(groundImage,x=0,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=0).draw()
    pyglet.sprite.Sprite(groundImage,x=0,y=winh/2).draw()
    pyglet.sprite.Sprite(groundImage,x=winw/2,y=winh/2).draw()

    for s in tmpDeadWords:
        s.draw()
    for s in attackers:
        s.draw()
    for s in defenders:
        s.draw()
    # Draw the questions
    if len(fightPairs) > 0:
        fightPairs[0].draw()
    # Draw the message
    if not message == "":
        x,y = 0,0
        drawrectangle(x,y,winw,wbh,name_to_rgb('black'),\
                      name_to_rgb('Orange'))
        pyglet.text.Label(message, anchor_x="left",anchor_y="bottom",\
                          font_name="Arial",font_size=wbh/2,x=x,y=y,\
                          color=(0,0,0,255)).draw()

init()

@window.event
def on_draw():
    window.clear()
    if currentCanvas == "menu":
        drawmenu()
    elif currentCanvas == "document":
        drawdoc()
    elif currentCanvas == "main":
        drawmain()
    elif currentCanvas == "select":
        drawselect()
    elif currentCanvas == "battle":
        drawbattle()

@window.event
def on_mouse_press(x,y,button,modifiers):
    if button == pyglet.window.mouse.LEFT:
        if currentCanvas == "menu":
            menuLeftClick(x,y)
        elif currentCanvas == "document":
            documentLeftClick(x,y)
        elif currentCanvas == "select":
            selectLeftClick(x,y)
        elif currentCanvas == "main":
            mainLeftClick(x,y)
        elif currentCanvas == "battle":
            battleLeftClick(x,y)
    if button == pyglet.window.mouse.RIGHT:
        if currentCanvas == "main":
            mainRightClick(x,y)
        elif currentCanvas == "select":
            selectRightClick(x,y)
        elif currentCanvas == "document":
            documentRightClick(x,y)

@window.event
def on_mouse_motion(x,y,dx,dy):
    if currentCanvas == "document":
        documentMouseMove(x,y)
    if currentCanvas == "select":
        selectMouseMove(x,y)
    if currentCanvas == "main":
        mainMouseMove(x,y)

@window.event
def on_mouse_drag(x,y,dx,dy,buttons,modifiers):
    if buttons == pyglet.window.mouse.LEFT:
        if currentCanvas == "main":
            mainMouseLeftMove(x,y)

@window.event
def on_key_press(symbol,modifiers):
    if symbol == pyglet.window.key.RETURN:
        returnPress()
    elif (symbol >= pyglet.window.key.A and symbol <= pyglet.window.key.Z):
        if modifiers & pyglet.window.key.MOD_SHIFT:
            keyPress(chr(symbol-32))
        else:
            keyPress(chr(symbol))
    elif symbol == pyglet.window.key.BACKSPACE:
        backSpacePress()

pyglet.clock.schedule_interval(mainfunc,0.1)
pyglet.clock.schedule_interval(animate,0.2)
pyglet.clock.schedule_interval(removeMark,0.1)
pyglet.clock.schedule_interval(removeMessage,0.1)
pyglet.clock.schedule_interval(battlemoveon,0.1)
bgmp1.play()
pyglet.app.run()
