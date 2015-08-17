# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.pininputext import PinInputExt
from Plugins.Extensions.MediaPortal.resources.myvideolink import MyvideoLink

class myVideoGenreScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("MyVideo.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Alle Filme", "74594"))
		self.genreliste.append(("Action", "74592"))
		self.genreliste.append(("Comedy", "74588"))
		self.genreliste.append(("Drama", "74589"))
		self.genreliste.append(("Dokumentation", "76116"))
		self.genreliste.append(("Erotik", "78357"))
		self.genreliste.append(("Horror", "74591"))
		self.genreliste.append(("Konzerte", "75833"))
		self.genreliste.append(("Sci-Fi", "74593"))
		self.genreliste.append(("Thriller", "74590"))
		self.genreliste.append(("Western", "75189"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pincheckok(self, pincode):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if pincode:
			self.session.open(myVideoFilmScreen, Link, Name)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		print Link
		if Link == "78357":
			if config.mediaportal.pornpin.value:
				self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
			else:
				self.session.open(myVideoFilmScreen, Link, Name)
		else:
			self.session.open(myVideoFilmScreen, Link, Name)

class myVideoFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self.page = 1
		self['title'] = Label("MyVideo.de")
		self['ContentTitle'] = Label("Auswahl: %s" % self.Name)

		self['Page'] = Label(_("Page:"))

		self.mvListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://www.myvideo.de/iframe.php?lpage=%s&function=mv_success_box&action=filme_video_list&searchGroup=%s&searchOrder=1" % (str(self.page), self.Link)
		print url
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		totalPages = re.search('pView pnResults\'>\s(\d+)\sbis\s(\d+)\svon\s(\d+)<', data, re.S)
		if totalPages:
			self.lastpage = int(totalPages.group(3))/15+1
			self['page'].setText("%s / %s" % (str(self.page), str(self.lastpage)))
		else:
			self.lastpage = 999
			self['page'].setText(str(self.page))

		mvVideo = re.findall("<div class='vThumb vViews'><a href='(.*?)' class='vLink' title='(.*?)'.*?src='(.*?.jpg)' class='vThumb' alt=''/><span class='vViews' id='.*?'>(.*?)</span></a></div><div class='clear'>.*?href='.*?' title='(.*?)'", data, re.S)
		if mvVideo:
			self.mvListe = []
			for (mvUrl,mvHandlung,mvImage,mvRuntime,mvTitle) in mvVideo:
				mvUrl = "http://www.myvideo.de" + mvUrl
				self.mvListe.append((decodeHtml(mvTitle), mvUrl, mvImage, decodeHtml(mvHandlung), mvRuntime))
			self.ml.setList(map(self._defaultlistleft, self.mvListe))
			self.keyLocked = False
			self.th_ThumbsQuery(self.mvListe, 0, 1, 2, 4, None, self.page, self.lastpage)
			self.showInfos()

	def showInfos(self):
		myTitle = self['liste'].getCurrent()[0][0]
		myPicLink = self['liste'].getCurrent()[0][2]
		myHandlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(myTitle)
		#self['page'].setText(str(self.page))
		self['handlung'].setText(myHandlung)
		CoverHelper(self['coverArt']).getCover(myPicLink)

	def keyOK(self):
		if self.keyLocked:
			return
		mvUrl = self['liste'].getCurrent()[0][1]
		print mvUrl
		id = re.search('/watch/(\w+)', mvUrl)
		if id:
			url = "http://www.myvideo.de/dynamic/get_player_video_xml.php?ID=" + id.group(1)
			kiTitle = self['liste'].getCurrent()[0][0]
			imgurl = self['liste'].getCurrent()[0][2]
			if config.mediaportal.useRtmpDump.value:
				MyvideoLink(self.session, bufferingOpt = 'rtmpbuffering').getLink(self.playRtmpStream, self.dataError, kiTitle, url, id.group(1), imgurl=imgurl)
			else:
				self.session.open(MyvideoPlayer, [(kiTitle, url, id.group(1), imgurl)])
		else:
			printl('No ID found!', self, 'E')

	def playRtmpStream(self, movietitle, moviepath, movie_img, cont_cb=None, exit_cb=None, http_fallback=False):
		self.playrtmp_cont_callback = cont_cb
		self.playrtmp_exit_callback = exit_cb
		if not http_fallback:
			self.session.openWithCallback(self.cb_Player, SimplePlayer, [(movietitle, moviepath, movie_img)], cover=True, showPlaylist=False, ltype='myvideo-rtmp', useResume=False, bufferingOpt = 'rtmpbuffering')
		else:
			self.session.open(SimplePlayer, [(movietitle, moviepath, movie_img)], cover=True, showPlaylist=False, ltype='myvideo-http')

	def cb_Player(self, retval=None):
		if retval == 'continue':
			self.playrtmp_cont_callback()
		else:
			self.playrtmp_exit_callback()

class MyvideoPlayer(SimplePlayer):

	def __init__(self, session, playList):
		print "MyvideoPlayer:"
		SimplePlayer.__init__(self, session, playList, showPlaylist=False, ltype='myvideo', cover=True)

	def getVideo(self):
		titel = self.playList[self.playIdx][0]
		url = self.playList[self.playIdx][1]
		token = self.playList[self.playIdx][2]
		imgurl = self.playList[self.playIdx][3]
		print titel, url, token

		MyvideoLink(self.session).getLink(self.playStream, self.dataError, titel, url, token, imgurl=imgurl)