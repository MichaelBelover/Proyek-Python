#V Inisialisasi Modul
from moduleInit import *
import moduleInit







#========================
# VARIABEL GLOBAL
#========================
###V VARIABEL YANG AMAN DIUBAH.
screenWidth = 1000            #< Lebar jendela game.
screenHeight = 800            #< Tinggi jendela game.
solidFPS = 30                #< (Frame Per Second) Jumlah bingkai yang akan dirender dalam 1 detik.


DEBUGUI = False                    #< Apakah informasi akan ditampilkan atau tidak.

#V Data yang akan disimpan untuk progres.
SaveData = {
}

#V Sekumpulan aset mentah yang akan digunakan untuk game, alih-alih menyatukan dengan variabel luar lain.
rawAssets = {
    "gameIcon" : pygame.image.load(os.path.join("assets" , "RedSoul.png")),
}

#V Sekumpulan aset yang sudah dibungkus.
Assets = {}

roomInstances = {} #< Variabel sekumpulan ruangan. 

globalVariables = {} #< Variabel yang aman untuk diakses semua event.
framePassed = 0
consts = { #< Konstanta yang aman untuk diakses semua event, tetapi tidak boleh diubah nilainya.
    "surface" : {
        "applicationSurface" : 0,
        "cameraSurface" : 1,
    },
    "col" : {
        "white" : (255, 255, 255),
        "black" : (0, 0, 0),
        "red"   : (255, 0, 0),
        "green" : (0, 255, 0),
        "blue"  : (0, 0, 255),
        "yellow": (255, 255, 0),
        "cyan"  : (0, 255, 255),
        "magenta": (255, 0, 255),
        "gray"  : (128, 128, 128),
        "lightYellow": (255, 255, 150),
        "lightGreen": (150, 255, 150),
        "neonPink": (255, 20, 147),
        "neonBlue": (0, 255, 255),
        "neonGreen": (57, 255, 20),
    },

}





###V VARIABEL YANG TIDAK AMAN DIUBAH.
aplicationSurface = pygame.display.set_mode((screenWidth , screenHeight))
clock = pygame.time.Clock()
isRunning = True

previousRoomName = "Undefined" #< Nama dunia/Ruangan sebelumnya.
currentRoomName  = "Undefined" #< Nama dunia/Ruangan saat ini.

currentRoom = None #< Data dunia ruangan saat ini yang dipakai.
layers = {}        #< Hasil dari konversi blueprintLayer

currentFPS = 0
deltaTime = 0

currentTime = pygame.time.get_ticks()

timeSpawns = {}

onGuiLoop = False #< Apakah di event saat ini sedang berada di fase digambarnya GUI.

currentDrawColour = (255,255,255) #< Warna yang saat ini digunakan untuk menggambar.
currentDrawFontAsset = None #< Font yang saat ini digunakan untuk menggambar.

#V Event dengan sekumpulan fungsi/method nya yang sedang dijalankan di step saat ini.
runingEventNodes = {
        "beginStep" : [], "step" : [], "endStep" : [],
        "beginDraw" : [], "draw" : [], "endDraw" : [],
        "beginDrawGUI" : [], "drawGUI" : [], "endDrawGUI" : [],
}

#V Inisialisasi sistem
pygame.display.set_caption("Determination")
pygame.display.set_icon(rawAssets["gameIcon"])


#V Memuat save data (Data terakhir yang disimpan)
## (nanti guwa buat lgi mls)
#========================
















#========================
# FUNGSI / METODE GLOBAL
#========================
def roomForceUpdate():
    currentRoom.cameraX = max(0, min(currentRoom.cameraX, currentRoom.roomWidth - currentRoom.cameraWidth))
    currentRoom.cameraY = max(0, min(currentRoom.cameraY, currentRoom.roomHeight - currentRoom.cameraHeight))

    # Cek jika surface kamera perlu di-resize (misal kamera zoom-in / zoom-out)
    if currentRoom.cameraSurface.get_width() != currentRoom.cameraWidth or currentRoom.cameraSurface.get_height() != currentRoom.cameraHeight:
        currentRoom.cameraSurface = pygame.Surface((max(1 , currentRoom.cameraWidth) , max(1 , currentRoom.cameraHeight)))


def roomGoto(roomName):
    global currentRoom
    global previousRoomName
    global currentRoomName

    previousRoomName = currentRoomName 
    currentRoomName = roomName
    
    if (roomName in roomInstances):
        baseRoomBlueprint = roomInstances[roomName]
        roomInstance = room(baseRoomBlueprint.roomWidth, baseRoomBlueprint.roomHeight)
        roomInstance.blueprintLayers = copy.deepcopy(baseRoomBlueprint.blueprintLayers)
        
        # 1. Dictionary untuk MENYARING HANYA instansi yang persisten berdasarkan nama layernya
        # Format: { "NamaLayer": { "NamaInstansi": ObjekInstansi } }
        persistInstancesData = {} 
        persistDepthData = {}
        

        if (isinstance(roomInstance, room)):
            currentRoom = roomInstance 

            # 2. Ekstrak objek persisten
            for layerName, layerObj in layers.items():
                if isinstance(layerObj, instanceLayer):
                    for instName, instObj in layerObj.instances.items():
                        if isinstance(instObj, instance) and instObj.roomPersist:
                            
                            # Buat dictionary layer jika belum ada di persistData
                            if layerName not in persistInstancesData:
                                persistInstancesData[layerName] = {}
                            
                            # Simpan HANYA instansi yang persisten
                            persistInstancesData[layerName][instName] = instObj
                    persistDepthData[layerName] = layerObj.depth        

            # 3. Bersihkan memori layer room lama
            layers.clear() 
            
            # 4. Bangun layer baru murni dari blueprint terlebih dahulu
            for layerName, blueprintLayer in roomInstance.blueprintLayers.items():
                if isinstance(blueprintLayer, backgroundLayer):
                    layers[layerName] = backgroundLayer(
                        blueprintLayer.spriteAsset, blueprintLayer.horizontalTile, 
                        blueprintLayer.verticalTile, blueprintLayer.strecth, blueprintLayer.colour
                    )
                elif isinstance(blueprintLayer, instanceLayer):
                    # Salin instansi murni dari blueprint
                    layers[layerName] = instanceLayer(blueprintLayer.instances, blueprintLayer.depth)
                else:
                    print(f"FATAL ERROR!!! Tipe layer tidak dikenali: {blueprintLayer}")
                    return

            # 5. SUNTIKKAN (Inject) instansi persisten ke layer room baru
            for layerName, persistInstancesDict in persistInstancesData.items():
                # Jika layer dengan nama yang sama ada di room baru, gabungkan instansinya
                if layerName in layers and isinstance(layers[layerName], instanceLayer):
                    layers[layerName].instances.update(persistInstancesDict)
                else:
                    # Jika room baru tidak memiliki layer tersebut, buat layer baru khusus 
                    # untuk menampung objek persisten ini (Depth bisa disesuaikan/diambil dari data lama)
                    layers[layerName] = instanceLayer(persistInstancesDict, persistDepthData[layerName])
                    

        else:
            print("FATAL ERROR!!! Gagal membuat instansi class room!!  di fungsi roomGoto!")
            return
    else:
        print(f"ERROR!!! Nama room tidak ditemukan: {roomName} di fungsi roomGoto!")
        return
    
    




    


# blueprint adalah suatu resep layer yang akan diciptakan saat ruangan/dunia dimasuki.
# Disarankan fungsi kaya gini harus dijalankan sebelum game berjalan.
def roomAddBlueprint(roomName, layerName, layerInstance):
    roomInstance = None


    #V Cek jika nama ruangan yang diberikan ada di variabel roomInstances, dan jika benar, cek apakah nilai yang diberikan berupa instansi class room atau tidak.
    if (roomName in roomInstances):
        roomInstance = roomInstances[roomName]
        if (not isinstance(roomInstance , room)):
            print(f"FATAL ERROR!!! Di variabel roomInstances terdapat nilai selain instansi class room!!\nNilai: {roomInstance}")
            return
    else:
        print(f"ERROR!!! Nama room tidak ditemukan di roomInstance di fungsi roomAddBlueprint\nArgumen \"roomName\": {roomName}")
        return
    

    #V Cek jika layerInstance yang diberikan berupa instansi class backgroundLayer atau instanceLayer atau tidak.
    if (not isinstance(layerInstance , backgroundLayer))and(not isinstance(layerInstance , instanceLayer)):
        print(f"ERROR!!! Argumen \"layerInstance\" SALAH DI FUNGSI BERNAMA \"roomAddBlueprint\"\nInfo Argumen: {layerInstance}")
        return
    
    #V Menambahkan blueprint layer ke dalam variabel blueprintLayers di class room.
    roomInstance.blueprintLayers[layerName] = layerInstance
    return layerInstance #< Mengembalikan layerInstance yang sudah ditambahkan ke dalam blueprint, untuk memudahkan manipulasi di dalam layer tersebut.



