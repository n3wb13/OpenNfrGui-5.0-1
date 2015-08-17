# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.myvideolink import MyvideoLink
from p7s1media import p7s1Main

class myvideotvGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, source, portal):
		self.source = source
		self.portal = portal
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

		self['title'] = Label("%s" % self.portal)
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Selection:"))


		self.keyLocked = True
		self.filmliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.ml.setList(map(self._defaultlistcenter, [(_("Please wait..."),"","","")]))
		url = "http://www.myvideo.at/Serien/%s" % self.source
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.source == "Alle_Serien_A-Z":
			entrys = data.split("'seriesEntry'>")
			if len(entrys) > 1:
				for entry in entrys[1:]:
					if entry.find('vFull') > 0:
						raw = re.search("href='(.*?)'.*?pChHead'>(.*?)</.*?vFullEpisode'.*?longdesc='(.*?)'", entry)
					else:
						continue
					if raw:
						Title = raw.group(2)
						Url = raw.group(1)
						Image = raw.group(3)
						self.filmliste.append((decodeHtml(Title), Url, Image, ''))
			else:
				self.filmliste.append(("No streams found!","","",""))
			del entrys
		else:
			raw = re.findall("class='vFullEpisode'.*?<a\shref='(/channel/.*?)'.*?title='(.*?)'><img\sid='\D(.*?)'.*?longdesc='(.*?)'.*?'pChText'>(.*?)</div>", data, re.S)
			if raw:
				for (Url, Title, id, Image, Handlung) in raw:
					self.filmliste.append((decodeHtml(Title), Url, Image, Handlung))
				if self.source == "Sat1":
					self.filmliste.insert(0, ("--- Sat.1 Videokatalog ---", None, None, None))
				if self.source == "ProSieben":
					self.filmliste.insert(0, ("--- ProSieben Videokatalog ---", None, None, None))
			else:
				self.filmliste.append(("No streams found!","","",""))
			self.filmliste.sort(key=lambda t : t[0].lower())

		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		ImageUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(ImageUrl)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if re.search('Videokatalog', Name, re.S):
			self.session.open(p7s1Main, self.source)
		else:
			self.session.open(myvideotvListScreen, Link, Name, self.portal)

class myvideotvListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal):
		self.Link = Link
		self.Name = Name
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

		self['title'] = Label("%s" % self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1
		self.ownerId = None
		self.onLayoutFinish.append(self.getOwnerId)

	def getOwnerId(self):
		url = "http://www.myvideo.at" + self.Link
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseOwnerId).addErrback(self.dataError)

	def parseOwnerId(self, data):
		try:
			self.ownerId = re.search("'ownerId':'(.*?)'", data).group(1)
			self.loadPage()
		except:
			pass

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = "http://www.myvideo.at/iframe.php?lpage=%s&function=mv_charts&action=full_episodes&page=%s" % (str(self.page), self.ownerId)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		lastpage = re.search("pnPages'>\s\(\d+/(.*?)\)", data, re.S)
		if lastpage:
			self.lastpage = int(lastpage.group(1))
			self['page'].setText("%s / %s" % (str(self.page), str(self.lastpage)))
		else:
			self.lastpage = 1
			self['page'].setText("%s / 1" % str(self.page))
		raw = re.findall("class='slThumb.*?href='.*?'\stitle='(.*?)'><img.*?id='(.*?)'.*?longdesc='(.*?)'.*?class='pChText'>(.*?)</div>", data, re.S)
		if raw:
			for (Title, id, Image, Handlung) in raw:
				self.filmliste.append((decodeHtml(Title), id, Image, Handlung))
		else:
			self.filmliste.append(("No streams found!","","",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		mvUrl = self['liste'].getCurrent()[0][1]
		id = re.search('\D(\d+)', mvUrl)
		if id:
			url = "http://www.myvideo.at/dynamic/get_player_video_xml.php?ID=" + id.group(1)
			Title = self['liste'].getCurrent()[0][0]
			imgurl = self['liste'].getCurrent()[0][2]
			if config.mediaportal.useRtmpDump.value:
				MyvideoLink(self.session, bufferingOpt = 'rtmpbuffering').getLink(self.playRtmpStream, self.dataError, Title, url, id.group(1), imgurl=imgurl)
			else:
				self.session.open(MyvideoPlayer, [(Title, url, id.group(1), imgurl)])
		else:
			printl('No ID found!', self, 'E')

	def playRtmpStream(self, movietitle, moviepath, movie_img, cont_cb=None, exit_cb=None, http_fallback=False):
		self.playrtmp_cont_callback = cont_cb
		self.playrtmp_exit_callback = exit_cb
		if not http_fallback:
			self.session.openWithCallback(self.cb_Player, SimplePlayer, [(movietitle, moviepath, movie_img)], cover=False, showPlaylist=False, ltype='myvideo-rtmp', useResume=False, bufferingOpt = 'rtmpbuffering')
		else:
			self.session.open(SimplePlayer, [(movietitle, moviepath, movie_img)], cover=False, showPlaylist=False, ltype='myvideo-http')

	def cb_Player(self, retval=None):
		if retval == 'continue':
			self.playrtmp_cont_callback()
		else:
			self.playrtmp_exit_callback()

class MyvideoPlayer(SimplePlayer):

	def __init__(self, session, playList):
		print "MyvideoPlayer:"
		SimplePlayer.__init__(self, session, playList, showPlaylist=False, ltype='myvideo', cover=False)

	def getVideo(self):
		titel = self.playList[self.playIdx][0]
		url = self.playList[self.playIdx][1]
		token = self.playList[self.playIdx][2]
		imgurl = self.playList[self.playIdx][3]

		MyvideoLink(self.session).getLink(self.playStream, self.dataError, titel, url, token, imgurl=imgurl)