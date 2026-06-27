#V Inisialisasi Modul
from moduleInit import *
import moduleInit







#========================
# VARIABEL GLOBAL
#========================
###V VARIABEL YANG AMAN DIUBAH.
screenWidth = 1000            #< Lebar jendela game.
screenHeight = 800            #< Tinggi jendela game.
actualFPS = 60                #< (Frame Per Second) Jumlah bingkai yang akan dirender dalam 1 detik.


DEBUGUI = False                    #< Apakah informasi akan ditampilkan atau tidak.

#V Data yang akan disimpan untuk progres.
SaveData = {
    "totalRunTime" : 0,
    "lastRunTime" : 0,
}

#V Sekumpulan aset mentah yang akan digunakan untuk game, alih-alih menyatukan dengan variabel luar lain.
rawAssets = {
    "gameIcon" : pygame.image.load(os.path.join("assets" , "Pong.png")),
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
def drawSprite(_spriteAsset , x , y , scaleX = 1 , scaleY = 1 , rotation = 0 , subImage = 0 , alpha = 255):
    imageSurface = None

    if (isinstance(_spriteAsset , spriteAsset)):
        if (isinstance(_spriteAsset.surface , pygame.surface.Surface)):
            imageSurface = _spriteAsset.surface
        elif (isinstance(_spriteAsset.surface , list)):
            imageSurface = _spriteAsset.surface[subImage]
        else:
            print(f"ARGUMEN \"_spriteAsset\" SALAH DI FUNGSI BERNAMA \"drawSprite\"\nInfo Argumen: {_spriteAsset}")
            return
    else:
        print(f"ERROR!!! Argumen '_spriteAsset' SALAH!\nArgumen: {_spriteAsset}")
        return
    

   

   
# 2. Terapkan Skala (Scaling) TERLEBIH DAHULU sebelum rotasi
    if scaleX != 1 or scaleY != 1:
        newWidth = int(imageSurface.get_width() * scaleX)
        newHeight = int(imageSurface.get_height() * scaleY)
        imageSurface = pygame.transform.scale(imageSurface, (newWidth, newHeight))

    # 3. Terapkan Rotasi (Hanya jika nilai rotation bukan 0 untuk menghemat performa CPU)
    if rotation != 0:
        # Tentukan posisi pivot di layar. 
        # Karena kita sudah mengubah skala di atas, titik rotasi (offset) juga dikalikan skala
        pivot_x = x + (_spriteAsset.xRotationPoint * scaleX)
        pivot_y = y + (_spriteAsset.yRotationPoint * scaleY)
        pivot_pos = pygame.math.Vector2(pivot_x, pivot_y)

        # Dapatkan Rect dari gambar (yang ukurannya sudah diskala)
        original_rect = imageSurface.get_rect(topleft=(x, y))

        # Hitung jarak (offset) dari titik tengah ke titik pivot
        offset = pivot_pos - original_rect.center

        # Putar gambar dan timpa variabel imageSurface
        imageSurface = pygame.transform.rotate(imageSurface, rotation)

        # Putar vektor offset ke arah yang berlawanan
        rotated_offset = offset.rotate(-rotation)

        # Hitung posisi koordinat yang baru agar pivot tidak bergeser
        new_center = pivot_pos - rotated_offset
        rotated_rect = imageSurface.get_rect(center=(round(new_center.x), round(new_center.y)))

        # Update nilai x dan y untuk proses blit di bawah
        x = rotated_rect.x
        y = rotated_rect.y
        
    #V Mewarnai surface
    coloredImageSurface = imageSurface.copy()
    coloredImageSurface.fill(currentDrawColour , special_flags=pygame.BLEND_RGBA_MULT)
    coloredImageSurface.set_alpha(alpha)
    
    # 4. Gambar (Blit) ke layar
    surfaceDraw(coloredImageSurface , x , y)




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
        self.animationPlay = True
        self.animationLoop = True
        self.animationSpeed = 0.025

        self.isDestroySoon = False #< Apakah di step berikutnya, instansi ini akan dihancurkan?
        self.createEventHasBeenCalled = False #< Apakah create event sudah di jalankan sebelumnya atau belum?


        self.var = {}

        

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
                    self.animationCurrentFramee = frameTotal - 1 #< Berhenti di frame terakhir

        #V Mencegah error jika nilai frameTotal tiba-tiba berubah
        frameTotal = int(self.animationCurrentFrame) % max(1, frameTotal)

        if (self.visible):
            originalDrawColour = currentDrawColour
            drawSetColour(self.blend)
            drawSprite(self.spriteAsset,
                        self.x, self.y,
                        self.xScale  , self.yScale   , self.rotation,
                        frameTotal)
            drawSetColour(originalDrawColour)


            



    def forceUpdate(self):
        #V Mengatur posisi sebelumnya agar dapat digunakan untuk logika seperti pergerakan dan tabrakan.
        self.previousX = self.x
        self.previousY = self.y


    def destroy(self):
        self.isDestroySoon = True


    def isColliding(self , instance2):
        surfaceImage = self.spriteAsset.surface
        surfaceImage = instance2.spriteAsset.surface
   

        width = surfaceImage.get_width()
        height = surfaceImage.get_width() + 100

        width2 = surfaceImage.get_width()
        height2 = surfaceImage.get_width() + 100

        return (self.x < instance2.x +width2 and self.x + width > instance2.x 
                and self.y < instance2.y + height2 and self.y + height > instance2.y)
    




    

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
    "Pembatas" : pygame.image.load(os.path.join("assets" , "Pembatas.png")),
    "PingPong" : pygame.image.load(os.path.join("assets" , "Pong.png")),

}


