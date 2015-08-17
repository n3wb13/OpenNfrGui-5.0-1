from re import compile as re_compile
from os import path as os_path, listdir
import os, glob, time, random
from Components.MenuList import MenuList
from Components.Harddisk import harddiskmanager
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename, pathExists, fileExists, crawlDirectory
from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, \
	eServiceReference, eServiceCenter, gFont
from Tools.LoadPixmap import LoadPixmap
from enigma import getDesktop
EXTENSIONS = {
		"m4a": "music",
		"mp2": "music",
		"mp3": "music",
		"wma": "music",
		"wav": "music",
		"ogg": "music",
		"m3u": "music",
		"flac": "music",
		"jpg": "picture",
		"jpeg": "picture",
		"png": "picture",
		"bmp": "picture",
		"mts": "movie",
		"m2ts": "movie",
		"pls": "music",
		"vdr": "movie",
		"vob": "movie",
		"ogm": "movie",
		"wmv": "movie",
		"ts": "movie",
		"avi": "movie",
		"divx": "movie",
		"mpg": "movie",
		"mpeg": "movie",
		"mkv": "movie",
		"mp4": "movie",
		"mov": "movie",
		"trp": "movie",
		"m4v": "movie",
		"flv": "movie",
		"rar": "rar",
		"iso": "iso",
		"img": "img"
	}
def FileEntryComponent(name, absolute = None, isDir = False, directory = "/", size = 0, timestamp = 0):
	res = [ (absolute, isDir, name) ]
	# breite des Balken
	if getDesktop(0).size().width() == 1920:
		if name == "..":
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 1000, 30, 0, RT_HALIGN_LEFT, name))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 1000, 30, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, name))
	else:
		if name == "..":
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 1000, 20, 0, RT_HALIGN_LEFT, name))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 1000, 20, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, name))
	#res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name))
	if isDir:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "extensions/directory.png"))
	else:
		extension = name.split('.')
		extension = extension[-1].lower()
		if EXTENSIONS.has_key(extension):
			png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "extensions/" + EXTENSIONS[extension] + ".png"))
		else:
			png = None
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))
	return res
