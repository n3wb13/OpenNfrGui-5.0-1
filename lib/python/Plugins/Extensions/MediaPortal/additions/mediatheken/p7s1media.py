# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.myvideolink import MyvideoLink

class p7s1Main(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "ProSieben":
			self.portal = "ProSieben Mediathek"
			self.baseurl = "http://videokatalog.prosieben.de/"
		if self.mode == "Sat1":
			self.portal = "Sat.1 Mediathek"
			self.baseurl = "http://videokatalog.sat1.de/"

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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		url = self.baseurl
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		step1 = re.search('<h2>Alle Kategorien</h2>(.*?)id="site_footer"', data, re.S)
		if self.mode == "Sat1":
			parse = re.findall('<h3><a\sclass="arrow"\shref="(.*?)">(.*?)</a></h3>.*?<p>\s+(.*?)</p>', step1.group(1), re.S)
		else:
			parse = re.findall('<li>.*?<a\shref="(.*?)">(.*?)</a>.*?<p>\s+(.*?)</p>', step1.group(1), re.S)
		for (Link, Title, Sub) in parse:
			Sub = Sub.strip()
			self.streamList.append((Title, Link, Sub))
		self.streamList.sort()
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self['name'].setText("")

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		sub = self['liste'].getCurrent()[0][2]
		if sub == "":
			self.session.open(p7s1vidScreen, url, title, self.mode, self.portal)
		else:
			self.session.open(p7s1subScreen, url, title, self.mode, self.portal)

class p7s1subScreen(MPScreen):

	def __init__(self, session, Link, Name, mode, portal):
		self.Link = Link
		self.Name = Name
		self.mode = mode
		self.portal = portal
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = self.Link
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self['name'].setText('')
		step1 = re.search('Unterkategorien:</strong>(.*?)</article>', data, re.S)
		if self.mode == "Sat1":
			parse = re.findall('<a.*?href="(.*?)"><strong>(.*?)</strong></a>', step1.group(1), re.S)
		else:
			parse = re.findall('<a\shref="(.*?)">(.*?)</a>', step1.group(1), re.S)
		if parse:
			for (Link, Title) in parse:
				self.filmliste.append((decodeHtml(Title).strip(), Link))
			self.filmliste.sort()
			if self.Name != "Sendungen":
				self.filmliste.insert(0, (self.Name, self.Link, None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(p7s1vidScreen, url, title, self.mode, self.portal)

class p7s1vidScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, mode, portal):
		self.Link = Link
		self.Name = Name
		self.mode = mode
		self.portal = portal
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

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.page == 1:
			url = self.Link
		else:
			url = self.Link + "%s.html" % self.page
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.mode == "Sat1":
			self.getLastPage(data, 'class="other">(.*?)</ul>')
		else:
			self.getLastPage(data, 'class="active">(.*?)</ul>')
		if self.mode == "Sat1":
			step1 = re.search('<h2>Videos</h2>(.*?)id="site_footer"', data, re.S)
			parse = re.findall('<a href="(.*?)".*?src="(.*?)">.*?align_right">(.*?)<.*?title=".*?">(.*?)</a>.*?"vs-description">(.*?)</div>', step1.group(1), re.S)
		else:
			step1 = re.search('class="videoList">(.*?)<div\sclass="clear">', data, re.S)
			parse = re.findall('<li class.*?href="(.*?)".*?src="(.*?)".*?date">(.*?)<.*?title.*?>(.*?)</a>.*?<span title="(.*?)"', step1.group(1), re.S)
		if parse:
			for (Link, Pic, Date, Title, Desc) in parse:
				self.filmliste.append((decodeHtml(Title), Link, Pic, Date, Desc))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText(decodeHtml(desc))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadIDData).addErrback(self.dataError)

	def loadIDData(self, data):
		id = re.findall('broadcast_date.*?id.":."(.*?)."', data, re.S)
		if id:
			url = 'http://vas.sim-technik.de/video/video.json?clipid=%s&app=megapp&method=1' % id[-1]
			getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream).addErrback(self.dataError)
			
	def getStream(self, data):
		title = self['liste'].getCurrent()[0][0]
		url = re.search('VideoURL"."(.*?)"', data, re.S)
		if url:
			url = url.group(1).replace('\/','/')
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='p7s1media')