# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.myvideolink import MyvideoLink

class myvideoTop100GenreScreen(MPScreen):

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

		self.keyLocked = True
		self['title'] = Label("MyVideo Top 100")
		self['ContentTitle'] = Label("Charts")
		self['name'] = Label(_("Selection:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('Top100 Single Charts',"http://www.myvideo.at/Top_100/Top_100_Single_Charts"),
							('Top100 Pop',"http://www.myvideo.at/Musik/Musik_Charts/Top_100_Pop"),
							('Top100 Rock',"http://www.myvideo.at/Musik/Musik_Charts/Top_100_Rock"),
							('Top100 Rap & RnB',"http://www.myvideo.at/Musik/Musik_Charts/Top_100_Rap/R%26B"),
							('Top100 Diverse',"http://www.myvideo.at/Musik/Musik_Charts/Top_100_Diverse")]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		myvideoTop100Name = self['liste'].getCurrent()[0][0]
		myvideoTop100Url = self['liste'].getCurrent()[0][1]

		print myvideoTop100Name, myvideoTop100Url
		self.session.open(myvideoTop100SongListeScreen, myvideoTop100Name, myvideoTop100Url)

class myvideoTop100SongListeScreen(MPScreen):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
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

		self.keyLocked = True
		self['title'] = Label("MyVideo Top 100")
		self['ContentTitle'] = Label("Charts: %s" % self.genreName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		print self.genreLink
		getPage(self.genreLink, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		print "drin"
		charts = re.findall("<a href='/watch/.*?' title='(.*?)'><img id='i(\d+)'.*?longdesc='(.*?.jpg)'.*?<span class='vViews'>(.*?)</span>.*?<span class='chartTop.*?'>(.*?)</span>", data, re.S)
		if charts:
			self.filmliste = []
			for (title, id, image, min, place) in charts:
				title = "%s. %s" % (place, decodeHtml(title))
				url = "http://www.myvideo.at/dynamic/get_player_video_xml.php?flash_playertype=D&ID=%s" % id
				self.filmliste.append((title,url,id,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		id = self['liste'].getCurrent()[0][2]
		imgurl = self['liste'].getCurrent()[0][3]
		idx = self['liste'].getSelectedIndex()

		print idx, title, url
		if config.mediaportal.useRtmpDump.value:
			MyvideoLink(self.session, bufferingOpt = 'rtmpbuffering').getLink(self.playRtmpStream, self.dataError, title, url, id, imgurl=imgurl)
		else:
			self.session.open(myvideoTop100Player, self.filmliste, int(idx) , True, self.genreName)

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

class myvideoTop100Player(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=True, listTitle=None):
		print "myvideoTop100Player:"
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle, ltype='myvideo')

	def getVideo(self):
		titel = self.playList[self.playIdx][self.title_inr]
		url = self.playList[self.playIdx][1]
		token = self.playList[self.playIdx][2]
		imgurl = self.playList[self.playIdx][3]
		print titel, url, token

		MyvideoLink(self.session).getLink(self.playStream, self.dataError, titel, url, token, imgurl=imgurl)