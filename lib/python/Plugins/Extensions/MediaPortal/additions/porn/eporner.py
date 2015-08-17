# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

class epornerGenreScreen(MPScreen):

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

		self['title'] = Label("Eporner.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.eporner.com/categories/"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('class="categoriesbox"\sid=".*?"><a\shref="(.*?)".*?title=".*?"><img\ssrc="(.*?)"\salt="(.*?)"', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "http://www.eporner.com" + Url
				Title = Title.replace(' porn videos', '')
				self.genreliste.append((Title, Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("HD", "http://www.eporner.com/hd//", None))
			self.genreliste.insert(0, ("Top Rated", "http://www.eporner.com/top_rated//", None))
			self.genreliste.insert(0, ("Popular", "http://www.eporner.com/weekly_top//", None))
			self.genreliste.insert(0, ("On Air", "http://www.eporner.com/currently//", None))
			self.genreliste.insert(0, ("New", "http://www.eporner.com/", None))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
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

		else:
			streamGenreLink = self['liste'].getCurrent()[0][1]
			self.session.open(epornerFilmScreen, streamGenreLink, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			Name = self['liste'].getCurrent()[0][0]
			self.suchString = callback.replace(' ', '-')
			streamGenreLink = 'http://www.eporner.com/search/%s/' % (self.suchString)
			self.session.open(epornerFilmScreen, streamGenreLink, Name)

class epornerFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, Name):
		self.CatLink = CatLink
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

		self['title'] = Label("Eporner.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 0
		self.lastpage = 0

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s/" % (self.CatLink, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		lastp = re.search('class="numlist2">.*?of\s(.*?[0-9])\s', data, re.S)
		if lastp:
			lastp = round((float(lastp.group(1).replace(',','')) / 51) + 0.5)
			self.lastpage = int(lastp)
		else:
			self.lastpage = 0
		self['page'].setText(str(self.page+1) + ' / ' + str(self.lastpage))
		Movies = re.findall('<div\sclass="mbtit".*?><a\shref="(.*?)"\stitle="(.*?)".*?src="(.*?)".*?"mbtim">(.*?)<\/div>.*?"mbvie">(.*?)<\/div>', data, re.S)
		if Movies:
			for (Url, Title, Image, Runtime, Views) in Movies:
				Views = Views.replace(',','')
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste,0,1,2,3,None,self.page+1,self.lastpage, mode=1, pagefix=-1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s" % (runtime, views))
		if not coverUrl == None:
			CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyPageNumber(self):
		self.session.openWithCallback(self.callbackkeyPageNumber, VirtualKeyBoardExt, title = (_("Enter page number")), text = str(self.page+1), is_dialog=True)

	def callbackkeyPageNumber(self, answer):
		if answer is not None:
			answer = re.findall('\d+', answer)
		else:
			return
		if answer:
			if int(answer[0])-1 < self.lastpage:
				self.page = int(answer[0])-1
				self.loadPage()
			else:
				self.page = self.lastpage-1
				self.loadPage()

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
		url = 'http://www.eporner.com%s' % (self['liste'].getCurrent()[0][1])
		self.keyLocked = True
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getXMLPage).addErrback(self.dataError)

	def getXMLPage(self, data):
		videoPage = re.findall(r"player4\\([^\\]*)\\", data, re.S)
		if videoPage:
			for url in videoPage:
				xml = 'http://www.eporner.com/config5%s' % (url)
		else:
			videoPage = re.findall('src="/config7(.*?)"', data, re.S)
			xml = 'http://www.eporner.com/config7%s' % (videoPage[0])
		getPage(xml, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		url = re.findall('file:\s"(.*?.mp4)",', data, re.S)
		if url:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url[0])], showPlaylist=False, ltype='eporner')