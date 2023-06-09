from datetime import datetime
import os
import random
from flask import Flask, render_template
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request, redirect, Response
from google.auth.transport import requests
from google.cloud import storage
import local_constants
from DirectoryClass import DirectoryClass
from RecordClass import RecordClass
from StorageSize import StorageSize

credential_path = "lukas-project.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request() #retrieve datastore client (verify users at any stage)

#Create User Info
def createUserInfo(claims):
 entity_key = datastore_client.key('UserInfo', claims['email'])
 entity = datastore.Entity(key = entity_key)
 entity.update({
 'email': claims['email'],
 'name': claims['name'],
 })
 datastore_client.put(entity)

#Get User Info
def retrieveUserInfo(claims):
 entity_key = datastore_client.key('UserInfo', claims['email'])
 entity = datastore_client.get(entity_key)
 return entity

#Get List of Files and Directories
def blobList(prefix):
 storage_client = storage.Client(project=local_constants.PROJECT_NAME)
 return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

#Naviagte to this Function to Add a Directory
@app.route('/add_directory', methods=['POST'])
def addDirectoryHandler():
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   directory_name = request.form['dir_name']
   if directory_name == '' or "/" in directory_name:
    return redirect('/')
   directory_name = directory_name + "/"
   user_info = retrieveUserInfo(claims)
   entity = datastore.Entity(key = datastore_client.key(user_info['email']))
   entity.update({"directory_name" : directory_name})

   datastore_client.put(entity)
   addDirectory(directory_name)
  except ValueError as exc:
   error_message = str(exc)
 return redirect('/')

#Naviagte to this Function to Download a File
@app.route('/download_file/<string:dirname>/<string:filename>', methods=['POST'])
def downloadFile(dirname,filename):
 print("File Downloaded:", filename, dirname)
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 file_bytes = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
  except ValueError as exc:
   error_message = str(exc)
 return Response(downloadBlob(dirname,filename), mimetype='application/octet-stream')

#Naviagte to this Function to Open a Directory
@app.route('/open_directory/<string:filename>' + '/', methods=['POST'])
def openDirectory(filename):
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 file_list = []
 no_directories = "true"
 openedDirectory.setDirectory(filename)
 found_same_file = "false"

 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   createUserInfo(claims)
   user_info = retrieveUserInfo(claims)
   if user_info == None:
    createUserInfo(claims)
    user_info = retrieveUserInfo(claims)

    #Display a List of Files within selected Directory
   blob_list = blobList(None)
   for i in blob_list:
    if i.name[len(i.name) - 1] != '/':
     if("/" in i.name):
      full_path = i.name.split("/", 1)
      file_in_current_directory = full_path[0]
      file_full_name = full_path[1]

      full_version_name = file_full_name.split("~", 1)
      file_ver = full_version_name[0]
      file_na = full_version_name[1]
      if(file_in_current_directory == filename):
       for j in file_list:
        full_path1 = j.name.split("~", 1)
        file_in_current_directory1 = full_path1[0]
        file_full_name1 = full_path1[1]
        if file_full_name1 == file_na:
         found_same_file = "true"
         break
       if found_same_file == "false":
        i.display_name = file_na

        query = datastore_client.query(kind=user_info['email'])
        friends_accessed_file = query.fetch(limit=10)
        for k in friends_accessed_file:
         if 'file_name' in k:
          if k['file_name'] == file_full_name:
           file_list.append(i)
         if 'shared_user' in k:
          print("Shared User:",k['shared_user'])

  except ValueError as exc:
   error_message = str(exc)
 return render_template('directory.html', user_data=claims, error_message=error_message, user_info=user_info, file_list=file_list, no_directories=no_directories)

#Naviagte to this Function to Add a File
@app.route('/upload_file', methods=['post'])
def uploadFileHandler():
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   file = request.files['file_name']
   if file.filename == '' or "/" in file.filename or "~" in file.filename:
    return redirect('/')
   user_info = retrieveUserInfo(claims)

   file_already_exists = "false"
   blob_list = blobList(None)
   if(blob_list):
    for i in blob_list:
     if i.name[len(i.name) - 1] != '/':
      if(openedDirectory.getDirectory() + "/" in i.name):
       full_path = i.name.split("/", 1)
       files = full_path[1]
       files = files.split("~", 1)
       files_version = files[0]
       files_name = files[1]
       if files_name == file.filename:
        print("A file with this name already exists within this directory, please rename file or choose another file")
        file_already_exists = "true"
        break
       else:
        file_already_exists = "false"
    else:
     file_already_exists = "false"

   if file_already_exists == "false":
    print("File does not exist within this directory, Uploading File")
    file.filename = "0~" + file.filename
    storage_size_bytes = getStorageSize()
    if storage_size_bytes > 5000000:
     print("Storage Over 5MB, Not Uploading File")
    else:
     entity = datastore.Entity(key = datastore_client.key(user_info['email']))
     entity.update({"file_name" : file.filename})

     datastore_client.put(entity)
     addFile(file)

  except ValueError as exc:
   error_message = str(exc)
 return redirect('/')

