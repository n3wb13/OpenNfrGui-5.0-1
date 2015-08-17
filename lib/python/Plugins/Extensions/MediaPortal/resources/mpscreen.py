﻿# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from debuglog import printlog as printl
from keyboardext import VirtualKeyBoardExt
import mp_globals
from tmdb import *

screenList = []

class MPScreen(Screen):

	if mp_globals.currentskin == "original":
		DEFAULT_LM = 20	# default Left-Margin "original"
	else:
		DEFAULT_LM = 0	# default Left-Margin

	def __init__(self, session, parent = None, *ret_args):
		Screen.__init__(self, session, parent)
		screenList.append((self, ret_args))
		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)
		self.mp_hide = False
		self["mp_specActions"]  = ActionMap(["MP_SpecialActions"], {
			"specTv": self.mp_showHide
		}, -2)

		self["mp_specActions2"]  = ActionMap(["MP_SpecialActions"], {
			"specTmdb" : self.mp_tmdb
		}, -1)

		self['title'] = Label("")
		self['ContentTitle'] = Label("")
		self['name'] = Label("")
		self['F1'] = Label("")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['coverArt'] = Pixmap()
		self['Page'] = Label("")
		self['page'] = Label("")
		self['handlung'] = ScrollLabel("")
		self['VideoPrio'] = Label("")
		self['vPrio'] = Label("")

		self.langoffset = 0

	def mp_showHide(self):
		if not self.mp_hide:
			self.mp_hide = True
			self.hide()
		else:
			self.mp_hide = False
			self.show()

	def close(self, *args):
		Screen.close(self, *args)
		if len(screenList):
			screenList.pop()

	def mp_close(self, *args):
		Screen.close(self, *args)

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		if not re.match('.*?----------------------------------------', title):
			self['name'].setText(title)
		else:
			self['name'].setText('')

	def mp_tmdb(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_title = self['liste'].getCurrent()[0][0]
		self.session.open(MediaPortalTmdbScreen, movie_title)

	def getLastPage(self, data, paginationregex, pageregex='.*>(\d+)<'):
		if paginationregex == '':
			lastp = re.search(pageregex, data, re.S)
			if lastp:
				lastp = lastp.group(1).replace(",","").replace('.','').strip()
				self.lastpage = int(lastp)
			else:
				self.lastpage = 1
		else:
			lastpparse = re.search(paginationregex, data, re.S)
			if lastpparse:
				lastp = re.search(pageregex, lastpparse.group(1), re.S)
				if lastp:
					lastp = lastp.group(1).replace(",","").replace('.','').strip()
					self.lastpage = int(lastp)
				else:
					self.lastpage = 1
			else:
				self.lastpage = 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))

	def keyPageNumber(self):
		self.session.openWithCallback(self.callbackkeyPageNumber, VirtualKeyBoardExt, title = (_("Enter page number")), text = str(self.page), is_dialog=True)

	def callbackkeyPageNumber(self, answer):
		if answer is not None:
			answer = re.findall('\d+', answer)
		else:
			return
		if answer:
			if int(answer[0]) < self.lastpage + 1:
				self.page = int(answer[0])
				self.loadPage()
			else:
				self.page = self.lastpage
				self.loadPage()

	def suchen(self):
		self.session.openWithCallback(self.SuchenCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.suchString, is_dialog=True)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 2:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyLeft(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()
		self.showInfos()

	def keyRight(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()
		self.showInfos()

	def keyUp(self):
		if self.keyLocked:
			return
		self['liste'].up()
		self.showInfos()

	def keyDown(self):
		if self.keyLocked:
			return
		self['liste'].down()
		self.showInfos()

	def keyTxtPageUp(self):
		self['handlung'].pageUp()

	def keyTxtPageDown(self):
		self['handlung'].pageDown()

	def keyCancel(self):
		self.close()

	def keyNumberGlobal(self, key, list):
		unichar = self.numericalTextInput.getKey(key)
		charstr = unichar.encode("utf-8")
		if len(charstr) == 1:
			print "keyNumberGlobal:", charstr[0]
			self.getListIndex(charstr[0], list)

	def getListIndex(self, letter, list):
		if len(list) > 0:
			countIndex = -1
			found = False
			for x in list:
				countIndex += 1
				if len(x[0]) > 1:
					if x[0][0].lower() == letter.lower():
						found = True
						break
				else:
					if x[0][0].lower() == letter.lower():
						found = True
						break
			print "index:", countIndex
			if found:
				self['liste'].moveToIndex(countIndex)

	def dataError(self, error):
		from debuglog import printlog as printl
		printl(error,self,"E")

	@staticmethod
	def closeAll():
		i = len(screenList)
		while i > 0:
			screen, args = screenList.pop()
			screen.mp_close(*args)
			i -= 1

####### defaults
	def _defaultlistleft(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def _defaultlistcenter(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]))
		return res

	def _defaultlistleftmarked(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]

		plugin_path = mp_globals.pluginPath
		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/images/watched.png" % (skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = "%s/%s/images/watched.png" % (skin_path, mp_globals.skinFallback)
			if not fileExists(path):
				path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/watched.png"

		watched = LoadPixmap(path)
		pwidth = watched.size().width()
		pheight = watched.size().height()
		vpos = round(float((height-pheight)/2))
		if entry[2]:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, watched))

		try:
			if entry[3]:
				iconlng = entry[3]
				path = "%s/%s/images/%s.png" % (skin_path, config.mediaportal.skin.value, iconlng)
				if not fileExists(path):
					path = "%s/%s/images/%s.png" % (skin_path, mp_globals.skinFallback, iconlng)
					if not fileExists(path):
						path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s.png" % iconlng

				lang = LoadPixmap(path)
				lwidth = lang.size().width()
				lheight = lang.size().height()
				vpos = round(float((height-lheight)/2))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, pwidth+50, vpos, lwidth, lheight, lang))
				self.langoffset = lwidth+25
		except:
			pass

		res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50+self.langoffset, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def _defaultlisthoster(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[0], re.S|re.I):
			premiumFarbe = int(config.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]))
		return res
