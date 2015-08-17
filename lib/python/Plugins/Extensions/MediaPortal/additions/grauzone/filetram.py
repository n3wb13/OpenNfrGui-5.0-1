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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.pininputext import PinInputExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.additions.porn.x2search4porn import toSearchForPorn

config.mediaportal.filetram_size = ConfigText(default="", fixed_size=False)
config.mediaportal.filetram_sort = ConfigText(default="", fixed_size=False)
config.mediaportal.filetram_hoster = ConfigText(default="all Hosters;0", fixed_size=False)
config.mediaportal.filetram_type = ConfigText(default="Video", fixed_size=False)

hosters =[]

def filetramListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0])
		]

def filetramMultiListEntry(entry):
	if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[2], re.S|re.I):
		premiumFarbe = int(config.mediaportal.premium_color.value, 0)
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 600, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]),
			(eListboxPythonMultiContent.TYPE_TEXT, 650, 0, 65, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]),
			(eListboxPythonMultiContent.TYPE_TEXT, 720, 0, 175, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe)
			]
	else:
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 600, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]),
			(eListboxPythonMultiContent.TYPE_TEXT, 650, 0, 65, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]),
			(eListboxPythonMultiContent.TYPE_TEXT, 720, 0, 175, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2])
			]

def filetramKeywordEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0])
		]

class filetramHelper():

	def keyType(self):
		if self.keyLocked:
			return
		if re.match(".*?2Search4Porn", self.Name):
			return
		if self.type != "Audio":
			self.type = "Audio"
		else:
			self.type = "Video"
		config.mediaportal.filetram_type.value = self.type
		config.mediaportal.filetram_type.save()
		configfile.save()
		self['F4'].setText(self.type)
		self.loadFirstPage()

	def keySize(self):
		if self.keyLocked:
			return
		rangelist = [['any Size', ''], ['Less than 10MB', '6-'], ['10 MB to 100 MB', '7-'], ['100 MB to 1 GB', '8-'], ['Bigger than 1 GB', '9-']]
		self.session.openWithCallback(self.returnSize, ChoiceBoxExt, title=_('Select Size'), list = rangelist)

	def returnSize(self, data):
		if data:
			self.size = data[1]
			config.mediaportal.filetram_size.value = self.size
			config.mediaportal.filetram_size.save()
			configfile.save
			self['F3'].setText(data[0])
			self.loadFirstPage()

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = [['Relevance', '1-'], ['Size', '2-'], ['Date', '3-']]
		self.session.openWithCallback(self.returnSort, ChoiceBoxExt, title=_('Select Sort order'), list = rangelist)

	def returnSort(self,data):
		if data:
			self.sort = data[1]
			config.mediaportal.filetram_sort.value = self.sort
			config.mediaportal.filetram_sort.save()
			configfile.save()
			self['F2'].setText(data[0])
			self.loadFirstPage()

	def keyHoster(self):
		if self.keyLocked:
			return
		rangelist =[]
		for hoster, id in self.hosters:
			rangelist.append([hoster, id])
		rangelist.sort()
		rangelist.insert(0, (['all Hosters', '0']))
		self.session.openWithCallback(self.returnHoster, ChoiceBoxExt, title=_('Select Hoster'), list = rangelist)

	def returnHoster(self, data):
		if data:
			self.hoster = data[1]
			config.mediaportal.filetram_hoster.value = data[0]+";"+data[1]
			config.mediaportal.filetram_hoster.save()
			configfile.save()
			self['F1'].setText(data[0])
			self.loadFirstPage()

	def loadFirstPage(self):
		try:
			self.page = 1
			self.filmliste = []
			self.loadPage()
		except:
			pass

	def errCancelDeferreds(self, error):
		myerror = error.getErrorMessage()
		if myerror:
			raise error

	def dataError(self, error):
		printl(error,self,"E")
		self.keyLocked = False

	def cancelSetValue(self):
		self.hoster = config.mediaportal.filetram_hoster.value.split(";")[1]
		self.sort = config.mediaportal.filetram_sort.value
		self.size = config.mediaportal.filetram_size.value
		self['F1'].setText(config.mediaportal.filetram_hoster.value.split(";")[0])
		rangelist = [['Relevance', '1-'], ['Size', '2-'], ['Date', '3-']]
		for item in rangelist:
			if item[1] == self.sort:
				self['F2'].setText(item[0])
		rangelist = [['any Size', ''], ['Less than 10MB', '6-'], ['10 MB to 100 MB', '7-'], ['100 MB to 1 GB', '8-'], ['Bigger than 1 GB', '9-']]
		for item in rangelist:
			if item[1] == self.size:
				self['F3'].setText(item[0])
		self['F4'].setText(config.mediaportal.filetram_type.value)

