# write the code for creating and managing the map here
import pickle

class Mapmanager():
   """ Manajemen kartu"""
   def __init__(self):
       self.model = 'block' # Model kubus ada di file block.egg
       # # tekstur berikut digunakan:
       self.texture = 'block.png'         
       self.colors = [
           (0.2, 0.2, 0.35, 1),
           (0.2, 0.5, 0.2, 1),
           (0.7, 0.2, 0.2, 1),
           (0.5, 0.3, 0.0, 1)
       ] #rgba
       # buat node peta utama:
       self.startNew()
       # self.addBlock((0,10, 0))


   def startNew(self):
       """menciptakan dasar untuk peta baru"""
       self.land = render.attachNewNode("Land") # node dimana semua blok peta terpasang


   def getColor(self, z):
       if z < len(self.colors):
           return self.colors[z]
       else:
           return self.colors[len(self.colors) - 1]


   def addBlock(self, position):
       # membuat blok bangunan
       self.block = loader.loadModel(self.model)
       self.block.setTexture(loader.loadTexture(self.texture))
       self.block.setPos(position)
       self.color = self.getColor(int(position[2]))
       self.block.setColor(self.color)
       self.block.setTag("at", str(position))
       self.block.reparentTo(self.land)


   def clear(self):
       """menghilangkan angka pada kartu"""
       self.land.removeNode()
       self.startNew()


   def loadLand(self, filename):
       """membuat peta bumi dari berkas teks, mengembalikan dimensinya"""
       self.clear()
       with open(filename) as file:
           y = 0
           for line in file:
               x = 0
               line = line.split(' ')
               for z in line:
                   for z0 in range(int(z)+1):
                       block = self.addBlock((x, y, z0))
                   x += 1
               y += 1
       return x,y
  
   def findBlocks(self, pos):
       return self.land.findAllMatches("=at=" + str(pos))


   def isEmpty(self, pos):
       blocks = self.findBlocks(pos)
       if blocks:
           return False
       else:
           return True


   def findHighestEmpty(self, pos):
       x, y, z = pos
       z = 1
       while not self.isEmpty((x, y, z)):
           z += 1
       return (x, y, z)


   def buildBlock(self, pos):
       """Kita menempatkan balok dengan mempertimbangkan gravitasi: """
       x, y, z = pos
       new = self.findHighestEmpty(pos)
       if new[2] <= z + 1:
           self.addBlock(new)


   def delBlock(self, position):
       """menghapus blok pada posisi yang ditentukan """
       blocks = self.findBlocks(position)
       for block in blocks:
           block.removeNode()


   def delBlockFrom(self, position):
       x, y, z = self.findHighestEmpty(position)
       pos = x, y, z - 1
       for block in self.findBlocks(pos):
               block.removeNode()


   def saveMap(self):
        blocks = self.land.getChildren()
        with open("my_map.dat","wb") as fout:
            pickle.dump(len(blocks), fout)

            for block in blocks:
                x,y,z = block.getPos()
                pickle.dump((int(x),int(y),int(z)), fout)


   def loadMap(self):
        self.clear()

        with open("my_map.dat","rb") as fin:

            for i in range(pickle.load(fin)):
                self.addBlock(pickle.load(fin))