##################

####### simplelist
	def simplelistListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]

		if entry[0] == '1':
			icon_name = "directory.png"
		else:
			icon_name = "playlist.png"

		plugin_path = mp_globals.pluginPath
		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/images/%s" % (skin_path, config.mediaportal.skin.value, icon_name)
		if not fileExists(path):
			path = "%s/%s/images/%s" % (skin_path, mp_globals.skinFallback, icon_name)
			if not fileExists(path):
				path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s" % icon_name

		icon = LoadPixmap(path)
		pwidth = icon.size().width()
		pheight = icon.size().height()
		vpos = round(float((height-pheight)/2))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, icon))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		return res
##################

####### kinokiste
	def kinokisteFilmLetterListEntry(entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width - 320, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 310, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 150, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
		return res
##################

####### pornhub
	def pornhubPlayListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width - 210, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Videos: " + entry[1]))
		return res

	def pornhubPornstarListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Rank: " + entry[3]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 160, 0, width - 370, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Videos: " + entry[4]))
		return res
##################

####### kinox
	def kinoxlistleftflagged(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]

		plugin_path = mp_globals.pluginPath
		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		try:
			if entry[3]:
				if entry[3] == '1' or entry[3] == '/img/us_ger_small.png':
					iconlng = '1'
				elif entry[3] == '2' or entry[3] == '/img/us_flag_small.png':
					iconlng = '2'
				elif entry[3] == '5' or entry[3] == '/img/flag_spain.gif':
					iconlng = '5'
				elif entry[3] == '6' or entry[3] == '/img/flag_france.gif':
					iconlng = '6'
				elif entry[3] == '8' or entry[3] == '/img/flag_japan.gif':
					iconlng = '8'
				elif entry[3] == '11' or entry[3] == '/img/flag_italy.gif':
					iconlng = '11'
				elif entry[3] == '15':
					iconlng = '15'
				elif entry[3] == '24' or entry[3] == '/img/flag_greece.gif':
					iconlng = '24'
				elif entry[3] == '25':
					iconlng = 'RU'
				elif entry[3] == '26':
					iconlng = 'IN'
				else:
					iconlng = entry[3]

				path = "%s/%s/images/%s.png" % (skin_path, config.mediaportal.skin.value, iconlng)
				if not fileExists(path):
					path = "%s/%s/images/%s.png" % (skin_path, mp_globals.skinFallback, iconlng)
					if not fileExists(path):
						path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s.png" % iconlng

				lang = LoadPixmap(path)
				lwidth = lang.size().width()
				lheight = lang.size().height()
				vpos = round(float((height-lheight)/2))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, lwidth, lheight, lang))
				self.langoffset = lwidth+25
		except:
			pass

		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.langoffset+25, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def kxStreamListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[0], re.S|re.I):
			premiumFarbe = int(config.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 250, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 340, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 180, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 250, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 340, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 180, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4]))
		return res

	def kxListSearchEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 120, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 130, 0, width - 130, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res
