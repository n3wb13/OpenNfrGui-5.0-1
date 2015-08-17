# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2015
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

glob_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0'
ck = {}
initCookies = True

class hdfilmeMain(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("HDFilme")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.hdfilmeExit)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("Kinofilme","http://hdfilme.tv/filme-im-kino/page/"))
		self.streamList.append(("Top IMDb","http://hdfilme.tv/top-imdb/page/"))
		self.streamList.append(("Abenteuer","http://hdfilme.tv/category/abenteuerfilm/page/"))
		self.streamList.append(("Action","http://hdfilme.tv/category/actionfilm/page/"))
		self.streamList.append(("Animation","http://hdfilme.tv/category/animationsfilm/page/"))
		self.streamList.append(("Drama","http://hdfilme.tv/category/drama/page/"))
		self.streamList.append(("Fantasy","http://hdfilme.tv/category/fantasyfilm/page/"))
		self.streamList.append(("Horror","http://hdfilme.tv/category/horrorfilm/page/"))
		self.streamList.append(("Komödie","http://hdfilme.tv/category/komodie/page/"))
		self.streamList.append(("Krimi","http://hdfilme.tv/category/kriminalfilm/page/"))
		self.streamList.append(("Sci-Fi","http://hdfilme.tv/category/science-fiction-film/page/"))
		self.streamList.append(("Romance","http://hdfilme.tv/category/romanze/page/"))
		self.streamList.append(("Thriller","http://hdfilme.tv/category/thriller/page/"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		genre = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(hdfilmeParsing, genre, url)

	def hdfilmeExit(self):
		global initCookies
		initCookies = True

class hdfilmeParsing(MPScreen):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("HDFilme")
		self['ContentTitle'] = Label("")
		self['Page'] = Label(_("Page:"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		if initCookies:
			self.onLayoutFinish.append(self.getCookies)
		else:
			self.onLayoutFinish.append(self.loadPage)

	def getCookies(self):
		getPage("http://hdfilme.tv/", cookies=ck, agent=glob_agent).addCallback(lambda _:self.loadPage()).addErrback(self.dataError)

	def loadPage(self):
		self.streamList = []
		url = self.url+str(self.page)+"/"
		getPage(url, cookies=ck, agent=glob_agent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		global initCookies
		if initCookies:
			initCookies = False
			return reactor.callLater(5,self.getCookies)

		self.getLastPage(data, '', '>Page.*?of\s*(\d+)')
		movies = re.findall('<a class="th tooltip" data-rel=.*?href="(.*?)" title="(.*?) stream.*?"><img src="(.*?)"', data, re.I)
		if movies:
			for url,title,bild in movies:
				self.streamList.append((decodeHtml(title),url,bild))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self.coverurl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.coverurl)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(hdfilmeStreams, title, url, cover)

class hdfilmeStreams(MPScreen):

	def __init__(self, session, title, url, cover):
		self.movietitle = title
		self.url = url
		self.cover = cover
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
		}, -1)

		self['title'] = Label("HDFilme")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movietitle)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.url, cookies=ck, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		for m in re.finditer(">(Server.*?:)</.*?<a href=.(http://hdfilme\..*?/stream-now/.*?\.html).*?<b>(.*?)</b>", data):
			server, stream, res = m.groups()
			self.streamList.append((server + res, stream))
		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.cover)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url, cookies=ck, agent=glob_agent).addCallback(self.findStream).addErrback(self.dataError)

	def findStream(self, data):
		link = re.search('(http://hdfilme\..*?/player/player.php.link=.*?)"', data)
		if link:
			getPage(link.group(1), cookies=ck, agent=glob_agent).addCallback(self.getStreamUrl).addErrback(self.dataError)
		else:
			self.keyLocked = True

	def getStreamUrl(self, data):
		stream_url = re.search("source src='(.*?)'", data, re.S)
		if stream_url:
			stream_url = stream_url.group(1)
			self.session.open(SimplePlayer, [(self.movietitle, stream_url, self.cover)], showPlaylist=False, ltype='hdfilme', cover=True)
		else:
			self.keyLocked = True