#Naviagte to this Function to Delete a File
@app.route('/delete_file/<string:dirname>/<string:filename>', methods=['post'])
def deleteFile(dirname,filename):
 print("Attempting to Delete:", filename)
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   user_info = retrieveUserInfo(claims)
   if user_info == None:
    createUserInfo(claims)
    user_info = retrieveUserInfo(claims)

   deleteBlob(dirname,filename)
  except ValueError as exc:
   error_message = str(exc)
 return redirect('/')

#Naviagte to this Function to Delete a Directory
@app.route('/delete_directory/<string:filename>' + "/", methods=['post'])
def deleteDirectory(filename):
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   deleteDir(filename)
  except ValueError as exc:
   error_message = str(exc)
 return redirect('/')

#Naviagte to this Function to Open file versions
@app.route('/versions/<string:dirname>/<string:filename>', methods=['post'])
def versionFileHandler(dirname,filename):
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 file_versions = []
 file_dates = []
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   user_info = retrieveUserInfo(claims)
   if user_info == None:
    createUserInfo(claims)
    user_info = retrieveUserInfo(claims)
   blob_list = blobList(None)
   if(blob_list):
    for i in blob_list:
     if i.name[len(i.name) - 1] != '/':
      if(openedDirectory.getDirectory() + "/" in i.name):
       full_path = i.name.split("/", 1)
       file_version_name = full_path[1]
       full_path1 = file_version_name.split("~", 1)
       file_name1 = full_path1[1]
       full_path2 = filename.split("~", 1)
       file_name2 = full_path2[1]
       if file_name1 == file_name2:
        date_raw = i.time_created
        date = date_raw.year , date_raw.month, date_raw.day
        file_dates.append(date)
        i.display_name = file_name1
        i.date = date
        file_versions.append(i)
   file_name_only = filename.split("~", 1)
   file_set_record_name = file_name_only[1]
   openedRecord.setRecord(file_set_record_name)
  except ValueError as exc:
   error_message = str(exc)

 return render_template('records.html', user_data=claims, error_message=error_message, file_list=file_versions, file_dates=file_dates)

#Naviagte to this Function to open shared files
@app.route('/shared_versions/<string:dirname>/<string:filename>', methods=['post'])
def sharedVersionFileHandler(dirname,filename):
 openedDirectory.setDirectory(dirname)
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 file_versions = []
 file_dates = []

 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   user_info = retrieveUserInfo(claims)
   if user_info == None:
    createUserInfo(claims)
    user_info = retrieveUserInfo(claims)
   blob_list = blobList(None)
   if(blob_list):
    for i in blob_list:
     if i.name[len(i.name) - 1] != '/':
      if(openedDirectory.getDirectory() + "/" in i.name):
       full_path = i.name.split("/", 1)
       file_version_name = full_path[1]
       full_path1 = file_version_name.split("~", 1)
       file_name1 = full_path1[1]
       full_path2 = filename.split("~", 1)
       file_name2 = full_path2[1]
       if file_name1 == file_name2:
        date_raw = i.time_created
        date = date_raw.year , date_raw.month, date_raw.day
        file_dates.append(date)
        i.display_name = file_name1
        i.date = date
        file_versions.append(i)
   file_name_only = filename.split("~", 1)
   file_set_record_name = file_name_only[1]
   openedRecord.setRecord(file_set_record_name)
  except ValueError as exc:
   error_message = str(exc)

 return render_template('shared_versions.html', user_data=claims, error_message=error_message, file_list=file_versions, file_dates=file_dates)

#Naviagte to this Function to Add a File version
@app.route('/upload_file_version', methods=['post'])
def uploadFileVersionHandler():
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   file = request.files['file_name']
   if file.filename == '' or "/" in file.filename or "~" in file.filename:
    return redirect('/')
   user_info = retrieveUserInfo(claims)

   highest_version = 0
   blob_list = blobList(None)
   if(blob_list):
    for i in blob_list:
     if i.name[len(i.name) - 1] != '/':
      if(openedDirectory.getDirectory() + "/" in i.name):
       full_path = i.name.split("/", 1)
       file_name = full_path[1]
       file_version_name = file_name.split("~", 1)
       file_version_only = file_version_name[0]
       file_name_only = file_version_name[1]
       if file_name_only == openedRecord.getRecord():
        file_version_only = int(file_version_only)
        if file_version_only >= highest_version:
         highest_version = file_version_only

   highest_version = highest_version + 1
   highest_version = str(highest_version)
   file.filename = highest_version + "~" + openedRecord.getRecord()
   storage_size_bytes = getStorageSize()
   if storage_size_bytes > 5000000:
       print("Storage Over 5MB, Not Uploading File")
   else:
    addFile(file)
  except ValueError as exc:
   error_message = str(exc)
 return redirect('/')

