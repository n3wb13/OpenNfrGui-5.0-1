﻿# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class fourtubeGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "4tube":
			self.portal = "4Tube.com"
			self.baseurl = "www.4tube.com"
			self.s = "s"
		if self.mode == "fux":
			self.portal = "fux.com"
			self.baseurl = "www.fux.com"
			self.s = ""
		if self.mode == "porntube":
			self.portal = "PornTube.com"
			self.baseurl = "www.porntube.com"
			self.s = "s"

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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://%s/tag%s" % (self.baseurl, self.s)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('>Categories<(.*?)>Channels<', data, re.S)
		Cats = re.findall('<li><a\shref="(\/tag.*?)"\stitle="(.*?)"', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://" + self.baseurl + Url
				Title = Title.title()
				self.genreliste.append((Title, Url))
		parse = re.search('All\scategories(.*?)</div', data, re.S)
		Cats = re.findall('<li><a\shref=".*?(\/tag.*?)"\stitle="(.*?)\ssex\smovies', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://" + self.baseurl + Url
				Title = Title.title()
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Websites", "http://%s/channel%s" % (self.baseurl, self.s)))
			self.genreliste.insert(0, ("Pornstars", "http://%s/pornstar%s" % (self.baseurl, self.s)))
			self.genreliste.insert(0, ("Highest Rating", "http://%s/video%s?sort=rating&time=month" % (self.baseurl, self.s)))
			self.genreliste.insert(0, ("Most Viewed", "http://%s/video%s?sort=views&time=month" % (self.baseurl, self.s)))
			self.genreliste.insert(0, ("Latest", "http://%s/video%s?sort=date" % (self.baseurl, self.s)))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Websites" or Name == "Pornstars":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(fourtubeSitesScreen, Link, Name, self.portal, self.baseurl)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(fourtubeFilmScreen, Link, Name, self.portal, self.baseurl)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = self.suchString
			self.session.open(fourtubeFilmScreen, Link, Name, self.portal, self.baseurl)

class fourtubeSitesScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.portal = portal
		self.baseurl = baseurl
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
			"green" : self.keyPageNumber,
			"yellow" : self.keySort
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.sort = 'likes'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s?sort=%s&p=%s" % (self.Link, self.sort, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'maxPage\s=\s(\d+);')
		Movies = re.findall('link"\shref="(.*?)"\stitle="(.*?)".*?original="(.*?)"', data, re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
			self.showInfos()
		self.keyLocked = False

	def keySort(self):
		if self.keyLocked:
			return
		if self.Name == 'Pornstars':
			chlist = ['likes', 'popularity', 'twitter', 'videos', 'name', 'date', 'subscribers']
		else:
			chlist = ['likes', 'videos', 'name', 'date', 'subscribers']
		for x in range(0, len(chlist)):
			if self.sort == chlist[x]:
				next = (x+1) % len(chlist)
				self.sort = chlist[next]
				break
		self.loadPage()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['handlung'].setText("%s: %s" % (_("Sort order"),self.sort.title()))
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(fourtubeFilmScreen, Link, Name, self.portal, self.baseurl)

class fourtubeFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.portal = portal
		self.baseurl = baseurl
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
			"green" : self.keyPageNumber,
			"yellow" : self.keySort,
			"blue" : self.keyFilter
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))
		self['F4'] = Label(_("Filter"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'date'
		self.filter = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://%s/search?q=%s&p=%s" % (self.baseurl, self.Link, str(self.page))
		else:
			sortpart = re.findall('^(.*?)\?sort=(.*?)(\&.*?|)$', self.Link)
			if sortpart:
				self.Link = sortpart[0][0]
				self.sort = sortpart[0][1]
				self.filter = sortpart[0][2]
			url = "%s?sort=%s%s&p=%s" % (self.Link, self.sort, self.filter, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.novideofound).addErrback(self.dataError)

	def novideofound(self, error):
		if error.value.status == '404':
			self.filmliste.append((_('No videos found!'), '', '', ''))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.showInfos()
			self.keyLocked = False
		raise error

	def loadData(self, data):
		self.getLastPage(data, '', 'maxPage\s=\s(\d+);')
		Movies = re.findall('button><a\shref="(.*?)".*?title="(.*?)".*?original="(.*?.jpeg)".*?(duration-top\">|icon-timer\"><\/i>)(.*?)<', data, re.S)
		if Movies:
			for (Url, Title, Image, dummy, Runtime) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()
		self.keyLocked = False

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("%s: %s\n%s: %s\nRuntime: %s" % (_("Sort order"),self.sort.title(),_("Filter"),self.filter[1:].title(),runtime))
		CoverHelper(self['coverArt']).getCover(pic)

	def keySort(self):
		if self.keyLocked:
			return
		chlist = ['date', 'duration', 'rating', 'views']
		for x in range(0, len(chlist)):
			if self.sort == chlist[x]:
				next = (x+1) % len(chlist)
				self.sort = chlist[next]
				break
		self.loadPage()

	def keyFilter(self):
		if self.keyLocked:
			return
		if self.filter == '':
			self.filter = '&none'
		chlist = ['quality=hd', 'duration=long', 'duration=medium','duration=short', 'time=month', 'time=week', 'none']
		for x in range(0, len(chlist)):
			if self.filter == "&%s" % chlist[x]:
				next = (x+1) % len(chlist)
				if chlist[next] != "none":
					self.filter = "&%s" % chlist[next]
				else:
					self.filter = ''
				break
		self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getVideoID).addErrback(self.dataError)

	def getVideoID(self, data):
		videoID = re.findall('data-id="(\d+)".*?data-quality="(\d+)"', data, re.S)
		if videoID:
			info = {}
			res = ''
			for x in videoID:
				res += x[1] + "+"
			res.strip('+')
			posturl = "http://%s/%s/desktop/%s" % (self.baseurl.replace('www','tkn'), videoID[-1][0], res)
			getPage(posturl, agent=std_headers, method='POST', postdata=info, headers={'Origin':'%s' % self.baseurl, 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getVideoUrl).addErrback(self.dataError)

	def getVideoUrl(self, data):
		videoUrl = re.findall('token":"(.*?)"', data, re.S)
		if videoUrl:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, videoUrl[-1])], showPlaylist=False, ltype='4tube')