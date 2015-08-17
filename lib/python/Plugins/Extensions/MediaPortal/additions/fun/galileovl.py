# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

class galileovlGenreScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Galileo-Videolexikon.de")
		self['ContentTitle'] = Label(_("Selection:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('Neueste Videos',"http://www.galileo-videolexikon.de/catalog/galileo/clips/mode/latest/t/"),
							('Suche',"http://www.galileo-videolexikon.de/catalog/galileo/clips/")]
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		self.galileovlName = self['liste'].getCurrent()[0][0]
		galileovlUrl = self['liste'].getCurrent()[0][1]
		if self.galileovlName == "Neueste Videos":
			self.session.open(galileovlListeScreen, self.galileovlName, galileovlUrl)
		else:
			self.session.openWithCallback(self.captchaCallback, VirtualKeyBoardExt, title = (_("Search:")), text = "", is_dialog=True)

	def captchaCallback(self, callback = None, entry = None):
		if callback != None or callback != "":
			url = "http://www.galileo-videolexikon.de/catalog/galileo/clips/%s" % callback
			self.session.open(galileovlListeScreen, self.galileovlName, url)

class galileovlListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, galileovlName, galileovlUrl):
		self.galileovlName = galileovlName
		self.galileovlUrl = galileovlUrl
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up": self.keyUp,
			"down": self.keyDown,
			"right": self.keyRight,
			"left": self.keyLeft,
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Galileo-Videolexikon.de")
		self['ContentTitle'] = Label("Videos - %s" % self.galileovlName)

		self.videoliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		print "hole daten"
		getPage(self.galileovlUrl).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.videoliste = []
		videos = re.findall('"id":"(.*?)".*?"assestid":"(.*?)".*?"title":"(.*?)".*?"serie":"(.*?)".*?"description":"(.*?)".*?"duration":"(.*?)"', data, re.S )
		if videos:
			for (id, videoid, title, date, desc, dur) in videos:
				title = "%s - %s" % (date, title)
				image = "http://www.prosieben.de/dynamic/h264/thumbnails/?res=high&app=galileo&ClipID=%s" % videoid
				self.videoliste.append((decodeHtml(title), videoid, desc, image))
			self.ml.setList(map(self._defaultlistleft, self.videoliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.videoliste, 0, 1, 3, None, None, 1, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][3]
		handlung = self['liste'].getCurrent()[0][2]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self.galileovltitle = self['liste'].getCurrent()[0][0]
		self.galileovlid = self['liste'].getCurrent()[0][1]
		self.imageurl = self['liste'].getCurrent()[0][3]
		self.idx = self['liste'].getSelectedIndex()
		url = "http://ws.vtc.sim-technik.de/video/video.jsonp?method=1&type=1&app=GalVidLex_web&clipid=%s" % self.galileovlid
		getPage(url).addCallback(self.get_link).addErrback(self.dataError)

	def get_link(self, data):
		stream_url = re.findall('"VideoURL":"(.*?)"', data, re.S)
		if stream_url:
			stream_url = stream_url[0].replace('\\','')
			self.session.open(SimplePlayer, [(self.galileovltitle, stream_url, self.imageurl)], showPlaylist=False, ltype='galileovl')