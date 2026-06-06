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

DEBUGUI = True                    #< Apakah informasi akan ditampilkan atau tidak.

#V Data yang akan disimpan untuk progres.
SaveData = {
    "totalRunTime" : 0,
    "lastRunTime" : 0,
}

#V Sekumpulan aset mentah yang akan digunakan untuk game, alih-alih menyatukan dengan variabel luar lain.
rawAssets = {
    "gameIcon" : pygame.image.load(os.path.join("assets" , "gameIcon2.png")),
}

#V Sekumpulan aset yang sudah dibungkus.
Assets = {}

roomInstances = {} #< Variabel sekumpulan ruangan. 

globalVariables = {} #< Variabel yang aman untuk diakses semua event.







###V VARIABEL YANG TIDAK AMAN DIUBAH.
aplicationSurface = pygame.display.set_mode((screenWidth , screenHeight))
clock = pygame.time.Clock()
isRunning = True

previousRoomName = "Undefined" #< Nama dunia/Ruangan sebelumnya.
currentRoomName  = "Undefined" #< Nama dunia/Ruangan saat ini.

currentRoom = None #< Data dunia ruangan saat ini yang dipakai.
layers = {}        #< Hasil dari konversi blueprintLayer

onGuiLoop = False #< Apakah di event saat ini sedang berada di fase digambarnya GUI.
currentDrawFontAsset = None #< Font yang saat ini digunakan untuk menggambar.

