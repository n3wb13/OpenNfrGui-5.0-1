# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2015
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

BASE_URL = 'http://kinoleak.tv'

class kinoLeak(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinoLeak")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.suchString = ''
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("Neue Filme", "/index.php?site=Index&page="))
		self.streamList.append(("Meistgesehen", "/index.php?site=Meistgesehen&page="))
		self.streamList.append(("Filme 1080p", "/index.php?site=Genre&do=1080p&page="))
		self.streamList.append(("Filme 720p", "/index.php?site=Genre&do=720p&page="))
		self.streamList.append(("Top IMDB Bewertung", "/index.php?site=IMDb&page="))
		self.streamList.append(("Alle Filme", "/index.php?site=MovieList&Jahr=&page="))
		self.streamList.append(("Suche", None))
		self.streamList.append(("Abenteuer", "/index.php?site=Genre&S=Abenteuer&page="))
		self.streamList.append(("Action", "/index.php?site=Genre&S=Action&page="))
		self.streamList.append(("Animation", "/index.php?site=Genre&S=Animation&page="))
		self.streamList.append(("Doku", "/index.php?site=Genre&S=Doku&page="))
		self.streamList.append(("Drama", "/index.php?site=Genre&S=Drama&page="))
		self.streamList.append(("Fantasy", "/index.php?site=Genre&S=Fantasy&page="))
		self.streamList.append(("Horror", "/index.php?site=Genre&S=Horror&page="))
		self.streamList.append(("Komödie", "/index.php?site=Genre&S=Komödie&page="))
		self.streamList.append(("Krieg", "/index.php?site=Genre&S=Krieg&page="))
		self.streamList.append(("Krimi", "/index.php?site=Genre&S=Krimi&page="))
		self.streamList.append(("Sci-Fi", "/index.php?site=Genre&S=Sci-Fi&page="))
		self.streamList.append(("Thriller", "/index.php?site=Genre&S=Thriller&page="))
		self.streamList.append(("Western", "/index.php?site=Genre&S=Western&page="))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		if auswahl == "Suche":
			self.suchen()
		else:
			url = BASE_URL + self['liste'].getCurrent()[0][1]
			self.session.open(kinoLeakParsing, auswahl, url)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			self.session.open(kinoLeakSearchResult, self.suchString)

class kinoLeakSearchResult(MPScreen, ThumbsHelper):

	def __init__(self, session, searchText):
		self.searchText = searchText
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinoLeak")
		self['ContentTitle'] = Label("Suche: %s" % self.searchText)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = BASE_URL + "/livesearch.php?q=%s" % str(self.searchText)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		movies = re.findall("<td width='51'>.*?<img src='(.*?)' width='40'/>.*?<td><a href='(index.php.*?)'.*?>(.*?)</a>", data, re.S)
		if movies:
			for (Image, Url, Title) in movies:
				Url = BASE_URL + "/" + Url
				self.streamList.append((decodeHtml(Title), Url, Image))

		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		if url != None:
			self.session.open(kinoLeakStreams, title, url, cover)

class kinoLeakParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("KinoLeak")
		self['ContentTitle'] = Label("%s" % self.genre)
		self['Page'] = Label(_("Page:"))

		self.page = 1
		self.lastpage = 999
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = self.url+str(self.page)
		self['page'].setText("%s" % str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.genre == "Neue Filme":
			movies = re.findall('<td width="48" valign="top"><a href="(index.php.*?)"><img src="(.*?)" title="(.*?)" width="43px" height="60px"/>.*?<img src="img/.*?" width=".*?" title="(.*?)"', data, re.S|re.I)
			if movies:
				for (Url, Image, Title, Format) in movies:
					Url = BASE_URL + "/" + Url
					self.streamList.append((decodeHtml(Title), Url, Image, str(Format)))
		else:
			getLastpage = re.findall('page=(\d+)" id="button.*?">', data, re.S|re.I)
			if getLastpage:
				self.lastpage = getLastpage[-1]
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			#movies = re.findall('<div class="ca-genre-main">.*?<a href="(index.php.*?)" id="MovieURL"><img src="(.*?)" id="Cover".*?title="(.*?)"></a>', data, re.S)
			movies = re.findall('<a href="(index.php\?site=Movies&id=.*?)" id="MovieURL"><img src="(.*?)" id="Cover".*?title="(.*?)".*?></a>', data, re.S)
			if movies:
				for (Url, Image, Title) in movies:
					Url = BASE_URL + "/" + Url
					self.streamList.append((decodeHtml(Title), Url, Image, None))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None, None))
		self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		format = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		if format != None:
			self['handlung'].setText(_("Videoresolution") + ": %s" % format)
		else:
			self['handlung'].setText("")
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		if url != None:
			self.session.open(kinoLeakStreams, title, url, cover)

class kinoLeakStreams(MPScreen):

	def __init__(self, session, stream_name, url, cover):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("KinoLeak")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.stream_name)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.streamList = []
		handlung = re.search('>Beschreibung:</u>(.*?)<hr/>', data)
		format = re.findall('<td align="center" valign="top">(.*?)</td>', data)
		if handlung:
			if format:
				format = _("Videoresolution") + ": %sp\n\n" % str(format[-1])
			self['handlung'].setText(format + decodeHtml(iso8859_Decode(handlung.group(1).strip())))
		else:
			if format:
				format = _("Videoresolution") + ": %sp" % str(format[-1])
			else:
				self['handlung'].setText(_("No information found."))
		streams_raw = re.findall('<div\sid="tab.*?"\sclass="swbox_content.*?"\sstyle="display:none;">.*?<center>.*?<IFRAME\sSRC="(http://(.*?)\/.*?)"', data, re.S|re.I)
		if streams_raw:
			for (url, hostername) in streams_raw:
				hostername = hostername.replace('www.','')
				if isSupportedHoster(hostername, True):
					self.streamList.append((hostername, url))
			self.ml.setList(map(self._defaultlisthoster, self.streamList))
			CoverHelper(self['coverArt']).getCover(self.cover)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(url, self.playfile)

	def playfile(self, stream_url):
		if stream_url != None:
			self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], showPlaylist=False, ltype='kinoleak', cover=True)