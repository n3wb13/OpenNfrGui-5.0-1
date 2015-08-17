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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.additions.mediatheken.myvideo import MyvideoPlayer
from Plugins.Extensions.MediaPortal.additions.porn.x2search4porn import toSearchForPorn
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.pininputext import PinInputExt
from cookielib import CookieJar, Cookie

keckse = CookieJar()

config.mediaportal.allucsearch_lang = ConfigText(default="all Languages", fixed_size=False)
config.mediaportal.allucsearch_timerange = ConfigText(default="no Timelimit", fixed_size=False)
config.mediaportal.allucsearch_sort = ConfigText(default="relevance", fixed_size=False)
config.mediaportal.allucsearch_hoster = ConfigText(default="all Hosters", fixed_size=False)

def allucListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0])
		]

def auWatchedMultiListEntry(entry):
	if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[2], re.S|re.I):
		premiumFarbe = int(config.mediaportal.premium_color.value, 0)
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 600, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]),
			(eListboxPythonMultiContent.TYPE_TEXT, 610, 0, 145, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]),
			(eListboxPythonMultiContent.TYPE_TEXT, 760, 0, 135, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe)
			]
	else:
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 600, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]),
			(eListboxPythonMultiContent.TYPE_TEXT, 610, 0, 145, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]),
			(eListboxPythonMultiContent.TYPE_TEXT, 760, 0, 135, mp_globals.fontsize, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2])
			]

