#Create your own shooter
import pygame
pygame.init()
import sys
import random
import math

#-----------------------
# VARIABEL GLOBAL
#-----------------------
displayWidth  = 1200
displayHeight = 800
isFullscreen  = False

applicationSurface = pygame.display.set_mode((displayWidth , displayHeight))
cameraSurface      = pygame.Surface((displayWidth , displayHeight))
clock = pygame.Clock()

onDrawGUI = False
isRunning = True
FramePerSecond = 60


queueInstance = {}
destroyQueueInstanceName = []
installedInstance = {}
assets = {
    "spr_asteroid"      : pygame.image.load("asteroid.png"),
    "spr_bullet"        : pygame.image.load("bullet.png"),
    "spr_galaxy"        : pygame.image.load("galaxy.jpg"),
    "spr_rocket"        : pygame.image.load("rocket.png"),
    "spr_ufo"           : pygame.image.load( "ufo.png"),

    "snd_fire"          : pygame.mixer.Sound("fire.ogg"),
    "snd_space"         : pygame.mixer.Sound("space.ogg"),

    "fnt_arial"         : pygame.font.SysFont("arial", 64 , True),
    "fnt_arialSmall"    : pygame.font.SysFont("arial", 32 , True),
    "fnt_determin"      : pygame.font.SysFont("determinationregular", 64),
}

backgroundColor = (255 , 255 , 255)


globalVariable = {}
#-----------------------





#-----------------------
# CLASS / KONSTRUKTOR GLOBAL
#-----------------------
class instance:
    def __init__(self , sprite , X , Y , width , height , rotation = 0):
        self.sprite = sprite
        self.previousX = 0
        self.previousY = 0
        self.x = X
        self.y = Y
        self.rotation = rotation
        self.width = width
        self.height = height

        self.onStep = None
        self.onDraw = self.drawSelf
        self.onDrawGUI = None

        self.drawRotationPos = "topleft"

        if (isinstance(sprite , str)):
            self.sprite = pygame.image.load(sprite)


    def forceUpdate(self):
        self.previousX = self.x
        self.previousY = self.y


    def isColliding(self , instance2):
        return (self.x < instance2.x + instance2.width and self.x + self.width > instance2.x
                and self.y < instance2.y + instance2.height and self.y + self.height > instance2.y)
    

    def collidingList(self):
        collidingInstanceList = []
        for instanceName , instanceObject in installedInstance.items():
            if (isinstance(instanceObject , instance)):
                if (self.isColliding(instanceObject)):
                    collidingInstanceList.append(instanceName)
        return collidingInstanceList
    

    def drawSelf(self):
        # 1. Selalu gunakan gambar asli (original) untuk dirotasi & di-scale
        #    agar tidak terjadi distorsi berulang.
        scaled_original = pygame.transform.scale(self.sprite, (self.width, self.height))
        rotated_sprite = pygame.transform.rotate(scaled_original, self.rotation)
        
        # 2. Buat rect baru dari gambar yang sudah dirotasi
        rotated_rect = rotated_sprite.get_rect()
        
        # 3. KUNCI UTAMA: Kunci titik pusat (center) rect baru 
        #    ke posisi koordinat objek (self.x, self.y)
        if self.drawRotationPos == "center":
            rotated_rect.center = (self.x, self.y)
        elif self.drawRotationPos == "topleft":
            # Ambil ukuran setengah dari gambar yang sudah di-scale (sebelum dirotasi)
            half_w = self.width / 2
            half_h = self.height / 2
            
            # Hitung posisi pusat (center) baru yang dinamis agar top-left asli tidak bergeser
            # Ingat: Sudut di Pygame berlawanan arah jarum jam, maka di-negatifkan dalam math.radians
            rad = math.radians(-self.rotation)
            
            # Rumus rotasi titik untuk mencari posisi center baru relatif terhadap top-left (self.x, self.y)
            center_x = self.x + (half_w * math.cos(rad) - half_h * math.sin(rad))
            center_y = self.y + (half_w * math.sin(rad) + half_h * math.cos(rad))
            
            # 3. Buat rect baru dan pasang center-nya ke posisi dinamis tadi
            rotated_rect = rotated_sprite.get_rect()
            rotated_rect.center = (center_x, center_y)
            
            # 4. Blit ke layar
            cameraSurface.blit(rotated_sprite, rotated_rect.topleft)
        
        # 4. Blit menggunakan rect sebagai posisinya (otomatis mengambil posisi kiri-atas yang pas)
        cameraSurface.blit(rotated_sprite, rotated_rect.topleft)
        