# Fungsi ini digunakan untuk membuat instansi baru di dalam layer yang sudah dibuat blueprint nya, agar dapat digunakan untuk menyimpan data objek instansi yang akan digunakan di dalam game. Fungsi ini hanya dapat digunakan setelah ruangan/dunia dimasuki, karena fungsi ini membutuhkan layer asli yang sudah dikonversi dari blueprint layer saat ruangan/dunia dimasuki.
# PERHATIAN: Instansi yang dibuat melalui fungsi ini tidak tetap di memori, jadi jika ruangan/dunia diganti, maka semua instansi yang dibuat melalui fungsi ini akan hilang. Jika ingin membuat instansi yang tetap di memori, maka harus membuatnya melalui blueprint layer di dalam ruangan/dunia.
def createInstance(layerName , instanceName , instanceObject):
    if (layerName in layers):
        layer = layers[layerName]
        if (isinstance(layer , instanceLayer)):
            layer.instances[instanceName] = instanceObject
        else:
            print(f"ERROR!!! Layer dengan nama \"{layerName}\" bukan berupa instanceLayer di fungsi room.createInstance\nArgumen \"layerName\": {layerName}\nArgumen \"instanceObject\": {instanceObject}")
    else:
        print(f"ERROR!!! Nama layer tidak ditemukan di variabel layers di fungsi room.createInstance\nArgumen \"layerName\": {layerName}\nArgumen \"instanceObject\": {instanceObject}")




#V Fungsi ini digunakan untuk mencari instansi pertama dengan nama tertentu di dalam layer
def findFirstInstance(layerName , instanceName):
    if (not layerName in layers): return print(f"ERROR!!! Layer dengan nama \"{layerName}\" bukan berupa instanceLayer di fungsi findFirstInstance\nArgumen \"layerName\": {layerName}")
    layerTargetInstances = layers[layerName].instances
    if (instanceName in layerTargetInstances):
        return layerTargetInstances[instanceName]
    else:
        print(f"INSTANSI TIDAK DITEMUKAN DI FUNGSI findFirstInstance! Nama instansi: {instanceName}")
        return









#V Mengembalikan surface yang sedang digunakan oleh engine (mengembalikan surface untuk GUI atau surface untuk dunia game)
def getCurrentUsedSurface():
    if (onGuiLoop): return aplicationSurface
    else:           return currentRoom.cameraSurface
    


#V Fungsi untuk menggambar permukaan tertentu ke permukaan yang sedang digunakan oleh engine (permukaan untuk GUI atau permukaan untuk dunia game)
def surfaceDraw(surfaceToDraw , x = 0 , y = 0 , surfaceTarget = None):
    if (surfaceTarget is not None):
        if (surfaceTarget == consts["surface"]["applicationSurface"])or(surfaceTarget == aplicationSurface):
            aplicationSurface.blit(surfaceToDraw , (x, y))

        elif (surfaceTarget == consts["surface"]["cameraSurface"])or(surfaceTarget == currentRoom.cameraSurface):
            currentRoom.cameraSurface.blit(surfaceToDraw , (x - currentRoom.cameraX, y - currentRoom.cameraY))

        elif (isinstance(surfaceTarget , pygame.surface.Surface)):
            surfaceTarget.blit(surfaceToDraw , (x, y))

        else:
            print(f"ERROR!!! Argumen \"surfaceTarget\" SALAH DI FUNGSI BERNAMA \"surfaceDraw\"\nInfo Argumen: {surfaceTarget}")
            return

    else:
        if (onGuiLoop):
            aplicationSurface.blit(surfaceToDraw , (x, y))
        else:
            currentRoom.cameraSurface.blit(surfaceToDraw , (x - currentRoom.cameraX, y - currentRoom.cameraY))







#V fungsi untuk mengatur warna yang akan digunakan untuk menggambar
def drawSetColour(colour):
    global currentDrawColour
    currentDrawColour = colour


#V Fungsi untuk mengatur font yang akan digunakan untuk menggambar text dengan fungsi bernama drawText()
def drawSetFont(_fontAsset):
    global currentDrawFontAsset
    if isinstance(_fontAsset , fontAsset):
        currentDrawFontAsset = _fontAsset
    else:
        currentDrawFontAsset = fontAsset("Arial" , 12)






# Fungsi untuk menggambar persegi dengan koordinat rect.
def drawRect(X1 , Y1 , X2 , Y2 , colour = None):
    if colour is None:
        colour = currentDrawColour
    pygame.draw.rect(getCurrentUsedSurface() , colour , (X1 , Y1 , X2 , Y2))






#V Fungsi untuk menggambar sprite ke dunia game atau ke GUI
def drawSprite(_spriteAsset, x, y, scaleX=1, scaleY=1, rotation=0, subImage=0, alpha=255, drawColor=(255, 255, 255)):
    imageSurface = None

    # Validasi Asset (Sama seperti kodemu)
    if isinstance(_spriteAsset, spriteAsset):
        if isinstance(_spriteAsset.surface, pygame.surface.Surface):
            imageSurface = _spriteAsset.surface
        elif isinstance(_spriteAsset.surface, list):
            imageSurface = _spriteAsset.surface[subImage]
        else:
            print(f"ARGUMEN \"_spriteAsset\" SALAH!\nInfo: {_spriteAsset}")
            return
    else:
        print(f"ERROR!!! Argumen '_spriteAsset' SALAH!\nArgumen: {_spriteAsset}")
        return

    # 1. Scaling (Hanya eksekusi jika scale bukan 1)
    if scaleX != 1 or scaleY != 1:
        newWidth = int(imageSurface.get_width() * scaleX)
        newHeight = int(imageSurface.get_height() * scaleY)
        imageSurface = pygame.transform.scale(imageSurface, (newWidth, newHeight))

    # 2. Rotasi (Hanya eksekusi jika rotation bukan 0)
    if rotation % 360 != 0:
        pivot_x = x + (_spriteAsset.xRotationPoint * scaleX)
        pivot_y = y + (_spriteAsset.yRotationPoint * scaleY)
        pivot_pos = pygame.math.Vector2(pivot_x, pivot_y)

        original_rect = imageSurface.get_rect(topleft=(x, y))
        offset = pivot_pos - original_rect.center

        imageSurface = pygame.transform.rotate(imageSurface, rotation)
        rotated_offset = offset.rotate(-rotation)

        new_center = pivot_pos - rotated_offset
        rotated_rect = imageSurface.get_rect(center=(round(new_center.x), round(new_center.y)))
        
        x = rotated_rect.x
        y = rotated_rect.y
    
    # 3. Pewarnaan & Alpha (HANYA DILAKUKAN JIKA DIPERLUKAN)
    # Jika drawColor putih (255,255,255) dan alpha 255, kita TIDAK PERLU copy dan fill.
    if drawColor != (255, 255, 255) or alpha < 255:
        coloredImageSurface = imageSurface.copy()
        
        if (drawColor != (255, 255, 255))or(currentDrawColour != (255, 255, 255)):
            if (currentDrawColour != (255, 255, 255)):
                drawColor = currentDrawColour

            coloredImageSurface.fill(drawColor, special_flags=pygame.BLEND_RGBA_MULT)
            
        if alpha < 255:
            coloredImageSurface.set_alpha(alpha)
            
        # Gambar yang sudah dimodifikasi warnanya
        surfaceDraw(coloredImageSurface, x, y)
    else:
        # Langsung gambar surface asli jika tidak ada perubahan warna/alpha (Sangat menghemat CPU)
        surfaceDraw(imageSurface, x, y)












 # fungsi untuk menggambar teks di dunia atau di GUI, namanya aja drawText
def drawText(string , x , y , xScale = 1 , yScale = 1 , rotation = 0 , color = None , alpha = 255):
    global currentDrawFontAsset
    
    if color is None:
        color = currentDrawColour

    textSurface = currentDrawFontAsset.font.render(str(string), True, color)
    textSurface.set_alpha(alpha)
    if xScale != 1 or yScale != 1:
        newWidth = int(textSurface.get_width() * xScale)
        newHeight = int(textSurface.get_height() * yScale)
        textSurface = pygame.transform.scale(textSurface, (newWidth, newHeight))

    if rotation != 0:
        textSurface = pygame.transform.rotate(textSurface, rotation)

    surfaceDraw(textSurface, x, y)






def wavy(axis, offset, amplitudo=6, kecepatan=7):
    """
    Mengembalikan nilai real (float) untuk efek pergerakan berputar/bergelombang.
    axis      : String 'X' atau 'Y'
    offset    : Nilai urutan/jarak antar huruf (misal: i * 0.5)
    amplitudo : Seberapa jauh jarak goyangannya
    kecepatan : Seberapa cepat pergerakannya
    """
    # Mengambil waktu dalam detik secara otomatis
    waktu = currentTime / 1000.0
    sudut = (waktu * kecepatan) + offset
    
    if axis.upper() == "X":
        return math.cos(sudut) * amplitudo
    elif axis.upper() == "Y":
        return math.sin(sudut) * amplitudo
    
    return 0.0 # Kembalikan 0 jika axis salah input
