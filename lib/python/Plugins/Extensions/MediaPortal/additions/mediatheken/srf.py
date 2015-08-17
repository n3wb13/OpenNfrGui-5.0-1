# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class SRFGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("SRF Player")
		self['ContentTitle'] = Label("Auswahl der Sendung")


		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://www.srf.ch/play/tv/sendungen?displayedKey=Alle"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		sendungen = re.findall('<img\sclass="az_thumb.*?data-src2x="(.*?)".*?alt="(.*?)"\s/></a><h3><a\sclass="sendung_name"\shref="/play/tv/.*?\?id=(.*?)">.*?</a></h3>.*?az_description">(.*?)</p>', data, re.S)
		if sendungen:
			self.genreliste = []
			for (image, title, id, handlung) in sendungen:
				image = image.replace("width=144","width=320")
				self.genreliste.append((decodeHtml(title), id, image, handlung))
			self.genreliste.sort(key=lambda t : t[0].lower())
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, 1, 1, mode=1)
			self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(streamHandlung))
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(SRFFilmeListeScreen, streamGenreLink)

class SRFFilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink):
		self.streamGenreLink = streamGenreLink
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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("SRF Player")
		self['ContentTitle'] = Label("Folgen Auswahl")


		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://www.srf.ch/play/tv/episodesfromshow?id=" + self.streamGenreLink + "&pageNumber=1"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		folgen = re.findall('class="sendung_item">.*?<a\shref=".*?\?id=(.*?)".*?data-src2x="(.*?)".*?class="title">(.*?)</h3.*?"description\scomplete".*?>(.*?)<', data, re.S)
		if folgen:
			for (id, image, title, desc) in folgen:
				url = "http://www.srf.ch/webservice/cvis/segment/%s/.json?nohttperr=1;omit_video_segments_validity=1;omit_related_segments=1" % id
				image = image.replace("width\/224","width\/320")
				desc = decodeHtml(desc).strip()
				self.filmliste.append((decodeHtml(title), url, desc, image))
		else:
			self.filmliste.append(("Keine Sendungen gefunden.",None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamHandlung = self['liste'].getCurrent()[0][2]
		self['handlung'].setText(decodeHtml(streamHandlung))
		streamPic = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			return
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.get_xml).addErrback(self.dataError)

	def get_xml(self, data):
		master = re.findall('"streaming":"hls","quality":".*?","url":"(.*?)"}', data, re.S)
		if master:
			url = master[-1].replace("\/","/")
			title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='srf')
		else:
			url = self['liste'].getCurrent()[0][1]
			getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.get_rtmp).addErrback(self.dataError)

	def get_rtmp(self, data):
		xml = re.findall('"url":"(rtmp:.*?)"', data, re.S)
		if xml:
			url = xml[-1].replace("\/","/")
			host = url.split('mp4:')[0]
			playpath = url.split('mp4:')[1]
			title = self['liste'].getCurrent()[0][0]
			final = "%s swfUrl=http://www.srf.ch/play/flash/srfplayer.swf playpath=mp4:%s swfVfy=1" % (host, playpath)
			playlist = []
			playlist.append((title, final))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='srf')
		else:
			message = self.session.open(MessageBoxExt, _("For legal reasons this video may be viewed only within Switzerland."), MessageBoxExt.TYPE_INFO, timeout=5)
			return