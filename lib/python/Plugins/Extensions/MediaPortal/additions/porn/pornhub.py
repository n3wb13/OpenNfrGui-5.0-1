# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

class pornhubGenreScreen(MPScreen):

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

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.pornhub.com/categories"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('<div\sclass="category-wrapper">.*?<a\shref="(/video\?c=.*?)"><img\ssrc="(.*?)".*?alt="(.*?)"', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "http://www.pornhub.com" + Url + "&page="
				self.filmliste.append((Title, Url, Image))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Playlists - Most Favorited", "http://www.pornhub.com/playlists?o=mf&page=", None))
			self.filmliste.insert(0, ("Playlists - Top Rated", "http://www.pornhub.com/playlists?page=", None))
			self.filmliste.insert(0, ("Playlists - Most Viewed", "http://www.pornhub.com/playlists?o=mv&page=", None))
			self.filmliste.insert(0, ("Playlists - Most Recent", "http://www.pornhub.com/playlists?o=mr&page=", None))
			self.filmliste.insert(0, ("Pornstars", "http://www.pornhub.com/pornstars?page=", None))
			self.filmliste.insert(0, ("HD", "http://www.pornhub.com/video?c=38&page=", 'http://cdn1a.static.pornhub.phncdn.com/images/categories/38.jpg'))
			self.filmliste.insert(0, ("Longest", "http://www.pornhub.com/video?o=lg&page=", None))
			self.filmliste.insert(0, ("Top Rated", "http://www.pornhub.com/video?o=tr&page=", None))
			self.filmliste.insert(0, ("Most Viewed", "http://www.pornhub.com/video?o=mv&page=", None))
			self.filmliste.insert(0, ("Most Recent", "http://www.pornhub.com/video?o=mr&page=", None))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Pornstars":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubPornstarScreen, Link, Name)
		elif re.match("Playlists", Name):
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubPlayListScreen, Link, Name)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback.replace(' ', '%2B')
			Link = 'http://www.pornhub.com/video/search?search=%s&page=' % (self.suchString)
			self.session.open(pornhubFilmScreen, Link, Name)

class pornhubPlayListScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Pornhub.com")
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
		self.filmliste = []
		self.keyLocked = True
		url = self.Link + str(self.page)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		Cats = re.findall('class="playlist-videos.*?<span>(.*?)</span>.*?src="(.*?)".*?class="title".*?href="(.*?)">(.*?)</a>', data, re.S)
		if Cats:
			for Videos, Image, Url, Title in Cats:
				Url = "http://www.pornhub.com" + Url
				self.filmliste.append((decodeHtml(Title), Videos, Image, Url))
			self.ml.setList(map(self.pornhubPlayListEntry, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self['page'].setText(str(self.page))
			self.th_ThumbsQuery(self.filmliste, 0, 3, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		CatLink = self['liste'].getCurrent()[0][3]
		NameLink = self['liste'].getCurrent()[0][0]
		self.session.open(pornhubFilmScreen, CatLink, NameLink)

class pornhubPornstarScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Pornhub.com")
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
		self.filmliste = []
		self.keyLocked = True
		url = self.Link + str(self.page)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('class="textFilter">Most Popular</span>(.*)', data, re.S)
		Cats = re.findall('rank_number">(.*?)<.*?src="(.*?)".*?href="(.*?)".*?class="title".*?>(.*?)<.*?videosNumber">(.*?)\sVideos</span>', parse.group(1), re.S)
		if Cats:
			for Rank, Image, Url, Title, Videos in Cats:
				Url = 'http://www.pornhub.com' + Url + "?page="
				self.filmliste.append((decodeHtml(Title), Url, Image, Rank.strip(), Videos))
			self.ml.setList(map(self.pornhubPornstarListEntry, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self['page'].setText(str(self.page))
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(pornhubFilmScreen, Link, Name)

class pornhubFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Pornhub.com")
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
		if re.match(".*\/playlist\/",self.Link):
			url = "%s" % (self.Link)
		else:
			url = "%s%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('nf-videos(.*?)pre-footer', data, re.S)
		if not parse:
			parse = re.search('class="videos\srow-5-thumbs(.*?)pre-footer', data, re.S)
		Movies = re.findall('class="videoblock".*?<a\shref="(.*?)".*?title="(.*?)".*?class="duration">(.*?)</var>.*?data-mediumthumb="(.*?)".*?<span\sclass="views"><var>(.*?)<.*?<var\sclass="added">(.*?)</var>', parse.group(1), re.S)
		if Movies:
			for (Url, Title, Runtime, Image, Views, Added) in Movies:
				Url = 'http://www.pornhub.com' + Url
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views, Added))
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
		twAgentGetPage(Link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		Title = self['liste'].getCurrent()[0][0]
		match = re.findall("quality_720p = '(.*?)';", data, re.S)
		if not match:
			match = re.findall("quality_480p = '(.*?)';", data, re.S)
		if not match:
			match = re.findall("quality_240p = '(.*?)';", data, re.S)
		fetchurl = urllib2.unquote(match[0])
		if fetchurl:
			self.session.open(SimplePlayer, [(Title, fetchurl)], showPlaylist=False, ltype='pornhub')