#========================



















#========================
# KONSTRUKTOR / KELAS GLOBAL
#========================
#V Ruangan adalah tempat dimana instansi berada. Ruangan memiliki ukuran, latar belakang, dan kamera.
class room:
    def __init__(self , roomWidth , roomHeight):
        self.roomWidth  = roomWidth
        self.roomHeight = roomHeight

        # LAYER HANYA BLUEPRINT SAJA (Akan dikonversi sebagai objek asli saat room dimasuki)
        self.blueprintLayers = {}



        self.cameraX = 0
        self.cameraY = 0
        self.cameraWidth = screenWidth
        self.cameraHeight = screenHeight
        self.cameraRoomSizeLimit = True
        self.cameraSurface = pygame.Surface((self.cameraWidth , self.cameraHeight))





    

                


       






#V Class spriteAsset ini digunakan untuk menyimpan gambar yang akan dapat digambar di layar tanpa bergantung pada class instance.
class spriteAsset:
    def __init__(self , pygameSurfaceOrList , xRotationPoint = 0 , yRotationPoint = 0):
        self.surface = None
        self.xRotationPoint = xRotationPoint
        self.yRotationPoint = yRotationPoint

        if (isinstance(pygameSurfaceOrList , pygame.surface.Surface))or(isinstance(pygameSurfaceOrList , list)):
            self.surface = pygameSurfaceOrList
        else:
            print("GAGAL MEMBUAT SURFACE DI CLASS \"SpriteAsset\"")
        
    def hasAnimation(self):
        return (isinstance(self.surface , list))
    
    def getSurface(self , index = 0):
        if (isinstance(self.surface , list)):
            return self.surface[index]
        elif (isinstance(self.surface , pygame.Surface)):
            return self.surface
        else:
            return None



#V Class fontAsset ini digunakan untuk menggambar teks.
class fontAsset:
    def __init__(self , nameOrPygameFontObject , fontSize):
        self.fontSize = fontSize
        self.font     = None

        if isinstance(nameOrPygameFontObject , pygame.font.Font):
            self.font = nameOrPygameFontObject
        else:
            self.font = pygame.font.SysFont(nameOrPygameFontObject, fontSize)









class backgroundLayer():
    def __init__(self , spriteAsset , horizontalTile = False , verticalTile = False , strecth = False , colour = (255,255,255)):
        self.spriteAsset    = spriteAsset
        self.horizontalTile = horizontalTile
        self.verticalTile   = verticalTile
        self.strecth        = strecth
        self.colour         = colour
        self.isActive       = True

        self.animationCurrentFrame = 0
        self.animationPlay = False
        self.animationLoop = False
        self.animationSpeed = 0.025


    def draw(self):
        if (not isinstance(self.spriteAsset , spriteAsset)):
            print(f"ERROR!! variabel \"self.spriteAsset\" SALAH! di fungsi draw di class backgroundLayer\nArg yang diberikan:{self.spriteAsset}")
            return 
        
        #V mempersiapkan warna penggambaran
        originalDrawColour = currentDrawColour
        drawSetColour(self.colour)

        
        
        frameTotal = 1 #< Jumlah gambar yang akan digunakan untuk menggambar sprite, jika spriteAsset berupa list, maka frameTotal akan diatur sesuai dengan jumlah gambar di dalam list tersebut.
        if (self.animationPlay):
            #V Logika animasi
            #V Menghitung jumlah gambar yang terinstal pada spriteAsset
            if (isinstance(self.spriteAsset.surface , list)):
                frameTotal = len(self.spriteAsset.surface)

            #V Jika jumlah gambar melebihi 1
            if (self.animationPlay and frameTotal > 1):
                self.animationCurrentFrame += self.animationSpeed

            
            #V Mencegah frame melebihi batas indeks list
                if self.animationCurrentFrame >= frameTotal:
                    if self.animationLoop:
                        self.animationCurrentFrame = 0 #< Kembali ke frame awal
                    else:
                        self.animationCurrentFrame = frameTotal - 1 #< Berhenti di frame terakhir

            #V Mencegah error jika nilai frameTotal tiba-tiba berubah
            frameTotal = int(self.animationCurrentFrame) % max(1, frameTotal)
        
        imageSurface = self.spriteAsset.getSurface(frameTotal)


        #V Jika gambar diperintahkan melebar memenuhi room
        if (self.strecth):
            # 1. Ambil ukuran asli gambar
            original_width = imageSurface.get_width()
            original_height = imageSurface.get_height()

            # 2. Hitung ScaleX dan ScaleY (Target / Asli)
            # Menggunakan ternary operator untuk mencegah pembagian dengan nol (ZeroDivisionError)
            scaleX = currentRoom.roomWidth / original_width if (original_width) > 0 else 1
            scaleY = currentRoom.roomHeight / original_height if (original_height) > 0 else 1
            
            
            # 3. Panggil fungsi drawSprite
            # KOREKSI 2: drawSprite meminta argumen pertama berupa object 'spriteAsset', bukan 'imageSurface'.
            drawSprite(self.spriteAsset, 0,0 , scaleX,scaleY , 0 , frameTotal)
            
            
            




        #V Jika gambar diperintahkan sebagai tile memenuhi room
        elif (self.horizontalTile)or(self.verticalTile):
            original_width = imageSurface.get_width()
            original_height = imageSurface.get_height()

            xTileCount = currentRoom.roomWidth // original_width + 1
            yTileCount = currentRoom.roomHeight // original_height + 1
            
            drawCurrentX = 0
            drawCurrentY = 0

            #V Menggambar sisi tile vertikal dan horizontal
            if (self.horizontalTile and self.verticalTile):
                for x in range(xTileCount):
                    for y in range(yTileCount):

                        drawSprite(self.spriteAsset, x*original_width,y*original_height , 1,1 , 0 , frameTotal)



            #V Menggambar sisi tile vertikal
            elif (self.verticalTile):
                for i in range(xTileCount):
                    drawSprite(self.spriteAsset , drawCurrentX,0 , 1,1 , 0 , frameTotal)
                    drawCurrentX += original_width

            #V Menggambar sisi tile horizontal
            elif (self.horizontalTile):
                for i in range(yTileCount):
                    drawSprite(self.spriteAsset , 0,drawCurrentY , 1,1 , 0 , frameTotal)
                    drawCurrentY += original_height
        
        #V Jika tidak ada parameter yang memenuhi syarat, background akan digambar hanya 1 tile saja
        else:
            drawSprite(self.spriteAsset, 0,0 , 1,1 , 0 , frameTotal)

        #V Mengembalikan warna sebelumnya untuk fase penggambaran berikutnya.
        drawSetColour(originalDrawColour)
        iterationCount += 1
                    
            





class instanceLayer():
    def __init__(self , instances = {} , depth = 0):
        self.instances         = instances
        self.depth             = depth
        




#V Klass jika cooldown (callDelay) mencapai 0, fungsi (functionToCall) akan dijalankan.
#V atur parameter callLoop ke nilai -1 agar perulangan akan berjalan selamanya.
class timeSpawn(): # tambahkan fitur maxloop, maximal perulangan pemanggilan
    def __init__(self , functionToCall , callDelay , callLoop = 0):
        self.functionToCall = functionToCall
        self.callDelay = callDelay
        self.callLoop = callLoop

        self.currentCallLoop = 0

        self.UID = f"tsid{uuid.uuid4()}"
        self.currentDelayTime = 0

        self.isPaused = False


    #V Memulai eksekusi
    def execute(self):
        self.currentCallLoop = self.callLoop
        self.isPaused = False
        self.currentDelayTime = self.callDelay
        timeSpawns[self.UID] = self

    #V Membatalkan eksekusi
    def cancel(self):
        timeSpawns.__delitem__(self.UID)







        