#V Event dengan sekumpulan fungsi/method nya yang sedang dijalankan di step saat ini.
runingEventNodes = {
        "create" : [],
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

    #V Memperbarui informasi room/dunia
    previousRoomName = currentRoomName 
    currentRoomName = roomName
    
    if (roomName in roomInstances):
        roomInstance = roomInstances[roomName]
        if (isinstance(roomInstance , room)):
            currentRoom = roomInstance #< Mengganti variabel yang menjelaskan instansi Room saat ini yang dimasuki.
            layers.clear()             #< Membersihkan objek di room sebelumnya di memori

            #V Mengonversi blueprint layer menjadi layer asli yang akan digunakan di dalam game, dan menyimpan hasilnya di variabel "layers".
            for layerName in roomInstance.blueprintLayers:
                blueprintLayer = roomInstance.blueprintLayers[layerName]

                #V Membuat ulang layer baru berdasarkan blueprint layer, dan menyimpan hasilnya di variabel "layers" untuk digunakan di dalam game.
                if (isinstance(blueprintLayer , backgroundLayer)):
                    layers[layerName] = backgroundLayer(blueprintLayer.spriteAsset , blueprintLayer.horizontalTile , blueprintLayer.verticalTile , blueprintLayer.strecth , blueprintLayer.colour)

                elif (isinstance(blueprintLayer , instanceLayer)):
                    layers[layerName] = instanceLayer(blueprintLayer.instances, blueprintLayer.depth)


                #V Jika blueprint layer bukan berupa instansi tidak termasuk daftar layer, maka akan muncul pesan error.
                else:
                    print(f"FATAL ERROR!!! Di variabel blueprintLayers di class room terdapat nilai selain instansi class backgroundLayer atau instanceLayer!!\nNilai: {blueprintLayer}")
                    return


        else:
            print(f"FATAL ERROR!!! Di variabel roomInstances terdapat nilai selain instansi class room!!\nNilai: {roomInstance}")
            return
        
    else:
        print(f"ERROR!!! Nama room tidak ditemukan di roomInstance di fungsi roomGoto\nArgumen \"roomName\": {roomName}")
        return
    
    




    

# Fungsi ini digunakan untuk menginisialisasi layer blueprint di dalam ruangan, agar dapat digunakan untuk menyimpan data layer yang akan dikonversi menjadi layer asli saat ruangan dimasuki. Blueprint layer ini tidak akan memakan banyak memori karena hanya menyimpan data yang diperlukan untuk membuat layer asli, dan tidak menyimpan data objek instansi yang ada di dalam layer tersebut.
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



def findFirstInstance(layerName , instanceObjectName , roomName = currentRoomName):
    if (roomName in roomInstances):
        roomInstance = roomInstances[roomName]

        if (isinstance(roomInstance , room)):
            if (layerName in roomInstance.blueprintLayers):
                layer = roomInstance.blueprintLayers[layerName]

                if (isinstance(layer , instanceLayer)):
                    if (instanceObjectName in layer.instances):

                        return layer.instances[instanceObjectName]
                
                    else:
                        print(f"ERROR!!! Nama instance tidak ditemukan di variabel instances di fungsi findFirstInstance\nArgumen \"instanceObjectName\": {instanceObjectName}\nArgumen \"layerName\": {layerName}\nArgumen \"roomName\": {roomName}")
                else:
                    print(f"ERROR!!! Layer dengan nama \"{layerName}\" bukan berupa instanceLayer di fungsi findFirstInstance\nArgumen \"layerName\": {layerName}\nArgumen \"roomName\": {roomName}")






# Mengembalikan surface yang sedang digunakan oleh engine (mengembalikan surface untuk GUI atau surface untuk dunia game)
def getCurrentUsedSurface():
    if (onGuiLoop): return aplicationSurface
    else:           return currentRoom.cameraSurface
    











#V Fungsi untuk mengatur font yang akan digunakan untuk menggambar text dengan fungsi bernama drawText()
def drawSetFont(_fontAsset):
    global currentDrawFontAsset
    if isinstance(_fontAsset , fontAsset):
        currentDrawFontAsset = _fontAsset
    else:
        currentDrawFontAsset = fontAsset("Arial" , 12)




# Fungsi untuk menggambar persegi dengan koordinat rect.
def drawRect(X1 , Y1 , X2 , Y2 , colour = (225,225,225)):
    pygame.draw.rect(getCurrentUsedSurface() , colour , (X1 , Y1 , X2 , Y2))



#V Fungsi untuk menggambar sprite ke dunia game atau ke GUI
def drawSprite(_spriteAsset , x , y , scaleX = 1 , scaleY = 1 , rotation = 0 , subImage = 0):
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
    

   
    if scaleX != 1 or scaleY != 1:
        newWidth = int(imageSurface.get_width() * scaleX)
        newHeight = int(imageSurface.get_height() * scaleY)
        imageSurface = pygame.transform.scale(imageSurface, (newWidth, newHeight))

    if rotation != 0:
        imageSurface = pygame.transform.rotate(imageSurface, rotation)

    if currentRoom is not None:
        if onGuiLoop:
            aplicationSurface.blit(imageSurface , (x , y))
        else:
            currentRoom.cameraSurface.blit(imageSurface , (x - currentRoom.cameraX , y - currentRoom.cameraY))




 
def drawText(string , x , y , xScale = 1 , yScale = 1 , rotation = 0 , color = (255 , 255 , 255)):
    global currentDrawFontAsset
    
    textSurface = currentDrawFontAsset.font.render(str(string), True, color)

    if xScale != 1 or yScale != 1:
        newWidth = int(textSurface.get_width() * xScale)
        newHeight = int(textSurface.get_height() * yScale)
        textSurface = pygame.transform.scale(textSurface, (newWidth, newHeight))

    if rotation != 0:
        textSurface = pygame.transform.rotate(textSurface, rotation)

    if currentRoom is not None:
        if onGuiLoop:
            aplicationSurface.blit(textSurface , (x , y))
        else:
            currentRoom.cameraSurface.blit(textSurface , (x - currentRoom.cameraX , y - currentRoom.cameraY))
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
        self.blueprintLayers = {
            instanceLayer: [],
            backgroundLayer: [],
        }

        self.cameraX = 0
        self.cameraY = 0
        self.cameraWidth = screenWidth
        self.cameraHeight = screenHeight
        self.cameraRoomSizeLimit = True
        self.cameraSurface = pygame.Surface((self.cameraWidth , self.cameraHeight))





    

                


       






#V Class spriteAsset ini digunakan untuk menyimpan gambar yang akan dapat digambar di layar tanpa bergantung pada class instance.
class spriteAsset:
    def __init__(self , pygameSurfaceOrList):
        self.surface = None

        if (isinstance(pygameSurfaceOrList , pygame.surface.Surface))or(isinstance(pygameSurfaceOrList , list)):
            self.surface = pygameSurfaceOrList
        else:
            print("GAGAL MEMBUAT SURFACE DI CLASS \"SpriteAsset\"")

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

class instanceLayer():
    def __init__(self , instances = {} , depth = 0):
        self.instances         = instances
        self.depth             = depth
        







        

#V Class instance adalah objek yang dapat ditempatkan di dalam ruangan. Instance memiliki posisi, ukuran, dan sprite yang dapat digambar di layar.
class instance:
    def __init__(self , _spriteAsset , x , y , xScale , yScale , eventDefinition = {} , optionalSettings = {}):
        #V INISIALISASI VARIABEL
        self.spriteAsset = _spriteAsset

        self.previousX = x
        self.previousY = y
        self.x = x
        self.y = y
        self.xScale = xScale
        self.yScale = yScale
        self.rotation = 0

        self.solid = False
        self.visible = True

        self.roomPersist = False
        
        self.draw = True
        self.update = True

        self.currentSprite = 0
        self.animationPlay = False
        self.animationLoop = False
        self.animationSpeed = 0.025

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
        for settingName in optionalSettings:
            if (settingName not in self):
                settingArgument = optionalSettings[settingName]
                self[settingName] = settingArgument

        #V Memanggil create event saat objek baru saja diciptakan
        if (callable(self.events["create"])):
            runingEventNodes["create"].append(self.events["create"])



        

    
    def drawSelf(self):
        frameTotal = 1

        #V Menghitung jumlah gambar yang terinstal pada spriteAsset
        if (isinstance(self.spriteAsset.surface , list)):
            frameTotal = len(self.spriteAsset.surface)

        #V Jika jumlah gambar melebihi 1
        if (self.animationPlay and frameTotal > 1):
            self.currentSprite += self.animationSpeed


        #V Mencegah frame melebihi batas indeks list
            if self.currentSprite >= frameTotal:
                if self.animationLoop:
                    self.currentSprite = 0 #< Kembali ke frame awal
                else:
                    self.currentSprite = frameTotal - 1 #< Berhenti di frame terakhir

        #V Mencegah error jika nilai frameTotal tiba-tiba berubah
        frameTotal = int(self.currentSprite) % max(1, frameTotal)


        drawSprite(self.spriteAsset,
                    self.x, self.y,
                    self.xScale  , self.yScale   , self.rotation,
                    frameTotal)


            



    def forceUpdate(self):
        #V Mengatur posisi sebelumnya agar dapat digunakan untuk logika seperti pergerakan dan tabrakan.
        self.previousX = self.x
        self.previousY = self.y





    def isColliding(self , instance2):
        return (self.x < instance2.x + instance2.width and self.x + self.width > instance2.x 
                and self.y < instance2.y + instance2.height and self.y + self.height > instance2.y)
    




    

currentRoom = room(1 , 1)     
 #========================   

















#========================
#INISIALISASI YANG LAIN
#========================
drawSetFont(fontAsset("Arial" , 12))
#========================

















#========================
# INISIALISASI ASET MENTAH (Cara cepat)
#========================
#V Sekumpulan aset mentah yang akan digunakan untuk game, alih-alih menyatukan dengan variabel luar lain.
rawAssets = {
    "gameIcon" : pygame.image.load(os.path.join("assets" , "gameIcon2.png")),
}


#V Sekumpulan aset yang sudah dibungkus.
Assets = {
    "spr_heart" : spriteAsset(rawAssets["gameIcon"]),
}
#========================
















#========================
# INISIALISASI RUANGAN
#========================
#V Inisialisasi semua ruangan
roomInstances["roomInit"] = room(1000 , 1000)
roomInstances["room2"]    = room(1000 , 1000)
#========================














#========================
# FUNGSI / METHOD GLOBAL KHUSUS UNTUK EVENT INSTANSI.
#========================
def control():
    if pygame.key.get_pressed()[pygame.K_RIGHT]: currentRoom.cameraX += 5
    if pygame.key.get_pressed()[pygame.K_LEFT]: currentRoom.cameraX -= 5
    if pygame.key.get_pressed()[pygame.K_DOWN]: currentRoom.cameraY += 5
    if pygame.key.get_pressed()[pygame.K_UP]: currentRoom.cameraY -= 5

    # Cara aman mengakses instance di dalam arsitektur layer-mu:
    if "instancesLayer" in layers and "instanceTest" in layers["instancesLayer"].instances:
        player = layers["instancesLayer"].instances["instanceTest"]
        
        if pygame.key.get_pressed()[pygame.K_d]: player.x += 5
        if pygame.key.get_pressed()[pygame.K_a]: player.x -= 5
        if pygame.key.get_pressed()[pygame.K_s]: player.y += 5
        if pygame.key.get_pressed()[pygame.K_w]: player.y -= 5
        print("Whoo!!")
   
#========================
















#========================
# INISIALISASI INSTANSI, DAN FUNGSI / METHOD UNTUK EVENT INSTANSI.
#========================

roomAddBlueprint("roomInit", "instancesLayer", instanceLayer(
    instances = {
            "instanceTest" : instance(Assets["spr_heart"], 200, 200, 1, 1, eventDefinition = {
                "step": control,
            })
    }
))



#V Ruangan yang pertama kali dimasuki saat game dimulai.
roomGoto("roomInit")

#========================




 












#========================
# PERULANGAN UTAMA
#========================
while isRunning:
    ##> SYSTEM STEP (untuk penanganan sistem seperti input, logika, dan menggambar)
    #V Penanganan input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            isRunning = False

    #V Penanganan logika instansi dan ruangan.
    for eventName in runingEventNodes:
        runingEventNodes[eventName].clear() #< Bersihkan fungsi / method lama

    #V Menambahkan fungsi awal (Fungsi inti agar game berjalan dengan benar)
    runingEventNodes["beginStep"].append( lambda: globals().update({"onGuiLoop": False}) )

    runingEventNodes["endStep"].append(roomForceUpdate)

    runingEventNodes["beginDrawGUI"].append( lambda: aplicationSurface.blit(pygame.transform.scale(currentRoom.cameraSurface, (screenWidth, screenHeight)), (0, 0)) )
    runingEventNodes["beginDrawGUI"].append( lambda: globals().update({"onGuiLoop": True}) )


    #V Menambahkan fungsi untuk menggambar informasi debug jika DEBUGUI bernilai True.
    if (DEBUGUI):
        runingEventNodes["endDrawGUI"].append( lambda: drawText(f"CAM: X:{currentRoom.cameraX} Y:{currentRoom.cameraY} WIDTH:{currentRoom.cameraWidth} HEIGHT:{currentRoom.cameraHeight}", 20 , 20 , 2 , 2))
    
    #V Menambahkan fungsi untuk menggambar permukaan kamera ke permukaan aplikasi, dengan ukuran yang disesuaikan dengan ukuran layar.
    scaledCamera = pygame.transform.scale(currentRoom.cameraSurface, (screenWidth, screenHeight))
    aplicationSurface.blit(scaledCamera, (0, 0))


    instanceLayers = {layerName: layer for layerName, layer in layers.items() if isinstance(layer, instanceLayer)} #< Mengambil semua instansi class instanceLayer di dalam variabel layers.
    for layerName, layer in instanceLayers.items():

        for instanceObjectName , instanceObject in layer.instances.items():
            if (instanceObjectName not in layer.instances or        #< Cek jika instansi masih terdaftar atau sudah dihapus di event sebelumnya.
               not isinstance(instanceObject , instance)): continue #< Cek jika objek saat ini berupa class instance atau tidak.


            #V Memanggil fungsi forceUpdate untuk setiap instansi, agar variabel posisi sebelumnya dapat digunakan untuk logika seperti pergerakan dan tabrakan.
            instanceObject.forceUpdate() 

            #V Menambahkan semua fungsi / method yang ada di setiap event instansi ke dalam variabel runingEventNodes, agar dapat dijalankan secara berurutan di step selanjutnya.
            for eventName , eventFunction in instanceObject.events.items():
                if callable(eventFunction):
                    runingEventNodes[eventName].append(eventFunction)

            


    #V Menjalankan semua fungsi yang sudah diurutkan di dalam variabel runingEventNodes secara berurutan.
    for eventName in runingEventNodes:
        for eventFunction in runingEventNodes[eventName]:
            if callable(eventFunction):
                eventFunction()

                



    ##V Akhir perulangan
    pygame.display.flip()
    clock.tick(actualFPS)
    ##<
#========================






#========================
# PENUTUP
#========================
pygame.quit()
sys.exit()
#========================