#-----------------------







#-----------------------
# FUNGSI GLOBAL
#-----------------------
def installInstance(instanceObject , instanceName):
    queueInstance[instanceName] = instanceObject
    return queueInstance[instanceName]


def instanceDestroy(instanceName):
    destroyQueueInstanceName.append(instanceName)


def instanceExist(instanceName):
    return (instanceName in installedInstance) or (instanceName in queueInstance)


def moveInstance(instanceName , horizontalSpeed , verticalSpeed):
    instanceObject = findFirstInstance(instanceName)
    instanceObject.x += horizontalSpeed
    instanceObject.y += verticalSpeed 



def instanceSetDebris(instanceName, timeInFrame):
    instanceObject = findFirstInstance(instanceName)

    if (instanceExist(instanceObject)):
        if not hasattr(instanceObject, "debrisTime"): # hasattr lebih aman dari vars()
            instanceObject.debrisTime = timeInFrame

        instanceObject.debrisTime -= 1

        
        if instanceObject.debrisTime <= 0:
            instanceDestroy(instanceName)






def findFirstInstance(instanceName):
    if (instanceName in installedInstance):
        return installedInstance[instanceName]
    elif (instanceName in queueInstance):
        return queueInstance[instanceName]
    else:
        print("ERRORR!!! Instansi tidak ditemukan! Dari fungsi findFirstInstance")




def fullscreenToggle():
    global isFullscreen
    global applicationSurface
    global cameraSurface
    isFullscreen = not isFullscreen
    if (isFullscreen):
        applicationSurface = pygame.display.set_mode((100 , 100) , pygame.FULLSCREEN)

        screenWidth , screenHeight = applicationSurface.get_size()

        cameraSurface      = pygame.Surface((screenWidth , screenHeight))
    else:
        applicationSurface = pygame.display.set_mode((displayWidth , displayHeight))
        cameraSurface      = pygame.Surface((displayWidth , displayHeight))
    
#-----------------------





#-----------------------
# FUNGSI 
#-----------------------
def playerControl(instanceName , horizontalSpeed , verticalSpeed):
    instanceObject = findFirstInstance(instanceName)
    pressPyKey = pygame.key.get_pressed()
    pressedPyKey   = pygame.key.get_just_pressed()

   
    if (globalVariable["isLose"])or(globalVariable["isWin"]): return
    if (pressPyKey[pygame.K_DOWN]): instanceObject.y += verticalSpeed
    if (pressPyKey[pygame.K_UP]):   instanceObject.y -= verticalSpeed
    if (pressPyKey[pygame.K_LEFT]): instanceObject.x -= horizontalSpeed 
    if (pressPyKey[pygame.K_RIGHT]):instanceObject.x += horizontalSpeed 

    if (pressedPyKey[pygame.K_z] and globalVariable["currentBulletMegazine"] > 0):
        instanceName = f"bulletInstWithId{random.randint(-99999999999999999999999999 , 9999999999999999999999999)}{random.randint(-9999 , 111111111111114342342)} {random.choice(["raand1","radnd2","rand3id2","radsf"])}"
        inst = installInstance(instance(assets["spr_bullet"], instanceObject.x+35,instanceObject.y , 30,30 , 0) , instanceName)

        def bulletLogic(instanceName=instanceName):
            moveInstance(instanceName , 0 , -20)
            instanceSetDebris(instanceName , FramePerSecond*5)


        inst.onStep = bulletLogic
        globalVariable["bulletList"].append(instanceName)

        globalVariable["currentBulletMegazine"] -= 1
        
        if (globalVariable["currentBulletMegazine"] <= 0):
            globalVariable["bulletReloadTimer"] = globalVariable["config_bulletReloadTime"]


        assets["snd_fire"].set_volume(max(1 * random.random() , 0.3))
        assets["snd_fire"].play()
    
    




