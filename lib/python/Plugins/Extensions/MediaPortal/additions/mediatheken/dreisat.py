# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

dreiurl = "http://www.3sat.de"
baseurl = "http://www.3sat.de/mediathek/"

class dreisatGenreScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("3sat Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = baseurl + "?mode=sendungenaz0"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('class="mediatheklistbox.*?_hover".*?href="(.*?)".*?img\sclass=.*?MediathekListPic"\salt="(.*?)"\ssrc="(.*?)"', data, re.S)
		if raw:
			for (Url, Title, Image) in raw:
				Image = dreiurl + "%s" % Image
				self.filmliste.append((decodeHtml(Title), Url, Image))
		url = baseurl + "?mode=sendungenaz1"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData2).addErrback(self.dataError)

	def parseData2(self, data):
		raw = re.findall('class="mediatheklistbox.*?_hover".*?href="(.*?)".*?img\sclass=.*?MediathekListPic"\salt="(.*?)"\ssrc="(.*?)"', data, re.S)
		if raw:
			for (Url, Title, Image) in raw:
				Image = dreiurl + "%s" % Image
				self.filmliste.append((decodeHtml(Title), Url, Image))
				self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		ImageUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(ImageUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = baseurl + self['liste'].getCurrent()[0][1]
		self.session.open(dreisatListScreen, Link, Name)

class dreisatListScreen(MPScreen, ThumbsHelper):

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
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("3sat Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 0
		self.lastpage = 0
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link + "&mode=verpasst" + str(self.page)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		lastpage = re.search('class="ClnNextNblEnd".*?mode=verpasst([\d]+)\&amp;red', data, re.S)
		if lastpage:
			self.lastpage = int(lastpage.group(1))+1
			self['page'].setText("%s / %s" % (str(self.page+1), str(self.lastpage)))
		else:
			lastpage = re.search('ClnInfo.*?class="mediathek_menu_.*?([\d]+)&nbsp;.*?class="ClnNextLock', data, re.S)
			if lastpage:
				self.lastpage = int(lastpage.group(1))
				self['page'].setText("%s / %s" % (str(self.page+1), str(self.lastpage)))
			else:
				self.lastpage = 0
				self['page'].setText("%s / 1" % str(self.page+1))

		raw = re.findall('BoxPicture.*?src="(.*?)".*?BoxHeadline.*?href=".*?obj=(.*?)">(.*?)<.*?FloatText.*?href=".*?">(.*?)</a>', data, re.S)
		if raw:
			for (Image, id, Title, Handlung) in raw:
				Image = dreiurl + "%s" % Image
				Handlung = Handlung.replace('<b>','').replace('</b>','')
				self.filmliste.append((decodeHtml(Title), id, Image, Handlung))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page+1, self.lastpage, mode=1, pagefix=-1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page+1 < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		self.title = self['liste'].getCurrent()[0][0]
		id = self['liste'].getCurrent()[0][1].replace('amp;','')
		url = baseurl + "xmlservice/web/beitragsDetails?ak=web&id=%s" % id
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getDataStream).addErrback(self.dataError)

	def getDataStream(self, data):
		stream = re.findall('basetype="h264_aac_mp4.*?".*?<quality>veryhigh</quality>.*?<url>(http://[nrodl|rodl].*?zdf.de.*?.mp4)</url>', data, re.S)
		if stream:
			url = stream[0].replace("http://rodl", "http://nrodl")
			playlist = []
			playlist.append((self.title, url))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='3sat')