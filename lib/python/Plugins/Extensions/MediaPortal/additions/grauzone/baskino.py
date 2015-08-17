# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class baskino(MPScreen, ThumbsHelper):

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
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"0": self.closeAll,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Baskino.com")
		self['ContentTitle'] = Label(_("Selection"))

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.page = 1
		self.lastpage = 999
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://baskino.com/new/page/%s/" % str(self.page)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		movies = re.findall('<div class="postcover">.*?<a href="(.*?)">.*?<img title="(.*?)" src="(.*?)"', data, re.S)
		if movies:
			self.streamList = []
			for (url,title,image) in movies:
				self.streamList.append((decodeHtml(title), url, image))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page)
		self.showInfos()

	def showInfos(self):
		self['page'].setText("%s" % str(self.page))
		coverUrl = self['liste'].getCurrent()[0][2]
		self.filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(self.filmName)
		ImageUrl = "%s" % coverUrl.replace('_170_120','_145_215')
		CoverHelper(self['coverArt']).getCover(ImageUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseVideo).addErrback(self.dataError)

	def parseVideo(self, data):
		video = re.findall('file:"(.*?)"', data, re.S)
		if video:
			self.session.open(SimplePlayer, [(self.filmName, video[0])], showPlaylist=False, ltype='baskino')
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)