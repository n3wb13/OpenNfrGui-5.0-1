# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def movie2kGenreListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 800, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0])
		]

def movie2kListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 800, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
		]

def movie2kStreamListEntry(entry):
	premiumFarbe = int(config.mediaportal.premium_color.value, 0)
	if config.mediaportal.premiumize_use.value:
		if re.search(mp_globals.premium_hosters, entry[2], re.S|re.I):
			return [entry,
				(eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 150, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1], premiumFarbe),
				(eListboxPythonMultiContent.TYPE_TEXT, 200, 0, 200, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe),
				(eListboxPythonMultiContent.TYPE_TEXT, 400, 0, 400, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3], premiumFarbe)
				]
		else:
			return [entry,
				(eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 150, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]),
				(eListboxPythonMultiContent.TYPE_TEXT, 200, 0, 200, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]),
				(eListboxPythonMultiContent.TYPE_TEXT, 400, 0, 400, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3])
				]
	else:
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 150, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]),
			(eListboxPythonMultiContent.TYPE_TEXT, 200, 0, 200, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]),
			(eListboxPythonMultiContent.TYPE_TEXT, 400, 0, 400, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3])
			]

class movie2kGenreScreen(MPScreen):

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
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Movie2k.tl")
		self['ContentTitle'] = Label(_(_("Genre Selection")))

		self.genreliste = []
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.chooseMenuList

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('Kinofilme',"http://www.movie2k.tl"),
							('Videofilme',"http://www.movie2k.tl")]
		self.chooseMenuList.setList(map(movie2kGenreListEntry, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		self.movie2kName = self['liste'].getCurrent()[0][0]
		movie2kUrl = self['liste'].getCurrent()[0][1]
		print self.movie2kName, movie2kUrl
		self.session.open(movie2kListeScreen, self.movie2kName, movie2kUrl)

class movie2kListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, movie2kName, movie2kUrl):
		self.movie2kName = movie2kName
		self.movie2kUrl = movie2kUrl
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
		self['title'] = Label("Movie2k.tl")
		self['ContentTitle'] = Label(self.movie2kName)

		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.chooseMenuList

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		print "hole daten.."
		getPage(self.movie2kUrl, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.movie2kName == "Kinofilme":
			self.kinofilme(data)
		elif self.movie2kName == "Videofilme":
			self.videofilme(data)

	def kinofilme(self, data):
		kino = re.findall('<div style="float:left">.*?<a href="(.*?)">.*?<img src="(.*?)".*?alt="(.*?).kostenlos".*?:</strong><br>(.*?)<', data, re.S)
		if kino:
			self.videoliste = []
			for (url, img, title, desc) in kino:
				self.videoliste.append((decodeHtml(title), url, img, desc))

			self.chooseMenuList.setList(map(movie2kListEntry, self.videoliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.videoliste, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def videofilme(self, data):
		video = re.findall('<div style="float: left;".*?<a href="(.*?)">.*?<img src="(.*?)".*?alt="(.*?)"', data, re.S)
		if video:
			self.videoliste = []
			for (url, img, title) in video:
				self.videoliste.append((decodeHtml(title), url, img))

			self.chooseMenuList.setList(map(movie2kListEntry, self.videoliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.videoliste, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		print self.movie2kName
		title = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)	
		self['name'].setText(title)
		if self.movie2kName == "Kinofilme":
			handlung = self['liste'].getCurrent()[0][3]
			self['handlung'].setText(decodeHtml(handlung))

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]

		print title, url, image
		self.session.open(movie2kStreamListeScreen, title, url, image)

class movie2kStreamListeScreen(MPScreen):

	def __init__(self, session, movie2kName, movie2kUrl, movie2kImage):
		self.movie2kName = movie2kName
		self.movie2kUrl = movie2kUrl
		self.movie2kImage = movie2kImage
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
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
		self['title'] = Label("Movie2k.tl")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movie2kName)

		self.streamliste = []
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.chooseMenuList

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.movie2kUrl, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		hoster = re.findall('<tr\sid=.*?tablemoviesindex2.*?>.*?td\sheight="20"\swidth="150">.*?<a\shref.*?"(.*?.html).*?>(.*?)<img.*?/>&\#160;(.*?)</a>.*?title="Movie\squality\s(.*?)"', data, re.S)
		if hoster:
			self.streamliste = []
			for (url, date, hostername, quali) in hoster:
				if isSupportedHoster(hostername, True):
					self.streamliste.append((url, date, hostername, quali))
			if len(self.streamliste) == 0:
				self.streamliste.append((_('No supported streams found!'), None, None, None))
			self.chooseMenuList.setList(map(movie2kStreamListEntry, self.streamliste))
			CoverHelper(self['coverArt']).getCover(self.movie2kImage)
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][0]
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.get_hoster_link).addErrback(self.dataError)

	def get_hoster_link(self, data):
		hoster_link = re.findall('</div><br />\r\n\r\n\t\r\n\t\t\t\t\t\t\t<a href="(.*?)" target="_BLANK"><img src="http://www.movie2k.tl/assets/img/click_link.jpg" border="0" /></a>', data, re.S)
		if hoster_link:
			print hoster_link[0]
			get_stream_link(self.session).check_link(hoster_link[0], self.got_link, False)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.movie2kName, stream_url, self.movie2kImage)], showPlaylist=False, ltype='movie2k', cover=True)