#V Class instance adalah objek yang dapat ditempatkan di dalam ruangan. Instance memiliki posisi, ukuran, dan sprite yang dapat digambar di layar.
class instance:
    def __init__(self , _spriteAsset , x , y , xScale , yScale , eventDefinition = {} , setVars = {}):
        #V INISIALISASI VARIABEL
        self.spriteAsset = _spriteAsset
    
        self.previousX = x
        self.previousY = y
        self.x = x
        self.y = y
        self.xScale = xScale
        self.yScale = yScale
        self.rotation = 0
        self.blend = (255,255,255)

        self.solid = False
        self.visible = True

        self.roomPersist = False

        self.animationCurrentFrame = 0
        self.animationPlay = False
        self.animationLoop = True
        self.animationSpeed = 0.025

        self.isDestroySoon = False #< Apakah di step berikutnya, instansi ini akan dihancurkan?
        self.createEventHasBeenCalled = False #< Apakah create event sudah di jalankan sebelumnya atau belum?


        

        

        #V INISIALISASI EVENT
        self.events = {
            "create"       : None,  

            "beginStep"    : None,
            "step"         : None,
            "endStep"      : None,

            "beginDraw"    : None,
            "draw"         : self.drawSelf,
            "endDraw"      : None,

            "beginDrawGUI" : None,
            "drawGUI"      : None,
            "endDrawGUI"   : None,

            "onDestroy"    : None,
        }

        #V Menginstal semua argumen event ke variabel "events"
        for eventName in eventDefinition:
            eventFunction = eventDefinition[eventName]
            if (callable(eventFunction)): self.events[eventName] = eventFunction

        #V Menginstal semua pengaturan opsional (Pengaturan opsional untuk mengatur variabel yang ada di class ini seperti animationSpeed, currentSprite, DLL)
        for settingName in setVars:
            setVarArgument = setVars[settingName]
            self.__dict__[settingName] = setVarArgument



    def setVar(self , variableName , variableValue):
        self.__dict__[variableName] = variableValue

    def getVar(self , variableName):
        value = self.__dict__[variableName]

        if (value is not None): return value;
        else:
            #print(f"Fungsi getVar di instance mengembalikan nilai None!\n di instansi {self}")
            return value


    
    def drawSelf(self):
        
        frameTotal = 1 #< Jumlah gambar yang akan digunakan untuk menggambar sprite, jika spriteAsset berupa list, maka frameTotal akan diatur sesuai dengan jumlah gambar di dalam list tersebut.
        #V Menghitung jumlah gambar yang terinstal pada spriteAsset
        if (isinstance(self.spriteAsset.surface , list)):
            frameTotal = len(self.spriteAsset.surface)

        #V Jika jumlah gambar melebihi 1
        if (self.animationPlay and frameTotal > 1):
            self.animationCurrentFrame += self.animationSpeed


        #V Mencegah frame melebihi batas indeks list
            if self.animationCurrentFrame >= frameTotal:
                if self.animationLoop:
                    self.animationCurrentFrame = 0 #< Kembali ke frame awal
                else:
                    self.animationCurrentFrame = frameTotal - 1 #< Berhenti di frame terakhir

        #V Mencegah error jika nilai frameTotal tiba-tiba berubah
        frameTotalSafe = int(self.animationCurrentFrame) % max(1, frameTotal)

        if (self.visible):
            originalDrawColour = currentDrawColour
            drawSetColour(self.blend)
            drawSprite(self.spriteAsset,
                        self.x, self.y,
                        self.xScale  , self.yScale   , self.rotation,
                        frameTotalSafe)
            drawSetColour(originalDrawColour)


            



    def forceUpdate(self):
        #V Mengatur posisi sebelumnya agar dapat digunakan untuk logika seperti pergerakan dan tabrakan.
        self.previousX = self.x
        self.previousY = self.y


    def destroy(self):
        self.isDestroySoon = True


    def isColliding(self, instance2):
        # 1. Perbaikan Validasi: Pastikan kedua instance memiliki spriteAsset
        if not hasattr(self, 'spriteAsset') or not hasattr(instance2, 'spriteAsset'):
            return False

        # --- HITUNG BOUNDING BOX UNTUK SELF ---
        originX = self.spriteAsset.xRotationPoint
        originY = self.spriteAsset.yRotationPoint
        
        # 2. Perbaikan Animasi: Cek apakah surface berupa list (animasi) atau single surface
        if isinstance(self.spriteAsset.surface, list):
            surfaceWidth = self.spriteAsset.surface[0].get_width()
            surfaceHeight = self.spriteAsset.surface[0].get_height()
        else:
            surfaceWidth = self.spriteAsset.surface.get_width()
            surfaceHeight = self.spriteAsset.surface.get_height()

        self_actual_width = surfaceWidth * abs(self.xScale)
        self_actual_height = surfaceHeight * abs(self.yScale)
        
        self_left = self.x - (originX * abs(self.xScale))
        self_right = self_left + self_actual_width
        self_top = self.y - (originY * abs(self.yScale))
        self_bottom = self_top + self_actual_height

        # --- HITUNG BOUNDING BOX UNTUK INSTANCE 2 ---
        inst2_originX = instance2.spriteAsset.xRotationPoint
        inst2_originY = instance2.spriteAsset.yRotationPoint
        
        # Cek hal yang sama untuk objek lawan tabrakan
        if isinstance(instance2.spriteAsset.surface, list):
            inst2_surfaceWidth = instance2.spriteAsset.surface[0].get_width()
            inst2_surfaceHeight = instance2.spriteAsset.surface[0].get_height()
        else:
            inst2_surfaceWidth = instance2.spriteAsset.surface.get_width()
            inst2_surfaceHeight = instance2.spriteAsset.surface.get_height()

        inst2_actual_width = inst2_surfaceWidth * abs(instance2.xScale)
        inst2_actual_height = inst2_surfaceHeight * abs(instance2.yScale)
        
        inst2_left = instance2.x - (inst2_originX * abs(instance2.xScale))
        inst2_right = inst2_left + inst2_actual_width
        inst2_top = instance2.y - (inst2_originY * abs(instance2.yScale))
        inst2_bottom = inst2_top + inst2_actual_height

        # --- LOGIKA TABRAKAN AABB ---
        return (self_left < inst2_right and 
                self_right > inst2_left and 
                self_top < inst2_bottom and 
                self_bottom > inst2_top)
    




    

currentRoom = room(1 , 1)     
 #========================   
















#========================
#INISIALISASI YANG LAIN
#========================
drawSetFont(fontAsset("Arial" , 12))
#========================





























#===========================================================================================================
#===========================================================================================================
#===========================================================================================================
#===========================================================================================================
#===========================================================================================================






#========================
# INISIALISASI ASET MENTAH
#========================
#V Sekumpulan aset mentah yang akan digunakan untuk game, alih-alih menyatukan dengan variabel luar lain.
rawAssets = {
    "grassTile" : pygame.image.load(os.path.join("assets" , "grassTile.jpg")),
    "emptySpr" : pygame.image.load(os.path.join("assets" , "Empty.png")),

    "Pencil" : pygame.image.load(os.path.join("assets" , "Pencil.png")),
    "Eye" : pygame.image.load(os.path.join("assets" , "Eye.png")),
    "EyeFlipped" : pygame.image.load(os.path.join("assets" , "EyeFlipped.png")),
    "Leaf" : pygame.image.load(os.path.join("assets" , "Leaf.png")),
    "Bread" : pygame.image.load(os.path.join("assets" , "Bread.png")),
    "smileMounth" : pygame.image.load(os.path.join("assets" , "smileMounth.png")),
    "smileMounthF2" : pygame.image.load(os.path.join("assets" , "smileMounthF2.png")),

    "staticF1" : pygame.image.load(os.path.join("assets" , "static1.png")),
    "staticF2" : pygame.image.load(os.path.join("assets" , "static2.png")),

    "gameOver" : pygame.image.load(os.path.join("assets" , "gameOverText.png")),

    "serpihanJiwa1" : pygame.image.load(os.path.join("assets" , "serpihanJiwa1.png")),
    "serpihanJiwa2" : pygame.image.load(os.path.join("assets" , "serpihanJiwa2.png")),

    "redSoul" : pygame.image.load(os.path.join("assets" , "RedSoul.png")),
    "redSoulCrack" : pygame.image.load(os.path.join("assets" , "RedSoulCrack.png")),

    "BGMvoidStar" : os.path.join("assets" , "VOID STAR.mp3"),
    "BGMomegaFloweyIntro" : os.path.join("assets" , "omegaFloweyIntro.mp3"),

    "BGMHelp1" : os.path.join("assets" , "BGMHelp1.ogg"),
    "BGMHelp2" : os.path.join("assets" , "BGMHelp2.ogg"),
    "BGMHelp3" : os.path.join("assets" , "BGMHelp3.mp3"),

    "BGMFightPart1" : os.path.join("assets" , "BGMFightPart1.ogg"),
    "BGMFightPart2" : os.path.join("assets" , "BGMFightPart2.ogg"),
    "BGMFightPart3" : os.path.join("assets" , "BGMFightPart3.ogg"),

    "BGMFinal1" : os.path.join("assets" , "BGMFinal1.mp3"),
    "BGMFinal2" : os.path.join("assets" , "BGMFinal2.mp3"),
    "BGMFinal3" : os.path.join("assets" , "BGMFinal3.mp3"),

    "BGMdefeated" : os.path.join("assets" , "BGMdefeated.mp3"),

    "SEalarm1" : os.path.join("assets" , "SEalarm1.mp3"),
    "SEdied" : os.path.join("assets" , "SEdied.mp3"),
    "SEfatalHit" : os.path.join("assets" , "SEfatalHit.mp3"),
    "SEheal" : os.path.join("assets" , "SEheal.mp3"),
    "SEheavyHit" : os.path.join("assets" , "SEheavyHit.mp3"),
    "SEslash" : os.path.join("assets" , "SEslash.mp3"),
    "SEstatic" : os.path.join("assets" , "SEstatic.mp3"),

    

    "SEfloweySpeakThatsAWonderfulIdea" : os.path.join("assets" , "floweySpeakThatsAWonderfulIdea.mp3"),
    "SEomegaFloweyFightIntro" : os.path.join("assets" , "omegaFloweyFightIntro.mp3"),
    "SEomegaFloweyLaugh" : os.path.join("assets" , "omegaFloweyLaugh.mp3"),

}


