from Tkinter import *
from collections import namedtuple
from os.path import dirname, splitext, realpath, isfile, join, basename
from os import listdir
from socket import gethostname
from time import strftime, gmtime, clock
from datetime import datetime
from hashlib import md5
from random import seed, randint
from PIL import Image, ImageTk
import string
import codecs
import math
import re

################################################################################
###########GLOBAL CONSTANTS#####################################################
sync = False # Determine if the movements of the computer players are
             # synchronized
useflag = False
winw = 1300
winh = 750
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
citySize = 55
# Word Block size
wbh = winh / 35
wbw = winw / 8
# Recruit Panel size
rpw = winw / 2
rph = winh / 30
rpx = (winw-rpw)/2
rpy = (winh-rph*2)/2
# Distance threshold
thresdst = 150 # Threshold distance for two cities being seen as neighbor
CURRENT_DIR = dirname(realpath(__file__))
NEWGAME_FILE = join(CURRENT_DIR, "new.txt")
DICT_FILE = join(CURRENT_DIR, "word.txt")
SAVE_DIR = join(CURRENT_DIR, "save")
IMG_DIR = join(CURRENT_DIR,"img")
# Constants for the battle field
soldierSpeed = 3
soldierSize = 30
soldierWidth = 30
soldierHeight = 50
interval = 0.1 # Update position every 0.1 second
################################################################################
############CLASS MYBUTTON######################################################
class mybutton():
    def __init__(self,x,y,w,h,shape,color,text,\
                 tag='none',font='Symbol',txtcolor="Black"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.shape = shape
        self.color = color
        self.text = text
        self.tag = tag
        self.font = font
        self.savcolor = txtcolor
    
    def draw(self,canvas):
        if(self.shape == "r"):
            canvas.create_rectangle(self.x,self.y,self.x+self.w,self.y+self.h,\
                                    outline='Black',fill=self.color,\
                                    tag=self.tag)
        elif(self.shape == "c"):
            canvas.create_oval(self.x, self.y, self.x+self.w, self.y+self.h,\
                               outline='Black', fill=self.color,tag=self.tag)
        elif(self.shape == "i"):
            canvas.create_image(self.x,self.y,anchor=NW,image=self.color,\
                                tag=self.tag)
        # Draw text, with font size being half of the smaller of the width and 
        # height
        canvas.create_text(self.x+self.w/2,self.y+self.h/2,text=self.text,\
                           anchor=CENTER,font=(self.font,min(self.w,self.h)/2),\
                           fill=self.savcolor,tag=self.tag)

    # Return if the point x, y hit this button
    def click(self,x,y):
        if(self.shape == "r" or self.shape == "i"):
            return x >= self.x and x <= self.x+self.w\
                and y >= self.y and y <= self.y+self.h
        elif(self.shape == "c"):
            a,b = self.w/2, self.h/2
            xx,yy = x-self.x-a, y-self.y-b
            return (xx/a)*(xx/a) + (yy/b)*(yy/b) <= 1
        else:
            return False

class city():
    def __init__(self):
        self.shape = mybutton(0,0,citySize,citySize,"r",colors[0],"")
        self.words = []
        self.c = 0
        # Buffer is used to temporily store the words selected to leave the
        # city
        self.buff = []

    def addWord(self,word):
        self.words.append(word)
    
    def draw(self,canvas):
        rank = len(self.words) / 20
        if rank >= len(cityImages): rank = len(cityImages)-1
        canvas.create_image(self.shape.x,self.shape.y,anchor=NW,\
                            image=cityImages[rank])
        canvas.create_rectangle(self.shape.x,self.shape.y,\
                                self.shape.x+citySize/5,\
                                self.shape.y+citySize/5,\
                                outline="Black",fill=self.shape.color)

class wordblock():
    def __init__(self,x,y,word):
        self.shape = mybutton(x,y,wbw,wbh,"r","Yellow",word,'control')
        self.selected = False
        self.movedover = False
        self.word = word

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
    
    def draw(self,canvas):
        s = soldierSize
        x,y= self.pos[0],self.pos[1]
        canvas.delete(self.word)
        if self.state != "die":
            canvas.create_rectangle(x, y-soldierHeight-5,\
                                    x+soldierWidth, y-soldierHeight,\
                                    outline="Black",fill=colors[self.color],\
                                    tag=self.word)
        indx = 0
        if self.color == yourColor: indx = 1
        if self.state == "walk":
            canvas.create_image(x,y,anchor=SW,\
                                image=self.walkImages[self.imgIndex],\
                                tag=self.word)
        elif self.state == "fight":
            canvas.create_image(x,y,anchor=SW,\
                                image=self.fightImages[self.imgIndex],\
                                tag=self.word)
        elif self.state == "die":
            canvas.create_image(x,y,anchor=SW,\
                                image=self.dieImages[self.imgIndex],\
                                tag=self.word)
    
    def setpos(self,x,y):
        self.pos = [x,y]

class fightPair():
    def __init__(self, sdr1, sdr2):
        self.soldier1 = sdr1
        self.soldier2 = sdr2
        self.answerIndex = randint(0,3)
        self.options = []
        x,y = 0,0
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
        self.buttons = [mybutton(x,y+(i+1)*h,w,h,"r","Yellow",self.options[i],\
                        'fight') for i in range(4)]
    def draw(self,canvas):
        x,y = self.x, self.y
        w,h = answerbw, answerbh 
        canvas.create_rectangle(x,y,x+w,y+h,outline="Black",fill="Yellow",\
                                tag='fight')
        canvas.create_text(x,y,anchor=NW,text=self.question,font=("Symbol",h/2),\
                           tag='fight')
        for b in self.buttons: b.draw(canvas)

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
root = Tk()
cv_menu = Canvas(root,width=winw,height=winh,bg='white')
cv_selectCity = Canvas(root,width=winw,height=winh,bg='white')
cv_main = Canvas(root,width=winw,height=winh,bg='white')
cv_document = Canvas(root,width=winw,height=winh,bg='white')
cv_battle = Canvas(root,width=winw,height=winh,bg='white')
################################################################################
###########IMAGES###############################################################
def getPhotoImage(filename,w,h):
    return ImageTk.PhotoImage(Image.open(join(IMG_DIR,filename)).resize((w,h)))

cityImages = [getPhotoImage("city%d.gif"%i,\
                            citySize*(i+15)/15,citySize*(i+15)/15)\
                            for i in range(5)]
groundImage = getPhotoImage("ground.jpeg",winw,winh)
buttonImages = [getPhotoImage("button%d.gif"%i,bw,bh)\
                for i in range(3)]
documentButtonImages = [getPhotoImage("button%d.gif"%i,winw,bh)\
                        for i in range(3,5)]
arrowImages = [Image.open(join(IMG_DIR,"arrow%d.gif"%i)) for i in range(2)]
fireImages = [getPhotoImage("fire%d.gif"%i,citySize,citySize) for i in range(3)]
fireImages.extend([getPhotoImage("fire%d.gif"%i,citySize/2,citySize/2)
                   for i in range(3)])
SOLDIER_PATHS = [join(IMG_DIR,"soldier%d"%i) for i in range(2)]
WALK_PATHS = [join(p,"walk") for p in SOLDIER_PATHS]
FIGHT_PATHS= [join(p,"fight") for p in SOLDIER_PATHS]
DIE_PATHS= [[join(p,"die%i"%i) for p in SOLDIER_PATHS] for i in range(2)]
def getWalkImage(filename,i):
    return ImageTk.PhotoImage(Image.open(join(WALK_PATHS[i],filename)).\
                              resize((soldierWidth,soldierHeight)))
def getFightImage(filename,i):
    return ImageTk.PhotoImage(Image.open(join(FIGHT_PATHS[i],filename)).\
                              resize((soldierWidth,soldierHeight)))
def getDieImage(filename,i,j):
    return ImageTk.PhotoImage(Image.open(join(DIE_PATHS[i][j],filename)).\
                              resize((soldierWidth,soldierHeight)))
    
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
menubuttons.append(mybutton(x0,y0,     bw,bh,"i",buttonImages[0],\
                   menuButtonLabels[0]))
menubuttons.append(mybutton(x0,y0+bh,  bw,bh,"i",buttonImages[0],\
                   menuButtonLabels[1]))
menubuttons.append(mybutton(x0,y0+2*bh,bw,bh,"i",buttonImages[0],\
                   menuButtonLabels[2]))
controlbuttons = []
ctrbw,ctrbh = winw/4, winh/12
controlbuttons.append(mybutton(0,y0,        ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[0],'control'))
controlbuttons.append(mybutton(0,y0+ctrbh,  ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[1],'control'))
controlbuttons.append(mybutton(0,y0+2*ctrbh,ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[2],'control'))
controlbuttons.append(mybutton(0,y0+3*ctrbh,ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[3],'control'))
controlbuttons.append(mybutton(0,y0+4*ctrbh,ctrbw,ctrbh,"i",buttonImages[1],
                      controlButtonLabels[4],'control'))
mainMenuButtons = []
mainMenuButtons.append(mybutton(x0,y0,     bw,bh,"i",buttonImages[0],\
                       mainMenuButtonLabels[0],'mainmenu'))
mainMenuButtons.append(mybutton(x0,y0+bh,  bw,bh,"i",buttonImages[0],\
                       mainMenuButtonLabels[1],'mainmenu'))
mainMenuButtons.append(mybutton(x0,y0+2*bh,bw,bh,"i",buttonImages[0],\
                       mainMenuButtonLabels[2],'mainmenu'))

savebutton = mybutton(winw-bw,winh-bh,bw,bh,"i",buttonImages[2],"Save")
# Word Blocks
wordblocks = []
# For the battle field
attackers = []
defenders = []
yourTroop = []
enemyTroop = []
flag = None
flagmove = [0,0]
fightPairs = []
fx,fy = 10,7

answerbw = winw/3
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
    cv_menu.pack_forget()
    if(not gameStarted):
        startNewGame()
        drawselect(True)
    else:
        continueGame()
        drawmain()

def continueGame():
    global currentCanvas
    cv_main.pack()
    currentCanvas = "main"

def startNewGame():
    global currentCanvas
    readCityInfo(NEWGAME_FILE)
    cv_selectCity.pack()
    currentCanvas = "select"

def document(mode):
    global documentbuttons, currentCanvas, documentMode, saveName
    SAVE_FILES = [join(SAVE_DIR, fname) for fname in listdir(SAVE_DIR) \
                  if isfile(join(SAVE_DIR, fname)) and \
                  splitext(basename(fname))[1]==".sav"]
    documentbuttons = [mybutton(0,i*bh,winw,bh,"i",documentButtonImages[0],\
                       splitext(basename(SAVE_FILES[i]))[0])\
                       for i in range(len(SAVE_FILES))]
    cv_menu.pack_forget()
    cv_main.pack_forget()
    cv_document.pack()
    currentCanvas = "document"
    documentMode = mode
    saveName = ""
    drawdoc()

def quit():
    saveCityInfo(join(SAVE_DIR,"autosave.sav"))
    root.quit()

def control(cmd, ct):
    global showControlPanel, wordblocks, selectTargetCity
    global srccity, currentCanvas, showRecruitPanel, recruitWord
    if cmd == "CANCEL":
        showControlPanel = False
        wordblocks = []
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
                srccity = ct
                selectTargetCity = True
                cv_main.pack_forget()
                cv_selectCity.pack()
                currentCanvas = "select"
                drawselect(True)
                citySelect = None
                showControlPanel = False
                wordblocks = []
    elif cmd == "RECRUIT":
        if len(deadWords) <= 0: return
        if ct and ct.c == yourColor:
            showControlPanel = False
            wordblocks = []
            word = deadWords[randint(0,len(deadWords)-1)]
            showRecruitPanel = True
            recruitWord = word
            recruitAnswer = ""

    drawmain()

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
# A special kind of algorithm to determine the position of a soldier relative
# to the flag of the army. The position is determined by the word of the
# soldier and the distance to the original is relatively determined by the
# total number of soldiers in the field. To garanteen the arbitrariness of the
# position, hash function is used
# To make the soldiers always moving, the target of the same word should be
# always changing, this is made by adding the time into the hash function
def targetByWord(flag,word, n):
    if n <= 1: return flag
    f = 2
    t = str(int(10*clock()))
    h = md5(word)
    h = h.hexdigest()
    # a and b serve as the x and y coordinates respectively
    a = h[:len(h)/2]
    b = h[len(h)/2:]
    x = hexsum(a)/(len(a)*16.0) * 2 - 1
    y = hexsum(b)/(len(b)*16.0) * 2 - 1
    x = int(x * math.sqrt(n-1) * 50) + flag[0]
    y = int(y * math.sqrt(n-1) * 50) + flag[1]
    h = md5(t+word)
    h = h.hexdigest()
    a = h[:len(h)/2]
    b = h[len(h)/2:]
    x += int((hexsum(a)/(len(a)*16.0)*2 - 1)*70)
    y += int((hexsum(b)/(len(b)*16.0)*2 - 1)*70)
    return [x,y]

# control soldier by ai
def ai(s,targets):
    mindist,targ,mmindist,ttarg = None,None,None,None
    for e in targets:
        x,y = s.pos[0], s.pos[1]
        ex,ey = e.pos[0], e.pos[1]
        dist = (ex-x)*(ex-x)+(ey-y)*(ey-y)
        if mmindist is None:
            mmindist = dist
            ttarg = e
        if mmindist > dist:
            mmindist = dist
            ttarg = e
        if e.state == "walk":
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
        if ttarg is not None:
            alpha = randint(0,360)/360.0 * 2 * math.pi;
            r = 100
            target = [ttarg.pos[0] + r*math.cos(alpha),
                      ttarg.pos[1] + r*math.sin(alpha)]
            s.setTarget(target)
            return s.moveon()
        else:
            s.setTarget(None)
            return None

def battlemoveon():
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
        cv_main.pack()
        cv_battle.pack_forget()
        currentCanvas = "main"
        drawmain()
        srccity = None
        dstcity = None
        return
    # Movement of your troop(follow the flag)
    if flag:
        flag[0] += flagmove[0]
        flag[1] += flagmove[1]
    for s in yourTroop:
        if s.over:
            deadWords.append(s.word)
            tmpDeadWords.append(s)
            yourTroop.remove(s)
            cv_battle.delete(s.word)
        elif s.state == "walk":
            if flag:
                s.setTarget(targetByWord(flag,s.word,len(yourTroop)))
                s.moveon()
            else:
                ai(s,enemyTroop)
        elif s.state == "fight" or s.state == "die":
            s.moveon()

    # Movement of the enemy troop
    for s in enemyTroop:
        if s.over:
            deadWords.append(s.word)
            tmpDeadWords.append(s)
            enemyTroop.remove(s)
            cv_battle.delete(s.word)
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
                # Failed to find a free space
                fightPairs.append(fightPair(yt,et))
                et.pos[0] = yt.pos[0]+soldierSize/2
                et.pos[1] = yt.pos[1]
                yt.fight()
                et.fight()

Message = namedtuple("Message","text loc")
def removeMessage(msg):
    global message,messages
    if message == msg:
        message = ""
    if msg in messages:
        messages.remove(msg)
    if currentCanvas == "main":
        drawmain()

def putMessage(msg,location=None):
    if not currentCanvas == "main": return
    global message, messages
    # location is None means this is a message generated by the player
    if location is None:
        message = msg
        cv_main.after(3000,removeMessage,msg)
    else: # else, this is from others
        m = Message(text=msg,loc=location)
        messages.append(m)
        cv_main.after(1000,removeMessage,m)

def removeMark(mark):
    global marks
    for m in marks:
        if m.ID == mark.ID:
            marks.remove(m)

markData = namedtuple("markData","Type X0 Y0 X1 Y1 Img index ID")
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
        img = [ImageTk.PhotoImage(\
            arrowImages[indx].resize((sz,15)).convert("RGBA").\
            rotate(ag*180/math.pi,expand=1))]
        mt = markData(Type = tp, X0=(x0+x1)/2, Y0=(y0+y1)/2,\
                      X1=x1, Y1=y1, Img=img, index = 0,\
                      ID = "%s%d%d"%(tp,int(clock()*1000),randint(0,1000)))
        marks.append(mt)
        cv_main.after(1000,removeMark,mt)
    elif tp == "fire":
        x0,y0 = data[0],data[1]
        img = fireImages
        mt = markData(Type = tp, X0=x0, Y0=y0, X1=0, Y1=0, Img=img, index = 0,\
                      ID = "%s%d%d"%(tp,int(clock()*1000),randint(0,1000)))
        marks.append(mt)
        cv_main.after(3000,removeMark,mt)


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

def enmiesInConvexHull(cts):
    if len(cts) == 0: return []
    left = min([c.shape.x for c in cts])
    right = max([c.shape.x for c in cts])
    bottom = min([c.shape.y for c in cts])
    top = max([c.shape.y for c in cts])
    return [ct for ct in cities if ct.shape.x > left and ct.shape.x < right \
                                and ct.shape.y > bottom and ct.shape.y < top and
                                ct.c != cts[0].c]

# On entering main scene, this function is executed repeatedly, controlling
# the enemies
def mainfunc():
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
            enm = enmiesInConvexHull(cts)
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
                        if nb in enm: # If in convex, attack with high
                        #probability
                            p = randint(1,m+n)
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
                                if useflag:
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
        drawmain()

    if sync:
        cv_main.after(1000,mainfunc)
    else:
        cv_main.after(randint(0,100),mainfunc)

# Control the move of animations
# markData = namedtuple("markData","Type X0 Y0 X1 Y1 Img index ID")
def animate():
    global marks
    if currentCanvas == "main":
        for i in range(len(marks)):
            m = markData( Type = marks[i].Type,\
                          X0 = marks[i].X0, Y0 = marks[i].Y0,\
                          X1 = marks[i].X1, Y1 = marks[i].Y1,\
                          Img = marks[i].Img, ID = marks[i].ID,\
                          index = (marks[i].index+1)%len(marks[i].Img))
            marks[i] = m
        drawmain()
    root.after(200,animate)

################################################################################
################EVENT HANDLE FUNCTIONS##########################################

def menuButtonClick(command):
    if(command == "START"):
        start()
    elif(command == "LOAD"):
        document("load")
    elif(command == "QUIT"):
        quit()

def menuLeftClick(event):
    for i in range(nbuts):
        if(menubuttons[i].click(event.x,event.y)):
            menuButtonClick(menubuttons[i].text) # Pass the text of the button
    
def documentMouseMove(event):
    for b in documentbuttons:
        if(b.click(event.x,event.y)):
            b.color = documentButtonImages[1]
        else:
            b.color = documentButtonImages[0]
    drawdoc()

def documentLeftClick(event):
    global currentCanvas, gameStarted, showControlPanel, showMainMenu, saveName
    global srccity, dstcity
    if documentMode == "load":
        for b in documentbuttons:
            if b.click(event.x,event.y):
                readCityInfo(join(SAVE_DIR,b.text+".sav"))
                cv_document.pack_forget()
                cv_main.pack()
                currentCanvas = "main"
                drawmain()
                if not gameStarted:
                    mainfunc()
                gameStarted = True
                showControlPanel = False
                showMainMenu = False
                srccity,dstcity = None,None
    elif documentMode == "save":
        for b in documentbuttons:
            if b.click(event.x,event.y):
                saveName = b.text
        if savebutton.click(event.x,event.y):
            saveCityInfo(join(SAVE_DIR,saveName+".sav"))
            cv_document.pack_forget()
            cv_main.pack()
            currentCanvas = "main"
            drawmain()
    drawdoc()

def documentRightClick(event):
    global currentCanvas
    if gameStarted:
        cv_document.pack_forget()
        cv_main.pack()
        currentCanvas = "main"
        drawmain()
    else:
        cv_document.pack_forget()
        cv_menu.pack()
        currentCanvas = "menu"
        drawmenu()

def keyPress(event):
    global saveName, flagMove, recruitAnswer
    if currentCanvas == "document" and documentMode == "save":
        if event.char.isalpha():
            saveName += event.char
        drawdoc()
    elif currentCanvas == "main":
        if showRecruitPanel:
            if event.char.isalpha():
                recruitAnswer += event.char
        drawmain()
    elif currentCanvas == "battle":
        if event.char == "h": # Move left
            flagmove[0] = -soldierSpeed * 2
        elif event.char == "j": # Move down
            flagmove[1] = soldierSpeed * 2
        elif event.char == "k": # Move up
            flagmove[1] = -soldierSpeed * 2
        elif event.char == "l": # Move right
            flagmove[0] = soldierSpeed * 2

def keyUp(event):
    global flagmove
    flagmove = [0,0]

def backSpacePress(event):
    global saveName, recruitAnswer
    if currentCanvas == "document" and documentMode == "save":
        saveName = saveName[:-1]
        drawdoc()
    elif currentCanvas == "main":
        if showRecruitPanel:
            recruitAnswer = recruitAnswer[:-1]
        drawmain()

def returnPress(event):
    global saveName, currentCanvas, showRecruitPanel, recruitWord, recruitAnswer
    global citySelect
    if currentCanvas == "document" and documentMode == "save":
        saveCityInfo(join(SAVE_DIR,saveName+".sav"))
        cv_document.pack_forget()
        cv_main.pack()
        currentCanvas = "main"
        drawdoc()
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
        drawmain()

def selectLeftClick(event):
    global currentCanvas, yourColor, selectTargetCity, dstcity, gameStarted
    global attackers, defenders, yourTroop, enemyTroop, flag, tmpDeadWords
    # selectTargetCity is set to True when the player is moving troop from one
    # city to another. It is False when start a new game and choose your own
    # color
    if not selectTargetCity:
        if(citySelect != None):
            if not gameStarted:
                mainfunc()
            gameStarted = True
            yourColor = citySelect.c
            cv_selectCity.pack_forget()
            cv_main.pack()
            currentCanvas = "main"
            drawmain()
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
                        if useflag:
                            flag = [winw/2,winh/2]
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
                    cv_selectCity.pack_forget()
                    cv_main.pack()
                    currentCanvas = "main"
                    drawmain()
                else:
                    cv_battle.pack()
                    cv_selectCity.pack_forget()
                    tmpDeadWords = []
                    currentCanvas = "battle"
                    drawbattle()

def selectRightClick(event):
    global currentCanvas,srccity
    if not selectTargetCity:
        cv_selectCity.pack_forget()
        cv_menu.pack()
        currentCanvas = "menu"
        drawmenu()
    else:
        cv_selectCity.pack_forget()
        cv_main.pack()
        currentCanvas = "main"
        for c in srccity.buff:
            srccity.words.append(c)
        srccity.buff = []
        srccity = None
        drawmain()

def selectMouseMove(event):
    global citySelect
    citySelect = None
    for c in cities:
        if(c.shape.click(event.x,event.y)):
            citySelect = c
    drawselect(False)

def mainLeftClick(event):
    global showControlPanel,wordblocks,showMainMenu,currentCanvas
    global youAreAttacked, hangon, srccity, dstcity, tmpDeadWords
    if hangon:
        if youAreAttacked:
            cv_main.pack_forget()
            cv_battle.pack()
            tmpDeadWords = []
            currentCanvas = "battle"
            drawbattle()
        hangon = False
        youAreAttacked = False
    elif showControlPanel:
        # If the control panel is visible while no city is selected
        # just turn off the control panel
        if not citySelect:
            showControlPanel = False
            return
        for b in controlbuttons:
            if(b.click(event.x,event.y)):
                control(b.text, citySelect)
            if citySelect.c is yourColor:
                # If this city is yours, the words would be shown
                # Click on them to select or unselect
                for w in wordblocks:
                    if w.shape.click(event.x,event.y):
                        w.selected = not w.selected
    elif showMainMenu:
        for b in mainMenuButtons:
            if b.click(event.x,event.y):
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
            showControlPanel = True
            for b in controlbuttons:
                if not b.text == "CANCEL" and citySelect.c is not yourColor:
                    b.savcolor = "Gray"
                else:
                    b.savcolor = "Black"
            else:
                # The city is yours, and the words in it would be shown
                # The words would be arranged in a matrix, whose size is
                # determined by the number of words, n
                n = len(citySelect.words)
                if n == 0: return
                # Number of columns and number of rows
                nc = math.ceil(math.sqrt(n/5.0))
                nr = nc * 5
                # Left-Top corner of this matrix
                x0,y0 = ctrbw,winh/2-nr*wbh/2
                # Add the word blocks into the array
                for i in range(n):
                    x,y = x0+wbw*math.floor(i/nr),y0+wbh*(i%nr)
                    wordblocks.append(wordblock(x,y,citySelect.words[i]))
    drawmain()

def mainRightClick(event):
    global showMainMenu, showControlPanel, citySelect, srccity, wordblocks
    global showRecruitPanel, hangon, youAreAttacked
    if hangon: return
    if not showControlPanel and not showRecruitPanel:
        showMainMenu = not showMainMenu
    if(showControlPanel):
        showControlPanel = False
        citySelect = None
        srccity = None
        wordblocks = []
    if showRecruitPanel:
        showRecruitPanel = False
        recruitWord = ""
        recruitAnswer = ""
    drawmain()

def mainMouseMove(event):
    global citySelect, controlButtonSelect, showMainMenu
    # If control panel is visible, just if any button is selected
    if showControlPanel:
        controlButtonSelect = None
        for b in controlbuttons:
            if b.click(event.x,event.y):
                controlButtonSelect = b
                b.color = buttonImages[2]
            else:
                b.color = buttonImages[1]
        if citySelect is not None and citySelect.c is yourColor:
            # In this case, the word panel is shown
            # Move the mouse over a word, the background is changed
            # and the Chinese meaning is shown
            for w in wordblocks:
                if w.shape.click(event.x,event.y):
                    w.movedover = True
                    w.shape.color = "Orange"
                else:
                    w.movedover = False
                    if w.selected:
                        w.shape.color = "Blue"
                    else:
                        w.shape.color = "Yellow"
    elif showMainMenu:
        pass
    elif showRecruitPanel:
        pass
    else:
        citySelect = None
        for c in cities:
            if(c.shape.click(event.x,event.y)):
                citySelect = c
                break
    drawmain()

def mainMouseLeftMove(event):
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
                if w.shape.click(event.x,event.y):
                    w.selected = True
                    w.movedover = True
                    w.shape.color = "Orange"
                else:
                    w.movedover = False
                    if w.selected:
                        w.shape.color = "Blue"
                    else:
                        w.shape.color = "Yellow"
    drawmain()

def battleLeftClick(event):
    global currentCanvas, fightPairs, deadWords, message
    F,S = None, None
    if len(fightPairs) > 0:
        F = fightPairs[0]
        S = F.click(event.x,event.y)
    if F is not None:
        if S == "correct":
            F.soldier1.walk()
            F.soldier2.die()
            fightPairs.remove(F)
            msg = S + "    " + F.soldier2.word + " " + wordDict[F.soldier2.word]
            message = msg
            cv_battle.after(3000,removeMessage,msg);
        elif S == "wrong":
            F.soldier1.die()
            F.soldier2.walk()
            fightPairs.remove(F)
            msg = S + "    " + F.soldier2.word + " " + wordDict[F.soldier2.word]
            message = msg
            cv_battle.after(3000,removeMessage,msg);
################################################################################
############DRAWING FUNCTIONS###################################################

def drawmenu():
    if(currentCanvas != "menu"): return
    cv_menu.delete(ALL)
    cv_menu.create_image(winw/2,winh/2,image=groundImage)
    for b in menubuttons: 
        b.draw(cv_menu)
    cv_menu.after(200,drawmenu)
    
def drawselect(redrawAll):
    global citySelect
    if(currentCanvas != "select"): return
    if(redrawAll):
        cv_selectCity.delete(ALL)
        cv_selectCity.create_image(0,0,image=groundImage)
        cv_selectCity.create_image(winw/2,0,image=groundImage)
        cv_selectCity.create_image(0,winh/2,image=groundImage)
        cv_selectCity.create_image(winw/2,winh/2,image=groundImage)
        for c in cities:
            c.draw(cv_selectCity)
        cv_selectCity.create_text(0,0,anchor=NW,text="Select a city.",\
                                  fill="White",font="Symbol 15")
    else:
        cv_selectCity.delete('select')
    if(citySelect != None):
        x,y,w = citySelect.shape.x, citySelect.shape.y, citySize
        W = w * 6/5
        x -= (W-w)/2
        y -= (W-w)/2
        cv_selectCity.create_rectangle(x,y,x+W,y+W,outline='black',fill="",\
                                       tag="select")
    # If it is in selectTargetCity mode, highlight the neighbors of the source
    # city by thick outlines
    if selectTargetCity:
        cv_selectCity.delete('target')
        for c in cities:
            if areNeighbors(c,srccity) and c is not srccity:
                x,y,w = c.shape.x, c.shape.y, citySize
                W = w * 6/5
                x -= (W-w)/2
                y -= (W-w)/2
                cv_selectCity.create_rectangle(x,y,x+W,y+W,outline='red',width=3,\
                                               tag='target')

def drawmain():
    global citySelect,showControlPanel
    if(currentCanvas != "main"): return
    cv_main.delete(ALL)
    cv_main.create_image(winw/2,winh/2,image=groundImage)
    for c in cities:
        c.draw(cv_main)
    if(citySelect != None):
        x = citySelect.shape.x
        y = citySelect.shape.y
        w = citySize
        W = w * 6/5
        x -= (W-w)/2
        y -= (W-w)/2
        cv_main.create_rectangle(x,y,x+W,y+W,outline='black',fill="",\
                                 tag="select")
    
    # Messages
    if not message == "":
        x,y = 0,winh-wbh
        cv_main.create_rectangle(x,y-wbh/3,winw,winh,outline='black',\
                                 fill='Orange',tag='message')
        cv_main.create_text(x,y-wbh/3,anchor=NW,font=("Symbol",wbh/2),\
                            text=message,tag='message')
    for m in messages:
        cv_main.create_text(m.loc[0],m.loc[1],anchor=CENTER,\
                            font=("Symbol",wbh/2),text=m.text,tag='message',\
                            fill="White")
    # Marks
    for m in marks:
        if m.Type  == "arrow" or m.Type == "attack" or m.Type == "fire":
            x,y,i = m.X0, m.Y0, m.index
            cv_main.create_image(x,y,anchor=CENTER,image=m.Img[i],\
                                 tag='mark')

    # City info panel
    if(citySelect):
        x,y,w,h = 0,0,winw/4,winh/20
        if(citySelect.shape.x < winw/2): x = winw - w
        if(citySelect.c == yourColor):
            relation = "Yourself"
        else:
            relation = "Enemy"
        totalNumber = 0
        cityNumber = 0
        for c in cities:
            if c.c == citySelect.c:
                totalNumber += len(c.words)
                cityNumber += 1
        infos = ["Relation: "+ relation,\
                 "Color: "+str(citySelect.shape.color),\
                 "Number Of Words: "+str(len(citySelect.words)),\
                 "Total Words: "+str(totalNumber),\
                 "City Number: "+str(cityNumber)]
        for i in range(len(infos)):
            cv_main.create_rectangle(x,y+i*h,x+w,y+(i+1)*h,outline='black',\
                                     fill='yellow',tag='infoPanel')
            cv_main.create_text(x,y+i*h,anchor=NW,font=("Symbol",h/2),\
                                text=infos[i],tag='infoPanel')
    # Control panel
    if showControlPanel:
        for b in controlbuttons:
            b.draw(cv_main)
        # Word panel
        if citySelect.c == yourColor:
            blockMovedOver = None
            for w in wordblocks:
                w.shape.draw(cv_main)
                if w.movedover:
                    blockMovedOver = w
            # If moved over by mouse, show the Chinese meaning
            if blockMovedOver is not None:
                bx,by = 0,winh-wbh-wbh/3
                cv_main.create_rectangle(bx,by,winw,winh,outline='black',\
                                         fill='Orange',tag='control')
                cv_main.create_text(bx,by,anchor=NW,font=("Symbol",wbh/2),\
                                    text=wordDict[blockMovedOver.word],\
                                    tag='control')

    # Recruit Panel
    cv_main.delete('recruit')
    if showRecruitPanel:
        cv_main.create_rectangle(rpx,rpy,rpx+rpw,rpy+rph*2,outline='black',\
                                 fill='Orange',tag='recruit')
        cv_main.create_text(rpx,rpy,anchor=NW,font=("Symbol",rph/2),\
                            text=wordDict[recruitWord],tag='recruit')
        cv_main.create_text(rpx,rpy+rph,anchor=NW,font=("Symbol",rph/2),\
                            text=recruitAnswer,tag='recruit')
    
    # Information
    census = {}
    for c in colors:
        census[c] = [0,0]
    for c in cities:
        census[colors[c.c]][0] += 1
        census[colors[c.c]][1] += len(c.words)
    ctdata = []
    for c in census:
        if census[c][1] > 0:
            ctdata.append([c,census[c][0],census[c][1]])
    for i in range(0,len(ctdata)-1):
        for j in range(len(ctdata)-1,i,-1):
            if ctdata[i][2] < ctdata[j][2]:
                ctdata[i],ctdata[j] = ctdata[j],ctdata[i]
    for i in range(0,len(ctdata)):
        cv_main.create_text(0,winh/16*i,anchor=NW,text=ctdata[i][0]+": ",\
            fill=ctdata[i][0],font=("Symbol",winh/32))
        cv_main.create_text(bw/3,winh/16*i,anchor=NW,text=\
            str(ctdata[i][2])+" "+str(ctdata[i][1]),\
            fill="white",font=("Symbol",winh/32))
    cv_main.create_text(winw-bw,winh-bh,anchor=NW,\
                text="unrecruited: %d"%len(deadWords),\
                fill="white",font=("Symbol",bh/4))
    
    # Menu
    if showMainMenu:
        for b in mainMenuButtons:
            b.draw(cv_main)

def drawdoc():
    if currentCanvas != "document": return
    cv_document.delete(ALL)
    cv_document.create_image(winw/2,winh/2,image=groundImage)
    for b in documentbuttons:
        b.draw(cv_document)
    if documentMode == "save":
        cv_document.create_image(0,winh-bh,anchor=NW,\
                                 image=documentButtonImages[0])
        #cv_document.create_rectangle(0,winh-bh/2,winw,winh,outline="Black",\
        #                            fill="Yellow")
        cv_document.create_text(0,winh-bh,anchor=NW,text=saveName,\
                                font=("Symbol",bh/2))
        savebutton.draw(cv_document)
        
def drawbattle():
    if currentCanvas != "battle": return
    cv_battle.delete(ALL)

    cv_battle.create_image(winw/2,winh/2,image=groundImage)

    for s in tmpDeadWords:
        s.draw(cv_battle)
    for s in attackers:
        s.draw(cv_battle)
    for s in defenders:
        s.draw(cv_battle)
    # Draw the flag
    if flag:
        color = colors[yourColor]
        if color == "white" or color == "White":
            color = "Gray"
        cv_battle.create_oval(flag[0]-10,flag[1]-10,flag[0]+10,flag[1]+10,\
                              outline=color,width=5,fill="",tag='flag')
        cv_battle.create_line(flag[0]-10,flag[1],flag[0]+10,flag[1],\
                              fill=color,width=5,tag='flag')
        cv_battle.create_line(flag[0],flag[1]-10,flag[0],flag[1]+10,\
                              fill=color,width=5,tag='flag')
    # Draw the questions
    if len(fightPairs) > 0:
        fightPairs[0].draw(cv_battle)
    # Draw the message
    if not message == "":
        x,y = 0,winh-wbh
        cv_battle.create_rectangle(x,y,winw,winh,outline='black',\
                                 fill='Orange',tag='message')
        cv_battle.create_text(x,y,anchor=NW,font=("Symbol",wbh/2),\
                            text=message,tag='message')
    battlemoveon()
    cv_battle.after(int(interval*1000),drawbattle)

init()
root.title('Word War')
root.bind('<KeyPress>',keyPress)
root.bind('<KeyRelease>',keyUp)
root.bind('<BackSpace>',backSpacePress)
root.bind('<Return>',returnPress)
cv_menu.pack()
cv_menu.bind('<Button-1>',menuLeftClick)
cv_document.bind('<Motion>',documentMouseMove)
cv_document.bind('<Button-1>',documentLeftClick)
cv_document.bind('<Button-3>',documentRightClick)
cv_selectCity.bind('<Button-1>',selectLeftClick)
cv_selectCity.bind('<Button-3>',selectRightClick)
cv_selectCity.bind('<Motion>',selectMouseMove)
cv_main.bind('<Button-1>',mainLeftClick)
cv_main.bind('<Button-3>',mainRightClick)
cv_main.bind('<Motion>',mainMouseMove)
cv_main.bind('<B1-Motion>',mainMouseLeftMove)
cv_battle.bind('<Button-1>',battleLeftClick)
drawmenu()
animate()
cv_selectCity.pack_forget()
cv_main.pack_forget()
cv_battle.pack_forget()

root.mainloop()
