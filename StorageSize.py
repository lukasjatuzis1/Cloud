class StorageSize:           #This class is used to keep track of the Storage Size
 size = 0
 def __init__(self, size):
  self._size = size

 def setSize(self, size):
  self._size = size

 def getSize(self):
  return self._size