#V Sekumpulan aset yang sudah dibungkus.
Assets = {
    "spr_heart" : spriteAsset([rawAssets["redSoul"] , rawAssets["redSoulCrack"]], 10,10),
    "spr_grassTile" : spriteAsset(rawAssets["grassTile"]),
    "spr_empty" : spriteAsset(rawAssets["emptySpr"]),

    "spr_pencil" : spriteAsset(rawAssets["Pencil"]),
    "spr_eye" : spriteAsset(rawAssets["Eye"]),
    "spr_eyeFlipped" : spriteAsset(rawAssets["EyeFlipped"] , 335),
    "spr_leaf" : spriteAsset(rawAssets["Leaf"] , 121),
    "spr_bread" : spriteAsset(rawAssets["Bread"]),
    "spr_smileMounth" : spriteAsset([rawAssets["smileMounth"] , rawAssets["smileMounthF2"]]),

    "spr_pieceOfHeart" : spriteAsset([rawAssets["serpihanJiwa1"] , rawAssets["serpihanJiwa2"]]),

    "spr_gameOverText" : spriteAsset(rawAssets["gameOver"]),

    "spr_static" : spriteAsset([rawAssets["staticF1"] , rawAssets["staticF2"]]),

    "snd_VOIDSTAR" : pygame.Sound(rawAssets["BGMvoidStar"]),
    "snd_thatsAWonderfulIdea" : pygame.Sound(rawAssets["SEfloweySpeakThatsAWonderfulIdea"]),
    "snd_omegaFloweyFightIntro" : pygame.Sound(rawAssets["SEomegaFloweyFightIntro"]),
    "snd_omegaFloweyLaugh" : pygame.Sound(rawAssets["SEomegaFloweyLaugh"]),
    "snd_MomegaFloweyFightIntro2" :  pygame.Sound(rawAssets["BGMomegaFloweyIntro"]),


    "snd_Help1" : pygame.Sound(rawAssets["BGMHelp1"]),
    "snd_Help2" : pygame.Sound(rawAssets["BGMHelp2"]),
    "snd_Help3" : pygame.Sound(rawAssets["BGMHelp3"]),

    "snd_FightPart1" : pygame.Sound(rawAssets["BGMFightPart1"]),
    "snd_FightPart2" : pygame.Sound(rawAssets["BGMFightPart2"]),
    "snd_FightPart3" : pygame.Sound(rawAssets["BGMFightPart3"]),

    "snd_Final1" : pygame.Sound(rawAssets["BGMFinal1"]),
    "snd_Final2" : pygame.Sound(rawAssets["BGMFinal2"]),
    "snd_Final3" : pygame.Sound(rawAssets["BGMFinal3"]),

    "snd_defeated" : pygame.Sound(rawAssets["BGMdefeated"]),
    
    "snd_alarm1" : pygame.Sound(rawAssets["SEalarm1"]),
    "snd_died" : pygame.Sound(rawAssets["SEdied"]),
    "snd_fatalHit" : pygame.Sound(rawAssets["SEfatalHit"]),
    "snd_heal" : pygame.Sound(rawAssets["SEheal"]),
    "snd_heavyHit" : pygame.Sound(rawAssets["SEheavyHit"]),
    "snd_slash" : pygame.Sound(rawAssets["SEslash"]),
    "snd_static" : pygame.Sound(rawAssets["SEstatic"]),

    

}
#========================





#========================
# INISIALISASI RUANGAN (1)
#========================
roomInstances["starterPlace"] = room(1000 , 1000)

roomInstances["bossFightPlace"] = room(screenWidth , screenHeight)

roomInstances["diedScene"] = room(screenWidth , screenHeight)

roomInstances["helpScene1"] = room(screenWidth , screenHeight)
roomInstances["helpScene2"] = room(screenWidth , screenHeight)
roomInstances["helpScene3"] = room(screenWidth , screenHeight)
roomInstances["final"] = room(screenWidth , screenHeight)

#========================





#========================
# FUNGSI / METHOD GLOBAL KHUSUS UNTUK EVENT INSTANSI.
#========================
def moveControl(instParentName , layerParentName , speed = 5 , collideLayerName = None):
    keys = pygame.key.get_pressed()
    parentInst = findFirstInstance(layerParentName , instParentName)
    if (not isinstance(parentInst , instance)): return 

    #V Penanganan anti tabrakan
    colliderInstances = None
    if (collideLayerName is not None and collideLayerName in layers):
        layer = layers[collideLayerName]
        if (not isinstance(layer , instanceLayer)): return print("ERROR!!!!! di fungsi moveControl!");

        colliderInstances = layer.instances





    moveSpeed = speed * (solidFPS * deltaTime)



    if keys[pygame.K_LEFT] or keys[pygame.K_a]: parentInst.x -= moveSpeed 
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: parentInst.x += moveSpeed 

    if (keys[pygame.K_0]): roomGoto("bossFightPlace")

    if colliderInstances is not None:
        for instanceName, instanceObject in colliderInstances.items(): # Asumsi ini berupa list of tuples atau array 2D
            # Skip jika bukan instance ATAU jika itu adalah player itu sendiri
            if not isinstance(instanceObject, instance) or instanceObject == parentInst: 
                continue
            
            if instanceObject.isColliding(parentInst):
                # Kembalikan HANYA sumbu X
                parentInst.x = parentInst.previousX
                break # Nabrak satu dinding saja sudah cukup untuk membatalkan gerak


    if keys[pygame.K_DOWN] or keys[pygame.K_s]: parentInst.y += moveSpeed 
    if keys[pygame.K_UP] or keys[pygame.K_w]: parentInst.y -= moveSpeed 

    if colliderInstances is not None:
        for instanceName, instanceObject in colliderInstances.items():
            if not isinstance(instanceObject, instance) or instanceObject == parentInst: 
                continue
            
            if instanceObject.isColliding(parentInst):
                # Kembalikan HANYA sumbu Y
                parentInst.y = parentInst.previousY
                break


   


    
def helpPlayer():
    globalVariables["helpCount"] += 1
    print(f"helpCount : {globalVariables["helpCount"]}")
    

    if (globalVariables["helpCount"] == 1):
        roomGoto("helpScene1")

    elif (globalVariables["helpCount"] == 2):
        roomGoto("helpScene2")

    elif (globalVariables["helpCount"] == 3):
        roomGoto("helpScene3")




#========================





#========================
# INISIALISASI INSTANSI, DAN FUNGSI / METHOD UNTUK EVENT INSTANSI.
#========================
#V STATE BOSS AWAL
globalVariables["Bstate"] = "opening1"
globalVariables["BAttackState"] = "att2"
globalVariables["helpCount"] = 0

globalVariables["attackDelay"] = solidFPS * 0.5
globalVariables["attackCurrentDelay"] = globalVariables["attackDelay"]

globalVariables["fightTime"] = 0
print("Bstate op1")

def tsf_changeBossAttackType():
    attackType = random.choice(["att1","att1","att1","att1","att1","att1","att2","att2","att2","att2","att2","att2","att2","att2","att2","att2"])
    globalVariables["BAttackState"] = attackType
ts_changeBossAttackType = timeSpawn(tsf_changeBossAttackType , solidFPS*8 , -1)
ts_changeBossAttackType.execute()


#> Inisialisasi blueprint "starterPlace"
def controlerOnStep():
    # 1. Ambil snapshot keyboard sekali saja di awal untuk efisiensi
    keys = pygame.key.get_pressed()

    # 2. Kontrol Kamera (Menggunakan variabel 'keys' yang sudah disimpan)
    if keys[pygame.K_RIGHT]: currentRoom.cameraX += 5
    if keys[pygame.K_LEFT]:  currentRoom.cameraX -= 5
    if keys[pygame.K_DOWN]:  currentRoom.cameraY += 5
    if keys[pygame.K_UP]:    currentRoom.cameraY -= 4

    

    if keys[pygame.K_o]:
        currentRoom.cameraHeight -= 2
        currentRoom.cameraWidth -= 2
    if keys[pygame.K_i]:    
        currentRoom.cameraHeight += 2
        currentRoom.cameraWidth += 2

    # 3. Kontrol Perpindahan Room
    if keys[pygame.K_2]: roomGoto("room2")
    if keys[pygame.K_1]: roomGoto("starterPlace")

    # 4. Akses Aman ke Instance Player dan Kontrolnya
    if "instancesLayer" in layers and "controler" in layers["instancesLayer"].instances:
        player = layers["instancesLayer"].instances["controler"]
        
        # Pergerakan Player
        if keys[pygame.K_d]: player.x += 5
        if keys[pygame.K_a]: player.x -= 5
        if keys[pygame.K_s]: player.y += 5
        if keys[pygame.K_w]: player.y -= 5

        # Rotasi dan Penghancuran (Dimasukkan ke dalam scope 'if' agar AMAN dari NameError)
        if keys[pygame.K_r]: 
            player.rotation += 5
        if keys[pygame.K_DELETE]: 
            player.destroy()
            return