class searchallucKeyword(MPScreen):

	def __init__(self, session, title=""):
		#TODO ready for moving searchKeyword to a global class, just like MPScreen.. everyone can use it
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

		self['title'] = Label(title)
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

	def keywordListEntry(self, entry):
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0])
			]

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
			self.chooseMenuList.setList(map(self.keywordListEntry, self.genreliste))
			self.keyLocked = False

	def SearchAdd(self):
		suchString = ""
		self.session.openWithCallback(self.SearchAdd1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True)

	def SearchAdd1(self, suchString):
		if suchString is not None and suchString != "":
			self.genreliste.append((suchString,None))
			self.chooseMenuList.setList(map(self.keywordListEntry, self.genreliste))

	def SearchEdit(self):
		if len(self.genreliste) > 0:
			suchString = self['liste'].getCurrent()[0][0].rstrip()
			self.session.openWithCallback(self.SearchEdit1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True)

	def SearchEdit1(self, suchString):
		if suchString is not None and suchString != "":
			pos = self['liste'].getSelectedIndex()
			self.genreliste.pop(pos)
			self.genreliste.insert(pos,(suchString,None))
			self.chooseMenuList.setList(map(self.keywordListEntry, self.genreliste))

	def keyOK(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			search = self['liste'].getCurrent()[0][0].rstrip()
			self.close(search)

	def keyRed(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			self.genreliste.pop(self['liste'].getSelectedIndex())
			self.chooseMenuList.setList(map(self.keywordListEntry, self.genreliste))

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

class searchAllucHelper():

	def keyTimeRange(self):
		if self.keyLocked:
			return
		rangelist = ['no Timelimit', 'last24h', 'lastweek', 'lastmonth']
		for x in rangelist:
			if self.timeRange == x:
				self.timeRange = rangelist[rangelist.index(x)-len(rangelist)+1]
				break
		config.mediaportal.allucsearch_timerange.value = self.timeRange
		config.mediaportal.allucsearch_timerange.save()
		configfile.save()
		self['F3'].setText(self.timeRange.title())
		self.loadFirstPage()

	def keyLanguage(self):
		if self.keyLocked:
			return
		rangelist = [
					['all Languages', 'all Languages'],
					['German', 'DE'],
					['English', 'EN'],
					['Spanish', 'ES'],
					['French', 'FR'],
					['Italian', 'IT'],
					['Hebrew', 'HE'],
					['Russian', 'RU'],
					['Finnish', 'FI'],
					['Norwegian', 'NO'],
					['Swedish', 'SE'],
					['Turkish', 'TR'],
					['Polish', 'PL'],
					['Slovakian', 'SK'],
					['Czech', 'CZ'],
					['Slovenian', 'SI'],
					['Lithuanian', 'LT'],
					['Latvian', 'LV'],
					['Estonian', 'EE'],
					['Bulgarian', 'BG'],
					['Hungarian', 'HU'],
					['Croatian', 'HR'],
					['Romanian', 'RO']
					]
		self.session.openWithCallback(self.returnLanguage, ChoiceBoxExt, title=_('Select Language'), list = rangelist)

	def returnLanguage(self, data):
		if data:
			self.lang = data[1]
			config.mediaportal.allucsearch_lang.value = self.lang
			config.mediaportal.allucsearch_lang.save()
			configfile.save
			self['F4'].setText(self.lang)
			self.loadFirstPage()

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = ['relevance', 'newlinks']
		for x in rangelist:
			if self.sort == x:
				self.sort = rangelist[rangelist.index(x)-len(rangelist)+1]
				break
		config.mediaportal.allucsearch_sort.value = self.sort
		config.mediaportal.allucsearch_sort.save()
		configfile.save()
		self['F2'].setText(self.sort.title())
		self.loadFirstPage()

	def keyHoster(self):
		if self.keyLocked:
			return
		rangelist =[]
		helper = mp_globals.hosters[1].replace('\\','')
		if not helper:
			return
		rangehelper = list(set(helper.split('|')))
		for x in rangehelper:
			rangelist.append([x])
		rangelist.append((['youtube.com']))
		rangelist.append((['myvideo.de']))
		rangelist.sort()
		rangelist.insert(0, (['all Hosters']))
		self.session.openWithCallback(self.returnHoster, ChoiceBoxExt, title=_('Select Hoster'), list = rangelist)

	def returnHoster(self, data):
		if data:
			self.hoster = data[0]
			config.mediaportal.allucsearch_hoster.value = self.hoster
			config.mediaportal.allucsearch_hoster.save()
			configfile.save()
			self['F1'].setText(self.hoster)
			self.loadFirstPage()

	def keySource(self):
		if self.keyLocked:
			return
		try:
			source = self['liste'].getCurrent()[0][3]
			if self.source[:4] == 'all@':
				self.source = ''
				self['ContentTitle'].setText("Search Streams all")
			elif source == self.source:
				self.source = "all@%s" % source
				self['ContentTitle'].setText("Search Streams all / Source: %s " % self.source)
			elif source != self.source:
				self.source = source
				self['ContentTitle'].setText("Search Streams all / Source: %s " % self.source)
			self.loadFirstPage()
		except:
			print "ERROR searchAlluc keySource"

	def loadFirstPage(self):
		try:
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

class searchAllucMenueScreen(searchAllucHelper, MPScreen):

	def __init__(self, session, mode=False):
		if mode == "porn":
			self.allucPorn = True
		else:
			self.allucPorn = False
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
			"yellow" : self.keyTimeRange,
			"blue" : self.keyLanguage
		}, -1)

		self.timeRange = config.mediaportal.allucsearch_timerange.value
		self.sort = config.mediaportal.allucsearch_sort.value
		self.lang = config.mediaportal.allucsearch_lang.value
		self.hoster = config.mediaportal.allucsearch_hoster.value
		self['title'] = Label("2SearchAlluc (BETA)")
		self['ContentTitle'] = Label("%s / Searchlimit 100!" % self.Name)
		self['F1'] = Label(self.hoster)
		self['F2'] = Label(self.sort.title())
		self['F3'] = Label(self.timeRange.title())
		self['F4'] = Label(self.lang)
		self.keyLocked = True
		self.suchString = ''
		self.pin = False

		self.genreliste = []
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.chooseMenuList

		self.onLayoutFinish.append(self.genreData)

	def pincheck(self):
		self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pincheckok(self, pincode):
		if pincode:
			self.pin = True
			self.keyOK()

	def genreData(self):
		if self.allucPorn:
			self.genreliste.append(("Search for Streams", "callSuchen"))
			self.genreliste.append(("Search for all Streams", "callSuchenall"))
			self.genreliste.append(("Search Streams use 2Search4Porn List", "call2SearchList"))
		else:
			self.genreliste.append(("Search for Streams", "callSuchen"))
			self.genreliste.append(("Search for all Streams", "callSuchenall"))
			self.genreliste.append(("Search using Keyword List", "callKeywordList"))
		self.chooseMenuList.setList(map(allucListEntry, self.genreliste))
		self.chooseMenuList.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Pick = self['liste'].getCurrent()[0][1]
		if config.mediaportal.pornpin.value and not self.allucPorn and not self.pin:
			self.pincheck()
		else:
			if Pick == "callSuchen":
				self.suchen()
			elif Pick == "callSuchenall":
				self.SuchenCallback('')
			elif Pick == "callKeywordList":
				self.session.openWithCallback(self.SuchenCallback, searchallucKeyword, title="SearchAlluc")
			else:
				self.session.openWithCallback(self.cancelSetValue, call2SearchList)

	def SuchenCallback(self, callback = None, entry = None):
		Name = self['liste'].getCurrent()[0][0]
		Pick = self['liste'].getCurrent()[0][1]
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			if not self.allucPorn:
				Link = "%s" % self.suchString
			else:
				Link = "%s+#xxx" % self.suchString
			self.session.openWithCallback(self.cancelSetValue, searchAllucListScreen, Link, Name, self.suchString, self.timeRange, self.lang, self.sort, self.hoster)
		elif Pick != "callSuchen":
			if not self.allucPorn:
				Link = ""
			else:
				Link = "#xxx"
			self.session.openWithCallback(self.cancelSetValue, searchAllucListScreen, Link, Name, '', self.timeRange, self.lang, self.sort, self.hoster)

	def cancelSetValue(self):
		self.hoster = config.mediaportal.allucsearch_hoster.value
		self.sort = config.mediaportal.allucsearch_sort.value
		self.timeRange = config.mediaportal.allucsearch_timerange.value
		self.lang = config.mediaportal.allucsearch_lang.value
		self['F1'].setText(self.hoster)
		self['F2'].setText(self.sort.title())
		self['F3'].setText(self.timeRange.title())
		self['F4'].setText(self.lang)

