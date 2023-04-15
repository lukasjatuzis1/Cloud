class RecordClass:           #This class is used to keep track whether a user is within a record or not
 currentRecord = ""
 def __init__(self, currentRecord):
  self._currentRecord = currentRecord

 def setRecord(self, rec):
  self._currentRecord = rec

 def getRecord(self):
  return self._currentRecord