roomAddBlueprint("starterPlace", "instancesLayer", instanceLayer(
    instances = {
            "controler" : instance(Assets["spr_empty"], 200, 200, 2, 2, eventDefinition = {
                
            },setVars = {
                "roomPersist": True
            })
    }
))
#<



#> Inisialisasi blueprint "diedScene"
roomAddBlueprint("diedScene" , "instancesLayer3", instanceLayer(
    {},
    1
))
#<




#> Inisialisasi blueprint "bossFightPlace"
def playerOnStep(instParentName):
    parentInst = findFirstInstance("instancesLayer2" , instParentName)
    if (not isinstance(parentInst , instance)): return
    
    #V Jika instansi TIDAK berada di room scene kematian player
    if (currentRoomName != "diedScene"):
        moveControl(instParentName , "instancesLayer2" , 6 , "collideLayer")
    elif (currentRoomName == "diedScene"):
        #parentInst.x += random.randint(-1,1)
        #parentInst.y += random.randint(-1,1)
        parentInst.rotation += random.randint(-1,1)
    
    #V Jika IYA, BLOK INI DIJALANKAN SEKALI SAAT MATI (Seharusnya).
    if (parentInst.getVar("health") <= 0 and not parentInst.getVar("hasBeenDied")):
        parentInst.setVar("hasBeenDied" , True)

        pygame.mixer.stop() #< Menghentikan semua suara
        roomGoto("diedScene")

        parentInst.animationCurrentFrame = 1
        Assets["snd_died"].play()
        #Assets["snd_fatalHit"].play()

        def tsf_JiwaPecah():
            parentInst.visible = False

            for i in range(100):
                def move(instanceName , speedOffset):
                    instanceObj = findFirstInstance("instancesLayer3" , instanceName)

                    kebalikan = 1
                    if (int(speedOffset) % 2 == 0):
                        kebalikan = -1

                    speed = 0.04

                    instanceObj.x += speedOffset * kebalikan * speed 
                    instanceObj.y += speedOffset * speed 
                    instanceObj.rotation += speedOffset * speed 

                    

                createInstance("instancesLayer3" , f"pieceOfHeart{i}" , instance(Assets["spr_pieceOfHeart"] ,parentInst.x+random.randint(0,35),parentInst.y+random.randint(0,35),
                                                                             random.random(),random.random(),
                                                                             {"step": lambda inst=i: move(f"pieceOfHeart{inst}" , inst)},
                                                                             {"animationPlay" : True,
                                                                              "animationSpeed": 0,
                                                                             }))
                
            globalVariables["diedSceneCurrentRedColourValueRect"] = 255
            def diedAnimControllerOnDraw():
                drawRect(0,0 , screenWidth,screenHeight , (globalVariables["diedSceneCurrentRedColourValueRect"],0,0))
                globalVariables["diedSceneCurrentRedColourValueRect"] -= abs(pygame.math.lerp(0 , globalVariables["diedSceneCurrentRedColourValueRect"] , 0.1))
            createInstance("instancesLayer3" , "diedAnimController" , instance(
                Assets["spr_empty"], 9999,9999,1,1,{
                    "beginDraw" : diedAnimControllerOnDraw
                }
            ))


        ts_jiwaPecah = timeSpawn(tsf_JiwaPecah , (2.5)*solidFPS)
        ts_jiwaPecah.execute()        
                

        def tsf_gameOver():
            global isRunning
            isRunning = False
        ts_gameOver = timeSpawn(tsf_gameOver , (2.5+8)*solidFPS)
        ts_gameOver.execute()  
def playerOnDraw(instParentName):
    parentInst = findFirstInstance("instancesLayer2" , instParentName)
    if (not isinstance(parentInst , instance)): return
    parentInst.drawSelf()
    if (globalVariables["Bstate"] == "attacking" and currentRoomName != "diedScene"):

    
        # 1. Menghitung waktu dalam detik
        globalVariables["fightTime"] += 1
        waktu_detik = globalVariables["fightTime"] / solidFPS
        
        # 2. Membulatkan ke 2 angka di belakang koma
        hasil_akhir = round(waktu_detik, 2)

        drawText(f"SOUL HEALTH: {parentInst.health}\nTIME: {hasil_akhir}" , 25,25 ,2,2 , 0 , (255,233,233))
        
def diedZoneColliderOnStep(instParentName):



    parentInst = findFirstInstance("instancesLayer2" , instParentName)
    playerInst = findFirstInstance("instancesLayer2" , "player")
    if (not isinstance(parentInst , instance)): return

    if (parentInst.isColliding(playerInst)):
        playerInst.setVar("health" , 0)

    if (globalVariables["Bstate"] == "opening1"):
        parentInst.y += 1 * (solidFPS * deltaTime) 

def bossOnCreate(instParentName):
    currentRoom.cameraWidth *= 0.95
    currentRoom.cameraHeight *= 0.95

    globalVariables["relCamPosX"] = currentRoom.cameraX
    globalVariables["relCamPosY"] = currentRoom.cameraY
    parentInst = findFirstInstance("instancesLayer2" , instParentName)
    playerInst = findFirstInstance("instancesLayer2" , "player")
    
    if (not isinstance(parentInst , instance)): return



    #V JIKA PERTARUNGAN BARU SAJA DIMULAI
    if (globalVariables["Bstate"] == "opening1"):
        #V MAINKAN MUSIK AWAL
        Assets["snd_MomegaFloweyFightIntro2"].play(0)

        laguAwalLen = Assets["snd_MomegaFloweyFightIntro2"].get_length() # 16 Detik
        suaraKetawaLen = Assets["snd_omegaFloweyLaugh"].get_length() # 6 detik
        laguBoss = Assets["snd_VOIDSTAR"].get_length()
       
        
        #V MAINKAN SUARA KETAWA HAHAHAHAH SAAT MUSIK AWAL SUDAH SELESAI, DAN JUGA MENGUBAH STATE
        def tsf_state2():
            if (playerInst.hasBeenDied): return;
            #V dimainkan sebanyak-banyaknya agar suaranya besar
            for i in range(3):
                Assets["snd_omegaFloweyLaugh"].play()
            globalVariables["Bstate"] = "opening2"
            print("Bstate op2")
        ts_state1 = timeSpawn(tsf_state2 , (1+laguAwalLen)*solidFPS*2 , 0)
        ts_state1.execute()



        #V SAAT SUARA KETAWA HAHAHA SELESAI, MAINKAN LAGU BOSS DAN PERTARUNGAN DIMULAI!!!!!!!!!!!!!!!!
        def tsf_stateBossFightBegin():
            if (playerInst.hasBeenDied): return;
            Assets["snd_VOIDSTAR"].set_volume(0.8)
            Assets["snd_VOIDSTAR"].play(-1)
            globalVariables["Bstate"] = "attacking"
            print("Bstate attacking")
        ts_stateBossFightbegin = timeSpawn(tsf_stateBossFightBegin , (1+suaraKetawaLen+laguAwalLen)*solidFPS*2 , 0)
        ts_stateBossFightbegin.execute()

        
        #def tsf_setHelp():
        #    helpPlayer()
        #    pygame.mixer.stop()
        #ts_setHelp = timeSpawn(tsf_setHelp , (1+suaraKetawaLen+laguAwalLen+laguBoss)*solidFPS*2)
        #ts_setHelp.execute()
    else:
        parentInst.y = 215.07000000000173
