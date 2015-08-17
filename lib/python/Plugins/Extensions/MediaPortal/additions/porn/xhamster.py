# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class xhamsterGenreScreen(MPScreen):

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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("xHamster.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://xhamster.com/channels.php"
		getPage(url, headers={'Cookie': 'videoFilters=%7B%22channels%22%3A%22%3B0%22%7D', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('title">Straight</div>(.*?)iconTrans"></div>', data, re.S)
		Cats = re.findall('<a\sclass="btnBig"\shref="(.*?)1.html">.*?\n\s\s+([a-z].*?)</a>', parse.group(1), re.S|re.I)
		if Cats:
			for (Url, Title) in Cats:
				Title = Title.strip(' ')
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Newest", 'http://xhamster.com/new/'))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(xhamsterFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '%s' % (self.suchString)
			Name = "--- Search ---"
			self.session.open(xhamsterFilmScreen, Link, Name)

class xhamsterFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("xHamster.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.streamList = []
		if re.match(".*?Search", self.Name):
			url = "http://xhamster.com/search.php?new=&q=%s&qcat=video&page=%s" % (self.Link, str(self.page))
		else:
			url = "%s%s.html" % (self.Link, str(self.page))
		getPage(url, headers={'Cookie': 'videoFilters=%7B%22channels%22%3A%22%3B0%22%7D', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		self.getLastPage(data, 'class=\'pager\'>(.*?)</table>')
		if re.search('vDate', data, re.S):
			parse = re.search('<div\sclass=\'vDate(.*)</html>', data, re.S)
		else:
			parse = re.search('<html(.*)</html>', data, re.S)
		Liste = re.findall('class=\'video\'><a\shref=\'(.*?/movies/.*?)\'.*?class=\'hRotator\'\s><img\ssrc=\'(.*?)\'.*?alt="(.*?)".*?start2.*?<b>(.*?)</b>', parse.group(1), re.S)
		if Liste:
			for (Link, Image, Name, Runtime) in Liste:
				self.streamList.append((decodeHtml(Name), Image, Link, Runtime))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 2, 1, 3, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][1]
		runtime = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s" % (runtime))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		self.keyLocked = True
		getPage(Link, headers={'Cookie': 'videoFilters=%7B%22channels%22%3A%22%3B0%22%7D', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.playData).addErrback(self.dataError)

	def playData(self, data):
		Title = self['liste'].getCurrent()[0][0]
		File = re.findall("file:.'(.*?)'", data)
		if File:
			self.keyLocked = False
			self.session.open(SimplePlayer, [(Title, File[0])], showPlaylist=False, ltype='xhamster')