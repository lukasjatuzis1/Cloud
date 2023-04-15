class DirectoryClass:           #This class is used to keep track whether a user is within a directory or not
 currentDirectory = ""
 def __init__(self, currentDirectory):
  self._currentDirectory = currentDirectory

 def setDirectory(self, dir):
  self._currentDirectory = dir

 def getDirectory(self):
  return self._currentDirectory