class call2SearchList(toSearchForPorn):

	def keyOK(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			search = self['liste'].getCurrent()[0][0].rstrip()
			Link = "%s+#xxx" % search
			Name = "2Search4Porn SearchAlluc"
			self.session.open(searchAllucListScreen, Link, Name, search, timeRange=config.mediaportal.allucsearch_timerange.value, lang=config.mediaportal.allucsearch_lang.value, sort=config.mediaportal.allucsearch_sort.value, hoster=config.mediaportal.allucsearch_hoster.value)

class searchAllucListScreen(searchAllucHelper, MPScreen):

	def __init__(self, session, Link, Name, searchfor, timeRange='no Timelimit', lang='all Languages', sort='newlinks', hoster='all Hosters'):
		self.Link = Link.replace(' ', '%20')
		self.Name = Name
		self.timeRange = timeRange
		self.sort = sort
		self.lang = lang
		self.hoster = hoster
		global keckse
		self.source = ''
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self.special_agent = 'Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20131011 Firefox/23.0'
		self.dsUrl = ""
		self.alluc_header = {
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
			'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
			'Accept-Encoding':'gzip, deflate, sdch',
			'Connection':'keep-alive'
			}

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"0" : self.closeAll,
			"8" : self.keySource,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyHoster,
			"green" : self.keySort,
			"yellow" : self.keyTimeRange,
			"blue" : self.keyLanguage
		}, -1)

		self['title'] = Label("2SearchAlluc")
		if searchfor:
			self['ContentTitle'] = Label("%s / Search for: %s" % (self.Name, searchfor))
		else:
			self['ContentTitle'] = Label("%s" % self.Name)
		self['F1'] = Label(self.hoster)
		self['F2'] = Label(self.sort.title())
		self['F3'] = Label(self.timeRange.title())
		self['F4'] = Label(self.lang)

		self.keyLocked = True
		self.autoload = True
		self.getPageProc = 0
		self.filmliste = []
		self.Cover = ''
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize - 4 * mp_globals.sizefactor))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize)
		self['liste'] = self.chooseMenuList

		self.deferreds = []
		self.deferreds2 = []
		self.ds = defer.DeferredSemaphore(tokens=1)
		self.ds2 = defer.DeferredSemaphore(tokens=1)
		self.onLayoutFinish.append(self.loadPage)

	def makeCookie(self, name, value):
		return Cookie(
			version=0,
			name=name,
			value=value,
			port=None,
			port_specified=False,
			domain=".alluc.com",
			domain_specified=True,
			domain_initial_dot=False,
			path="/",
			path_specified=False,
			secure=False,
			expires=None,
			discard=False,
			comment=None,
			comment_url=None,
			rest=None
		)

	def encodeBase16(self, data):
		z=""
		for i in range(0, len(data), 2):
			substring = data[i:i + 2]
			zadd = int(substring, 16)
			z = z + str(zadd) + ","
		subz = z[0:len(z) -1]
		zarray = subz.split(',')
		codestring = ""
		for zeichen in zarray:
			codestring = codestring + unichr(int(zeichen))
		return codestring

	def loadPage(self):
		self.keyLocked = True
		self.getPageProc = 0
		self.filmliste = []
		self.chooseMenuList.setList(map(auWatchedMultiListEntry, self.filmliste))
		self['handlung'].setText('')
		self['name'].setText(_('Please wait...'))
		Url = "%s" % self.Link
		if self.source != '':
			if "all@" == self.source[:4]:
				if Url and Url[0] != "+":
					if "+" in Url:
						Url = "+%s+src:%s" % (Url.split('+', 1)[-1], self.source[4:])
					else:
						Url = "+src:%s" % self.source[4:]
				else:
					Url = "%s+src:%s" % (Url, self.source[4:])
			else:
				Url = "%s+src:%s" % (Url, self.source)
		if self.timeRange != 'no Timelimit':
			Url = "%s+#%s" % (Url,self.timeRange)
		if self.lang != 'all Languages':
			Url = "%s+lang:%s" % (Url, self.lang.lower())
		if self.sort != 'relevance':
			Url = "%s+#%s" % (Url, self.sort)
		if self.hoster != 'all Hosters':
			Url = "%s+host:%s" % (Url, self.hoster)
		if Url:
			if Url[0] == '+':
				Url = Url[1:]
		for items in self.deferreds:
			items.cancel()
		Url = Url.replace('#','%23').replace(':','%3A')
		for getPageNr in range(1,11):
			if getPageNr != 1:
				self.dsUrl = "http://www.alluc.com/stream/%s?page=%s" % (Url, getPageNr)
			else:
				self.dsUrl = "http://www.alluc.com/stream/" + Url
			d = self.ds.run(twAgentGetPage, self.dsUrl, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.loadPageData).addErrback(self.dataError)
			self.deferreds.append(d)
		self.deferreds.append(d)

	def errorNoVideo(self, error):
		try:
			if error.getErrorMessage():
				self.getPageProc += 10
				if self.getPageProc != 100:
					self['Page'].setText("%s%%" % str(self.getPageProc))
				else:
					self['Page'].setText("")
					self.allFinish()
		except:
			pass
		raise error

	def loadPageData(self, data):
		preparse = re.search('<META NAME="robots" CONTENT="noindex,nofollow">', data, re.I)
		if preparse:
			incapsCode = re.search('var b="(.*?)(\s|")', data, re.S)
			if incapsCode:
				self.incapsuPack(data)
			else:
				preparse = re.search('<iframe src="(.*?)"', data, re.S)
				if preparse:
					url = "http://www.alluc.com%s" % preparse.group(1).replace(' ','%20')
					twAgentGetPage(url, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.incapsReset).addErrback(self.dataError)
		else:
			self.findMovieStreams(data)

	def findMovieStreams(self, data):
		preparse = re.search('resultlist(.*?)<div id=(|")sidebar', data, re.S)
		if preparse:
			if preparse.group(1)[0] == '\"':
				regex = '"title"><!--<h2>--><a href="(.*?)".*?_blank">(.*?)<.*?target="_blank">(.*?)</a>\s+-(.*?)</div>.*?_blank">(.*?)<.*?alt="(.*?)"'
			else:
				regex = 'title><a href="(.*?)".*?target=_blank>(.*?)</a>.*?target=_blank>(.*?)</a>\s+-(.*?)</div>.*?target=_blank>(.*?)<.*?alt=(.*?) /></a>'
			Movies = re.findall(regex, preparse.group(1), re.S)
			if Movies:
				for Url, Title, Hostername, SizeDate, Source, Lang in Movies:
					if not re.search("(\.rar|\.zip|\.7z|\.pps|\.png|\.pdf|\.exe|\.jpg)$", Title, re.S):
						Url = "http://www.alluc.com%s" % Url.replace('&amp;','&')
						if isSupportedHoster(Hostername, True) or Hostername == "youtube.com" or Hostername == "myvideo.de":
							SizeDate = SizeDate.split('-')
							if len(SizeDate) == 2:
								Size = SizeDate[0].replace(" ", "")
								Date = SizeDate[1].replace(" ", "")
							else:
								Size = ''
								Date = SizeDate[0].replace(" ", "")
							self.filmliste.append((decodeHtml(Title), Url, Hostername, Source.replace(" ", ""), Size, Date, Lang))
		self.getPageProc += 10
		if self.getPageProc != 100:
			self['Page'].setText("%s%%" % str(self.getPageProc))
		else:
			self['Page'].setText("")
			self.allFinish()
		if len(self.filmliste) > 0:
			self.chooseMenuList.setList(map(auWatchedMultiListEntry, self.filmliste))
			self.keyLocked = False
			if self.autoload:
				self.autoload = False
				self.showInfos()

	def incapsReset(self, data):
		keckse.set_cookie(self.makeCookie("___utmvc", "navigator%3Dobject,navigator.vendor%3DKDE,opera%3DReferenceError%3A%20Can't%20find%20variable%3A%20opera,ActiveXObject%3DReferenceError%3A%20Can't%20find%20variable%3A%20ActiveXObject,navigator.appName%3DNetscape,plugin%3DTypeError%3A%20Undefined%2"))
		allucrandom = random.randrange(1, 100000000000000000)
		url = "http://www.alluc.com/_Incapsula_Resource?SWKMTFSR=1&e=0.%s" % str(allucrandom)
		twAgentGetPage(url, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.incapsulWait).addErrback(self.dataError)

	def incapsuPack(self, data=""):
		incapsCode = re.search('var b="(.*?)(\s|")', data, re.S)
		if incapsCode:
			codestring = self.encodeBase16(incapsCode.group(1))
			if codestring:
				keckse.set_cookie(self.makeCookie("___utmvc", "navigator%3Dobject,navigator.vendor%3DKDE,opera%3DReferenceError%3A%20Can't%20find%20variable%3A%20opera,ActiveXObject%3DReferenceError%3A%20Can't%20find%20variable%3A%20ActiveXObject,navigator.appName%3DNetscape,plugin%3DTypeError%3A%20Undefined%2"))
				SWHANEDL = re.search('.GET.,.(.*?).,false', codestring, re.S)
				SWKMTFSR = re.search('\)\.src\s=\s"(.*?)"', data, re.S)
				if SWKMTFSR:
					SWHANEDL = "http://www.alluc.com%s" % str(SWHANEDL.group(1))
					allucrandom = random.randrange(1, 100000000000000000)
					url = "http://www.alluc.com%s0.%s" % (SWKMTFSR.group(1), str(allucrandom))
					twAgentGetPage(url, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.loadIncapData, SWHANEDL).addErrback(self.dataError)

	def incapsulWait(self,data):
		self.reloadPage()

	def loadIncapData(self, data, nexturl):
		twAgentGetPage(nexturl, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.incapsulWait).addErrback(self.dataError)

	def reloadPage(self, data=None):
		twAgentGetPage(self.dsUrl, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.reloadPageData).addErrback(self.dataError)
	
	def reloadPageData(self, data):
		incapsCode = re.search('var b="(.*?)(\s|")', data, re.S)
		if incapsCode:
			self.incapsuPack(data)
		else:
			self.findMovieStreams(data)

	def allFinish(self):
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), None, '', '', '', ''))
		self.chooseMenuList.setList(map(auWatchedMultiListEntry, self.filmliste))
		self['name'].setText('')
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		for items in self.deferreds2:
			items.cancel()
		self.deferreds2 = []
		if self['liste'].getCurrent()[0][1] != None:
			Title = self['liste'].getCurrent()[0][0]
			Url = self['liste'].getCurrent()[0][1]
			self['name'].setText(Title)
			d = self.ds2.run(twAgentGetPage, Url, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.loadPageInfos).addErrback(self.dataError)
			self.deferreds2.append(d)

	def loadPageInfos(self, data):
		#TODO Image ist auch geschuetzt --- muss nun mit cookie geladen werden. Muesste in CoverLoader und showAsThumbs intigriert werden
		Description = re.search('<td><b>Description</b></td>.*?<td>(.*?)</td>', data, re.S)
		Title = self['liste'].getCurrent()[0][0]
		Hoster = self['liste'].getCurrent()[0][2]
		Source = self['liste'].getCurrent()[0][3]
		Size = self['liste'].getCurrent()[0][4]
		Date = self['liste'].getCurrent()[0][5]
		Lang = self['liste'].getCurrent()[0][6]
		if Description:
			if re.match('.*?alluc.to', Description.group(1)):
				Handlung = 'There is no description for this movie yet'
			else:
				Handlung = decodeHtml(Description.group(1).strip())
		else:
			Handlung = 'No Description found.'
		Handlung = "Language: %s    Date: %s    Size: %s    Hoster: %s    Source: %s\n%s:\n%s" % (Lang.upper(), Date, Size, Hoster, Source, Title, Handlung)
		self['handlung'].setText(Handlung)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		self.keyLocked = True
		twAgentGetPage(Link, cookieJar=keckse, gzip_decoding=True, agent=self.special_agent, headers=self.alluc_header).addCallback(self.getHosterLink).addErrback(self.noVideoError).addErrback(self.dataError)

	def getHosterLink(self, data):
		streams = re.search('linktitleurl.*?<a href="(.*?)"', data, re.S)
		if streams:
			Hoster = self['liste'].getCurrent()[0][2]
			if Hoster == 'youtube.com':
				m2 = re.search('//www.youtube.com/(embed/|v/|watch.v=)(.*?)(\?|" |&amp|\&|$)', streams.group(1))
				if m2:
					Title = self['liste'].getCurrent()[0][0]
					dhVideoId = m2.group(2)
					self.session.open(YoutubePlayer, [(Title, dhVideoId, None)], showPlaylist=False)
			elif Hoster == 'myvideo.de':
				m2 = re.search('//www.myvideo.de/watch/(.*?)/', streams.group(1))
				if not m2:
					m2 = re.search('//www.myvideo.de/serien/.*?(\d+)$', streams.group(1))
				if m2:
					url = "http://www.myvideo.de/dynamic/get_player_video_xml.php?ID=" + m2.group(1)
					Title = self['liste'].getCurrent()[0][0]
					self.session.open(MyvideoPlayer, [(Title, url, m2.group(1), '')])
			else:
				self.get_redirect(streams.group(1).replace('&amp;','&'))
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
		self.close()

	def get_redirect(self, url):
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self.keyLocked = False
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, stream_url)], showPlaylist=False, ltype='searchalluc')