class FileList(MenuList):
	def __init__(self, directory, showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = None, useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None, sort = "default"):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.additional_extensions = additionalExtensions
		self.mountpoints = []
		self.current_directory = None
		self.current_mountpoint = None
		self.useServiceRef = useServiceRef
		self.showDirectories = showDirectories
		self.showMountpoints = showMountpoints
		self.showFiles = showFiles
		self.isTop = isTop
		# example: matching .nfi and .ts files: "^.*\.(nfi|ts)"
		self.matchingPattern = matchingPattern
		self.sort = sort
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []
		self.refreshMountpoints()
		self.changeDir(directory, sort = sort)
		if getDesktop(0).size().width() == 1920:
			self.l.setFont(0, gFont("Regular", 26))
			self.l.setItemHeight(36)
		else:
			self.l.setFont(0, gFont("Regular", 18))
			self.l.setItemHeight(21)
		self.serviceHandler = eServiceCenter.getInstance()
	def refreshMountpoints(self):
		self.mountpoints = [os_path.join(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
		self.mountpoints.sort(reverse = True)
	def getMountpoint(self, file):
		file = os_path.join(os_path.realpath(file), "")
		for m in self.mountpoints:
			if file.startswith(m):
				return m
		return False
	def getMountpointLink(self, file):
		if os_path.realpath(file) == file:
			return self.getMountpoint(file)
		else:
			if file[-1] == "/":
				file = file[:-1]
			mp = self.getMountpoint(file)
			last = file
			file = os_path.dirname(file)
			while last != "/" and mp == self.getMountpoint(file):
				last = file
				file = os_path.dirname(file)
			return os_path.join(last, "")
	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return None
		return self.l.getCurrentSelection()[0]
	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		if not l or l[0][1] == True:
			return None
		else:
			return self.serviceHandler.info(l[0][0]).getEvent(l[0][0])
	def getFileList(self):
		return self.list
	def inParentDirs(self, dir, parents):
		dir = os_path.realpath(dir)
		for p in parents:
			if dir.startswith(p):
				return True
		return False
	def changeDir(self, directory, sort = "default", select = None):
		isDir = False
		if sort == "shuffle":
			sort = "default"
			shuffle = True
		else:
			shuffle = False
		self.list = []
		if self.current_directory is None:
			if directory and self.showMountpoints:
				self.current_mountpoint = self.getMountpointLink(directory)
			else:
				self.current_mountpoint = None
		self.current_directory = directory
		directories = []
		files = []
		if directory is None and self.showMountpoints:
			for p in harddiskmanager.getMountedPartitions():
				path = os_path.join(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(FileEntryComponent(name = p.description, absolute = path, isDir = True, directory = directory))
			files = [ ]
			directories = [ ]
		elif directory is None:
			files = [ ]
			directories = [ ]
		elif self.useServiceRef:
			root = eServiceReference(2, 0, directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			list = serviceHandler.list(root)
			while 1:
				s = list.getNext()
				if not s.valid():
					del list
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if fileExists(directory):
				try:
					files = listdir(directory)
				except:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if os_path.isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)
		if directory is not None and self.showDirectories and not self.isTop:
			if directory == self.current_mountpoint and self.showMountpoints:
				self.list.append(FileEntryComponent(name = "<" +_("List of storage Devices") + ">", absolute = None, isDir = True, directory = directory))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(FileEntryComponent(name = "<" +_("Parent directory") + ">", absolute = '/'.join(directory.split('/')[:-2]) + '/', isDir = True, directory = directory))
		date_file_list = []
		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					file = x
					path = x
					if pathExists(path):
						stats = os.stat(path)
						size = stats[6]
						lastmod_date = time.localtime(stats[8])
					else:
						size = 0
						lastmod_date = 0
					isDir = True
					if sort == "size" or sort == "sizereverse":
						date_file_tuple = size, name, path, file, lastmod_date, isDir
					elif sort == "date" or sort == "datereverse" or sort == "default":
						date_file_tuple = lastmod_date, name, path, file, size, isDir
					elif sort == "alpha" or sort == "alphareverse":
						date_file_tuple = name, lastmod_date, path, file, size, isDir
					date_file_list.append(date_file_tuple)
		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
					file = x
					if pathExists(path):
						stats = os.stat(path)
						size = stats[6]
						lastmod_date = time.localtime(stats[8])
					else:
						size = 0
						lastmod_date = 0
					isDir = False
					if sort == "size" or sort == "sizereverse":
						date_file_tuple = size, name, path, file, lastmod_date, isDir
					elif sort == "date" or sort == "datereverse" or sort == "default":
						date_file_tuple = lastmod_date, name, path, file, size, isDir
					elif sort == "alpha" or sort == "alphareverse":
						date_file_tuple = name, lastmod_date, path, file, size, isDir
					date_file_list.append(date_file_tuple)	
				else:
					path = directory + x
					name = x
					if sort == "size" or sort == "sizereverse":
						date_file_tuple = size, name, path, file, lastmod_date, isDir
					elif sort == "date" or sort == "datereverse" or sort == "default":
						date_file_tuple = lastmod_date, name, path, file, size, isDir
					elif sort == "alpha" or sort == "alphareverse":
						date_file_tuple = name, lastmod_date, path, file, size, isDir
					date_file_list.append(date_file_tuple)
		if sort == "datereverse" or sort == "alpha" or sort == "sizereverse" or sort == "date" or sort == "alphareverse" or sort == "size":
			date_file_list.sort()
		if sort == "date" or sort == "alphareverse" or sort == "size":
			date_file_list.reverse()
		if shuffle == True:
			random.shuffle(date_file_list)
		for x in date_file_list:
			if sort == "size" or sort == "sizereverse":
				size = x[0]				
				name = x[1]
				path = x[2]
				file = x[3] 
				timestamp = x[4]				
				isDir = x[5]
			elif sort == "date" or sort == "datereverse" or sort == "default":		
				timestamp = x[0]					
				name = x[1]
				path = x[2]
				file = x[3] 
				size = x[4]
				isDir = x[5]			
			elif sort == "alpha" or sort == "alphareverse":
				name = x[0]
				timestamp = x[1]					
				path = x[2]
				file = x[3] 
				size = x[4]
				isDir = x[5]
			if isDir == True:
				if not (self.inhibitMounts and self.getMountpoint(file) in self.inhibitMounts) and not self.inParentDirs(file, self.inhibitDirs):
					self.list.append(FileEntryComponent(name = name, absolute = file, isDir = isDir, directory = directory, size = size, timestamp = timestamp))
			else:
				if (self.matchingPattern is None) or re_compile(self.matchingPattern).search(path):
					self.list.append(FileEntryComponent(name = name, absolute = file , isDir = isDir, directory = directory, size = size, timestamp = timestamp))
		if self.showMountpoints and len(self.list) == 0:
			self.list.append(FileEntryComponent(name = _("nothing connected"), absolute = None, isDir = False))
		self.l.setList(self.list)
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]
				if isinstance(p, eServiceReference):
					p = p.getPath()
				if p == select:
					self.moveToIndex(i)
				i += 1
	def getCurrentDirectory(self):
		return self.current_directory
	def canDescent(self):
		if self.getSelection() is None:
			return False
		return self.getSelection()[1]
	def descent(self):
		if self.getSelection() is None:
			return
		self.changeDir(self.getSelection()[0], select = self.current_directory)
	def gotoParent(self):
		if self.current_directory is not None:
			if self.current_directory == self.current_mountpoint and self.showMountpoints:
				absolute = None
			else:
				absolute = '/'.join(self.current_directory.split('/')[:-2]) + '/'
			self.changeDir(absolute, select = self.current_directory)
	def getName(self):
		if self.getSelection() is None:
			return False
		return self.getSelection()[2]
	def getFilename(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			x = x.getPath()
		return x
	def getServiceRef(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			return x
		return None
	def execBegin(self):
		harddiskmanager.on_partition_list_change.append(self.partitionListChanged)
	def execEnd(self):
		harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)
	def refresh(self, sort = "default"):
		self.sort = sort
		self.changeDir(self.current_directory, self.sort, self.getFilename())
	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()
def MultiFileSelectEntryComponent(name, absolute = None, isDir = False, selected = False):
	res = [ (absolute, isDir, selected, name) ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 1, 470, 30, 0, RT_HALIGN_LEFT, name))
	if isDir:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "extensions/directory.png"))
	else:
		extension = name.split('.')
		extension = extension[-1].lower()
		if EXTENSIONS.has_key(extension):
			png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "extensions/" + EXTENSIONS[extension] + ".png"))
		else:
			png = None
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 30, 2, 20, 20, png))
	if not name.startswith('<'):
		if selected is False:
			icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_off.png"))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 2, 0, 25, 25, icon))
		else:
			icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 2, 0, 25, 25, icon))
	return res