def bossOnStep(instParentName):
    parentInst = findFirstInstance("instancesLayer2" , instParentName)
    if (not isinstance(parentInst , instance)): return

    playerInst = findFirstInstance("instancesLayer2" , "player")
    
    if (globalVariables["Bstate"] == "opening1"):
        parentInst.y += 1 * (solidFPS * deltaTime) 
    

    if (globalVariables["Bstate"] == "opening2"):
        currentRoom.cameraX = globalVariables["relCamPosX"] + random.randint(-20,20) 
        currentRoom.cameraY = globalVariables["relCamPosY"] + random.randint(-20,20) 




    if (parentInst.isColliding(playerInst)):
        print(parentInst.x , parentInst.y , playerInst.getVar("health"))
        playerInst.setVar("health" , 0)





    
    #V PENANGANAN SERANGAN BOSS
    if (globalVariables["Bstate"] == "attacking"):

        #V Tipe serangan 1
        if (globalVariables["BAttackState"] == "att1"):
            globalVariables["attackDelay"] = solidFPS * 0.2
            globalVariables["attackCurrentDelay"] -= 1

            if (globalVariables["attackCurrentDelay"] <= 0):
                globalVariables["attackCurrentDelay"] = globalVariables["attackDelay"]
                
                for i in range(3):

                    def bulletOnStep(instParentName):
                        bulletInst = findFirstInstance("instancesLayer2" , instParentName)    
                        if (not isinstance(bulletInst , instance)): return 

                        bulletInst.rotation += 8

                        bulletInst.y += 10
                        if (bulletInst.isColliding(playerInst)):
                            playerInst.health -= 8
                            Assets["snd_fatalHit"].set_volume(0.5)
                            Assets["snd_fatalHit"].play()
                            bulletInst.destroy()

                        def tsf_destroy():
                            bulletInst.destroy()
                        ts_destroy = timeSpawn(tsf_destroy , solidFPS*4 , False)
                        ts_destroy.execute()

                    def bulletOnBeginDraw(instParentName):
                        bulletInst = findFirstInstance("instancesLayer2" , instParentName)    
                        if (not isinstance(bulletInst , instance)): return 

                        drawSprite(bulletInst.drawThisImage , bulletInst.x,bulletInst.y , bulletInst.xScale,bulletInst.yScale , bulletInst.rotation)

                    
                    name = f"bullet{uuid.uuid4()}"
                    scale = max(0.45*random.random() , 0.1)
                    createInstance("instancesLayer2" , name , instance(Assets["spr_empty"] , random.randint(30,screenWidth-30),parentInst.y ,scale,scale ,{
                        "step" : lambda n=name: bulletOnStep(n),
                        "beginDraw" : lambda n=name: bulletOnBeginDraw(n),
                    },{
                        "drawThisImage" : random.choice([Assets["spr_bread"] , Assets["spr_leaf"] , Assets["spr_leaf"] , Assets["spr_leaf"], Assets["spr_leaf"] , Assets["spr_leaf"] , Assets["spr_leaf"]])
                    }))
        elif (globalVariables["BAttackState"] == "att2"):
            globalVariables["attackDelay"] = solidFPS * 0.5
            globalVariables["attackCurrentDelay"] -= 1

            if (globalVariables["attackCurrentDelay"] <= 0):
                globalVariables["attackCurrentDelay"] = globalVariables["attackDelay"]

                def bulletOnStep(instParentName):
                    bulletInst = findFirstInstance("instancesLayer2" , instParentName)    
                    if (not isinstance(bulletInst , instance)): return 

                    if (bulletInst.strecthing):
                        bulletInst.xScale += 0.2*random.random()
                    else:
                        bulletInst.xScale = max(pygame.math.lerp(bulletInst.xScale - 0.035 , 0 , 0.2) , 0)

                    if (bulletInst.isColliding(playerInst)):
                        bulletInst.destroy()
                        playerInst.health -= 5
                        Assets["snd_fatalHit"].play()

                def bulletOnCreate(instParentName):
                    bulletInst = findFirstInstance("instancesLayer2" , instParentName)    
                    if (not isinstance(bulletInst , instance)): return 

                    def tsf_s():
                        bulletInst.setVar("strecthing" , False)
                    ts = timeSpawn(tsf_s , random.randint(1,2)*solidFPS)
                    ts.execute()

                name = f"bullet{uuid.uuid4()}"
                createInstance("instancesLayer2" , name , instance(Assets["spr_eye"] , 0,random.randint(parentInst.x+20,screenHeight) ,0,0.3,
                                                                   {"step":lambda n=name: bulletOnStep(n) , "create":lambda n=name:bulletOnCreate(n)},{"strecthing":True}))
def bossOnDraw(instParentName):

    parentInst = findFirstInstance("instancesLayer2" , instParentName)     
    if (not isinstance(parentInst , instance)): return  
    
    parentInst.drawSelf()




    if (globalVariables["Bstate"] == "opening1"):
        dr = wavy("Y", 20, amplitudo=0.9, kecepatan=4)
        drawRect(0,0 , screenWidth,screenHeight , (int(pygame.math.clamp(100*dr , 0 , 255)),0,0))
    elif (globalVariables["Bstate"] == "opening2"):
        dr = wavy("Y", 20, amplitudo=0.9, kecepatan=10)
        drawRect(0,0 , screenWidth,screenHeight , (int(pygame.math.clamp(255*dr , 0 , 255)),0,0))

    dx = wavy("X", 50, amplitudo=5, kecepatan=11)
    dy = wavy("Y", 1100, amplitudo=5, kecepatan=11)
    dr = wavy("Y", 99, amplitudo=5, kecepatan=11)

    #V gambar buntut
    offset = 0
    droffset = 0
    for i in range(7):
        offset += 40
        droffset += 1

        if (globalVariables["Bstate"] == "opening2"):
            dr = wavy("Y", 99+droffset, amplitudo=5, kecepatan=22)
        else:
            dr = wavy("Y", 99+droffset, amplitudo=5, kecepatan=11)
    
        dx = wavy("X", 99+droffset, amplitudo=5, kecepatan=11)
        drawSprite(Assets["spr_leaf"] , parentInst.x+-30+dx,parentInst.y-100-offset , 1,0.5 , dr , 0 , 255 , (115, 115, 115))


    
    dx = wavy("X", 50, amplitudo=5, kecepatan=11)
    dy = wavy("Y", 1100, amplitudo=5, kecepatan=11)
    dr = wavy("Y", 99, amplitudo=5, kecepatan=11)

    #V gambar tangan
    handRot = 39
    if (globalVariables["Bstate"] == "opening2"):
        handRot = 60
        dr = wavy("Y", 99, amplitudo=8, kecepatan=20)

    drawSprite(Assets["spr_leaf"] , parentInst.x-200,parentInst.y , 0.6 , 1 , -handRot+dr)
    drawSprite(Assets["spr_leaf"] , parentInst.x+200,parentInst.y , 0.6 , 1 , +handRot+(dr*-1))
    

    dx = wavy("X", 50, amplitudo=5, kecepatan=11)
    dy = wavy("Y", 1100, amplitudo=5, kecepatan=11)
    dr = wavy("Y", 99, amplitudo=5, kecepatan=11)

    #V gambar badan / kepala
    offset = -3
    for i in range(4):
        offset += 3
        drawSprite(Assets["spr_leaf"] , parentInst.x-220,parentInst.y+70+dy+offset , 1,1.2 , 90 , 0 , 255)

    offset = -3
    for i in range(4):
        offset += 3
        drawSprite(Assets["spr_leaf"] , parentInst.x+160,parentInst.y+70+dy+offset , 1,1.2 , -90)  
        

        

        




    #V gambar mulut


    dy = 0
    frame = 0
    if (parentInst.getVar("isLaugh") == True)or(globalVariables["Bstate"] == "opening2"):
        dy = wavy("Y", 1100, amplitudo=11, kecepatan=50)
        frame = int(min(max(wavy("Y", 50, amplitudo=11, kecepatan=50) , 0) , 1))
        
    else:
        dy = wavy("Y", 1100, amplitudo=2, kecepatan=11)
    
    drawSprite(Assets["spr_smileMounth"] , parentInst.x-20,parentInst.y+dy , 0.9,0.8 , 0 , frame)

    
    #V gambar mata
    eyeXS = 0.5
    eyeYS = 0.5
    eyesOffset = 0

    dx = wavy("X", 50, amplitudo=5, kecepatan=11)
    dy = wavy("Y", 1100, amplitudo=5, kecepatan=11)
    

    if (globalVariables["Bstate"] == "opening2"):
        #eyeXS += max(wavy("X", 50, amplitudo=0.1, kecepatan=11) , 0)
        #eyeYS += max(wavy("Y", 50, amplitudo=0.1, kecepatan=11) , 0)
        eyesOffset += random.randrange(-5 , 5)
        dr = wavy("Y", 99, amplitudo=7, kecepatan=30)

    offset = -2
    for i in range(4):
        offset += 2

        dr = wavy("Y", 99, amplitudo=5, kecepatan=11)
        drawSprite(Assets["spr_eye"] , parentInst.x+dx+offset-200+eyesOffset,parentInst.y+dy+offset+eyesOffset , eyeXS,eyeYS , dr , 0 , 255)

        dr = wavy("Y", 99, amplitudo=5, kecepatan=11) 
        drawSprite(Assets["spr_eyeFlipped"] , parentInst.x+dx+-offset+220+eyesOffset,parentInst.y+dy+offset+eyesOffset , eyeXS,eyeYS , dr , 0 , 255)