#V Sekumpulan aset yang sudah dibungkus.
Assets = {
    "spr_pembatas" : spriteAsset(rawAssets["Pembatas"]),
    "spr_Pong" : spriteAsset(rawAssets["PingPong"] , 50,50),
}
#========================





#========================
# INISIALISASI RUANGAN (1)
#========================
roomInstances["game"] = room(screenWidth , screenHeight)
#========================





#========================
# FUNGSI / METHOD GLOBAL KHUSUS UNTUK EVENT INSTANSI.
#========================
    
#========================





#========================
# INISIALISASI INSTANSI, DAN FUNGSI / METHOD UNTUK EVENT INSTANSI.
#========================
#> Inisialisasi blueprint "game"

    

roomAddBlueprint("game", "instancesLayer", instanceLayer(
    instances = {
        "pong" : instance(Assets["spr_Pong"] , screenWidth/2,screenHeight/2 , 1,1),
        "player": instance(Assets["spr_pembatas"] , 20,screenHeight/2 , 1,1),
        "player2": instance(Assets["spr_pembatas"] , screenWidth-60,screenHeight/2 , 1,1),


    }
))

#========================





#========================
# INISIALISASI RUANGAN (2)
#========================
#V Ruangan yang pertama kali dimasuki saat game dimulai.
roomGoto("game")
#========================


#===========================================================================================================
#===========================================================================================================
#===========================================================================================================
#===========================================================================================================
#===========================================================================================================







pongMoveX = -4
pongMoveY = -4


isLose1 = False
isLose2 = False

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
    currentRoom.cameraSurface.fill((0,0,255)) 
    aplicationSurface.fill((0,0,255))

    #V Penanganan logika instansi dan ruangan.
    for eventName in runingEventNodes:
        runingEventNodes[eventName].clear() #< Bersihkan fungsi / method lama

    #V Menambahkan fungsi awal (Fungsi inti agar game berjalan dengan benar)
    runingEventNodes["beginStep"].append( lambda: globals().update({"onGuiLoop": False}) )

    runingEventNodes["endStep"].append(roomForceUpdate)

    runingEventNodes["beginDrawGUI"].append( lambda: aplicationSurface.blit(pygame.transform.scale(currentRoom.cameraSurface, (screenWidth, screenHeight)), (0, 0)) )
    runingEventNodes["beginDrawGUI"].append( lambda: globals().update({"onGuiLoop": True}) )

    player1 = layers["instancesLayer"].instances["player"]
    player2 = layers["instancesLayer"].instances["player2"]


    pong = layers["instancesLayer"].instances["pong"]

    

    key = pygame.key.get_pressed()
    if (key[pygame.K_w]): player1.y -=5
    if (key[pygame.K_s]): player1.y +=5

    if (key[pygame.K_UP]): player2.y -=5
    if (key[pygame.K_DOWN]): player2.y +=5

    if (not isLose1)and(not isLose2):
        pong.x += pongMoveX
        pong.y += pongMoveY


    pongSurface = pong.spriteAsset.surface

    if (pong.isColliding(player1))or(pong.isColliding(player2)):
        pongMoveX *= -1
        pongMoveY *= -1
        print("TERDETEKSI TABRAKAN!!!!")


    if (pong.x <= 0):
        pong.x = 0
        isLose1 = True
        
    elif (pong.x >= screenWidth - pong.spriteAsset.surface.width):
        pong.x = screenWidth - pong.spriteAsset.surface.width
        isLose2 = True


    if (pong.y <= 0):
        pong.y = 0
        pongMoveY *= -1
    elif (pong.y >= screenHeight - pong.spriteAsset.surface.height):
        pong.y = screenHeight - pong.spriteAsset.surface.height
        pongMoveY *= -1






    

    


    

    
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
                    timeSpawnObject.currentDelayTime -= 1

                if (timeSpawnObject.currentDelayTime <= 0):
                    timeSpawnObject.functionToCall()
                    timeSpawnObject.currentDelayTime = 0
                    

                    if (timeSpawnObject.currentCallLoop == 0):
                        timeSpawnIDDeleteList.append(timeSpawnId)
                    elif (timeSpawnObject.currentCallLoop == -1)or(timeSpawnObject.currentCallLoop > 0):
                        timeSpawnObject.currentCallLoop -= 1
                        timeSpawnObject.currentDelayTime = timeSpawnObject.callDelay

        for timeSpawnId in timeSpawnIDDeleteList:
            timeSpawns.__delitem__(timeSpawnId)
        timeSpawnIDDeleteList.clear()

                
         


    #V Menjalankan semua fungsi yang sudah diurutkan di dalam variabel runingEventNodes secara berurutan.
    for eventName in runingEventNodes:
        for eventFunction in runingEventNodes[eventName]:
            if callable(eventFunction):
                eventFunction()



    if (isLose1):
        drawText("PLAYER 1 KALAH!" , screenWidth/2.5,screenHeight/2 ,2,2)

    if (isLose2):
        drawText("PLAYER 2 KALAH!" , screenWidth/2.5,screenHeight/2 ,2,2)


    ##V Akhir perulangan
    pygame.display.flip()
    deltaTime = clock.tick(actualFPS) / 1000.0
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













