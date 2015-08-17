# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class arteFirstScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.filmliste.append(("Themen", "by_channel"))
		self.filmliste.append(("Programm", "by_cluster"))
		self.filmliste.append(("Datum", "by_date"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(arteSubGenreScreen, Link, Name)

class arteSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://www.arte.tv/guide/de/plus7"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		helper = re.findall('data-filter=\'%s\'(.*?)</div>\n</div>' % self.Link, data, re.S)
		if helper:
			sendungen = re.findall('href="(.*?)">(.*?)<', helper[0], re.S)
			if sendungen:
				for link,title in sendungen:
					link = "http://www.arte.tv%s" % link.replace("amp;", "")
					self.filmliste.append((decodeHtml(title), link))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(arteSecondScreen, Link, Name)

class arteSecondScreen(MPScreen, ThumbsHelper):

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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label("Auswahl: %s" % self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		addLink = "&regions=default%2CEUR_DE_FR%2CDE_FR%2CSAT%2CALL"
		Url = "%s%s" % (self.Link,addLink)
		self.Link = unquote(self.Link).replace('Â°', '%C3%82%C2%B0')
		getPage(Url, agent=std_headers, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Referer': self.Link}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		videos = re.findall('"image_url":"(.*?)".*?"title":"(.*?)",.*?"duration":(.*?),.*?"airdate_long":".*?,(.*?)".*?"desc":"(.*?)",.*?"url":"(.*?)"', data, re.S)
		if videos:
			self.filmliste = []
			for (image, title, dauer, datum, handlung, link) in videos:
				title = "%s - %s" % (decodeHtml(datum) ,decodeHtml(title))
				handlung = handlung.replace('\/','/')
				handlung = "%s min\n%s" % (dauer, handlung)
				title = title.replace('\/','/')
				link = "%s" % link.replace('\/','/')
				image = image.replace('\/','/')
				self.filmliste.append((title, link, image, handlung, dauer))
		else:
			self.filmliste.append((_("No videos found!"), '','','','',''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		self.ImageUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(self.ImageUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		self.title = self['liste'].getCurrent()[0][0]
		link = self['liste'].getCurrent()[0][1]
		getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getDataStream).addErrback(self.dataError)

	def getDataStream(self, data):
		artejson = re.findall('arte_vp_url=\'(.*?)\'>', data)
		if artejson:
			url = artejson[0].replace("/player/","/")
			getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		streamSQ = re.findall('"HBBTV","VQU":"SQ","VMT":"mp4","VUR":"(.+?)"', data)
		if streamSQ:
			self.playStream(streamSQ[0])
		else:
			streamEQ = re.findall('"HBBTV","VQU":"EQ","VMT":"mp4","VUR":"(.+?)"', data)
			if streamEQ:
				self.playStream(streamEQ[0])

	def playStream(self, url):
		self.session.open(SimplePlayer, [(self.title, url, self.ImageUrl)], showPlaylist=False, ltype='arte')