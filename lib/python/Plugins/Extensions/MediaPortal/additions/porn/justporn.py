﻿# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class justPornGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("JustPorn")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://justporn.to/"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('Genre</a>(.*?)>Herkunft</a>', data, re.S)
		raw = re.findall('class="nochildren">.*?href="(.*?)"\stitle=.*?>(.*?)</a></li>', parse.group(1), re.S)
		if raw:
			for (Url, Title) in raw:
				Url = Url + "page/"
				self.filmliste.append((decodeHtml(Title), Url))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Neue Scenes", "http://justporn.to/category/scenes/page/", None))
			self.filmliste.insert(0, ("Neue DVDRips", "http://justporn.to/category/dvdrips-full-movies/page/", None))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '-')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(justPornListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(justPornListScreen, Link, Name)

class justPornListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("JustPorn")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://justporn.to/page/" + str(self.page) + "/?s=" + self.Link
		else:
			url = self.Link + str(self.page)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '', "class='pages'>.*?von\s(.*?)<")
		raw = re.findall('<h2><a\shref="(.*?)".*?title="(.*?)">.*?src="(.*?)".*?duration">(.*?)</span>', data, re.S)
		if raw:
			for (link, title, image, duration) in raw:
				self.filmliste.append((decodeHtml(title), link, image, duration))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % (runtime))
		self['name'].setText(title)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][0]
		Title = self['liste'].getCurrent()[0][1]
		Cover = self['liste'].getCurrent()[0][2]
		self.session.open(StreamAuswahl, Link, Title, Cover)

class StreamAuswahl(MPScreen):

	def __init__(self, session, Title, Link, Cover):
		self.Link = Link
		self.Title = Title
		self.Cover = Cover
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("JustPorn")
		self['ContentTitle'] = Label("%s" %self.Title)

		self.filmliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.Cover)
		self.keyLocked = True
		url = self.Link
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		streams = re.findall('(http://(streamcloud.eu).*?)"', data, re.S|re.I)
		if streams:
			for (stream, hostername) in streams:
				self.filmliste.append((hostername, stream))
		streams2 = re.findall('<iframe width=".*?" height=".*?" src="(http://.*?(flashx.tv)/.*?)"', data, re.S|re.I)
		if streams2:
			for (stream2, hostername2) in streams2:
				self.filmliste.append((hostername2, stream2))
		streams3 = re.findall('<iframe\ssrc="(http://.*?(streamin.to)/.*?)"', data, re.S|re.I)
		if streams3:
			for (stream3, hostername3) in streams3:
				self.filmliste.append((hostername3, stream3))
		if not streams and not streams2 and not streams3:
			self.filmliste.append(("No streams found!", None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			return
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			title = self.Title
			self.session.open(SimplePlayer, [(self.Title, stream_url, self.Cover)], showPlaylist=False, ltype='justporn', cover=True)