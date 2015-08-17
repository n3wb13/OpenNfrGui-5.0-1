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

BASE_URL = 'http://www.vkstreamingfilm.biz'

class vkstreamingfilmMain(MPScreen):

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

		self['title'] = Label("VKStreamingFilm")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("New Movies","/films/page/"))
		self.streamList.append(("Action","/films/action/page/"))
		self.streamList.append(("Animation","/films/animation/page/"))
		self.streamList.append(("Arts-Martiaux","/films/arts-martiaux/page/"))
		self.streamList.append(("Aventure","/films/aventure/page/"))
		self.streamList.append(("Biographique","/films/biographique/page/"))
		self.streamList.append(("Comedie","/films/comedie/page/"))
		self.streamList.append(("Danse","/films/danse/page/"))
		self.streamList.append(("Documentaire","/films/documentaire/page/"))
		self.streamList.append(("Drame","/films/drame/page/"))
		self.streamList.append(("Epouvante-Horreur","/films/epouvante-horreur/page/"))
		self.streamList.append(("Espionnage","/films/espionnage/page/"))
		self.streamList.append(("Fantastique","/films/fantastique/page/"))
		self.streamList.append(("Famille","/films/famille/page/"))
		self.streamList.append(("Divers","/films/divers/page/"))
		self.streamList.append(("Guerre","/films/guerre/page/"))
		self.streamList.append(("Historique","/films/historique/page/"))
		self.streamList.append(("Musical","/films/musical/page/"))
		self.streamList.append(("Peplum","/films/peplum/page/"))
		self.streamList.append(("Polcicier","/films/policier/page/"))
		self.streamList.append(("Romance","/films/romance/page/"))
		self.streamList.append(("Science-Fiction","/films/science-fiction/page/"))
		self.streamList.append(("Spectacle","/films/spectacle/page/"))
		self.streamList.append(("Sport","/films/sport/page/"))
		self.streamList.append(("Thriller","/films/thriller/page/"))
		self.streamList.append(("Western","/films/western/page/"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		genre = self['liste'].getCurrent()[0][0]
		url = BASE_URL + self['liste'].getCurrent()[0][1]
		self.session.open(vkstreamingfilmParsing, genre, url)

class vkstreamingfilmParsing(MPScreen, ThumbsHelper):

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
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("VKStreamingFilm")
		self['ContentTitle'] = Label("")
		self['Page'] = Label(_("Page:"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = self.url+str(self.page)+"/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		getLastpage = re.findall('<a href="http://www.vkstreamingfilm.biz/films/.*?page/.*?/">(\d*?)</a>', data, re.S)
		if getLastpage:
			self.lastpage = int(getLastpage[-1])
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self['page'].setText(str(self.page))

		movies = re.findall('<div class="img-block border-2">.*?<img src="(.*?)" alt="(.*?)\sstreaming".*?<a href="(http://www.vkstreamingfilm.*?)" title', data, re.S|re.I)
		if movies:
			for bild,title,url in movies:
				if not bild.startswith('http'):
					bild = BASE_URL + bild
				self.streamList.append((decodeHtml(title),url,bild))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, self.lastpage)
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
		self.session.open(vkstreamingfilmStreams, title, url, cover)

class vkstreamingfilmStreams(MPScreen):

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

		self['title'] = Label("VKStreamingFilm")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movietitle)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		streams = re.findall('<div class="fstory-video-block" id="video.*?">.*?<iframe.*?src="(.*?)"', data, re.S)
		if streams:
			streamcount = 0
			for stream in streams:
				streamcount += 1
				self.streamList.append(("Stream "+str(streamcount), stream))
		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None, None))
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		self.keyLocked = False
		CoverHelper(self['coverArt']).getCover(self.cover)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_url = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(stream_url, self.got_link, False)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.movietitle, stream_url, self.cover)], showPlaylist=False, ltype='vkstreamingfilm', cover=True)