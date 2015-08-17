# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.decrypt import *

class tube8GenreScreen(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Tube8.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.url = "http://www.tube8.com/categories.html"
		getPage(self.url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('id="categories-wrapper"(.*?)</div>', data,re.S)
		Cats = re.findall('href="(.*?)">(.*?)</a>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = Url + "page/"
				self.filmliste.append((Title, Url))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Longest", "http://www.tube8.com/longest/page/"))
			self.filmliste.insert(0, ("Most Voted", "http://www.tube8.com/most-voted/page/"))
			self.filmliste.insert(0, ("Most Discussed", "http://www.tube8.com/most-discussed/page/"))
			self.filmliste.insert(0, ("Most Favorited", "http://www.tube8.com/most-favorited/page/"))
			self.filmliste.insert(0, ("Top Rated", "http://www.tube8.com/top/page/"))
			self.filmliste.insert(0, ("Most Viewed", "http://www.tube8.com/most-viewed/page/"))
			self.filmliste.insert(0, ("Featured", "http://www.tube8.com/latest/page/"))
			self.filmliste.insert(0, ("Newest", "http://www.tube8.com/newest/page/"))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen"))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		getPage(self.url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getCover).addErrback(self.dataError)

	def getCover(self, data):
		cat = self['liste'].getCurrent()[0][0]
		parse = re.search('class="sh1"><span>%s</span></h2>.*?src="(.*?.jpg)"' % cat, data, re.S)
		if parse:
			cover = parse.group(1)
		else:
			cover = None
		CoverHelper(self['coverArt']).getCover(cover)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(tube8FilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = 'http://www.tube8.com/searches.html?q=%s&page=' % (self.suchString)
			self.session.open(tube8FilmScreen, Link, Name)

class tube8FilmScreen(MPScreen, ThumbsHelper):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Tube8.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 999

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		self['page'].setText(str(self.page))
		url = "%s%s/" % (self.Link, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Movies = re.findall('id="video_.*?a\shref="(.*?)".*?"(http://cdn.[\w]?\.image\.tube8.*?\.jpg)".*?title="(.*?)".*?<strong>(.*?)</strong>.*?float-right">(.*?)\sviews.*?float-right">(.*?)\sago</div>', data, re.S)
		if Movies:
			for (Url, Image, Title, Runtime, Views, Added) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views.strip(), Added))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s\nAdded: %s" % (runtime, views, added))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		Title = self['liste'].getCurrent()[0][0]
		match = re.search('"video_url":"(http.*?)"', data)
		if match:
			fetchurl = urllib2.unquote(match.group(1))
			Stream = fetchurl.replace('\/','/')
			self.session.open(SimplePlayer, [(Title, Stream)], showPlaylist=False, ltype='tube8')
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found"), MessageBoxExt.TYPE_INFO, timeout=5)