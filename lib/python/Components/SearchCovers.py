#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
# maintainer: <schomi@vuplus-support.org> 
# THX @einfall for search part of code

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.

#######################################################################
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import *
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmap, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.PluginComponent import plugins
# from Components.FileList import FileList
from re import compile as re_compile
from os import path as os_path, listdir
from Components.MenuList import MenuList
from Components.Harddisk import harddiskmanager
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename, fileExists
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, eServiceReference, eServiceCenter, gFont
from Tools.LoadPixmap import LoadPixmap
#
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.GUIComponent import GUIComponent
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools.Directories import pathExists, fileExists, SCOPE_SKIN_IMAGE, resolveFilename
from Screens.Screen import Screen
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, loadPNG, RT_WRAP, eConsoleAppContainer, eServiceCenter, eServiceReference, getDesktop, loadPic, loadJPG, RT_VALIGN_CENTER, gPixmapPtr, ePicLoad, eTimer
import sys, os, re, shutil
from os import path, remove
from twisted.web.client import getPage
from twisted.web.client import downloadPage
from twisted.web import client, error as weberror
from twisted.internet import reactor
from twisted.internet import defer
from urllib import urlencode
#from __init__ import _

pname = _("Find Covers")
pdesc = _("Find covers ... function for Movielist")
pversion = "0.5-r0"
pdate = "20140425"