class filetramMenueScreen(filetramHelper, MPScreen):

	def __init__(self, session):
		self.Name = "--- Multi Search Engine ---"
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
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"0" : self.closeAll,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"red" : self.keyHoster,
			"green" : self.keySort,
			"yellow" : self.keySize,
			"blue" : self.keyType
		}, -1)

		self.hoster = config.mediaportal.filetram_hoster.value.split(";")[1]
		self.sort = config.mediaportal.filetram_sort.value
		self.size = config.mediaportal.filetram_size.value
		self.type = config.mediaportal.filetram_type.value
		self['title'] = Label("FileTram (BETA)")
		self['ContentTitle'] = Label("%s" % self.Name)
		self['F1'] = Label(config.mediaportal.filetram_hoster.value.split(";")[0])
		self['F4'] = Label(self.type)
		self.keyLocked = True
		self.suchString = ''
		self.hosters = []
		self.pin = False

		self.genreliste = []
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.chooseMenuList

		self.onLayoutFinish.append(self.getHosters)

	def getHosters(self):
		self.cancelSetValue()
		url = "http://filetram.com/a"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadHosters).addErrback(self.dataError)

	def loadHosters(self, data):
		parse = re.search('class="left-group" style="border(.*?)</div>', data, re.S)
		hosterdata = re.findall('<a\shref="/(.*?)/1-0/.">(.*?)</a><br/>', parse.group(1), re.S)
		if hosterdata:
			for (id, hostername) in hosterdata:
				if isSupportedHoster(hostername, True):
					self.hosters.append((hostername, id))
			global hosters
			hosters = self.hosters
		self.genreData()

	def genreData(self):
		self.genreliste.append(("--- Search ---", "callSuchen"))
		self.genreliste.append(("Search using Keyword List", "callKeywordList"))
		if config.mediaportal.showporn.value and config.mediaportal.show2search4porn.value:
			self.genreliste.append(("Search using 2Search4Porn List", "call2SearchList"))
		self.chooseMenuList.setList(map(filetramListEntry, self.genreliste))
		self.chooseMenuList.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Pick = self['liste'].getCurrent()[0][1]
		if config.mediaportal.pornpin.value and not self.pin:
			self.pincheck()
		else:
			if Pick == "callSuchen":
				self.type = config.mediaportal.filetram_type.value
				self.suchen()
			elif Pick == "callKeywordList":
				self.session.openWithCallback(self.cancelSetValue, filetramKeyword, self.type)
			else:
				self.session.openWithCallback(self.cancelSetValue, call2SearchList)

	def SuchenCallback(self, callback = None, entry = None):
		Name = self['liste'].getCurrent()[0][0]
		Pick = self['liste'].getCurrent()[0][1]
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '-')
			self.session.openWithCallback(self.cancelSetValue, filetramListScreen, self.suchString, Name, self.hoster, self.type, self.size, self.sort)

	def pincheck(self):
		self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pincheckok(self, pincode):
		if pincode:
			self.pin = True
			self.keyOK()