def enemyLogic(instanceName):
    if (globalVariable["isLose"])or(globalVariable["isWin"]): return
    if (instanceExist(instanceName)):
        instanceObject = findFirstInstance(instanceName)
        instanceObject.y += 2

        def resetEnemy():
            instanceObject.x = random.randint(0 , displayWidth-100)
            instanceObject.y = -150



        if (instanceExist("player")):
            if (instanceObject.isColliding(findFirstInstance("player"))):
                resetEnemy()
                globalVariable["playerHealth"] -= 1
                



        

        for bulletName in globalVariable["bulletList"]:
            if (instanceExist(bulletName)):
                bulletObject = findFirstInstance(bulletName)

                if (instanceObject.isColliding(bulletObject)):
                    resetEnemy()
                    globalVariable["score"] += 1

                    instanceDestroy(bulletName)
            







def enemyCollidePlaceholderLogic(instanceName):
    instanceObject = findFirstInstance(instanceName)
    if (not isinstance(instanceObject , instance)): return
    

    collidingInstanceList = instanceObject.collidingList()
    for collidingInstanceName in collidingInstanceList:
        collidingInstance = findFirstInstance(collidingInstanceName)
        if (isinstance(collidingInstance , instance)):
            if ("enemyWithId" in collidingInstanceName):
                collidingInstance.x = random.randint(0 , displayWidth-100)
                collidingInstance.y = 150
                globalVariable["enemyMissCount"] += 1

    
            
        






def asteroidLogic(instanceName):
    if (globalVariable["isLose"])or(globalVariable["isWin"]): return
    instanceObject = findFirstInstance(instanceName)
    instanceObject.y += 1
    instanceObject.rotation += 1

    if (instanceExist("player")):
        if (instanceObject.isColliding(findFirstInstance("player"))):
            instanceObject.x = random.randint(0 , displayWidth-100)
            instanceObject.y = -150

            globalVariable["playerHealth"] -= 1
        



        



def controllerDrawLogic(instanceName):
    instanceObject = findFirstInstance("controller")

    globalVariable["surfaceIndicatorGUI"] = assets["fnt_arialSmall"].render(f"Score:{globalVariable['score']}\nMissed:{globalVariable['enemyMissCount']}\nHealth:{globalVariable['playerHealth']}" , True , (255 , 255, 255))
    applicationSurface.blit(globalVariable["surfaceIndicatorGUI"] , (20 , 40))

    if (globalVariable["enemyMissCount"] >= 10)or(globalVariable["playerHealth"] <= 0):
        globalVariable["isLose"] = True

    if (globalVariable["score"] >= 20):
        globalVariable["isWin"] = True

    if (globalVariable["isLose"]):
        applicationSurface.blit(globalVariable["surfaceGameoverText"],
                                (displayWidth*0.38 , displayHeight*0.45))
        
    if (globalVariable["isWin"]):
        surfaceWinText = assets["fnt_arial"].render("YOU WIN" , True , (0 , 255 , 0))
        applicationSurface.blit(surfaceWinText , (displayWidth*0.38 , displayHeight*0.45))



    if (globalVariable["currentBulletMegazine"] <= 0):

        globalVariable["currentBulletMegazine"] = 0

        globalVariable["bulletReloadTimer"] -= 1

        if (globalVariable["bulletReloadTimer"] <= 0):
            globalVariable["currentBulletMegazine"] = globalVariable["config_bulletMegazine"]
            globalVariable["bulletReloadTimer"] = 0

    
    if (globalVariable["currentBulletMegazine"] <= 0):
        detik = round(globalVariable['bulletReloadTimer'] / FramePerSecond, 2)
        globalVariable["surfaceIndicatorGUI2"]= assets["fnt_arialSmall"].render(f"RELOADING... ({detik})" , True , (255 , 255, 255))
        applicationSurface.blit(globalVariable["surfaceIndicatorGUI2"] , (displayWidth*0.38 , displayHeight*0.92))



        





    
#-----------------------








#-----------------------
# INISIALISASI (Init instansi atau DLL)
#-----------------------
assets["snd_space"].set_volume(0.08)
assets["snd_space"].play(-1)

globalVariable["isLose"] = False
globalVariable["isWin"] = False

globalVariable["enemyMissCount"] = 0
globalVariable["bulletList"] = []
globalVariable["score"] = 0