def main(session, service, **kwargs):
	session.open(CoverFindScreen, service, session.current_dialog, **kwargs)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("CoverFind"), description=_("Find Covers ..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc=main)

def decodeHtml(text):
	text = text.replace('&auml;','ä')
	text = text.replace('\u00e4','ä')
	text = text.replace('&#228;','ä')

	text = text.replace('&Auml;','Ä')
	text = text.replace('\u00c4','Ä')
	text = text.replace('&#196;','Ä')

	text = text.replace('&ouml;','ö')
	text = text.replace('\u00f6','ö')
	text = text.replace('&#246;','ö')

	text = text.replace('\xc3\xb6','ö')
	text = text.replace('\xc3\x96','Ö')
	text = text.replace('\xc3\xbc','ü')
	text = text.replace('\xc3\x9c','Ü')
	text = text.replace('\xc3\xab','ä')
	text = text.replace('\xc3\x84','Ä')

	text = text.replace('&ouml;','Ö')
	text = text.replace('&Ouml;','Ö')
	text = text.replace('\u00d6','Ö')
	text = text.replace('&#214;','Ö')

	text = text.replace('&uuml;','ü')
	text = text.replace('\u00fc','ü')
	text = text.replace('&#252;','ü')

	text = text.replace('&Uuml;','Ü')
	text = text.replace('\u00dc','Ü')
	text = text.replace('&#220;','Ü')

	text = text.replace('&szlig;','ss')
	text = text.replace('\u00df','ss')
	text = text.replace('&#223;','ss')

	return text

def cleanFile(text):
	cutlist = ['x264','720p','1080p','1080i','PAL','GERMAN','ENGLiSH','WS','DVDRiP','UNRATED','RETAIL','Web-DL','DL','LD','MiC','MD','DVDR','BDRiP','BLURAY','DTS','UNCUT','ANiME',
				'AC3MD','AC3','AC3D','TS','DVDSCR','COMPLETE','INTERNAL','DTSD','XViD','DIVX','DUBBED','LINE.DUBBED','DD51','DVDR9','DVDR5','h264','AVC',
				'WEBHDTVRiP','WEBHDRiP','WEBRiP','WEBHDTV','WebHD','HDTVRiP','HDRiP','HDTV','ITUNESHD','REPACK','SYNC']
	text = text.replace('.flv','').replace('.ts','').replace('.m2ts','').replace('.mkv','').replace('.avi','').replace('.mpeg','').replace('.mpg','').replace('.iso','').replace('.mp4','')
	
	for word in cutlist:
		text = re.sub('(\_|\-|\.|\+)'+word+'(\_|\-|\.|\+)','+', text, flags=re.I)
	text = text.replace('.',' ').replace('-',' ').replace('_',' ').replace('+','')

	return text
	
def cleanEnd(text):
	text = text.replace('.flv','').replace('.ts','').replace('.m2ts','').replace('.mkv','').replace('.avi','').replace('.mpeg','').replace('.mpg','').replace('.iso','').replace('.mp4','')
	return text
	
class PicLoader:
    def __init__(self, width, height, sc=None):
        self.picload = ePicLoad()
        if(not sc):
            sc = AVSwitch().getFramebufferScale()
        self.picload.setPara((width, height, sc[0], sc[1], False, 1, "#ff000000"))

    def load(self, filename):
        self.picload.startDecode(filename, 0, 0, False)
        data = self.picload.getData()
        return data
    
    def destroy(self):
        del self.picload
		
class CoverFindScreen(Screen):
	skin = """
		<screen name="CoverFindScreen" position="40,80" size="1200,600" title=" ">
				<widget name="searchinfo" position="10,10" size="1180,30" font="Regular;24" foregroundColor="unfff000" />
				<widget name="list" position="10,60" size="1180,500" scrollbarMode="showOnDemand" />
				<widget name="key_red" position="53,568" size="260,25" transparent="1" font="Regular;20" />
				<widget name="key_green" position="370,568" size="260,25" transparent="1" font="Regular;20" />
				<widget name="key_yellow" position="681,568" size="260,25" transparent="1" font="Regular;20" />
				<widget name="key_blue" position="979,568" size="260,25" transparent="1" font="Regular;20" />
				<ePixmap pixmap="skin_default/buttons/red.png" position="17,566" size="30,30" alphatest="blend" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="335,566" size="30,30" alphatest="blend" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="647,566" size="30,30" alphatest="blend" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="946,566" size="30,30" alphatest="blend" />
				</screen>"""	

	def __init__(self, session, service, parent, args = 0):
		Screen.__init__(self, session, parent = parent)
		self.session = session

		self.isDirectory = False
		serviceHandler = eServiceCenter.getInstance()
		info = serviceHandler.info(service)
		path = service.getPath()
#		if path.endswith(".ts") is True:
#			path = path[:-3]
		self.savePath = path
		self.dir = '/'.join(path.split('/')[:-1]) + '/'
		self.file = self.baseName(path)
		if path.endswith("/") is True:
			path = path[:-1]
			self.file = self.baseName(path)
			self.text = self.baseName(path)
			self.isDirectory = True
		else:
			self.text = cleanFile(info.getName(service))
			self.isDirectory = False
		print "[CoverFind] " + str(self.isDirectory)
		print "[CoverFind] " + path
		print "[CoverFind] " + str(self.dir)
		print "[CoverFind] " + str(self.file)	
		print "[CoverFind] " + str(self.text)


		self["actions"]  = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"red": self.cancel,
			"green": self.fileSearch,
			"yellow": self.searchSeries,
			"blue": self.manSearch,
			"cancel": self.cancel,
			"ok": self.ok
		}, -1)

		self['searchinfo'] = Label(_("Search for Covers ..."))
		self['key_red'] = Label(_("Cancel"))
		self['key_green'] = Label(_("Open cover file"))
		self['key_yellow'] = Label(_("Find more covers"))
		self['key_blue'] = Label(_("Search cover manual"))
		self['list'] = createCoverList()		
		
		self.onLayoutFinish.append(self.onFinish)
		
	def onFinish(self):
		self.setTitle(_("Cover finden ..."))
		self.getCoverMovie()
		
	def manSearch(self):
		self.session.openWithCallback(self.manSearchCB, VirtualKeyBoard, title = (_("Search for Cover:")), text = self.text)	
	
	def manSearchCB(self, text):
		if text:
			print "[CoverFind] " + text
			self.text = text
			self.getCoverMovie()
			
	def fileSearch(self):
		start_dir = "/tmp/"
		self.session.openWithCallback(self.fileSearchCB, CoverFindFile, start_dir)

	def fileSearchCB(self, res):
		if res:
			print "[CoverFind] " + res
			print "[CoverFind] " + self.savePath
			extension = res.split('.')
			extension = extension[-1].lower()
			self.savePath = cleanEnd(self.savePath)
			
			if self.isDirectory:
				print "[CoverFind] Folder"
				target = self.savePath + "folder." + extension
				print "[CoverFind] " + target
			else:
				print "[CoverFind] File"
				target = self.savePath + "." + extension
				print "[CoverFind] " + target
			try:		
				shutil.copy(res, target)
			except:
				print "[CoverFind] User rights are not sufficiently!"
			
			self.close(False)
		
	def searchSeries(self):
		#Proceed with search for series cover
		self.getCoverTV()

	def getCoverMovie(self):
		self['searchinfo'].setText(_("Try to find %s in tmdb ...")% self.text)
		url = "http://api.themoviedb.org/3/search/movie?api_key=8789cfd3fbab7dccf1269c3d7d867aff&query=%s&language=de" % self.text.replace(' ','%20')
		print "[CoverFind] " + url
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.readCoverMovie).addErrback(self.dataError)

	def getCoverTV(self):
		self['searchinfo'].setText(_("Try to find %s in tvdb ...")% self.text)
		url = "http://thetvdb.com/api/GetSeries.php?seriesname=%s&language=de" % self.text.replace(' ','%20')
		print "[CoverFind] " + url
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.readCoverTV).addErrback(self.dataError)

	def readCoverMovie(self, data):
		self.piclist = []
		urls = []
		list = re.findall('"id":(.*?),.*?original_title":"(.*?)".*?"poster_path":"(.*?)".*?title":"(.*?)"', data, re.S)
		if list:
			for id,otitle,coverPath,title in list:
				coverUrl = "http://image.tmdb.org/t/p/w185"+coverPath
				print "[CoverFind] " + title, coverUrl
				urls.append((title, coverUrl, id))

		if len(urls) != 0:
			ds = defer.DeferredSemaphore(tokens=2)
			downloads = [ds.run(self.download, url, title).addCallback(self.buildList,title,url,id,"movie").addErrback(self.dataError) for title,url,id in urls]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)
			self['searchinfo'].setText(_("Found for: %s") % self.text)
		else:
			self['searchinfo'].setText(_("%s not found.") % self.text)

	def readCoverTV(self, data):
		self.piclist = []
		urls = []
		tv = re.findall('<seriesid>(.*?)</seriesid>.*?<SeriesName>(.*?)</SeriesName>', data, re.S)
		if tv:
			for id,title in tv:
				coverUrl1 = "http://www.thetvdb.com/banners/_cache/posters/%s-1.jpg" % str(id)
				coverUrl2 = "http://www.thetvdb.com/banners/_cache/posters/%s-2.jpg" % str(id)
				coverUrl3 = "http://www.thetvdb.com/banners/_cache/posters/%s-3.jpg" % str(id)
				print "[CoverFind] " + title, coverUrl1
				urls.append((title, coverUrl1, id, "1"))
				urls.append((title, coverUrl2, id, "2"))
				urls.append((title, coverUrl3, id, "3"))

		if len(urls):
			ds = defer.DeferredSemaphore(tokens=2)
			downloads = [ds.run(self.download2, url, title, count).addCallback(self.buildList2,title,url,id,"tv",count).addErrback(self.dataError) for title,url,id,count in urls]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)
			self['searchinfo'].setText(_("Found for: %s") % self.text)
		else:
			self['searchinfo'].setText(_("%s not found.") % self.text)

	def dataError(self, error):
		print "[CoverFind] " + "ERROR:", error

	def download(self, url, title):
		return downloadPage(url, '/tmp/'+title+'.jpg')

	def download2(self, url, title, count):
		return downloadPage(url, '/tmp/'+title+count+'.jpg')
		
	def buildList(self, data, title, url, id, type):
		self.piclist.append(((title, '/tmp/'+title+'.jpg', id, type),))
		self['list'].setList(self.piclist, 'Test')

	def buildList2(self, data, title, url, id, type, count):
		self.piclist.append(((title, '/tmp/'+title+count+'.jpg', id, type),))
		self['list'].setList(self.piclist, 'Test')

	
	def ok(self):
		check = self['list'].getCurrent()
		if check == None:
			return

		bild = self['list'].getCurrent()[1]
		idx = self['list'].getCurrent()[2]
		type = self['list'].getCurrent()[3]
		self.savePath = cleanEnd(self.savePath)

		if fileExists(bild):
			if self.isDirectory == True:
				try:
					shutil.move(bild, self.savePath + "folder.jpg")
				except:
					print "[CoverFind] User rights are not sufficiently!"
			else:
				try:
					shutil.move(bild, self.savePath + ".jpg")
				except:
					print "[CoverFind] User rights are not sufficiently!"

		iurl = "http://api.themoviedb.org/3/movie/%s?api_key=8789cfd3fbab7dccf1269c3d7d867aff&language=de" % idx
		print "[CoverFind] " + iurl
		getPage(iurl, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getInfos, type).addErrback(self.dataError)
		self.close(False)

	def getInfos(self, data, type):
		if type == "movie":
			infos = re.findall('"genres":\[(.*?)\].*?"overview":"(.*?)",', data, re.S)
			if infos:
				(genres, desc) = infos[0]
				genre = re.findall('"name":"(.*?)"', genres, re.S)
				genre = str(genre).replace('\'','').replace('[','').replace(']','')
				self.cur.execute('UPDATE files SET description=?, genre=? WHERE id=?', (decodeHtml(desc), decodeHtml(genre), self.id))

		elif type == "tv":
			infos = re.findall('<Overview>(.*?)</Overview>', data, re.S)
			if infos:
				desc = infos[0]
				print "beschreibung:", desc
				self.cur.execute('UPDATE files SET description=? WHERE id=?', (decodeHtml(desc), self.id))

	def dataError(self, error):
		print error

	def cancel(self):
		self.close(False)
		
	def baseName(self, str):
		name = str.split('/')[-1]
		return name

