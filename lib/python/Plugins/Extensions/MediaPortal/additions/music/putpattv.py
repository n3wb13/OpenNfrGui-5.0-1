# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.putpattvlink import PutpattvLink

class putpattvGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("putpat.tv")
		self['ContentTitle'] = Label("Kanal Auswahl:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		# http://www.putpat.tv/ws.xml?client=miniplayer&method=Channel.all
		self.genreliste.append(("--- Search ---", "callSuchen"))
		self.genreliste.append(("Charts", "2"))
		self.genreliste.append(("Heimat", "3"))
		self.genreliste.append(("Retro", "4"))
		self.genreliste.append(("2Rock", "5"))
		self.genreliste.append(("Vibes", "6"))
		self.genreliste.append(("Hooray!", "7"))
		self.genreliste.append(("INTRO TV", "9"))
		self.genreliste.append(("JAZZthing.TV", "11"))
		self.genreliste.append(("Festival Guide", "12"))
		self.genreliste.append(("studiVZ", "15"))
		self.genreliste.append(("meinVZ", "16"))
		self.genreliste.append(("MELT Festival", "29"))
		self.genreliste.append(("Splash! Festival", "30"))
		self.genreliste.append(("Berlin Festival", "31"))
		self.genreliste.append(("Flux TV", "34"))
		self.genreliste.append(("Introducing", "36"))
		self.genreliste.append(("Pop10", "39"))
		self.genreliste.append(("Rock Hard", "41"))
		self.genreliste.append(("Sneakerfreaker", "43"))
		self.genreliste.append(("Paradise TV", "45"))
		self.genreliste.append(("PUTPAT one", "46"))
		self.genreliste.append(("detektor.fm", "47"))
		self.genreliste.append(("Party", "48"))
		self.genreliste.append(("HD-Kanal", "49"))
		self.genreliste.append(("Chiemsee Festival", "50"))
		self.genreliste.append(("Hurricane/Southside Festival", "51"))
		self.genreliste.append(("Highfield Festival", "52"))
		self.genreliste.append(("M'era Luna", "53"))
		self.genreliste.append(("FazeMag", "54"))
		self.genreliste.append(("Seat Cupra Camp", "55"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][1]
		Image = 'http://files.putpat.tv/artwork/channelgraphics/%s/channelteaser_500.png' % Image
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		if streamGenreName == "--- Search ---":
			self.suchen()
		else:
			streamGenreLink = self['liste'].getCurrent()[0][1]
			self.session.open(putpattvFilmScreen, streamGenreLink, streamGenreName)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '%20')
			streamGenreLink = '%s' % (self.suchString)
			selfGenreName = "--- Search ---"
			self.session.open(putpattvFilmScreen, streamGenreLink, selfGenreName)

class putpattvFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, catName):
		self.CatLink = CatLink
		self.catName = catName
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
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Titel Auswahl")
		self['ContentTitle'] = Label("Genre: %s" % self.catName)
		self['F2'] = Label(_("Page"))

		self.keyLocked = True
		self.page = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(self.catName)
		self.filmliste = []
		if self.catName == '--- Search ---':
			url = "http://www.putpat.tv/ws.xml?limit=100&client=putpatplayer&partnerId=1&searchterm=%s&method=Asset.quickbarSearch" % (self.CatLink)
		else:
			url = "http://www.putpat.tv/ws.xml?method=Channel.clips&partnerId=1&client=putpatplayer&maxClips=500&channelId=%s&streamingId=tvrl&streamingMethod=http" % (self.CatLink)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.catName == '--- Search ---':
			Search = re.findall('<video-file-id\stype="integer">(.*?)</video-file-id>.*?<token>(.*?)</token>.*?<description>(.*?)</description>', data, re.S)
			if Search:
				for (Image, Token, Title) in Search:
					if len(Image) == 4:
						Image = '0' + Image
					Image = 'http://files.putpat.tv/artwork/posterframes/00%s/00%s/v00%s_posterframe_putpat_small.jpg' % (Image[0:3], Image, Image)
					self.filmliste.append((decodeHtml(Title), None, Token, Image))
		else:
			Movies = re.findall('<clip>.*?<medium>(.*?)</medium>.*?<title>(.*?)</title>.*?<display-artist-title>(.*?)</display-artist-title>.*?<video-file-id\stype="integer">(.*?)</video-file-id>', data, re.S)
			if Movies:
				for (Url, Title, Artist, Image) in Movies:
					Title = Artist + ' - ' + Title
					Url = Url.replace('&amp;','&')
					if len(Image) == 4:
						Image = '0' + Image
					Image = 'http://files.putpat.tv/artwork/posterframes/00%s/00%s/v00%s_posterframe_putpat_small.jpg' % (Image[0:3], Image, Image)
					if not (re.search('pop10_trenner.*?', Title, re.S) or re.search('Pop10 Trenner', Title, re.S) or re.search('pop10_pspot', Title, re.S) or re.search('pop10_opn_neu', Title, re.S) or re.search('PutPat Top Ten', Title, re.S)):
						self.filmliste.append((decodeHtml(Title), Url, None, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No songs found!"),'','',''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		self.session.open(
			PutpatTvPlayer,
			self.filmliste,
			playIdx = self['liste'].getSelectedIndex(),
			playAll = True,
			listTitle = self.catName
			)

class PutpatTvPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=False, listTitle=None):
		print "PutpatTvPlayer:"
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle, ltype='putpattv')

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		Title = self.playList[self.playIdx][0]
		token = self.playList[self.playIdx][2]
		Image = self.playList[self.playIdx][3]
		PutpattvLink(self.session).getLink(self.playStream, self.dataError, Title, url, token, Image)