##################

####### streamit
	def streamitFilmListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 210 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200 - 2 * self.DEFAULT_LM, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
		return res

	def streamitStreamListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[0], re.S|re.I):
			premiumFarbe = int(config.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]+entry[2]+entry[3], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]+entry[2]+entry[3]))
		return res
##################

####### topimdb
	def timdbEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 75, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 85, 0, width - 305, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 210, 0, 100, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 100, 0, 100, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
		return res
##################

####### evonic
	def evonicWatchListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+" - "+entry[1]))
		return res
##################

####### ddl.me
	def DDLME_FilmListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 210 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200 - 2 * self.DEFAULT_LM, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4]))
		return res

	def DDLMEStreamListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[0], re.S|re.I):
			premiumFarbe = int(config.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0] + entry[2], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0] + entry[2]))
		return res

	def DDLMEStreamListEntry2(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[0], re.S|re.I):
			premiumFarbe = int(config.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, 220, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, width - 720 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 450 - 2 * self.DEFAULT_LM, 0, 450, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, 250, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, width - 720 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 450 - 2 * self.DEFAULT_LM, 0, 450, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
		return res
##################

####### YouTube
	def ChannelsListEntryLeft(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		return res

	def ChannelsListEntryCenter(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[1]))
		return res

	def YT_ListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if entry[6] == 'R':
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, 160, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], int("0xFF0000", 0)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 170, 0, width - 170 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER,entry[1]))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+entry[1]))
		return res
##################

####### fashiontvguide
	def TvListEntry(self, entry):
		width = self['liste'].instance.size().width()
		self.height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', self.height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, self.height * 2, 0, RT_HALIGN_LEFT, entry[0]+entry[1]))
		return res
##################

####### GEOde
	def GEOdeListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0] + entry[1]))
		return res
##################

####### DOKUH
	def DOKUHStreamListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+entry[3]))
		return res
##################

####### animeworld
	def awListEntry3(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 100, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 110, 0, width - 110, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		return res
##################

####### musicstreamcc
	def show_MSCC_GenreListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]

		if entry[2] == 1:
			icon_name = "musicfolder.png"
		elif entry[2] == 2:
			icon_name = "musiccd.png"

		plugin_path = mp_globals.pluginPath
		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/images/%s" % (skin_path, config.mediaportal.skin.value, icon_name)
		if not fileExists(path):
			path = "%s/%s/images/%s" % (skin_path, mp_globals.skinFallback, icon_name)
			if not fileExists(path):
				path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s" % icon_name

		icon = LoadPixmap(path)
		pwidth = icon.size().width()
		pheight = icon.size().height()
		vpos = round(float((height-pheight)/2))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, icon))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		return res

	def show_MSCC_GenreListEntry2(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		return res

	def show_MSCC_ListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+entry[1]))
		return res
##################

####### songsto
	def songsto_playlist(self, entry):
		if not entry[1] or entry[1] == '':
			title = entry[0]
		else:
			title = entry[1] + ' - ' + entry[0]
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, title))
		return res
##################

####### br_tv
	def BRBody1(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2] + " - " + entry[0]))
		return res
##################

####### allucxxx
	def allucHostersEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		if config.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters, entry[0], re.S|re.I):
			premiumFarbe = int(config.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]+"  Links: "+entry[1], premiumFarbe))
			return res
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]+"  Links: "+entry[1]))
			return res

	def allucSubHostersEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width - 370, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 360, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Rate: "+entry[3]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Hits: "+entry[4]))
		return res
##################

####### siterip
	def siteRipHosterListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		premiumFarbe = int(config.mediaportal.premium_color.value, 0)
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], premiumFarbe))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 210, 0, width - 210, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
		return res
##################

####### heisetv
	def heiseTvGenreListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[4]))
		return res
##################

####### live-stream.tv
	def livestreamtvListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont('mediaportal', height - 2 * mp_globals.sizefactor))
		res = [entry]

		path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/stations/%s.png" % entry[2]
		if fileExists(path):
			icon = LoadPixmap(path)
			pwidth = icon.size().width()
			pheight = icon.size().height()
			vpos = round(float((height-pheight)/2))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 20, vpos, pwidth, pheight, icon))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 50, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res
##################