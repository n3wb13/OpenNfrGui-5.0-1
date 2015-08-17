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

class pornerbrosGenreScreen(MPScreen):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Pornerbros.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.pornerbros.com/tags/"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('<a class="thumb-link"\shref="(.*?)"\stitle="(.*?)".*?original="(.*?)"', data, re.S)
		if Cats:
			for (Url, Title, Image) in Cats:
				self.genreliste.append((Title.title(), Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "http://www.pornerbros.com/videos?sort=date", None))
			self.genreliste.insert(0, ("Most Viewed", "http://www.pornerbros.com/videos?sort=views&time=month", None))
			self.genreliste.insert(0, ("Top Rated", "http://www.pornerbros.com/videos?sort=rating&time=month", None))
			self.genreliste.insert(0, ("New", "http://www.pornerbros.com/videos", None))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornerbrosFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = 'http://www.pornerbros.com/search/?q=%s' % (self.suchString)
			self.session.open(pornerbrosFilmScreen, Link, Name)

class pornerbrosFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Pornerbros.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.streamList = []
		if re.search('\?', self.Link):
			url = "%s&p=%s" % (self.Link, str(self.page))
		else:
			url = "%s?p=%s" % (self.Link, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		self.getLastPage(data, 'contents_paging(.*?)</div>')
		pages = re.search('class="filter\smain">.*?(\d+)\sporn', data, re.S)
		self.lastpage = int(pages.group(1))/28+1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		parse = re.search('porn videos found(.*)', data, re.S)
		if parse:
			Liste = re.findall('data-idmodal="(.*?)".*?href="(.*?)"\sclass="thumb-link"\stitle="(.*?)"\s><div\sclass="thumb"><img\sdata-master="(.*?)".*?"(topHD|bottom)".*?timer"></i>(.*?)</li><li><i\sclass="icon\sicon-eye"></i>(.*?)<', parse.group(1), re.S)
			if Liste:
				for (Idnr, Link, Name, Image, isHD, Runtime, Views) in Liste:
					Views = Views.strip().replace('views','')
					if isHD == "topHD":
						isHD = "HD Stream"
					else:
						isHD = "SD Stream"
					self.streamList.append((decodeHtml(Name), Link, Idnr, Image, isHD, Runtime, Views))
		if len(self.streamList) == 0:
			self.streamList.append((_('No videos found!'), '', '', '', '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 3, 4, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][3]
		quality = self['liste'].getCurrent()[0][4]
		runtime = self['liste'].getCurrent()[0][5]
		views = self['liste'].getCurrent()[0][6]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s\nQuality: %s" % (runtime, views, quality))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		Title = self['liste'].getCurrent()[0][0]
		getPage(Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStreamPage, Title).addErrback(self.dataError)

	def getStreamPage(self, data, Title):
		streamdata = re.findall(' \$\.ajax\(url,\sopts\);.*?\)\((\d+),\s\d+,\s\[(.*?)\]\);', data, re.S)
		if streamdata:
			Link = 'http://tkn.pornerbros.com/%s/desktop/%s' % (streamdata[0][0], streamdata[0][1].replace(',','+'))
			getPage(Link, method='POST', headers={'Origin': 'http://www.pornerbros.com', 'Accept':'application/json, text/javascript, */*'}).addCallback(self.getStreamData, Title).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found"), MessageBoxExt.TYPE_INFO, timeout=5)

	def getStreamData(self, data, Title):
		Stream = re.findall('"token":"(.*?)"', data, re.S)
		if Stream:
			self.session.open(SimplePlayer, [(Title, Stream[-1])], showPlaylist=False, ltype='pornerbros')
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found"), MessageBoxExt.TYPE_INFO, timeout=5)