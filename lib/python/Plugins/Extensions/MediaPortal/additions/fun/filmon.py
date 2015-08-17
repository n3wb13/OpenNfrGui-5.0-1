# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

special_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
	'Accept': 'application/json, text/javascript, */*; q=0.01',
	'Accept-Language': 'en-us,de-de;q=0.8,de;q=0.5,en;q=0.3',
	'Referer': 'http://www.filmon.com/'
}

kekse = {}

class filmON(MPScreen, ThumbsHelper):

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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmOn")

		self.keyLocked = True
		self.filmliste = []
		self.datarange = ""
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.filmon.com/tv/"
		getPage(url, cookies=kekse, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		parse = re.search('var groups = \[(.*?)groups\[i\]', data, re.S)
		if parse:
			self.datarange = parse.group(1)
			data = re.findall('\{"group_id":"(\d+)","id":"(\d+)","title":"(.*?)"', self.datarange, re.S)
			if data:
				for (id, nr, title) in data:
					image = "http://static.filmon.com/couch/groups/%s/big_logo.png" % id
					self.filmliste.append((decodeHtml(title), id, image))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No channels found.", "",""))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		alldata = []
		id = self['liste'].getCurrent()[0][1]
		name = self['liste'].getCurrent()[0][0]
		data = re.findall('\{"id":(.*?)\}', self.datarange, re.S)
		if data:
			for sublink in data:
				data1 = re.findall('^(.*?)group_id":%s,' % id, sublink, re.S)
				if data1:
					data1 = re.findall('^(.*?),.*?"title":"(.*?)".*?"description":"(.*?)"', data1[0], re.S)
					alldata = alldata + data1
		if alldata:
			self.session.open(filmONFilm, name, alldata)

class filmONFilm(MPScreen, ThumbsHelper):

	def __init__(self, session, Name, Data):
		self.Name = Name
		self.Data = Data
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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmOn - %s" % self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.pageData)

	def pageData(self):
		for (id, title, desc) in self.Data:
			image = "http://static.filmon.com/couch/channels/%s/big_logo.png" % id
			self.filmliste.append((decodeHtml(title).replace('\/','/'), id, image, decodeHtml(desc)))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No channels found.", "","",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		handlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(handlung)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		id = self['liste'].getCurrent()[0][1]
		info = urlencode({
		'channel_id': id,
		'quality': "low"
		})
		kekse.update({"xheader":"1"})
		kekse.update({"return_url":"/tv/live"})
		url = "http://www.filmon.com/ajax/getChannelInfo"
		getPage(url, agent=special_headers, cookies=kekse, method='POST', postdata=info, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'Content-Length': '26'}).addCallback(self.streamData).addErrback(self.dataError)

	def streamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		streamDaten = re.findall('"serverURL":"(.*?)","streamName":"(.*?)"', data, re.S)
		if streamDaten:
			(rtmpServer, rtmpFile) = streamDaten[0]
			url = "%s" % rtmpServer.replace('\/','/')
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='filmon')