class call2SearchList(toSearchForPorn):

	def keyOK(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			search = self['liste'].getCurrent()[0][0].rstrip()
			Name = "2Search4Porn FileTram"
			self.type = "Video"
			self.session.open(filetramListScreen, search, Name, config.mediaportal.filetram_hoster.value.split(";")[1], self.type , config.mediaportal.filetram_size.value, config.mediaportal.filetram_sort.value)

class filetramKeyword(MPScreen):

	def __init__(self, session, type):
		self.type = type
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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyRed,
			"green" : self.keyGreen,
			"yellow" : self.keyYellow
		}, -1)

		self['title'] = Label("FileTram")
		self['name'] = Label("Your Search Requests")
		self['ContentTitle'] = Label("Annoyed, typing in your search-words again and again?")

		self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Add"))
		self['F3'] = Label(_("Edit"))
		self.keyLocked = True
		self.suchString = ''

		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.chooseMenuList

		self.onLayoutFinish.append(self.Searches)

	def Searches(self):
		self.genreliste = []
		self['liste'] = self.chooseMenuList
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_keywords"):
			open(config.mediaportal.watchlistpath.value+"mp_keywords","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_keywords"):
			fobj = open(config.mediaportal.watchlistpath.value+"mp_keywords","r")
			for line in fobj:
				self.genreliste.append((line, None))
			fobj.close()
			self.chooseMenuList.setList(map(filetramKeywordEntry, self.genreliste))
			self.keyLocked = False

	def SearchAdd(self):
		suchString = ""
		self.session.openWithCallback(self.SearchAdd1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True)

	def SearchAdd1(self, suchString):
		if suchString is not None and suchString != "":
			self.genreliste.append((suchString,None))
			self.chooseMenuList.setList(map(filetramKeywordEntry, self.genreliste))

	def SearchEdit(self):
		if len(self.genreliste) > 0:
			suchString = self['liste'].getCurrent()[0][0].rstrip()
			self.session.openWithCallback(self.SearchEdit1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True)

	def SearchEdit1(self, suchString):
		if suchString is not None and suchString != "":
			pos = self['liste'].getSelectedIndex()
			self.genreliste.pop(pos)
			self.genreliste.insert(pos,(suchString,None))
			self.chooseMenuList.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			search = self['liste'].getCurrent()[0][0].rstrip()
			Name = "Keywords FileTram"
			self.session.open(filetramListScreen, search, Name, config.mediaportal.filetram_hoster.value.split(";")[1], self.type , config.mediaportal.filetram_size.value, config.mediaportal.filetram_sort.value)

	def keyRed(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			self.genreliste.pop(self['liste'].getSelectedIndex())
			self.chooseMenuList.setList(map(self._defaultlistcenter, self.genreliste))

	def keyGreen(self):
		if self.keyLocked:
			return
		self.SearchAdd()

	def keyYellow(self):
		if self.keyLocked:
			return
		self.SearchEdit()

	def keyCancel(self):
		if self.keyLocked:
			return
		self.genreliste.sort(key=lambda t : t[0].lower())
		fobj_out = open(config.mediaportal.watchlistpath.value+"mp_keywords","w")
		x = len(self.genreliste)
		if x > 0:
			for c in range(x):
				writeback = self.genreliste[c][0].rstrip()+"\n"
				fobj_out.write(writeback)
			fobj_out.close()
		else:
			os.remove(config.mediaportal.watchlistpath.value+"mp_keywords")
		self.close()

class filetramListScreen(filetramHelper, MPScreen):

	def __init__(self, session, suchString, Name, hoster, type, size, sort):
		self.suchString = suchString
		self.Name = Name
		self.type = type
		self.sort = sort
		self.size = size
		self.hoster = hoster
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"0" : self.closeAll,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"red" : self.keyHoster,
			"green" : self.keySort,
			"yellow" : self.keySize,
			"blue" : self.keyType
		}, -1)

		self['title'] = Label("FileTram")
		self['ContentTitle'] = Label("%s / Search for: %s" % (self.Name, self.suchString))
		self['Page'] = Label(_("Page:"))
		self['F1'] = Label(config.mediaportal.filetram_hoster.value.split(";")[0])
		self['F4'] = Label(self.type)

		self.keyLocked = True
		self.page = 1
		self.lastpage = 100
		self.hosters = hosters

		self.filmliste = []
		self.Cover = ''
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize - 4 * mp_globals.sizefactor))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize)
		self['liste'] = self.chooseMenuList

		self.deferreds = []

		self.ds = defer.DeferredSemaphore(tokens=1)
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.cancelSetValue()
		if re.match(".*?2Search4Porn", self.Name):
			self['F4'].setText("")
		self['page'].setText("%s" % str(self.page))
		if self.hoster == '0':
			self.hoster = ""
		self.keyLocked = True
		self.filmliste = []
		self.chooseMenuList.setList(map(filetramMultiListEntry, self.filmliste))
		self['handlung'].setText('')
		self['name'].setText(_('Please wait...'))
		Url = "%s" % self.suchString.replace(" ", "-")
		if self.type == "Audio":
			ftype = "audio"
		else:
			ftype = "video"
		if self.hoster != '':
			fhoster = self.hoster + "/"
		else:
			fhoster = ''
		farg = self.size + self.sort + str(int(self.page)*10-10)
		for items in self.deferreds:
			items.cancel()
		dsUrl = "http://filetram.com/%s/%s%s/%s" % (ftype, fhoster, farg, Url)
		print dsUrl
		d = self.ds.run(getPage, dsUrl, agent=std_headers, timeout=5, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)
		self.deferreds.append(d)

	def loadPageData(self, data):
		if not "No results containing all your search terms" in data:
			parse = re.search('class="social-container"(.*?)id="directDownloadFrame"', data, re.S)
			Movies = re.findall('class="search-item">.*?href="(.*?)"\stitle="(.*?)".*?class="fs">(.*?)</b>(.*?)</div>.*?Source:\shttp://(.*?)\/', parse.group(1), re.S)
			if Movies:
				for Url, Title, Hostername, Data, Source in Movies:
					Url = "http://filetram.com%s" % Url
					if isSupportedHoster(Hostername, True):
						Ext = re.search('Ext:\s<b>.(.*?)</b>', Data, re.S)
						Size = re.search('File\sSize:\s<b>(.*?)</b>', Data, re.S)
						if Size:
							Size = Size.group(1)
						else:
							Size = ""
						Date = re.search('Created:\s<b>(.*?)</b>', Data, re.S)
						self.filmliste.append((decodeHtml(Title), Url, Hostername, Ext.group(1).lower(), Size, Date.group(1), Source.strip("www.").strip("search.")))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No Files found!"), None, '', '', '', ''))
		self.chooseMenuList.setList(map(filetramMultiListEntry, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Hoster = self['liste'].getCurrent()[0][2]
		Ext = self['liste'].getCurrent()[0][3]
		Size = self['liste'].getCurrent()[0][4]
		Date = self['liste'].getCurrent()[0][5]
		Source = self['liste'].getCurrent()[0][6]
		Handlung = "Extension: %s    Date: %s    Size: %s    Hoster: %s    Source: %s\n%s" % (Ext, Date, Size, Hoster, Source, Title)
		self['name'].setText(Title)
		self['handlung'].setText(Handlung)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		self.keyLocked = True
		getPage(Link, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getHosterLink).addErrback(self.noVideoError).addErrback(self.dataError)

	def getHosterLink(self, data):
		streams = re.search('Copy filesharing links:</div>.*?<textarea.*?>(.*?)</textarea>', data, re.S)
		if streams:
			Hoster = self['liste'].getCurrent()[0][2]
			self.get_redirect(streams.group(1).strip())
		self.keyLocked = False

	def noVideoError(self, error):
		try:
			if error.value.status == '404':
				message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass
		self.keyLocked = False
		raise error

	def keyCancel(self):
		for items in self.deferreds:
			items.cancel()
		self.deferreds = []
		self.close()

	def get_redirect(self, url):
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self.keyLocked = False
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, stream_url)], showPlaylist=False, ltype='filetram')