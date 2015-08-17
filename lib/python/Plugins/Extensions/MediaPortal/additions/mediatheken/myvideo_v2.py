# -*- coding: utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.mv_client_v12 import Client, mvClient
from Components.ProgressBar import ProgressBar

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
	from Plugins.Extensions.TMDb.plugin import *
	TMDbPresent = True
elif fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
	TMDbPresent = False
	IMDbPresent = True
	from Plugins.Extensions.IMDb.plugin import *
else:
	IMDbPresent = False
	TMDbPresent = False

MV2_Version = "MyVideo.de v1.21"
MV2_siteEncoding = 'utf-8'
MV_LOGO = 'file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/powered-by-myvideo.png'

class SearchHelper:

	def __init__(self):
		self.lastSearchNum = -1
		self.searchKey = None
		self["suchtitel"] = Label(_("Search char."))
		self["suchhinweis"] = Label(_("A-Z search"))
		self["suche"] = Label("")
		self["suche"].hide()
		self["suchtitel"].hide()

		self.numericalTextInput = NumericalTextInput()
		self.numericalTextInput.setUseableChars(u'1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
		if mp_globals.isDreamOS:
			self.numericalTextInput.timer_conn = self.numericalTextInput.timer.timeout.connect(self.doSearch)
		else:
			self.numericalTextInput.timer.callback.append(self.doSearch)

		self["search_actions"] = NumberActionMap(["NumberActions", "InputAsciiActions"], {
			"1": self.showSearchkey,
			"2": self.showSearchkey,
			"3": self.showSearchkey,
			"4": self.showSearchkey,
			"5": self.showSearchkey,
			"6": self.showSearchkey,
			"7": self.showSearchkey,
			"8": self.showSearchkey,
			"9": self.showSearchkey
		}, -1)

	def showSearchkey(self, num):
		pass

	def doSearch(self):
		pass

class show_MV2_Genre(MenuHelper, SearchHelper):

	LISTALL = 0

	def __init__(self, session, genre_title=_('Selection'), request_data=None, series_nm=None, connect=True):
		self.genre_title = genre_title
		self.request_data = request_data
		self.series_nm = series_nm
		self.connect = connect
		self.menuData = {}
		self.metadata = {}
		self.page = self.pages = self.pageSize = self.pageCount = 0
		self.param_qr = ''

		if request_data:
			self.widget = request_data.get('widget',{})
			self.listAll = request_data.get('listAll',0)
			self.hasSearchOrders = len(request_data.get('searchOrderArray',''))
		else:
			self.widget = {}
			self.listAll = 0
			self.hasSearchOrders = False

		if self.listAll:
			self.maxSize = 200
		else:
			self.maxSize = 50

		if self.widget and self.widget.get('type', '') == 'alphanumeric':
			self.filterData = {
				u'filterData': [
						{
							u'searchWord':"",
							u'searchType':self.widget.get('searchType',0)
						}
					]
				}
		else:
			self.filterData = {}

		widgets_files = ('search_widgets.xml', 'cover_widgets_wide.xml')

		MenuHelper.__init__(self, session, 0, None, None, "", self._defaultlistleft, skin_name='defaultListWideScreen.xml', widgets_files=widgets_files)

		SearchHelper.__init__(self)
		if not self.widget and not self.listAll:
			self["suchhinweis"].hide()

		self["length"] = Label("")
		self['rating5'] = ProgressBar()
		self['rating0'] = Pixmap()

		self["mv_actions"] = ActionMap(['MP_Actions'], {
			"green" : self.searchOrder,
			"blue" :  self.keyTxtPageDown,
			"yellow" :  self.keyTxtPageUp,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label(MV2_Version)
		self['ContentTitle'] = Label(self.genre_title)
		self['handlung'] = ScrollLabel("")
		if self.hasSearchOrders: self['F2'] = Label(_('Search order'))
		self['F3'] = Label('Text-')
		self['F4'] = Label('Text+')
		self['Page'] = Label(_("Page:"))
		self.mh_On_setGenreStrTitle.append((self.showInfos,()))
		self.onFirstExecBegin.append(self.mh_initMenu)
		if connect: self.onClose.append(mvClient.stopSessionTimer)

	def mh_initMenu(self, init=True):
		self.mh_menuListe = []
		self.mh_menuListe.append((_('Please wait...'),None))
		self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
		if self.connect:
			menu=[]
			mvClient.connect(self.session).addCallback(self.cbConnect, menu)
		elif self.request_data and self.request_data['type'] == 'group_video_search':
			self.paraQuery(init)
		elif self.request_data and self.request_data['type'] in ('group_videos', 'videolist'):
			self.getGroupVideos(self.request_data, self.filterData)
		elif self.request_data and self.request_data['type'].startswith('group') or self.request_data['type'] == 'video_charts':
			self.getGroups(self.request_data, self.filterData)
		elif self.request_data and self.request_data['type'] == 'playlist':
			self.getVideolist(self.request_data)

	def cbConnect(self, result, menu):
		self.connect = False
		d = mvClient.requestNavigation()
		d.addCallback(self.getMenus, menu).addErrback(self.dataError)

	def getMenus(self, jsonData, menu):
		d = self.parseMenuGroups(jsonData, menu)
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def extendMenu(self, list, menu):
		return menu + list

	def appendToMenu(self, menu, entry):
		return menu.append(entry)

	def parseMenuGroups(self, jsonData, menu):
		try:
			entry = jsonData["resultList"]
			title0 = entry.get("title","")
		except:
			return self.deferredData(menu)

		self.menuData[title0] = {}
		self.menuData[title0]['listTitle'] = entry.get("listTitle","")
		self.menuData[title0]['id'] = entry.get("id",0)
		self.menuData[title0]['type'] = entry.get("type","")
		self.menuData[title0]['ga_action'] = self.getTrackingInfo(entry, 'ga_action')
		menu.append((0, (self.menuData[title0], ''), str(title0)))

		for entry in jsonData["resultList"]["subNavEntries"]:
			title0 = entry["title"]
			self.menuData[title0] = {}
			ga_action = self.menuData[title0]['ga_action'] = self.getTrackingInfo(entry, 'ga_action')
			menu.append((0, (self.menuData[title0], ''), str(title0)))

			title1 = entry.get("listTitle","")
			if title1:
				self.menuData[title0][title1] = {}
				self.menuData[title0][title1]['listTitle'] = title1
				self.menuData[title0][title1]['id'] = entry.get("id",0)
				self.menuData[title0][title1]['type'] = entry.get("type","")
				self.menuData[title0][title1]['ga_action'] = ga_action
				menu.append((1, (self.menuData[title0][title1], ''), str(title1)))

			for entry2 in entry.get("subNavEntries"):
				title1 = entry2['title']
				self.menuData[title0][title1] = {}
				self.menuData[title0][title1]['listTitle'] = entry2.get("listTitle","")
				self.menuData[title0][title1]['id'] = entry2['id']
				self.menuData[title0][title1]['type'] = entry2['type']
				self.menuData[title0][title1]['searchOrder'] = entry2.get('searchOrder', 0)
				self.menuData[title0][title1]['searchOrderArray'] = entry2.get('searchOrderArray', '')
				self.menuData[title0][title1]['searchFilter'] = entry2.get('searchFilter', '')
				if 'Alle Serien,' in entry2.get('listTitle', '') or title1 == 'Sender':
					listAll = self.menuData[title0][title1]['listAll'] = self.LISTALL
				else:
					listAll = 0

				self.menuData[title0][title1]['ga_action'] = ga_action
				menu.append((1, (self.menuData[title0][title1], ''), str(title1)))

				for filt_entry in entry2.get("filter",""):
					title = filt_entry.get('title', '')
					id = filt_entry.get('id', filt_entry.get('ids', [0])[0])
					widget = filt_entry.get('widget', '')
					if not title or not id:
						if widget:
							self.menuData[title0][title1]['widget'] = widget
						continue

					self.menuData[title0][title1][title] = {}
					self.menuData[title0][title1][title]['listTitle'] = filt_entry.get("listTitle","")
					self.menuData[title0][title1][title]['listAll'] = listAll
					self.menuData[title0][title1][title]['id'] = id
					self.menuData[title0][title1][title]['type'] = filt_entry['type']
					if not self.menuData[title0][title1][title].has_key('searchOrder'): self.menuData[title0][title1][title]['searchOrder'] = filt_entry.get('searchOrder', self.menuData[title0][title1]['searchOrder'])
					self.menuData[title0][title1][title]['searchFilter'] = filt_entry.get('searchFilter', self.menuData[title0][title1]['searchFilter'])
					#self.menuData[title0][title1][title]['icon'] = str(filt_entry.get("icon",""))
					if not self.menuData[title0][title1][title].has_key('searchOrderArray'): self.menuData[title0][title1][title]['searchOrderArray'] = self.menuData[title0][title1]['searchOrderArray']
					self.menuData[title0][title1][title]['ga_action'] = ga_action
					menu.append((2, (self.menuData[title0][title1][title], ''), str(title)))

		entry = jsonData["resultList"]["search"]
		title0 = entry.get("title","")
		self.menuData[title0] = {}
		self.menuData[title0]['id'] = entry.get("id",0)
		self.menuData[title0]['type'] = entry.get("type","")
		self.menuData[title0]['searchOrder'] = entry.get('searchOrder', 0)
		self.menuData[title0]['searchFilter'] = entry.get('searchFilter', '')
		self.menuData[title0]['searchOrderArray'] = entry.get('searchOrderArray', '')
		self.menuData[title0]['ga_action'] = self.getTrackingInfo(entry, 'ga_action')
		menu.append((0, (self.menuData[title0], ''), str(title0)))
		return self.deferredData(menu)

	def getTrackingInfo(self, entry, t_id):
		for infos in entry.get('tracking', ()):
			id = infos.get('id','')
			if id != 'mv_analytics': continue
			return str(infos['param'].get(t_id, ''))

		return ''

	def deferredData(self, data):
		d = defer.Deferred()
		d.callback(data)
		return d

	def parseGroupPlaylist(self, jsonData, lev, menu):
		metadata = jsonData.get("metadata", {})
		resultId = metadata.get("resultId", 0)
		resultSize = metadata.get("resultSize", 0)
		resultCount = metadata.get("resultCount", 0)
		resultOffset = metadata.get("resultOffset", 0)
		resultType = metadata.get("resultType", "")
		if resultCount == 0:
			msg = jsonData.get("returnMessageScreen", None)
			if msg:
				self.session.open(MessageBoxExt, str(msg[0]), type=MessageBoxExt.TYPE_INFO)

			return []

		type = jsonData['type']
		for entry in jsonData.get("resultList", {}):
			menudata = {}
			menudata['id'] = entry["id"]
			menudata['playListID'] = entry.get("playListID",0)
			menudata['movieCount'] = entry.get("movieCount",0)
			menudata['image'] = str(entry["preview"])
			menudata['type'] = str(type)
			menudata['length'] = entry.get("length","")
			menudata['rate'] = entry.get("rate","")
			title = entry["title"]
			if type not in ('group_playlists', 'playlist', 'videolist'):
				continue
			menu.append((lev, (menudata, ''), str(title)))

		if (resultOffset+resultSize) < resultCount and self.listAll:
			d = mvClient.requestGroupPlaylists(self.request_data, self.filterData, resultSize, resultOffset+resultSize)
			d.addCallback(self.parseGroupPlaylist, lev, menu).addErrback(self.dataError)
			return d
		else:
			self.metadata.update(metadata)
			self.getLastPage()
			return menu

	def getVideolist(self, request_data):
		d = mvClient.requestVideodetailsPlaylist(request_data, sz=self.maxSize)
		d.addCallback(self.parseVideolist)
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def parseVideolist(self, jsonData, pl_type=False):
		try:
			if not pl_type:
				jsonData = jsonData["resultList"]["videolist"]["init"]
		except:
			self.getLastPage()
			return []

		metadata = jsonData.get("metadata", {})
		resultCount = metadata.get("resultCount", 0)
		if resultCount == 0:
			msg = jsonData.get("returnMessageScreen", None)
			if msg:
				self.session.open(MessageBoxExt, str(msg[0]), type=MessageBoxExt.TYPE_INFO)

			self.getLastPage()
			return []

		clip_type = 4
		menu = None
		while clip_type > 2 and not menu:
			clip_type -= 1
			menu = self.parseVideoDetails(jsonData, (clip_type,))

		if not menu:
			clip_type = (1,5,6)
			menu = self.parseVideoDetails(jsonData, clip_type)

		if clip_type == 3:
			clip_type_nm = ' (%s)' % _('Full length episodes')
		elif clip_type == 2:
			clip_type_nm = ' (%s)' % _('Only Clips')
		else:
			clip_type_nm = ''

		self['ContentTitle'].setText(self.genre_title + clip_type_nm)
		self.metadata.update(metadata)
		self.getLastPage()
		return menu

	def parseVideoDetails(self, jsonData, clip_type):
		menu = []
		for entry in jsonData.get("resultList",[]):
			clipType = entry.get("clipType",-1)
			if clipType in clip_type:
				menudata = {}
				menudata['id'] = entry["id"]
				menudata['playListID'] = entry.get("playListID",0)
				menudata['image'] = str(entry["preview"])
				menudata['type'] = 'video'
				menudata['length'] = entry.get("length","")
				menudata['rate'] = entry.get("rate","")
				desc = entry["description"]
				title = entry["title"]
				menu.append((0, (menudata, str(desc)), str(title)))

		return menu

	def getGroups(self, request_data, filter_data={}):
		d = mvClient.requestGroupPlaylists(request_data, filter_data).addCallback(self.parseGroupPlaylist, 0, [])
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def getCharts(self, request_data):
		d = mvClient.requestHome(request_data).addCallback(self.parseGroupPlaylist, 0, [])
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def getGroupVideos(self, request_data, filter_data={}):
		d = mvClient.requestGroupVideos(request_data, filter_data, sz=self.maxSize).addCallback(self.parseGroupPlaylist, 0, [])
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def searchGroupVideos(self, param_qr):
		self.request_data['searchFilter'][0]['searchWord'] = param_qr
		d = mvClient.requestGroupVideoSearch(self.request_data, sz=20).addCallback(self.parseGroupPlaylist, 0, [])
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def getSeries(self, request_data):
		d = mvClient.requestGroupPlaylists(request_data, sz=self.maxSize)
		d.addCallback(self.parseGroupPlaylist, 0, [])
		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def mh_callGenreListScreen(self):
		request_data = self.mh_genreUrl[self.mh_menuLevel][0]
		if not request_data.has_key('ga_action'):
			request_data['ga_action'] = self.request_data.get('ga_action','')

		if not request_data['type'].endswith('_charts') and request_data['type'].startswith('video'):
			self.session.open(
				MyvideoPlayer,
				self.mh_menuListe,
				self['liste'].getSelectedIndex(),
				playAll = True,
				listTitle = self.genre_title,
				useResume = 'Musik' not in (request_data.get('ga_action',''),)
				)
		else:
			title = request_data.get('listTitle',"")
			if not title: title = self.mh_genreTitle
			self.session.open(show_MV2_Genre, str(title), request_data, self['liste'].getCurrent()[0][0], False)

	def showInfos(self):
		infos = self.mh_genreUrl[self.mh_menuLevel]
		if infos and len(infos) > 1:
			self['handlung'].setText(self.mh_genreUrl[self.mh_menuLevel][1])
			ImageUrl = self.mh_genreUrl[self.mh_menuLevel][0].get('image', MV_LOGO)
			length = self.mh_genreUrl[self.mh_menuLevel][0].get('length', "")
			if not length:
				mc = self.mh_genreUrl[self.mh_menuLevel][0].get('movieCount', 0)
				if mc: length = '%s Videos' % str(mc)

			self['length'].setText(str(length))
			rate = self.mh_genreUrl[self.mh_menuLevel][0].get('rate', 0.0)
			rating = int(100 * round(float(rate) / 5, 2))
			if rating > 100:
				rating = 100
			self['rating5'].setValue(rating)

			CoverHelper(self['coverArt']).getCover(ImageUrl)

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

	def getLastPage(self):
		if not self.pages and self.metadata:
			self.pageSize = resultSize = self.metadata.get("resultSize", 0)
			self.pageCount = resultCount = self.metadata.get("resultCount", 0)
			pages = resultCount // resultSize
			if resultCount % resultSize:
				pages += 1
			self.pages = min(999, pages)
		elif not self.pages:
			self.pages = 1

		self.page = max(self.page, 1)

	def showSearchkey(self, num):
		if self.mh_keyLocked:
			return
		if self.widget or self.listAll:
			self.keyNumberGlobal(num, self.mh_menuListe)
			self.searchKey = self.numericalTextInput.mapping[num][self.numericalTextInput.pos]
			self['suche'].setText(str(self.searchKey))
			if self.lastSearchNum == -1:
				self['suche'].show()
				self["suchtitel"].show()
			self.lastSearchNum = num

	def doSearch(self):
		self.lastSearchNum = -1
		self['suche'].hide()
		self["suchtitel"].hide()
		if self.widget and not self.listAll:
			self.mh_keyLocked = True
			self.filterData['filterData'][0]['searchWord'] = self.searchKey
			self.metadata.clear()
			self.page = self.pages = 0
			self.mh_initMenu(False)

	def paraQuery(self, init=False):
		if init:
			self.param_qr = ''
			self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True)
		else:
			self.searchGroupVideos(self.param_qr)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				self.param_qr = urllib.quote(self.param_qr)
				self.searchGroupVideos(self.param_qr)
		else: self.close()

	def keyPageUp(self):
		if self.mh_keyLocked or not self.page or not self.pages:
			return
		oldpage = self.page
		if self.page < self.pages:
			self.page += 1
			resultOffset = self.metadata.get("resultOffset", 0)
			resultSize = self.pageSize
			resultCount = self.pageCount
			resultOffset += resultSize
			if resultOffset >= resultCount:
				resultOffset -= resultCount

		if oldpage != self.page:
			self.loadNextPageData(resultOffset, resultCount, resultSize)

	def keyPageDown(self):
		if not self.page or not self.pages:
			return
		oldpage = self.page
		if self.page > 1:
			self.page -= 1
			resultOffset = self.metadata.get("resultOffset", 0)
			if self.page < self.pages:
				resultSize = self.pageSize
			else:
				resultSize = self.metadata.get("resultSize", 0)
			resultCount = self.pageCount
			resultOffset -= resultSize
			if resultOffset < 0:
				resultOffset += resultCount

		if oldpage != self.page:
			self.loadNextPageData(resultOffset, resultCount, resultSize)

	def loadNextPageData(self, offset, resultCount, resultSize):
		self.mh_keyLocked = True
		if (self.page * self.pageSize) > resultCount:
			sz = resultCount - (self.page - 1) * self.pageSize
		else: sz = resultSize
		self.mh_menuListe = [(_('Please wait...'),None)]
		self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
		if self.request_data['type'] == 'playlist':
			if self.page > 1:
				d = mvClient.requestPlaylist(self.request_data, sz, offset)
				d.addCallback(self.parseVideolist,pl_type=True).addErrback(self.dataError)
			else: return self.getVideolist(self.request_data)
		else:
			d = mvClient.requestGroupPlaylists(self.request_data, self.filterData, sz, offset)
			d.addCallback(self.parseGroupPlaylist, 0, [])

		d.addCallback(self.mh_genMenu2).addErrback(self.mh_dataError)

	def searchOrder(self):
		if not self.mh_keyLocked and self.hasSearchOrders:
			if len(self.request_data.get('searchOrderArray','')):
				soArray = self.request_data.get('searchOrderArray',{})
			else:
				return

			list = ()
			for item in soArray.iteritems():
				k, v = item
				list += ((str(v), str(k)),)

			if list:
				self.session.openWithCallback(self.cb_searchOrder, ChoiceBoxExt, title=_("Search Order Selection"), list = list)

	def cb_searchOrder(self, answer):
		order = answer and answer[1]
		if order:
			self.mh_keyLocked = True
			self.request_data['searchOrder'] = order
			self.metadata.clear()
			self.page = self.pages = 0
			self.mh_initMenu(False)

class MyvideoPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=False, listTitle=None, useResume=True):
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle, ltype='myvideo2.de', cover=False, useResume=useResume)

	def getVideo(self):
		title = self.playList[self.playIdx][0]
		request_data = self.playList[self.playIdx][1][0]
		if request_data.get('playListID', 0) > 0:
			d = mvClient.requestVideodetailsPlaylist(request_data)
		else:
			d = mvClient.requestVideodetails(request_data)
		d.addCallback(mvClient.getVideodetailsPlaylist)
		d.addCallback(self.getVideodetails, title, request_data).addErrback(self.dataError)

	def getVideodetails(self, url, title, request_data):
		d = mvClient.requestM3U8(url)
		d.addCallback(self.openPlayer, title, request_data).addErrback(self.dataError)

	def openPlayer(self, vurl, title, request_data):
		img = request_data.get('image', MV_LOGO)
		self.playStream(title, str(vurl), imgurl=img)