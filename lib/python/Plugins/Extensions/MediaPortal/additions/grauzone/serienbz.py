# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class SerienFirstScreen(MPScreen):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serien.bz")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Serien A-Z","dump"))
		self.genreliste.append(("Watchlist","dump"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		Auswahl = self['liste'].getCurrent()[0][0]
		if Auswahl == "Serien A-Z":
			self.session.open(SerienLetterScreen)
		else:
			self.session.open(sbzWatchlistScreen)

class SerienLetterScreen(MPScreen):

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
			"0" : self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serien.bz")
		self['ContentTitle'] = Label("Genre Asuwahl")
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://serien.bz"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('<a class="LetterMode " href="(.*?)">(.*?)<', data, re.S)
		if raw:
			self.filmliste = []
			for (serienUrl, serienTitle) in raw:
				self.filmliste.append((decodeHtml(serienTitle), serienUrl))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)

	def keyOK(self):
		if self.keyLocked:
			return
		serienName = self['liste'].getCurrent()[0][0]
		serienLink = self['liste'].getCurrent()[0][1]
		self.session.open(SerienSecondScreen, serienLink, serienName)

class SerienSecondScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, serienLink, serienName):
		self.serienLink = serienLink
		self.serienName = serienName
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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.addWatchlist
		}, -1)

		self['title'] = Label("Serien.bz")
		self['ContentTitle'] = Label("Letter: %s" % self.serienName)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Add to Watchlist"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 0
		self.ImageUrl = ""
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		if self.serienName == "Top50":
			url = "http://serien.bz"
		else:
			url = self.serienLink
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('<li><a href="(.*?)".*?>(.*?)</a>', data, re.S)
		if raw:
			for (serienUrl, serienTitle) in raw:
				self.filmliste.append((decodeHtml(serienTitle), serienUrl))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 1, None, '<p\sstyle="text-align:\scenter;"><a\shref="(.*?)"><img class', 1, 1)
			self.showInfos()

	def showInfos(self):
		serienUrl = self['liste'].getCurrent()[0][1]
		getPage(serienUrl, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		sbzCover = re.findall('<div class="entry">.*?<p.*?src="(.*?)".*?</p>.*?<p.*?</p>.*?<p.*?</p>', data, re.S)
		if sbzCover:
			self.ImageUrl = "http://serien.bz%s" % sbzCover[0]
			CoverHelper(self['coverArt']).getCover(self.ImageUrl)
		else:
			self.ImageUrl = ""
		serienTitle = self['liste'].getCurrent()[0][0]
		if re.match('.*?Sorry, but there.*?category yet.</h2>', data, re.S):
			self['handlung'].setText("Kein Stream vorhanden!")
			self['name'].setText("Kein Stream vorhanden!")
		else:
			self['name'].setText(decodeHtml(serienTitle))
			sbzdescription = re.findall('<div class="entry">.*?<p.*?</p>.*?<p.*?</p>.*?<p style="text-align: left;">(.*?)</p>', data, re.S)
			self.handlung = sbzdescription
			if sbzdescription:
				self['handlung'].setText(decodeHtml(sbzdescription[0]))
			else:
				self['handlung'].setText(_("No information found."))

	def addWatchlist(self):
		if self.keyLocked:
			return

		self.serienName = self['liste'].getCurrent()[0][0]
		self.serienLink = self['liste'].getCurrent()[0][1]

		print self.serienName, self.serienLink, self.ImageUrl, self.handlung

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist"):
			print "erstelle watchlist"
			open(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist","w").close()

		if fileExists(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist"):
			print "schreibe watchlist", self.serienName, self.serienLink, self.ImageUrl, self.handlung
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist","a")
			writePlaylist.write('"%s" "%s" "%s" "%s"\n' % (self.serienName, self.serienLink, self.ImageUrl, self.handlung))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("%s was added to the watchlist." % self.serienName), MessageBoxExt.TYPE_INFO, timeout=3)

	def keyOK(self):
		if self.keyLocked:
			return
		serienName = self['liste'].getCurrent()[0][0]
		serienLink = self['liste'].getCurrent()[0][1]
		print serienName, serienLink
		self.session.open(SerienEpListingScreen, serienLink, serienName, self.ImageUrl)

class SerienEpListingScreen(MPScreen):

	def __init__(self, session, serienLink, serienName, serienPic):
		self.serienLink = serienLink
		self.serienName = serienName
		self.serienPic = serienPic
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Serien.bz")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.serienName)

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = self.serienLink
		CoverHelper(self['coverArt']).getCover(self.serienPic)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		streams_raw = re.findall('>Staffel:.(.*?)</th>(.*?)</table>', data, re.S)
		if streams_raw:
			for staffel,ep_raw in streams_raw:
				ep_raw2 = re.findall('<strong>Episode.(.*?)</strong>(.*?</p>)', ep_raw,)
				if ep_raw2:
					for episode,ep_rawData in ep_raw2:
						streams = re.findall('<strong>Stream:</strong> <a href="(.*?)".*?\| (.*?)<', ep_rawData, re.S)
						if streams:
							if int(staffel) < 10:
								s = "S0%s" % str(staffel)
							else:
								s = "S%s" % str(staffel)

							if int(episode) < 10:
								e = "E0%s" % str(episode)
							else:
								e = "E%s" % str(episode)

							title = "%s%s" % (s, e)

							self.filmliste.append((title, streams))
					self.ml.setList(map(self._defaultlistleft, self.filmliste))
					self.keyLocked = False

	def keyOK(self):
		serienName = self['liste'].getCurrent()[0][0]
		serienLink = self['liste'].getCurrent()[0][1]
		print serienName, serienLink
		self.session.open(SerienStreamListingScreen, serienLink, serienName, self.serienPic)

class SerienStreamListingScreen(MPScreen):

	def __init__(self, session, serienLink, serienName, serienPic):
		self.serienLink = serienLink
		self.serienName = serienName
		self.serienPic = serienPic
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Serien.bz")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.serienName)

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		CoverHelper(self['coverArt']).getCover(self.serienPic)
		for hoster,hostrname in self.serienLink:
			if isSupportedHoster(hostrname, True):
				self.filmliste.append((hostrname, hoster))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		hostername = self['liste'].getCurrent()[0][0]
		hoster = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(hoster, self.playfile)

	def playfile(self, stream_url):
		if stream_url != None:
			self.session.open(SimplePlayer, [(self.serienName, stream_url, self.serienPic)], showPlaylist=False, ltype='serien.bz', cover=True)

class sbzWatchlistScreen(MPScreen):

	def __init__(self, session):
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red"	: self.delWatchListEntry
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Serien.bz")
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.watchListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.watchListe = []
		if fileExists(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist"):
			print "read watchlist"
			readStations = open(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(title, link, image, handlung) = data[0]
					print title, link, image
					self.watchListe.append((title, link, image, handlung))
			print "Load Watchlist.."
			self.watchListe.sort()
			self.ml.setList(map(self._defaultlistleft, self.watchListe))
			readStations.close()
			self.showInfos()
			self.keyLocked = False

	def showInfos(self):
		if fileExists(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist"):
			print "read watchlist"
			readStations = open(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					self.ImageUrl = self['liste'].getCurrent()[0][2]
					self.Handlung = self['liste'].getCurrent()[0][3]
					self['handlung'].setText(decodeHtml(self.Handlung))
					CoverHelper(self['coverArt']).getCover(self.ImageUrl)
		else:
			self['handlung'].setText(_("No information found."))
			picPath = "%s/skins/%s/images/no_coverArt.png" % (self.plugin_path, config.mediaportal.skin.value)
			CoverHelper(self['coverArt']).getCover(picPath)

	def delWatchListEntry(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		entryDeleted = False
		selectedName = self['liste'].getCurrent()[0][0]

		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist"):
			readWatchlist = open(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist","r")
			for rawData in readWatchlist.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(title, link, image, handlung) = data[0]
					if title != selectedName:
						writeTmp.write('"%s" "%s" "%s" "%s"\n' % (title, link, image, handlung))
					else:
						if entryDeleted:
							writeTmp.write('"%s" "%s" "%s" "%s"\n' % (title, link, image, handlung))
						else:
							entryDeleted = True
			readWatchlist.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_sbz_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_sbz_watchlist")
			self.loadPage()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		serienName = self['liste'].getCurrent()[0][0]
		serienLink = self['liste'].getCurrent()[0][1]
		serienPic = self['liste'].getCurrent()[0][2]
		self.session.open(SerienEpListingScreen, serienLink, serienName, serienPic)