class MultiFileSelectList(FileList):
	def __init__(self, preselectedFiles, directory, showMountpoints = False, matchingPattern = None, showDirectories = True, showFiles = True,  useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None):
		self.selectedFiles = preselectedFiles
		if self.selectedFiles is None:
			self.selectedFiles = []
		FileList.__init__(self, directory, showMountpoints = showMountpoints, matchingPattern = matchingPattern, showDirectories = showDirectories, showFiles = showFiles,  useServiceRef = useServiceRef, inhibitDirs = inhibitDirs, inhibitMounts = inhibitMounts, isTop = isTop, enableWrapAround = enableWrapAround, additionalExtensions = additionalExtensions)
		self.changeDir(directory)			
		if getDesktop(0).size().width() == 1920:
			self.l.setItemHeight(35)
			self.l.setFont(0, gFont("Regular", 40))
		else:
			self.l.setItemHeight(25)
			self.l.setFont(0, gFont("Regular", 20))
		self.onSelectionChanged = [ ]
	def selectionChanged(self):
		for f in self.onSelectionChanged:
			f()
	def changeSelectionState(self):
		idx = self.l.getCurrentSelectionIndex()
		count = 0
		newList = []
		for x in self.list:
			if idx == count:
				if x[0][3].startswith('<'):
					newList.append(x)
				else:
					if x[0][1] is True:
						realPathname = x[0][0]
					else:
						realPathname = self.current_directory + x[0][0]
					if x[0][2] == True:
						SelectState = False
						for entry in self.selectedFiles:
							if entry == realPathname:
								self.selectedFiles.remove(entry)
					else:
						SelectState = True
						alreadyinList = False	
						for entry in self.selectedFiles:
							if entry == realPathname:
								alreadyinList = True
						if not alreadyinList:
							self.selectedFiles.append(realPathname)
					newList.append(MultiFileSelectEntryComponent(name = x[0][3], absolute = x[0][0], isDir = x[0][1], selected = SelectState ))
			else:
				newList.append(x)
			count += 1
		self.list = newList
		self.l.setList(self.list)
	def getSelectedList(self):
		return self.selectedFiles
	def changeDir(self, directory, select = None):
		self.list = []
		# if we are just entering from the list of mount points:
		if self.current_directory is None:
			if directory and self.showMountpoints:
				self.current_mountpoint = self.getMountpointLink(directory)
			else:
				self.current_mountpoint = None
		self.current_directory = directory
		directories = []
		files = []
		if directory is None and self.showMountpoints: # present available mountpoints
			for p in harddiskmanager.getMountedPartitions():
				path = os_path.join(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(MultiFileSelectEntryComponent(name = p.description, absolute = path, isDir = True))
			files = [ ]
			directories = [ ]
		elif directory is None:
			files = [ ]
			directories = [ ]
		elif self.useServiceRef:
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			list = serviceHandler.list(root)
			while 1:
				s = list.getNext()
				if not s.valid():
					del list
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if fileExists(directory):
				try:
					files = listdir(directory)
				except:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if os_path.isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)
		if directory is not None and self.showDirectories and not self.isTop:
			if directory == self.current_mountpoint and self.showMountpoints:
				self.list.append(MultiFileSelectEntryComponent(name = "<" +_("List of Storage Devices") + ">", absolute = None, isDir = True))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(MultiFileSelectEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(directory.split('/')[:-2]) + '/', isDir = True))
		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					alreadySelected = False
					for entry in self.selectedFiles:
						if entry  == x:
							alreadySelected = True					
					if alreadySelected:		
						self.list.append(MultiFileSelectEntryComponent(name = name, absolute = x, isDir = True, selected = True))
					else:
						self.list.append(MultiFileSelectEntryComponent(name = name, absolute = x, isDir = True, selected = False))
		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x
				if (self.matchingPattern is None) or re_compile(self.matchingPattern).search(path):
					alreadySelected = False
					for entry in self.selectedFiles:
						if os_path.basename(entry)  == x:
							alreadySelected = True	
					if alreadySelected:
						self.list.append(MultiFileSelectEntryComponent(name = name, absolute = x , isDir = False, selected = True))
					else:
						self.list.append(MultiFileSelectEntryComponent(name = name, absolute = x , isDir = False, selected = False))
		self.l.setList(self.list)
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]
				if isinstance(p, eServiceReference):
					p = p.getPath()
				if p == select:
					self.moveToIndex(i)
				i += 1