#Naviagte to this Function share a file
@app.route('/share_file/<string:dirname>/<string:filename>', methods=['post'])
def shareFileHandler(dirname,filename):
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   friend_id = request.form['friend_id']
   entity = datastore.Entity(key = datastore_client.key(friend_id))
   entity.update({"shared_file_name" : dirname + "/" + filename})
   datastore_client.put(entity)
   query = datastore_client.query(kind=friend_id)
   friends_accessed_file = query.fetch(limit=10)

   for i in friends_accessed_file:
    if 'main_user' in i:
     print(i['main_user'])
    if 'shared_user' in i:
     print(i['shared_user'])
  except ValueError as exc:
   error_message = str(exc)
 return redirect('/')

#Get Storage Size
def getStorageSize():
 size = 0
 blob_list = blobList(None)
 if(blob_list):
  for i in blob_list:
   if i.name[len(i.name) - 1] != '/' or i.name != "/~" :
    size = size + i.size
 size = size - 6618
 return size

#Add new Directory within Home Page
def addDirectory(directory_name):
 storage_client = storage.Client(project=local_constants.PROJECT_NAME)
 bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
 blob = bucket.blob(directory_name)
 blob.upload_from_string('', content_type='application/x-www-formurlencoded;charset=UTF-8')

#Add new File within Directory
def addFile(file):
 storage_client = storage.Client(project=local_constants.PROJECT_NAME)
 bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
 if openedDirectory.getDirectory() != "":
  file.filename = openedDirectory.getDirectory() + "/" + file.filename
 blob = bucket.blob(file.filename)
 blob.upload_from_file(file)

#Download a file
def downloadBlob(dirname,filename):
 storage_client = storage.Client(project=local_constants.PROJECT_NAME)
 bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
 filename = dirname + "/" + filename
 blob = bucket.blob(filename)
 return blob.download_as_bytes()

#Delete a Directory within Home Page
def deleteDir(filename):
 print("Directory Deleting:",filename + "/")
 files_exist_in_directory = "false"
 blob_list = blobList(None)
 for i in blob_list:
  if i.name[len(i.name) - 1] != '/':
   if filename + "/" in i.name:
    files_exist_in_directory = "true"
    break

 if files_exist_in_directory == "true":
  print("This Directory Contains Files, Not Deleting")
 else:
  print("This Directory is Empty, Deleteing Directory")
  storage_client = storage.Client(project=local_constants.PROJECT_NAME)
  bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
  blob = bucket.blob(filename + "/")
  blob.delete()

#Delete a File
def deleteBlob(dirname,filename):
 print("File Deleted:", filename)
 currentDir = openedDirectory.getDirectory()
 storage_client = storage.Client(project=local_constants.PROJECT_NAME)
 bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
 filename = dirname + "/" + filename
 blob = bucket.blob(filename)
 blob.delete()
 openedDirectory.setDirectory("")

#Naviagte back to Home Page
@app.route('/back', methods=['POST'])
def back():
 return redirect('/')

#Route to Home Page
@app.route('/')
def root():
 id_token = request.cookies.get("token")
 error_message = None
 claims = None
 times = None
 user_info = None
 file_list = []
 directory_list = []
 shared_list = []
 openedDirectory.setDirectory("")
 openedRecord.setRecord("")
 if id_token:
  try:
   claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
   user_info = retrieveUserInfo(claims)
   if user_info == None:
    createUserInfo(claims)
    user_info = retrieveUserInfo(claims)

    #Display a List of Directories
   blob_list = blobList(None)
   for i in blob_list:
    if i.name[len(i.name) - 1] == '/':
     query = datastore_client.query(kind=user_info['email'])
     friends_accessed_file = query.fetch(limit=10)

     for k in friends_accessed_file:
      if 'directory_name' in k:
       if k['directory_name'] == i.name:
        directory_list.append(i)
    elif "/" not in i.name:
     file_list.append(i)

   blob_list = blobList(None)
   for i in blob_list:
    if i.name[len(i.name) - 1] != '/' and i.name != '/':
     query = datastore_client.query(kind=user_info['email'])
     friends_accessed_file = query.fetch(limit=10)

     full_path = i.name.split('/')
     file_path = full_path[0]
     file_name = full_path[1]

     for k in friends_accessed_file:
      if 'shared_file_name' in k:
       if k['shared_file_name'] == i.name:
        if 'shared_file_name' in k:
         shared_list.append(i)

  except ValueError as exc:
   error_message = str(exc)
 storage_size_bytes = getStorageSize()
 storage_size_kb = storage_size_bytes/1000
 storage_size = storage_size_kb/1000

 return render_template('index.html', user_data=claims, error_message=error_message, user_info=user_info, directory_list=directory_list, storage_size=storage_size, shared_files=shared_list)

#Start Application
if __name__ == '__main__':
 global openedDirectory
 openedDirectory = DirectoryClass("")
 global openedRecord
 openedRecord = RecordClass("")
 global storageSize
 storageSize = StorageSize(0)
 getStorageSize()

 app.run(host='127.0.0.1', port=8060, debug=True)
