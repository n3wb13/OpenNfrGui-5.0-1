﻿# -*- coding: utf-8 -*-
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

SERIES_BASE_URL = "http://bs.to"
COVER_BASE_URL = "http://s.bs.to"

class bsMain(MPScreen):

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

		self['title'] = Label("Burning-seri.es")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("Neueste Episoden","last"))
		self.streamList.append(("Serien von A-Z","serien"))
		self.streamList.append(("Watchlist","watchlist"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][1]
		if auswahl == "serien":
			self.session.open(bsSerien)
		elif auswahl == "watchlist":
			self.session.open(bsWatchlist)
		elif auswahl == "last":
			self.session.open(bsLast)

class bsSerien(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self.numericalTextInput = NumericalTextInput()
		self.numericalTextInput.setUseableChars(u'1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"green" : self.keyAdd,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -2)

		self["actions2"] = NumberActionMap(["NumberActions", "InputAsciiActions"], {
			"1": self.goToLetter,
			"2": self.goToLetter,
			"3": self.goToLetter,
			"4": self.goToLetter,
			"5": self.goToLetter,
			"6": self.goToLetter,
			"7": self.goToLetter,
			"8": self.goToLetter,
			"9": self.goToLetter
		}, -1)

		self['title'] = Label("Burning-seri.es")
		self['ContentTitle'] = Label("Serien A-Z")
		self['F2'] = Label(_("Add to Watchlist"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def goToLetter(self, letter):
		self.keyNumberGlobal(letter, self.streamList)

	def loadPage(self):
		url = SERIES_BASE_URL + "/api/series/"
		twAgentGetPage(url, agent=None, headers=std_headers).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		serien = re.findall('series":"(.*?)","id":"(.*?)"', data, re.S)
		if serien:
			for (Title, ID) in serien:
				serie = ID
				cover = COVER_BASE_URL + "/img/cover/" + ID + ".jpg"
				self.streamList.append((decodeHtml(Title.replace('\/','/')),serie, cover, ID))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Title = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		self.session.open(bsStaffeln, Title, Url)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		muTitle = self['liste'].getCurrent()[0][0]
		muID = self['liste'].getCurrent()[0][1]
		fn = config.mediaportal.watchlistpath.value+"mp_bs_watchlist"
		if not fileExists(fn):
			open(fn,"w").close()
		try:
			writePlaylist = open(fn, "a")
			writePlaylist.write('"%s" "%s"\n' % (muTitle, muID))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass

class bsWatchlist(MPScreen):

	def __init__(self, session):
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
			"red" : self.keyDel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Burning-seri.es")
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		self.streamList = []
		change = 0
		self.wl_path = config.mediaportal.watchlistpath.value+"mp_bs_watchlist"
		try:
			readStations = open(self.wl_path,"r")
			rawData = readStations.read()
			readStations.close()
		except:
			return

		for m in re.finditer('"(.*?)" "(.*?)"', rawData):
			(stationName, stationLink) = m.groups()
			if stationLink.startswith('http'):
				change = 1
				break
			self.streamList.append((stationName, stationLink))

		if change == 1:
			url = SERIES_BASE_URL + "/api/series/"
			twAgentGetPage(url, agent=None, headers=std_headers).addCallback(self.convertPlaylist, rawData).addErrback(self.dataError)
		else:
			self.streamList.sort()
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.showInfos()

	def convertPlaylist(self, seriesdata, rawData):
		seriesdata = decodeHtml(seriesdata)
		try:
			writeTmp = open(self.wl_path,"w")
			for m in re.finditer('"(.*?)" "(.*?)"', rawData):
				(stationName, stationLink) = m.groups()
				if stationLink.startswith('http'):
					stationLink = self.getID(stationName, seriesdata)
					if stationLink:
						writeTmp.write('"%s" "%s"\n' % (stationName, stationLink))
					else:
						writeTmp.write('"%s" "%s"\n' % (stationName + " (N/A)", stationLink))
				else:
					writeTmp.write('"%s" "%s"\n' % (stationName, stationLink))
			writeTmp.close()
		except:
			return
		else:
			self.loadPlaylist()

	def getID(self, name, data):
		print "Searching ID for %s" % name
		ID = re.search('"%s","id":"(.*?)"' % name, data, re.S|re.I)
		if ID:
			print "Found ID (%s) for %s" % (ID.group(1), name)
			return ID.group(1)
		else:
			return False

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		id = self['liste'].getCurrent()[0][1]
		self.coverUrl = COVER_BASE_URL + "/img/cover/%s.jpg" % id
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		serienTitle = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		self.session.open(bsStaffeln, serienTitle, auswahl)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		i = self['liste'].getSelectedIndex()
		c = j = 0
		l = len(self.streamList)
		try:
			f1 = open(self.wl_path, 'w')
			while j < l:
				if j != i:
					(stationName, stationLink) = self.streamList[j]
					f1.write('"%s" "%s"\n' % (stationName, stationLink))
				j += 1

			f1.close()
			self.loadPlaylist()
		except:
			pass

class bsLast(MPScreen):

	def __init__(self, session):
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
			"green" : self.keyAdd,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Burning-seri.es")
		self['ContentTitle'] = Label("Neueste Episoden")
		self['F2'] = Label(_("Add to Watchlist"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = "http://bs.e2-mediaportal.so/bs_read.php"
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		last = re.findall('<name>(.*?)</name><id>(.*?)</id>', data, re.S)
		if last:
			for name,id in last:
				name = name.replace('\/','/').replace('\"','"')
				self.streamList.append((decodeHtml(name), id))
			if len(self.streamList) == 0:
				self.streamList.append((_('No seasons found!'), None))
			else:
				self.ml.setList(map(self._defaultlistleft, self.streamList))
				self.keyLocked = False
				self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		id = self['liste'].getCurrent()[0][1]
		self.coverUrl = COVER_BASE_URL + "/img/cover/%s.jpg" % id
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		serienTitle = self['liste'].getCurrent()[0][0]
		id = self['liste'].getCurrent()[0][1]
		epidata = re.findall('S([0-9][0-9])E([0-9][0-9])',serienTitle)
		serienUrl = SERIES_BASE_URL + "/api/series/%s/%s/%s" % (id,epidata[0][0],epidata[0][1])
		self.session.open(bsStreams, serienUrl, self.coverUrl, serienTitle, "", "")

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		muTitle = self['liste'].getCurrent()[0][0]
		muID = self['liste'].getCurrent()[0][1]
		stitle =  re.split(' S[0-9][0-9]', muTitle)
		if stitle:
			fn = config.mediaportal.watchlistpath.value+"mp_bs_watchlist"
			if not fileExists(fn):
				open(fn,"w").close()
			try:
				writePlaylist = open(fn, "a")
				writePlaylist.write('"%s" "%s"\n' % (stitle[0], muID))
				writePlaylist.close()
				message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)
			except:
				pass

class bsStaffeln(MPScreen):

	def __init__(self, session, Title, Url):
		self.Url = SERIES_BASE_URL + "/api/series/" + Url
		self.Title = Title
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
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("Burning-seri.es")
		self['ContentTitle'] = Label(_("Season Selection"))
		self['name'] = Label(self.Title)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = self.Url + "/1"
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		desc = re.search('description":"(.*?)","', data, re.S)
		if desc:
			self['handlung'].setText(decodeHtml(desc.group(1).replace('\\"','"')))
		else:
			self['handlung'].setText(_("No information found."))
		ID = re.search('"id":"(.*?)"', data, re.S)
		cover = COVER_BASE_URL + "/img/cover/" + ID.group(1) + ".jpg"
		movies = re.search('movies":"(.*?)"', data, re.S)
		if movies:
			movies = int(movies.group(1))
			if movies > 0:
				Staffel = "Staffel 0"
				buildurl = self.Url + "/0"
				self.streamList.append((Staffel,buildurl,cover))
		seasons = re.search('seasons":"(.*?)"', data, re.S)
		if seasons:
			season = int(seasons.group(1))
			for i in range(1,int(season)+1):
				Staffel = "Staffel %s" %i
				buildurl = self.Url + "/%s" %i
				self.streamList.append((Staffel,buildurl,cover))
		if len(self.streamList) == 0:
			self.streamList.append((_('No seasons found!'), None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		staffel = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(bsEpisoden, url, staffel, self.Title, cover)

class bsEpisoden(MPScreen):

	def __init__(self, session, Url, Staffel, Title, Cover):
		self.Url = Url
		self.Staffel = Staffel
		self.Title = Title
		self.Cover = Cover
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
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("Burning-seri.es")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.Title)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		twAgentGetPage(self.Url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.watched_liste = []
		self.mark_last_watched = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_bs_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_bs_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_bs_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_bs_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.watched_liste.append("%s" % (line[0]))
				self.updates_read.close()
		Staffel = self.Staffel.replace('Staffel ','')
		if int(Staffel) < 10:
			Staffel = "S0"+str(Staffel)
		else:
			Staffel = "S"+str(Staffel)
		episoden = re.findall('german":"(.*?)","english":"(.*?)","epi":"(.*?)","watched', data, re.S)
		if episoden:
			Flag = ""
			for (TitleDE, TitleEN, epiID) in episoden:
				if int(epiID) < 10:
					epiID1= "E0"+str(epiID)
				else:
					epiID1= "E"+str(epiID)
				if TitleDE == "":
					Flag = "EN"
					Episode = Staffel + epiID1 + " - " + TitleEN
					check = (decodeHtml(self.Title)) + " - " + Staffel + epiID1 + " - " + (decodeHtml(TitleEN))
				else:
					Flag = "DE"
					Episode = Staffel + epiID1 + " - "  + TitleDE
					check = (decodeHtml(self.Title)) + " - " + Staffel + epiID1 + " - " + (decodeHtml(TitleDE))
				checkname = check
				checkname2 = check.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue')
				if (checkname in self.watched_liste) or (checkname2 in self.watched_liste):
					self.streamList.append((decodeHtml(Episode),epiID,True,Flag))
				else:
					self.streamList.append((decodeHtml(Episode),epiID,False,Flag))
		if len(self.streamList) == 0:
			self.streamList.append((_('No episodes found!'), None, False))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleftmarked, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.Cover)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		epiID = self['liste'].getCurrent()[0][1]
		url = self.Url + "/"
		finalcall = url + epiID
		twAgentGetPage(finalcall).addCallback(self.callInfos).addErrback(self.dataError)

	def callInfos(self, data):
		desc = re.search('description":"(.*?)","', data, re.S)
		if desc:
			self['handlung'].setText(decodeHtml(desc.group(1).replace('\\"','"')))
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		episode = self['liste'].getCurrent()[0][0]
		epiID = self['liste'].getCurrent()[0][1]
		url = self.Url + "/"
		finalcall = url + epiID
		Cover = self.Cover
		Staffel = self.Staffel
		self.session.openWithCallback(self.reloadList, bsStreams, finalcall, Cover, self.Title, episode, Staffel)

	def reloadList(self):
		self.keyLocked = True
		self.loadPage()

class bsStreams(MPScreen):

	def __init__(self, session, serienUrl, Cover, Title, Episode, Staffel):
		self.serienUrl = serienUrl
		self.Cover = Cover
		self.Title = Title
		self.episode = Episode
		self.staffel = Staffel
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
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("Burning-seri.es")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.Title)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		printl(self.serienUrl,self,'E')
		twAgentGetPage(self.serienUrl).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		printl(data,self,'E')
		desc = re.search('description":"(.*?)","', data, re.S)
		if desc:
			self['handlung'].setText(decodeHtml(desc.group(1).replace('\\"','"')))
		else:
			self['handlung'].setText(_("No information found."))
		streams =  re.findall('"hoster":"(.*?)","part":"(.*?)","id":"(.*?)"', data, re.S)
		if streams:
			for (Hoster,Part,ID) in streams:
				Url = SERIES_BASE_URL + "/api/watch/"
				if isSupportedHoster(Hoster, True):
					self.streamList.append((Hoster, ID, Url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.Cover)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		ID = self['liste'].getCurrent()[0][1]
		url = self['liste'].getCurrent()[0][2]
		auswahl = url + ID
		twAgentGetPage(auswahl).addCallback(self.findStream).addErrback(self.dataError)

	def playfile(self, link):
		if not re.search('\S[0-9][0-9]E[0-9][0-9]', self.Title, re.I):
			self.streamname = self.Title + " - " + self.episode
		else:
			self.streamname = self.Title
		if re.search('\sS[0-9][0-9]E[0-9][0-9]', self.streamname) and not re.search('-\sS[0-9][0-9]E[0-9][0-9]', self.streamname):
			new_title = ""
			splits = re.split('(S[0-9][0-9]E[0-9][0-9])', self.streamname, re.I)
			count = 0
			for split in splits:
				if count == 1:
					new_title += "- "
				new_title += split
				count += 1
			self.streamname = new_title

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_bs_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_bs_watched","w").close()
		self.update_liste = []
		leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_bs_watched")
		if not leer == 0:
			self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "r")
			for lines in sorted(self.updates_read.readlines()):
				line = re.findall('"(.*?)"', lines)
				if line:
					self.update_liste.append("%s" % (line[0]))
			self.updates_read.close()
			updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "a")
			check = ("%s" % self.streamname)
			if not check in self.update_liste:
				print "update add: %s" % (self.streamname)
				updates_read2.write('"%s"\n' % (self.streamname))
				updates_read2.close()
			else:
				print "dupe %s" % (self.streamname)
		else:
			updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "a")
			print "update add: %s" % (self.streamname)
			updates_read3.write('"%s"\n' % (self.streamname))
			updates_read3.close()
		self.session.open(SimplePlayer, [(self.streamname, link, self.Cover)], showPlaylist=False, ltype='burningseries', cover=True)

	def findStream(self, data):
		test = re.search('"fullurl":"(.*?)"', data)
		if test:
			get_stream_link(self.session).check_link(test.group(1).replace('\/','/'), self.got_link, False)
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.playfile(stream_url)