class createCoverList(GUIComponent, object):
	GUI_WIDGET = eListbox
	
	def __init__(self):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont('Regular', 22))
		self.l.setItemHeight(138)
		self.l.setBuildFunc(self.buildList)

	def buildList(self, entry):
		width = self.l.getItemSize().width()
		(title, bild, id, type) = entry
		res = [ None ]

		self.picloader = PicLoader(92, 138)
		bild = self.picloader.load(bild)
		#color, color_sel, backcolor, backcolor_sel
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 0, 138, 138, bild))
		self.picloader.destroy()
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 150, 0, 1280, 30, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(title)))
		return res

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)

	def setList(self, list, type):
		self.type = type
		self.l.setList(list)

	def moveToIndex(self, idx):
		self.instance.moveSelectionTo(idx)

	def getSelectionIndex(self):
		return self.l.getCurrentSelectionIndex()

	def getSelectedIndex(self):
		return self.l.getCurrentSelectionIndex()

	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)

	def up(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)

	def down(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)

class CoverFindFile(Screen):
	skin = """
		<screen name="CoverFindFile" position="40,80" size="1200,600" title=" ">
			<widget name="media" position="10,10" size="1180,30" font="Regular;24" foregroundColor="unfff000" />
			<widget name="filelist" position="10,60" size="800,480" scrollbarMode="showOnDemand" />
			<widget name="picture" position="850,90" size="300,420" alphatest="blend" />
			<widget name="key_red" position="53,568" size="260,25" transparent="1" font="Regular;20" />
			<widget name="key_green" position="370,568" size="260,25" transparent="1" font="Regular;20" />
			<widget name="key_yellow" position="681,568" size="260,25" transparent="1" font="Regular;20" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="17,566" size="30,30" alphatest="blend" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="335,566" size="30,30" alphatest="blend" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="647,566" size="30,30" alphatest="blend" />
			</screen>"""

	def __init__(self, session, initDir, plugin_path = None):
		Screen.__init__(self, session)
		#self.skin_path = plugin_path
		self["filelist"] = FileList(initDir, inhibitMounts = False, inhibitDirs = False, showMountpoints = False, matchingPattern = "(?i)^.*\.(jpg|png)")
		self["media"] = Label()
		self["picture"] = Pixmap()
		
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"yellow": self.yellow,
			"green": self.green,
			"red": self.cancel
		}, -1)

		self.title=_("Select a cover file")
		try:
			self["title"]=StaticText(self.title)
		except:
			print 'self["title"] was not found in skin'	
			
		self['key_red'] = Label(_("Cancel"))
		self['key_green'] = Label(_("Select Cover"))
		self['key_yellow'] = Label(_("Delete cover"))

	def cancel(self):
		self.close(None)

	def green(self):
		if self["filelist"].getSelection()[1] == True:
			self["media"].setText(_("Invalid Choice"))
		else:
			directory = self["filelist"].getCurrentDirectory()
			if (directory.endswith("/")):
				self.fullpath = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			else:
				self.fullpath = self["filelist"].getCurrentDirectory() + "/" + self["filelist"].getFilename()
			self.close(self.fullpath)

	def yellow(self):
		if self["filelist"].getSelection()[1] == True:
			self["media"].setText(_("Invalid Choice"))
		else:
			print "[CoverFind] remove " + self.fullpath
			remove(self.fullpath)
			self["filelist"].refresh()
			self.updateFile()
			
	def up(self):
		self["filelist"].up()
		self.updateFile()

	def down(self):
		self["filelist"].down()
		self.updateFile()

	def left(self):
		self["filelist"].pageUp()
		self.updateFile()

	def right(self):
		self["filelist"].pageDown()
		self.updateFile()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateFile()

	def updateFile(self):
		currFolder = self["filelist"].getSelection()[0]
		if self["filelist"].getFilename() is not None:
			directory = self["filelist"].getCurrentDirectory()
			if (directory.endswith("/")):
				self.fullpath = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			else:
				self.fullpath = self["filelist"].getCurrentDirectory() + "/" + self["filelist"].getFilename()
			
			self["media"].setText(self["filelist"].getFilename())

		else:
			currFolder = self["filelist"].getSelection()[0]
			if currFolder is not None:
				self["media"].setText(currFolder)
			else:
				self["media"].setText(_("Invalid Choice"))

		print "[CoverFind] " + self.fullpath		
		self.showPreview(self.fullpath)

	def showPreview(self, pic):
		if pic:
			jpgpath = pic
			if jpgpath and os.path.exists(jpgpath):
				sc = AVSwitch().getFramebufferScale()
				size = self["picture"].instance.size()
				self.picload = ePicLoad()
				self.picload.PictureData.get().append(self.showPreviewCB)
				if self.picload:
					self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, "#00000000"))
					if self.picload.startDecode(jpgpath) != 0:
						del self.picload
			else:
				self["picture"].hide()
		else:
			self["picture"].hide()

	def showPreviewCB(self, picInfo=None):
		if self.picload and picInfo:
			ptr = self.picload.getData()
			if ptr != None:
				self["picture"].instance.setPixmap(ptr)
				self["picture"].show()
			del self.picload

# FileList mod
EXTENSIONS = {"jpg": "picture",	"png": "picture"}
		
def FileEntryComponent(name, absolute = None, isDir = False):
	res = [ (absolute, isDir) ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 1280, 30, 0, RT_HALIGN_LEFT, name))
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
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 5, 20, 20, png))
	
	return res

class FileList(MenuList):
	def __init__(self, directory, showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = None, useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None):
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
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []

		self.refreshMountpoints()
		self.changeDir(directory)
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setItemHeight(30)
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
					self.list.append(FileEntryComponent(name = p.description, absolute = path, isDir = True))
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
				self.list.append(FileEntryComponent(name = "<" +_("List of Storage Devices") + ">", absolute = None, isDir = True))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(directory.split('/')[:-2]) + '/', isDir = True))

		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					self.list.append(FileEntryComponent(name = name, absolute = x, isDir = True))

		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x

				if (self.matchingPattern is None) or re_compile(self.matchingPattern).search(path):
					self.list.append(FileEntryComponent(name = name, absolute = x , isDir = False))

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

	def refresh(self):
		idx = self.l.getCurrentSelectionIndex()
		self.changeDir(self.current_directory, self.getFilename())
		self.moveToIndex(idx-1)

	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()
