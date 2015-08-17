﻿# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

VGDE_Version = "VideoGold.de v0.94"

VGDE_siteEncoding = 'utf-8'

"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel		: Menu Up / Exit
	KeyOK			: Menu Down / Select

Doku Auswahl:
	Bouquet +/-				: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'			: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau				: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau				: Die Beschreibung Seitenweise scrollen
"""

class show_VGDE_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "http://www.videogold.de"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter)

		self['title'] = Label(VGDE_Version)
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseCategorys(self, data):
		print 'mh_parseCategorys:'
		themes = ['Video-Formate','Video-Themen']
		menu_marker = '"art-hmenu'
		excludes = ['/livestreams','/videos-eintragen','/wp-login']
		menu=self.scanMenu(data,menu_marker,themes=themes,base_url=self.mh_baseUrl,url_ex=excludes)
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		genreurl = self.mh_genreUrl[self.mh_menuLevel]
		if not genreurl.startswith('http'):
			genreurl = self.mh_baseUrl+genreurl
		print 'GenreURL:',genreurl
		self.session.open(VGDE_FilmListeScreen, genreurl, self.mh_genreTitle)

class VGDE_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions","DirectionActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"0"	: self.closeAll,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(VGDE_Version)

		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.page = 0
		self.pages = 0;

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		#print genreName
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		print "loadPage:"
		url = "%s/page/%d/" % (self.genreLink, max(self.page,1))

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()
		print "eventL ",self.eventL.is_set()

	def loadPageQueued(self):
		print "loadPageQueued:"
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		print url
		twAgentGetPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		print "dataError:"
		printl(error,self,"E")
		self.dokusListe.append((_("No dokus / streams found!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, data):
		print "loadPageData:",len(data)
		data = data.replace('\n','')
		self.dokusListe = []
		l = len(data)
		a = 0
		while a < l:
			i = data.find('"art-postheader">',a)
			if i < 0:
				break

			j = data.find('<img class="alignleft" src="',a,i)
			if j >= 0:
				a = j
				m = re.search('<img class="alignleft" src="(.*?)".*?href="(.*?)".*?title="(.*?)">.*?"art-postcontent">(.*?) <a', data[a:], re.S)
				if m:
					a += m.end()
					img = m.group(1)
					url = m.group(2)
					nm = m.group(3)
					desc = m.group(4)
					desc = desc.replace('<!-- article-content -->','').strip()
					self.dokusListe.append((decodeHtml(nm), url, img, decodeHtml(desc)))
				else:
					break
			else:
				a = i
				m = re.search('"art-postheader"></br><a href="(.*?)".*?title="(.*?)">.*?"art-postcontent">(.*?) <a', data[a:], re.S)
				if m:
					a += m.end()
					url = m.group(1)
					nm = m.group(2)
					desc = m.group(3)
					desc = desc.replace('<!-- article-content -->','').strip()
					self.dokusListe.append((decodeHtml(nm), url, None, decodeHtml(desc)))
				else:
					break

		if self.dokusListe:
			print "Dokus found !"
			if not self.pages:
				m = re.search('class="page_info">Seite 1 von (\d+)<', data)
				try:
					pages = int(m.group(1))
				except:
					pages = 1

				if pages > self.pages:
					self.pages = pages

			if not self.page:
				self.page = 1
			print "Page: %d / %d" % (self.page,self.pages)
			self['page'].setText("%d / %d" % (self.page,self.pages))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.pages)
			self.loadPicQueued()
		else:
			print "No dokus found!"
			print data
			self.dokusListe.append((_("No dokus found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):
		print "loadPic:"

		if self.picQ.empty():
			self.eventP.clear()
			print "picQ is empty"
			return

		if self.updateP:
			print "Pict. or descr. update in progress"
			print "eventP: ",self.eventP.is_set()
			print "updateP: ",self.updateP
			return

		while not self.picQ.empty():
			self.picQ.get_nowait()

		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		#print "streamName: ",streamName
		#print "streamPic: ",streamPic
		#print "streamUrl: ",streamUrl
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def getHandlung(self, desc):
		print "getHandlung:"
		if desc == None:
			print "No Infos found !"
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		print "setHandlung:"
		self['handlung'].setText(data)

	def ShowCoverFileExit(self):
		print "showCoverExitFile:"
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		print "loadPicQueued:"
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		desc = self['liste'].getCurrent()[0][3]
		self.getHandlung(desc)
		self.loadPic()
		print "eventP: ",self.eventP.is_set()

	def parseYTStream(self, data):
		print "parseYTStream:"
		m2 = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m2:
			dhVideoId = m2.group(2)
		else:
			m2 = re.search('youtu.*?/(.*?)</p>', data)
			if m2:
				dhVideoId = m2.group(1)
			else:
				m2 = None
		if m2:
			print "Streams found"
			dhTitle = self['liste'].getCurrent()[0][0]
			if 'p' == m2.group(1):
				url = 'http://gdata.youtube.com/feeds/api/playlists/PL'+dhVideoId+'?'
				self.session.open(YT_ListScreen, url, dhTitle, title=VGDE_Version)
			else:
				self.session.open(
					YoutubePlayer,
					[(dhTitle, dhVideoId, None)],
					showPlaylist=False
					)
		else:
			self.parseSRFStream(data)

	def parseSRFStream(self, data):
		print "parseSRFStream:"
		m2 = re.search('//www.srf.ch/player/.*?id=(.*?)&', data)
		if m2:
			print "Streams found"
			id = m2.group(1)
			self.getSRFStream(id)
		else:
			print "No stream found"
			self.session.open(MessageBoxExt,"Kein abspielbarer Stream gefunden!", MessageBoxExt.TYPE_INFO, timeout=10)

	def getSRFStream(self, id):
		self.srf_url = "http://www.srf.ch/webservice/cvis/segment/%s/.json?nohttperr=1;omit_video_segments_validity=1;omit_related_segments=1;nearline_data=1" % id
		twAgentGetPage(self.srf_url).addCallback(self.get_srf_xml).addErrback(self.dataError)

	def get_srf_xml(self, data):
		master = re.findall('"streaming":"hls","quality":".*?","url":"(.*?)"}', data, re.S)
		if master:
			url = master[-1].replace("\/","/")
			twAgentGetPage(url).addCallback(self.get_srf_master).addErrback(self.dataError)
		else:
			twAgentGetPage(self.srf_url).addCallback(self.get_srf_rtmp).addErrback(self.dataError)

	def get_srf_master(self, data):
		xml = re.findall('CODECS="avc.*?"\n(.*?)\n', data, re.S)
		if xml:
			if re.search('http://.*?', xml[-1], re.S):
				url = xml[-1]
				title = self['liste'].getCurrent()[0][0]
				playlist = []
				playlist.append((title, url))
				self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='srf')
			else:
				url = self['liste'].getCurrent()[0][1]
				twAgentGetPage(url).addCallback(self.get_rtmp).addErrback(self.dataError)

	def get_srf_rtmp(self, data):
		xml = re.findall('"url":"(rtmp:.*?)"', data, re.S)
		if xml:
			url = xml[-1].replace("\/","/")
			host = url.split('mp4:')[0]
			playpath = url.split('mp4:')[1]
			title = self['liste'].getCurrent()[0][0]
			final = "%s swfUrl=http://www.srf.ch/player/flash/srfplayer.swf playpath=mp4:%s swfVfy=1" % (host, playpath)
			playlist = []
			playlist.append((title, final))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='srf')
		else:
			message = self.session.open(MessageBoxExt, _("For legal reasons this video may be viewed only within Switzerland."), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink).addCallback(self.parseYTStream).addErrback(self.dataError)

	def keyUpRepeated(self):
		#print "keyUpRepeated"
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		#print "keyDownRepeated"
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		#print "key_repeatedUp"
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		#print "keyPageDown()"
		self.keyPageDownFast(1)

	def keyPageUp(self):
		#print "keyPageUp()"
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		#print "keyPageUpFast: ",step
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page = 1
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		print "keyPageDownFast: ",step
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		#print "keyPageDownFast(2)"
		self.keyPageDownFast(2)

	def key_4(self):
		#print "keyPageDownFast(5)"
		self.keyPageDownFast(5)

	def key_7(self):
		#print "keyPageDownFast(10)"
		self.keyPageDownFast(10)

	def key_3(self):
		#print "keyPageUpFast(2)"
		self.keyPageUpFast(2)

	def key_6(self):
		#print "keyPageUpFast(5)"
		self.keyPageUpFast(5)

	def key_9(self):
		#print "keyPageUpFast(10)"
		self.keyPageUpFast(10)