roomAddBlueprint("bossFightPlace", "instancesLayer2", instanceLayer(
    instances = {
            "boss" : instance(Assets["spr_grassTile"], 400, -300, 4, 4, eventDefinition = {
                "create": lambda: bossOnCreate("boss"),
                "step": lambda: bossOnStep("boss"),
                "draw": lambda: bossOnDraw("boss"),
            }, setVars={
                "health" : 1000,

                "isLaugh" : False,
            }),
            "player" : instance(Assets["spr_heart"], screenWidth/2.2, screenHeight/1.4, 2.5, 2.5, eventDefinition = {

                "step": lambda: playerOnStep("player"),
                "draw": lambda: playerOnDraw("player"),
            }, setVars={
                "health" : 100,
                "hasBeenDied" : False,

                "roomPersist" : True,
            }),

            "diedZone" : instance(Assets["spr_empty"] , 0,-140, 30,1 , {"step":lambda:diedZoneColliderOnStep("diedZone")})
    }       
    
))
roomAddBlueprint("bossFightPlace", "collideLayer" , instanceLayer({
    "col1" : instance(Assets["spr_empty"] ,-50,0, 1,50 , {} ,  {"roomPersist" : True}),
    "col2" : instance(Assets["spr_empty"] ,screenWidth-80,0, 1,50 , {} ,  {"roomPersist" : True}),
    "col3" : instance(Assets["spr_empty"] ,0,screenHeight-80, 50,1 , {} ,  {"roomPersist" : True}),
    "col4" : instance(Assets["spr_empty"] ,0,0, 50,1 , {} ,  {"roomPersist" : True}),
},1))
#<
#========================

# BIKIN SISTEM SERANGAN BOSS!!!!!!! DAN JUGA BANTUAN DARI JIWA LAINYA!!



#========================
# INISIALISASI RUANGAN (2)
#========================
#V Ruangan yang pertama kali dimasuki saat game dimulai.
roomGoto("bossFightPlace")
#========================


#===========================================================================================================
#===========================================================================================================
#===========================================================================================================
#===========================================================================================================
#===========================================================================================================











#========================
# PERULANGAN UTAMA
#========================
while isRunning:
    ##> SYSTEM STEP (untuk penanganan sistem seperti input, logika, dan menggambar)
    #V Penanganan input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            isRunning = False

    #V Mengatur warna background ke hitam.
    currentRoom.cameraSurface.fill((0,0,0)) 
    aplicationSurface.fill((0,0,0))

    #V Penanganan logika instansi dan ruangan.
    for eventName in runingEventNodes:
        runingEventNodes[eventName].clear() #< Bersihkan fungsi / method lama

    #V Menambahkan fungsi awal (Fungsi inti agar game berjalan dengan benar)
    runingEventNodes["beginStep"].append( lambda: globals().update({"onGuiLoop": False}) )

    runingEventNodes["endStep"].append(roomForceUpdate)

    runingEventNodes["beginDrawGUI"].append( lambda: aplicationSurface.blit(pygame.transform.scale(currentRoom.cameraSurface, (screenWidth, screenHeight)), (0, 0)) )
    runingEventNodes["beginDrawGUI"].append( lambda: globals().update({"onGuiLoop": True}) )

    

    #aguAwalLen = Assets["snd_MomegaFloweyFightIntro2"].get_length() # 16 Detik
    #suaraKetawaLen = Assets["snd_omegaFloweyLaugh"].get_length() # 6 detik
    
    
    #V Menambahkan fungsi untuk menggambar informasi debug jika DEBUGUI bernilai True.
    if (DEBUGUI):
        runingEventNodes["endDrawGUI"].append( lambda: drawText(f"CAM: X:{currentRoom.cameraX} Y:{currentRoom.cameraY} Width:{currentRoom.cameraWidth} Height:{currentRoom.cameraHeight}\nRoomName: {currentRoomName}\nDisplay: Width{screenWidth} Height{screenHeight}\nFPS{currentFPS} FramePassed{framePassed}", 20 , 20 , 2 , 2.3))
    
    #V Menambahkan fungsi untuk menggambar permukaan kamera ke permukaan aplikasi, dengan ukuran yang disesuaikan dengan ukuran layar.
    scaledCamera = pygame.transform.scale(currentRoom.cameraSurface, (screenWidth, screenHeight))
    aplicationSurface.blit(scaledCamera, (0, 0))




    #V (Nama variabel berati nama layernya, nilainya adalah nama instansinya)
    destroyThisInstances = {}

    #V Mengiterasikan semua instansi layer yang tercipta.
    for layerName, layer in layers.items():

        #V Jika tipe layer adalah instanceLayer
        if (isinstance(layer , instanceLayer)):
            #V Mengiterasikan semua objek yang ada di layer.
            for instanceName , instanceObject in layer.instances.items():
                #V Pengecekan
                #V Cek jika instansi masih terdaftar atau sudah dihapus di event sebelumnya. Cek jika objek saat ini berupa class instance atau tidak.
                if (instanceName not in layer.instances)or(not isinstance(instanceObject , instance)):
                    print(f"ERROR!!! Salah satu nilai dari instanceLayer Salah! Name instansi:{instanceName}")
                    continue

                #V Memanggil fungsi forceUpdate untuk setiap instansi, agar variabel posisi sebelumnya dapat digunakan untuk logika seperti pergerakan dan tabrakan.
                instanceObject.forceUpdate() 


                #V Menambahkan semua fungsi / method yang ada di setiap event instansi ke dalam variabel runingEventNodes, agar dapat dijalankan secara berurutan di step selanjutnya.
                for eventName , eventFunction in instanceObject.events.items():

                    #V Menjalankan create event sekali seumur hidup instansi saat instansi baru saja diciptakan
                    if (eventName == "create" and not instanceObject.createEventHasBeenCalled):
                        if (callable(eventFunction)):
                            eventFunction()
                            instanceObject.createEventHasBeenCalled = True


                    #V NAMA EVENT YANG TIDAK AKAN DIJALANKAN 
                    blacklistEventName = ["create" , "onDestroy"]
                    #V Jika nama event termasuk dalam blacklist
                    if (eventName in blacklistEventName): continue

                    if callable(eventFunction):
                        runingEventNodes[eventName].append(eventFunction)

                #V Menambahkan instansi ke antrian yang akan dihancurkan jika flag isDestroySoon bernilai True
                if (instanceObject.isDestroySoon):
                    destroyThisInstances[layerName] = instanceName


                #V Jika instansi diperintahkan tidak bisa menembus saat bertabrak
                if (instanceObject.solid):
                    for instanceName2 , instanceObject2 in layer.instances.items():
                        if (instanceObject.isColliding(instanceObject2)):
                            print("menyentuh!") #< nanti ditambah!!!!!!!!!!!!!!!!!!!!!!!!!! agar instansi gk bisa nembus #BUG #BUG    


        #V Jika tipe layer adalah backgroundLayer
        elif (isinstance(layer , backgroundLayer)):
            if (layer.isActive):
                runingEventNodes["beginDraw"].append(layer.draw)


        #V Menghapus instansi yang terdaftar sebagai yang akan dihapus
        for layerName , instanceName in destroyThisInstances.items():
            layerTarget = layers[layerName]
            if (isinstance(layerTarget , instanceLayer)):
                onDestroyEvent = layerTarget.instances[instanceName].events["onDestroy"]
                
                if (callable(onDestroyEvent)):
                    onDestroyEvent()

                layerTarget.instances.__delitem__(instanceName)
        destroyThisInstances.clear()        


        timeSpawnIDDeleteList = []
        for timeSpawnId , timeSpawnObject in timeSpawns.items():
            if (isinstance(timeSpawnObject , timeSpawn)):

                if (not timeSpawnObject.isPaused):
                    timeSpawnObject.currentDelayTime -= 1 * (deltaTime * solidFPS)
                

                if (timeSpawnObject.currentDelayTime <= 0):
                    timeSpawnObject.functionToCall()
                    timeSpawnObject.currentDelayTime = 0
                    

                    if (timeSpawnObject.currentCallLoop == 0):
                        timeSpawnIDDeleteList.append(timeSpawnId)
                    elif (timeSpawnObject.currentCallLoop == -1)or(timeSpawnObject.currentCallLoop > 0):
                        timeSpawnObject.currentCallLoop -= 1
                        timeSpawnObject.currentDelayTime = timeSpawnObject.callDelay

        for timeSpawnId in timeSpawnIDDeleteList:
            del timeSpawns[timeSpawnId]
        

                
         


    #V Menjalankan semua fungsi yang sudah diurutkan di dalam variabel runingEventNodes secara berurutan.
    for eventName in runingEventNodes:
        for eventFunction in runingEventNodes[eventName]:
            if callable(eventFunction):
                eventFunction()





    ##V Akhir perulangan
    pygame.display.flip()
    deltaTime = clock.tick(solidFPS) / 1000.0
    currentFPS = int(clock.get_fps())
    currentTime = pygame.time.get_ticks()
    framePassed += 1

    ##<
#========================






#========================
# PENUTUP
#========================
pygame.quit()
sys.exit()
#========================