globalVariable["playerHealth"] = 3
globalVariable["bulletReloadTimer"] = 0
globalVariable["currentBulletMegazine"] = 5

globalVariable["config_bulletMegazine"] = globalVariable["currentBulletMegazine"]
globalVariable["config_bulletReloadTime"] = FramePerSecond*3




globalVariable["surfaceGameoverText"] = assets["fnt_arial"].render("YOU LOSE" , True , (255 , 0 , 0))
globalVariable["surfaceIndicatorGUI"] = assets["fnt_arialSmall"].render(f"Score:{globalVariable['score']}\nMissed:{globalVariable['enemyMissCount']}\nHealth:{globalVariable['playerHealth']}" , True , (255 , 255, 255))
globalVariable["surfaceIndicatorGUI2"]= assets["fnt_arialSmall"].render(f"RELOADING... ({globalVariable['bulletReloadTimer']})" , True , (255 , 255, 255))


controller = installInstance(instance(assets["spr_bullet"] , 0 , 0 , 1 , 1 , 0) , "controller")
controller.onDraw = lambda: controllerDrawLogic(controller)


installInstance(instance(assets["spr_galaxy"] , 0 , 0 , displayWidth + 60 , displayHeight , 0) , "background")

player = installInstance(instance(assets["spr_rocket"] , displayWidth/2.3, displayHeight*0.75 , 100 , 130) , "player")
player.onStep = lambda: playerControl("player" , 10 , 0)

for i in range(1 , 6):
    instName = f"enemyWithId{i}"
    enemy = installInstance(instance(assets["spr_ufo"] , random.randint(0 , displayWidth - 100) ,-150 , 110 , 80 , 0) , instName)
    enemy.onStep = lambda n=instName: enemyLogic(n)

for i in range(1 , 3):
    instName = f"enemyWithId{i+10}"
    asteroid = installInstance(instance(assets["spr_asteroid"] , random.randint(0 , displayWidth - 100) , -150  , 90 , 90 , 0) , instName)
    asteroid.onStep = lambda n=instName: asteroidLogic(n)
    asteroid.drawRotationPos = "center"
    

collider = installInstance(instance(assets["spr_galaxy"] , 45 , displayHeight + 150 , displayWidth - 100 , 40 , 0) , "enemyCollidePlaceholder")
collider.onStep = lambda: enemyCollidePlaceholderLogic("enemyCollidePlaceholder")

#-----------------------






  

#-----------------------
# PERULANGAN LOGIKA GAME
#-----------------------
while (isRunning):


    #---
    #V ENGINE STEP
    #---
    onDrawGUI = False
    for pyKey in pygame.event.get():
        if (pyKey.type == pygame.QUIT):
            isRunning = False

    for instanceName , instanceObject in queueInstance.items():
        installedInstance[instanceName] = instanceObject
    queueInstance.clear()


    for instanceName in destroyQueueInstanceName:
        if (instanceName in installedInstance): installedInstance.pop(instanceName)
        elif (instanceName in queueInstance):   queueInstance.pop(instanceName)
    destroyQueueInstanceName.clear()

    for instanceName , instanceObject in installedInstance.items():
            if (isinstance(instanceObject , instance)):
                instanceObject.forceUpdate()
                if (callable(instanceObject.onStep)):
                    instanceObject.onStep()
                
            
    #---








    #---
    #V STEP
    #---
  

    #---




    #---
    #V ENGINE DRAW CAMERA
    #---
    applicationSurface.blit(cameraSurface)
    cameraSurface.fill(backgroundColor)
    for instanceName , instanceObject in installedInstance.items():
        if (isinstance(instanceObject , instance)):
            if (callable(instanceObject.onDraw)):
               instanceObject.onDraw()
    #---





    #---
    #V DRAW CAMERA
    #---


    #---






    #---
    #V DRAW GUI
    #---
    onDrawGUI = True
    for instanceName , instanceObject in installedInstance.items():
        if (isinstance(instanceObject , instance)):
            if (callable(instanceObject.onDrawGUI)):
                instanceObject.onDrawGUI()
    #---





    #V Very end step
    pygame.display.flip()
    clock.tick(FramePerSecond)
#-----------------------






#-----------------------
# AKHIR LOGIKA GAME
#-----------------------
pygame.quit()
sys.exit()
#-----------------------


