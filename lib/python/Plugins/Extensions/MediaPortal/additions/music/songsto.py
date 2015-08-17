# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.songstolink import SongstoLink
from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayer, SimplePlaylist

class showSongstoGenre(MPScreen):

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

		self.baseurl = 'http://songs.to/json/songlist.php?'

		self["title"] = Label("Songs.to Music Player")
		self['ContentTitle'] = Label('Music Tops')
		self['name'] = Label(_("Selection:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://s.songs.to/js/data-en.js"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		preparse = re.search('chart_types={(.*?)}', data, re.S).groups()
		if preparse:
			parse = re.findall("(music.*?):\\'(.*?)\\'", preparse[0], re.S)
		if parse:
			for (scUrl, scName) in parse:
				self.genreliste.append((scName, "charts="+scUrl))
			self.genreliste.insert(0, ("Songs Top 500", "top=all"))
			self.genreliste.insert(0, ("Search Album", "&col=album"))
			self.genreliste.insert(0, ("Search Title", "&col=title"))
			self.genreliste.insert(0, ("Search Artist", "&col=artist"))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		scName = self['liste'].getCurrent()[0][0]
		scUrl = self['liste'].getCurrent()[0][1]
		if scName == "Songs Top 500":
			scUrl = self.baseurl + scUrl
			self.session.open(showSongstoAll, scUrl, scName)
		elif re.match('Search.*?', scName):
			self.suchtitel = scName
			self.suchmodus = scUrl
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (self.suchtitel), text = "", is_dialog=True)
		else:
			scUrl = self.baseurl + scUrl
			self.session.open(showSongstoTop, scUrl, scName)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			self.suchString = callbackStr.replace(' ', '%20')
			scUrl = self.baseurl + "keyword=" + self.suchString + self.suchmodus
			scName = self.suchtitel + ": " + callbackStr
			self.session.open(showSongstoAll, scUrl, scName)

class showSongstoAll(MPScreen):

	def __init__(self, session, link, name):
		self.scLink = link
		self.scGuiName = name
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
			"ok" : self.keyOK,
			"cancel" : self.keyCancel
		}, -1)

		self["title"] = Label("Songs.to Music Player")
		self['ContentTitle'] = Label(self.scGuiName)
		self['name'] = Label(_("Selection:"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		if self.scGuiName != "Songs Top 500" and not re.match('Search.*?', self.scGuiName):
			self.scData(self.scLink)
		else:
			getPage(self.scLink, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.scData).addErrback(self.dataError)

	def scData(self, data):
		data = data.replace('"cover":null','"cover":"",')
		findSongs = re.findall('"hash":"(.*?)","title":"(.*?)","artist":"(.*?)","album":"(.*?)".*?"cover":"(.*?)"', data, re.S)
		if findSongs:
			for (scHash,scTitle,scArtist,scAlbum,scCover) in findSongs:
				self.streamList.append((decodeHtml(scTitle), decodeHtml(scArtist), scAlbum, scCover, scHash))
		if len(self.streamList) == 0:
			self.streamList.append((_("No songs found!"), None, None, None, None))
		self.ml.setList(map(self.songsto_playlist, self.streamList))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		if self['liste'].getCurrent()[0][1] == None:
			return
		idx = self['liste'].getSelectedIndex()
		self.session.open(SongstoPlayer, self.streamList, 'songstoall', int(idx), self.scGuiName)

class showSongstoTop(MPScreen):

	def __init__(self, session, link, name):
		self.scLink = link
		self.scGuiName = name
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
			"ok" : self.keyOK,
			"cancel" : self.keyCancel
		}, -1)

		self["title"] = Label("Songs.to Music Player")
		self['ContentTitle'] = Label(self.scGuiName)
		self['name'] = Label(_("Selection:"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		getPage(self.scLink, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.scDataGet).addErrback(self.dataError)

	def scDataGet(self, data):
		findSongs = re.findall('name1":"(.*?)","name2":"(.*?)"', data, re.S)
		if findSongs:
			for (scArtist, scTitle) in findSongs:
				self.streamList.append((decodeHtml(scTitle), decodeHtml(scArtist)))
		if len(self.streamList) == 0:
			self.streamList.append((_("No songs found!"), None))
		self.ml.setList(map(self.songsto_playlist, self.streamList))
		self.keyLocked = False

	def scDataPost(self, data):
		self.keyLocked = False
		if self.artist == '':
			title = self.album
		else:
			title = self.artist + ' - ' + self.album
		self.session.open(showSongstoAll, data, title)

	def keyOK(self):
		if self.keyLocked:
			return
		if self['liste'].getCurrent()[0][1] == None:
			return
		if "album" in self.scLink:
			self.keyLocked = True
			self.artist = self['liste'].getCurrent()[0][1]
			self.album = self['liste'].getCurrent()[0][0]
			url = "http://songs.to/json/songlist.php?quickplay=1"
			dataPost = "data=%7B%22data%22%3A%5B%7B%22artist%22%3A%22"+self.artist+"%22%2C%20%22album%22%3A%22"+self.album+"%22%2C%20%22title%22%3A%22%22%7D%5D%7D"
			getPage(url, method='POST', postdata=dataPost, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.scDataPost).addErrback(self.dataError)
		else:
			idx = self['liste'].getSelectedIndex()
			self.session.open(SongstoPlayer, self.streamList, 'songstotop', int(idx), self.scGuiName)

class songstoPlaylist(SimplePlaylist):

	def playListEntry(self, entry):
		if entry[1] == '':
			title = entry[0]
		else:
			title = entry[1] + ' - ' + entry[0]
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, title))
		return res

class SongstoPlayer(SimplePlayer):

	def __init__(self, session, playList, songsto_type, playIdx=0, listTitle=None):
		self.songsto_type = songsto_type

		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=True, listTitle=listTitle, ltype='songsto', cover=True, autoScrSaver=True)

	def getVideo(self):
		sc_artist = self.playList[self.playIdx][1]
		sc_title = self.playList[self.playIdx][self.title_inr]
		if self.songsto_type == 'songstotop':
			sc_album = ''
			token = ''
			imgurl = ''
		else:
			sc_album = self.playList[self.playIdx][2]
			token = self.playList[self.playIdx][4]
			imgurl = self.playList[self.playIdx][3]
			imgurl = "http://songs.to/covers/"+imgurl

		SongstoLink(self.session).getLink(self.playStream, self.dataError, sc_title, sc_artist, sc_album, token, imgurl)

	def openPlaylist(self, pl_class=songstoPlaylist):
		SimplePlayer.openPlaylist(self, pl_class)