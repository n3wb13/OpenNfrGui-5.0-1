﻿# -*- coding: utf-8 -*-

import json
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.yt_url import isVEVODecryptor
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

YT_Version = "Youtube Search v3.50"

YT_siteEncoding = 'utf-8'

useProxy = lambda : config.mediaportal.premiumize_use.value and config.mediaportal.sp_use_yt_with_proxy.value

config.mediaportal.yt_param_regionid_idx = ConfigInteger(default = 0)
config.mediaportal.yt_param_time_idx = ConfigInteger(default = 0)
config.mediaportal.yt_param_meta_idx = ConfigInteger(default = 1)
config.mediaportal.yt_paramListIdx = ConfigInteger(default = 0)
config.mediaportal.yt_param_3d_idx = ConfigInteger(default = 0)
config.mediaportal.yt_param_duration_idx = ConfigInteger(default = 0)
config.mediaportal.yt_param_video_definition_idx = ConfigInteger(default = 0)
config.mediaportal.yt_param_event_types_idx = ConfigInteger(default = 0)
config.mediaportal.yt_param_video_type_idx = ConfigInteger(default = 0)
config.mediaportal.yt_refresh_token = ConfigText(default="")

APIKEYV3 = 'AIzaSyBPEkhZzAvfYQZYLmIQcOsklbZbTbymjb0'
param_hl = ('&hl=en_GB', '&hl=de_DE', '&hl=fr_FR', '&hl=it_IT', '')

class youtubeGenreScreen(MenuHelper):
	def __init__(self, session):
		global yt_oauth2

		self.param_qr = ""
		self.param_author = ""
		self.old_mainidx = -1

		self.param_safesearch = ['&safeSearch=none']
		self.param_format = '&format=5'
		self.subCat = [(_('No Category'), '')]
		self.subCat_L2 = [None]

		self.param_time = [
			(_("Date"), "&order=date"),
			(_("Rating"), "&order=rating"),
			(_("Relevance"), "&order="),
			(_("Title"), "&order=title"),
			(_("Video count"), "&order=videoCount"),
			(_("View count"), "&order=viewCount")
			]

		self.param_metalang = [
			(_('English'), '&relevanceLanguage=en'),
			(_('German'), '&relevanceLanguage=de'),
			(_('French'), '&relevanceLanguage=fr'),
			(_('Italian'), '&relevanceLanguage=it'),
			(_('Any'), '')
			]

		self.param_regionid = [
			(_('Whole world'), '&regionCode=US'),
			(_('England'), '&regionCode=GB'),
			(_('Germany'), '&regionCode=DE'),
			(_('France'), '&regionCode=FR'),
			(_('Italy'), '&regionCode=IT')
			]

		self.param_duration = [
			(_('Any'), ''),
			('< 4 Min', '&videoDuration=short'),
			('4..20 Min', '&videoDuration=medium'),
			('> 20 Min', '&videoDuration=long')
			]

		self.param_3d = [
			(_('Any'), ''),
			(_('2D'), '&videoDimension=2d'),
			(_('3D'), '&videoDimension=3d')
			]

		self.param_video_definition = [
			(_('Any'), ''),
			(_('High'), '&videoDefinition=high'),
			(_('Low'), '&videoDefinition=standard')
			]

		self.param_event_types = [
			(_('None'), ''),
			(_('Completed'), '&eventType=completed'),
			(_('Live'), '&eventType=live'),
			(_('Upcoming'), '&eventType=upcoming')
			]

		self.param_video_type = [
			(_('Any'), ''),
			(_('Episode'), '&videoType=episode'),
			(_('Movie'), '&videoType=movie')
			]

		self.paramList = [
			(_('Search request'), (self.paraQuery, None), (0,1,2)),
			(_('Event type'), (self.param_event_types, config.mediaportal.yt_param_event_types_idx), (0,)),
			(_('Sort by'), (self.param_time, config.mediaportal.yt_param_time_idx), (0,1,2)),
			(_('Language'), (self.param_metalang, config.mediaportal.yt_param_meta_idx), (0,1,2,4)),
			(_('Search region'), (self.param_regionid, config.mediaportal.yt_param_regionid_idx), (0,1,2,4)),
			(_('User name'), (self.paraAuthor, None), (0,1,2)),
			(_('3D Search'), (self.param_3d, config.mediaportal.yt_param_3d_idx), (0,)),
			(_('Runtime'), (self.param_duration, config.mediaportal.yt_param_duration_idx), (0,)),
			(_('Video definition'), (self.param_video_definition, config.mediaportal.yt_param_video_definition_idx), (0,)),
			(_('Video type'), (self.param_video_type, config.mediaportal.yt_param_video_type_idx), (0,))
			]

		self.subCatUserChannel = [
			('Start', '/featured?'),
			('Videos', '/videos?'),
			('Playlists', '/playlists?'),
			('Channels', '/channels?')
			]

		self.subCatMusicGenres = [
			('Featured Playlists','https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ/featured?'),
			('All Playlists','https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ/playlists?view=1&sort=lad&'),
			('Genres','https://www.youtube.com/channel/%s/videos?'),
			('All Video Uploads','https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ/videos?')
			]

		self.subCatMusicChannels = [
			('Rap & Hip-Hop', 'UCUnSTiCHiHgZA9NQUG6lZkQ'),
			('Rock', 'UCRZoK7sezr5KRjk7BBjmH6w'),
			('Popmusik', 'UCE80FOXpJydkkMo-BYoJdEg'),
			('Klassische Musik', 'UCLwMU2tKAlCoMSbGQDuiMSg'),
			('Country', 'UClYMFaf6IdjQnZmsnw9N1hQ'),
			('Jazz', 'UC7KZmdQxhcajZSEFLJr3gCg'),
			('Disco', 'UCNGkvx5UwHzqlo6zDgRDYsQ'),
			('Blues', 'UCYlU_M1PLtYZ6qTfKIUlxLQ'),
			('Alternative Rock', 'UCHtUkBSmt4d92XP8q17JC3w'),
			('Soul', 'UCsFaF_3y_L__y8kWAIEhv1w'),
			('Funk', 'UCxk1wRJGOTmzJAbvbQ8VicQ'),
			('R&B', 'UCvwDeZSN2oUHlLWYRLvKceA'),
			('Reggae', 'UCEdvzYtzTH_FFpB3VRjFV6Q'),
			("Children's Music", 'UCMBT_zT5NtEG_3Nn3XSPTxw'),
			('Volksmusic', 'UCbMcht964OUJoeVi9oxFcKg'),
			('Fingerstyle', 'UC63oXoh_yThcEiUmHbAiLiw'),
			('Folk', 'UC9GxgUzRt2qUIII3tSSRjwQ'),
			('Elektronische Musik', 'UCCIPrrom6DIftcrInjeMvsQ'),
			('Lateinamerikanische Musik', 'UCYYsyo5ekR-2Nw10s4mj3pQ'),
			('New Age', 'UCfqBDMEJrevX2_2XBUSxAqg'),
			('K-Pop', 'UCsEonk9fs_9jmtw9PwER9yg'),
			('Afrikanische Musik', 'UCadO807x4w5SAo-KKnQTMcA'),
			('Arabische Musik', 'UCCStUvXbY5TbjDYJD_xKByQ'),
			('Vokalmusik', 'UCrrrTqJSxijC3hIJ-2oL8mw'),
			('Geistliche Musik', 'UCiIRzxB4CUW9vt5js6UFCRQ'),
			('Comedy music', 'UCxKwRTQMME5HahBLLLMMELg'),
			('Music of Asia', 'UCDQ_5Wcc54n1_GrAzf05uWQ'),
			('Weltmusik', 'UCMHQZBr9QGPkACZ4hu2wqbQ'),
			('Elektronische Tanzmusik', 'UCeAIo5P3sKEiuhGn-rExx7Q'),
			('Techno', 'UCQLbTKToYT86oML-jx_DJMA'),
			('Trance', 'UC5d4piMBQlBQRFpS9m_8UZQ'),
			('Indische Musik', 'UC4K4LBy_IQGmQrAQVIa1JlA'),
			('Pop-Rock', 'UCcu0YYUpyosw5_sLnK4wK4A'),
			('Turkish pop music', 'UC7PC8CGB-pU7OJgMGhXIA_g'),
			('Softrock', 'UCFGhkqw3_rCSBTb2_i0P0Zg')
			]
		self.subCatMusicChannels.sort(key=lambda t : t[0].lower())

		self.subCatYourChannel = [
			('Favorites', 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=favorites%'),
			('History', 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=watchHistory%'),
			('Likes', 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=likes%'),
			('New Subscription Videos', 'https://www.googleapis.com/youtube/v3/activities?part=contentDetails%2Csnippet&home=true&access_token=%ACCESSTOKEN%%ACT-upload%'),
			('Playlists', 'https://www.googleapis.com/youtube/v3/playlists?part=snippet%2Cid&mine=true&access_token=%ACCESSTOKEN%'),
			('Recommendations', 'https://www.googleapis.com/youtube/v3/activities?part=contentDetails%2Csnippet&home=true&access_token=%ACCESSTOKEN%%ACT-recommendation%'),
			('Subscriptions', 'https://www.googleapis.com/youtube/v3/subscriptions?part=snippet&mine=true&access_token=%ACCESSTOKEN%'),
			('Uploads', 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=uploads%'),
			('Watch Later', 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=watchLater%')
			]

		self.mainGenres = [
			('Video search', 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=%QR%&type=video&key=%KEY%'),
			('Playlist search', 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=%QR%&type=playlist&key=%KEY%'),
			('Channel search', 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=%QR%&type=channel&key=%KEY%'),
			('Your channel', ''),
			('Guide Categories', 'https://www.googleapis.com/youtube/v3/guideCategories?part=snippet&key=%KEY%'),
			('Favoriten', ''),
			('Beliebt auf YouTube - Deutschland', 'http://www.youtube.com/channel/UCK274iXLZhs8MFGLsncOyZQ'),
			('Sport', 'https://www.youtube.com/channel/UCEgdi0XIXXZ-qJOFPf4JSKw'),
			('KinoCheck', 'https://www.youtube.com/user/KinoCheck'),
			('#Live', 'https://www.youtube.com/channel/UC4R8DWoMoI7CAwX8_LjQHig')
			]
		if useProxy() and isVEVODecryptor:
			self.mainGenres.append(('Youtube Music', ''))
			self.mainGenres.append(('VEVO Music', 'https://www.youtube.com/user/VEVO'))

		MenuHelper.__init__(self, session, 2, None, "", "", self._defaultlistcenter, "ytSearchScreen.xml")

		self["yt_actions"] = ActionMap(["MP_Actions"], {
			"yellow": self.keyYellow,
			"blue": self.login
		}, -1)

		self['title'] = Label(YT_Version)
		self['ContentTitle'] = Label(_("VIDEOSEARCH"))
		self['Query'] = Label(_("Search request"))
		self['query'] = Label()
		self['Time'] = Label(_("Sort by"))
		self['time'] = Label()
		self['Metalang'] = Label(_("Language"))
		self['metalang'] = Label()
		self['Regionid'] = Label(_("Search region"))
		self['regionid'] = Label()
		self['Author'] = Label(_("User name"))
		self['author'] = Label()
		self['Keywords'] = Label(_("Event type"))
		self['keywords'] = Label()
		self['Parameter'] = Label(_("Parameter"))
		self['ParameterToEdit'] = Label()
		self['parametertoedit'] = Label()
		self['3D'] = Label(_("3D Search"))
		self['3d'] = Label()
		self['Duration'] = Label(_("Runtime"))
		self['duration'] = Label()
		self['Reserve1'] = Label(_("Video definition"))
		self['reserve1'] = Label()
		self['Reserve2'] = Label(_("Video type"))
		self['reserve2'] = Label()

		self['F3'] = Label(_("Edit Parameter"))
		self['F4'] = Label(_("Request YT-Token"))

		self.onLayoutFinish.append(self.initSubCat)
		self.mh_On_setGenreStrTitle.append((self.keyYellow, [0]))
		self.onClose.append(self.saveIdx)

		self.channelId = None

	def initSubCat(self):

		hl = param_hl[config.mediaportal.yt_param_meta_idx.value]

		rc = self.param_regionid[config.mediaportal.yt_param_regionid_idx.value][1].split('=')[-1]
		if not rc:
			rc = 'US'

		url = 'https://www.googleapis.com/youtube/v3/videoCategories?part=snippet%s&regionCode=%s&key=%s' % (hl, rc, APIKEYV3)
		twAgentGetPage(url).addCallback(self.parseCats)

	def parseCats(self, data):
		data = json.loads(data)
		self.subCat = [(_('No Category'), '')]
		self.subCat_L2 = [None]
		for item in data.get('items', {}):
			self.subCat.append((str(item['snippet']['title']), '&videoCategoryId=%s' % str(item['id'])))
			self.subCat_L2.append(None)

		self.mh_genreMenu = [
			self.mainGenres,
			[
			self.subCat, None, None, self.subCatYourChannel, None, None, self.subCatUserChannel, self.subCatUserChannel, self.subCatUserChannel, self.subCatUserChannel, self.subCatMusicGenres, self.subCatUserChannel
			],
			[
			self.subCat_L2,
			None,
			None,
			[None,None,None,None,None,None,None,None,None],
			None,
			None,
			[None,None,None,None],
			[None, None, None, None],
			[None, None, None, None],
			[None, None, None, None],
			[None, None, self.subCatMusicChannels, None],
			[None, None, None,None]
			]
			]
		self.mh_loadMenu()

	def paraQuery(self):
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			self.showParams()

	def paraAuthor(self):
		self.session.openWithCallback(self.cb_paraAuthor, VirtualKeyBoardExt, title = (_("Author")), text = self.param_author, is_dialog=True)

	def cb_paraAuthor(self, callback = None, entry = None):
		if callback != None:
			self.param_author = callback.strip()
			self.channelId = None
			self.showParams()

	def showParams(self):
		try:
			self['query'].setText(self.param_qr)
			self['time'].setText(self.param_time[config.mediaportal.yt_param_time_idx.value][0])
			self['reserve1'].setText(self.param_video_definition[config.mediaportal.yt_param_video_definition_idx.value][0])
			self['reserve2'].setText(self.param_video_type[config.mediaportal.yt_param_video_type_idx.value][0])
			self['metalang'].setText(self.param_metalang[config.mediaportal.yt_param_meta_idx.value][0])
			self['regionid'].setText(self.param_regionid[config.mediaportal.yt_param_regionid_idx.value][0])
			self['3d'].setText(self.param_3d[config.mediaportal.yt_param_3d_idx.value][0])
			self['duration'].setText(self.param_duration[config.mediaportal.yt_param_duration_idx.value][0])
			self['author'].setText(self.param_author)
			self['keywords'].setText(self.param_event_types[config.mediaportal.yt_param_event_types_idx.value][0])
		except:
			pass

		self.paramShowHide()

	def paramShowHide(self):
		if self.old_mainidx == self.mh_menuIdx[0]:
			return
		else:
			self.old_mainidx = self.mh_menuIdx[0]

		showCtr = 0
		if self.mh_menuIdx[0] in self.paramList[0][2]:
			self['query'].show()
			self['Query'].show()
			showCtr = 1
		else:
			self['query'].hide()
			self['Query'].hide()

		if self.mh_menuIdx[0] in self.paramList[1][2]:
			self['keywords'].show()
			self['Keywords'].show()
			showCtr = 1
		else:
			self['keywords'].hide()
			self['Keywords'].hide()

		if self.mh_menuIdx[0] in self.paramList[2][2]:
			self['time'].show()
			self['Time'].show()
			showCtr = 1
		else:
			self['time'].hide()
			self['Time'].hide()

		if self.mh_menuIdx[0] in self.paramList[3][2]:
			self['metalang'].show()
			self['Metalang'].show()
			showCtr = 1
		else:
			self['metalang'].hide()
			self['Metalang'].hide()

		if self.mh_menuIdx[0] in self.paramList[4][2]:
			self['regionid'].show()
			self['Regionid'].show()
			showCtr = 1
		else:
			self['regionid'].hide()
			self['Regionid'].hide()

		if self.mh_menuIdx[0] in self.paramList[5][2]:
			self['author'].show()
			self['Author'].show()
			showCtr = 1
		else:
			self['author'].hide()
			self['Author'].hide()

		if self.mh_menuIdx[0] in self.paramList[6][2]:
			self['3d'].show()
			self['3D'].show()
			showCtr = 1
		else:
			self['3d'].hide()
			self['3D'].hide()

		if self.mh_menuIdx[0] in self.paramList[7][2]:
			self['duration'].show()
			self['Duration'].show()
			showCtr = 1
		else:
			self['duration'].hide()
			self['Duration'].hide()

		if self.mh_menuIdx[0] in self.paramList[8][2]:
			self['reserve1'].show()
			self['Reserve1'].show()
			showCtr = 1
		else:
			self['reserve1'].hide()
			self['Reserve1'].hide()

		if self.mh_menuIdx[0] in self.paramList[9][2]:
			self['reserve2'].show()
			self['Reserve2'].show()
			showCtr = 1
		else:
			self['reserve2'].hide()
			self['Reserve2'].hide()

		if showCtr:
			self['F3'].show()
		else:
			self['F3'].hide()

	def mh_loadMenu(self):
		self.showParams()
		self.mh_setMenu(0, True)
		self.mh_keyLocked = False

	def keyYellow(self, edit=1):
		c = len(self.paramList)
		list = []
		if config.mediaportal.yt_paramListIdx.value not in range(0, c):
			config.mediaportal.yt_paramListIdx.value = 0
		old_idx = config.mediaportal.yt_paramListIdx.value
		for i in range(c):
			if self.mh_menuIdx[0] in self.paramList[i][2]:
				list.append((self.paramList[i][0], i))

		if list and edit:
			self.session.openWithCallback(self.cb_handlekeyYellow, ChoiceBoxExt, title=_("Edit Parameter"), list = list, selection=old_idx)
		else:
			self.showParams()

	def cb_handlekeyYellow(self, answer):
		pidx = answer and answer[1]
		if pidx != None:
			config.mediaportal.yt_paramListIdx.value = pidx
			if type(self.paramList[pidx][1][0]) == list:
				self.changeListParam(self.paramList[pidx][0], *self.paramList[pidx][1])
			else:
				self.paramList[pidx][1][0]()
		self.showParams()

	def changeListParam(self, nm, l, idx):
		if idx.value not in range(0, len(l)):
			idx.value = 0

		list = []
		for i in range(len(l)):
			list.append((l[i][0], (i, idx)))

		if list:
			self.session.openWithCallback(self.cb_handleListParam, ChoiceBoxExt, title=_("Edit Parameter") + " '%s'" % nm, list = list, selection=idx.value)

	def cb_handleListParam(self, answer):
		p = answer and answer[1]
		if p != None:
			p[1].value = p[0]
			self.showParams()

	def getUserChannelId(self, usernm, callback):
		url = 'https://www.googleapis.com/youtube/v3/channels?part=id&forUsername=%s&key=%s' % (usernm, APIKEYV3)
		twAgentGetPage(url).addCallback(self.parseChannelId).addCallback(lambda x: callback()).addErrback(self.parseChannelId, True)

	def parseChannelId(self, data, err=False):
		try:
			data = json.loads(data)
			self.channelId = str(data['items'][0]['id'])
		except:
			printl('No CID found.',self,'E')
			self.channelId = 'none'

	def openListScreen(self):
		qr = '&q='+urllib.quote(self.param_qr)
		tm = self.param_time[config.mediaportal.yt_param_time_idx.value][1]
		lr = self.param_metalang[config.mediaportal.yt_param_meta_idx.value][1]
		regionid = self.param_regionid[config.mediaportal.yt_param_regionid_idx.value][1]
		_3d = self.param_3d[config.mediaportal.yt_param_3d_idx.value][1]
		dura = self.param_duration[config.mediaportal.yt_param_duration_idx.value][1]
		vid_def = self.param_video_definition[config.mediaportal.yt_param_video_definition_idx.value][1]
		event_type = self.param_event_types[config.mediaportal.yt_param_event_types_idx.value][1]

		genreurl = self.mh_genreUrl[0] + self.mh_genreUrl[1]
		if 'googleapis.com' in genreurl:
			if '/guideCategories' in genreurl or '/playlists' in genreurl:
				lr = param_hl[config.mediaportal.yt_param_meta_idx.value]

			if not '%ACCESSTOKEN%' in genreurl:
				if self.param_author:
					if not self.channelId:
						return self.getUserChannelId(self.param_author, self.openListScreen)
					else:
						channel_id = '&channelId=%s' % self.channelId
				else: channel_id = ''
				genreurl = genreurl.replace('%QR%', urllib.quote_plus(self.param_qr))
				genreurl += regionid + lr + tm + channel_id + self.param_safesearch[0]
				if 'type=video' in genreurl:
					vid_type = self.param_video_type[config.mediaportal.yt_param_video_type_idx.value][1]
					genreurl += _3d + dura + vid_def + event_type + vid_type

		elif 'Favoriten' in self.mh_genreTitle:
			genreurl = ''
		elif ':Genres' in self.mh_genreTitle:
			genreurl = self.mh_genreUrl[1] % self.mh_genreUrl[2]
		elif 'Sport:' in self.mh_genreTitle or 'Beliebt auf' in self.mh_genreTitle or 'Music:' in self.mh_genreTitle or 'KinoCheck' in self.mh_genreTitle or '#Live' in self.mh_genreTitle:
			genreurl = self.mh_genreUrl[0] + self.mh_genreUrl[1] + self.mh_genreUrl[2]

		self.session.open(YT_ListScreen, genreurl, self.mh_genreTitle)

	def mh_callGenreListScreen(self):
		if 'Your channel' in self.mh_genreTitle:
			if not config.mediaportal.yt_refresh_token.value:
				self.session.open(MessageBoxExt, _("You need to request a token to allow access to your YouTube account."), MessageBoxExt.TYPE_INFO)
				return
		self.openListScreen()

	def login(self):
		if not config.mediaportal.yt_refresh_token.value:
			yt_oauth2.requestDevCode(self.session)
		else:
			self.session.openWithCallback(self.cb_login, MessageBoxExt, _("Did you revoke the access?"), type=MessageBoxExt.TYPE_YESNO, default=False)

	def cb_login(self, answer):
		if answer is True:
			yt_oauth2.requestDevCode(self.session)

	def saveIdx(self):
		config.mediaportal.yt_param_meta_idx.save()
		yt_oauth2._tokenExpired()

class YT_ListScreen(MPScreen, ThumbsHelper):

	param_regionid = (
		('&gl=US'),
		('&gl=GB'),
		('&gl=DE'),
		('&gl=FR'),
		('&gl=IT')
		)

	def __init__(self, session, stvLink, stvGenre, title=YT_Version):
		self.stvLink = stvLink
		self.genreName = stvGenre
		self.headers = std_headers

		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self.favoGenre = self.genreName.startswith('Favoriten')
		self.playlistGenre = 'Playlist feeds' == self.genreName or ':Playlists' in self.genreName
		self.channelGenre =  self.genreName in ('Channel feeds', 'Channel search')
		self.subscriptionGenre = ':Subscriptions' in self.genreName
		self.apiUrl = 'gdata.youtube.com' in self.stvLink
		self.apiUrlv3 = 'googleapis.com' in self.stvLink
		self.musicGenre = 'Music:' in self.genreName
		self.ajaxUrl = '/c4_browse_ajax' in self.stvLink
		self.c4_browse_ajax = ''
		self.url_c4_browse_ajax_list = ['']

		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions","DirectionActions"], {
			"ok" 		: self.keyOK,
			"red"		: self.keyRed,
			"cancel"	: self.keyCancel,
			"5" 		: self.keyShowThumb,
			"up" 		: self.keyUp,
			"down" 		: self.keyDown,
			"right" 	: self.keyRight,
			"left" 		: self.keyLeft,
			"upUp" 		: self.key_repeatedUp,
			"rightUp" 	: self.key_repeatedUp,
			"leftUp" 	: self.key_repeatedUp,
			"downUp" 	: self.key_repeatedUp,
			"upRepeated"	: self.keyUpRepeated,
			"downRepeated"	: self.keyDownRepeated,
			"rightRepeated"	: self.keyRightRepeated,
			"leftRepeated"	: self.keyLeftRepeated,
			"nextBouquet"	: self.keyPageUpFast,
			"prevBouquet"	: self.keyPageDownFast,
			"yellow" 	: self.keyTxtPageUp,
			"blue" 		: self.keyTxtPageDown,
			"green"		: self.keyGreen,
			"0"			: self.closeAll,
			"1" 		: self.key_1,
			"3" 		: self.key_3,
			"4" 		: self.key_4,
			"6" 		: self.key_6,
			"7" 		: self.key_7,
			"9" 		: self.key_9
		}, -1)

		self['title'] = Label(title)

		self['ContentTitle'] = Label(self.genreName)
		if not self.favoGenre:
			self['F2'] = Label(_("Favorite"))
			self['F3'] = Label(_("Text-"))
			self['F4'] = Label(_("Text+"))
		else:
			self['F2'] = Label(_("Delete"))
			self['F3'] = Label(_("Text-"))
			self['F4'] = Label(_("Text+"))

		if ('order=' in self.stvLink) and ('type=video' in self.stvLink) or (self.apiUrl and '/uploads' in self.stvLink):
			self['F1'] = Label(_("Sort by"))
			self.key_sort = True
		else:
			self['F1'] = Label(_("Exit"))
			self.key_sort = False

		self['Page'] = Label(_("Page:"))

		self['coverArt'].hide()
		self.coverHelper = CoverHelper(self['coverArt'])
		self.propertyImageUrl = None
		self.keyLocked = True
		self.baseUrl = "https://www.youtube.com"
		self.lastUrl = None

		self.videoPrio = int(config.mediaportal.youtubeprio.value)
		self.videoPrioS = ['L','M','H']
		self.setVideoPrio()

		self.favo_path = config.mediaportal.watchlistpath.value + "mp_yt_favorites.xml"
		self.keckse = CookieJar()
		self.filmliste = []
		self.start_idx = 1
		self.max_res = int(config.mediaportal.youtube_max_items_pp.value)
		self.max_pages = 1000 / self.max_res
		self.total_res = 0
		self.pages = 0
		self.page = 0
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.load_more_href = None
		self.onClose.append(self.youtubeExit)
		self.modeShowThumb = 1
		self.playAll = True
		self.showCover = False
		self.actType = None

		if not self.apiUrl:
			self.onLayoutFinish.append(self.loadPageData)
		else:
			self.onLayoutFinish.append(self.checkAPICallv2)

	def checkAPICallv2(self):
		m = re.search('/api/users/(.*?)/uploads\?', self.stvLink)
		if m:
			if not m.group(1).startswith('UC'):
				url = 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forUsername=%s&key=%s' % (m.group(1), APIKEYV3)
				return twAgentGetPage(url, agent=None, headers=self.headers).addCallback(self.parsePlaylistId).addErrback(self.dataError)
			else:
				self.apiUrl = False
				self.apiUrlv3 = True
				self.stvLink = 'https://www.googleapis.com/youtube/v3/search?part=snippet&order=date&channelId=%s&key=%s' % (m.group(1), APIKEYV3)

		reactor.callLater(0, self.loadPageData)

	def parsePlaylistId(self, data):
		data = json.loads(data)
		try:
			plid = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
		except:
			printl('No PLID found.',self,'E')
		else:
			self.stvLink = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&order=date&playlistId=%s&key=%s' % (str(plid), APIKEYV3)
			self.apiUrl = False
			self.apiUrlv3 = True

		reactor.callLater(0, self.loadPageData)

	def loadPageData(self):
		self.keyLocked = True
		self.ml.setList(map(self.YT_ListEntry, [(_('Please wait...'),'','','','','','')]))

		if self.favoGenre:
			self.getFavos()
		else:
			url = self.stvLink
			if self.apiUrlv3:
				url = url.replace('%KEY%', APIKEYV3)
				url += "&maxResults=%d" % (self.max_res,)
				if self.c4_browse_ajax:
					url += '&pageToken=' + self.c4_browse_ajax
			elif self.ajaxUrl:
				if not 'paging=' in url:
					url += '&paging=%d' % max(1, self.page)
				url = '%s%s' % (self.baseUrl, url)
			elif self.c4_browse_ajax:
				url = '%s%s' % (self.baseUrl, self.c4_browse_ajax)
			else:
				if url[-1] == '?' or url[-1] == '&':
					url = '%sflow=list' % url
				elif url[-1] != '?' or url[-1] != '&':
					url = '%s&flow=list' % url
				if not '&gl=' in url:
					url += self.param_regionid[config.mediaportal.yt_param_regionid_idx.value]

			self.lastUrl = url
			if self.apiUrlv3 and '%ACT-' in url:
				self.actType = re.search('(%ACT-.*?%)', url).group(1)
				url = url.replace(self.actType, '', 1)
				self.actType = unicode(re.search('%ACT-(.*?)%', self.actType).group(1))

			if '%ACCESSTOKEN%' in url:
				token = yt_oauth2.getAccessToken()
				if not token:
					yt_oauth2.refreshToken(self.session).addCallback(self.getData, url).addErrback(self.dataError)
				else:
					self.getData(token, url)
			else:
				self.getData(None, url)

	def getData(self, token, url):
		if token:
			url = url.replace('%ACCESSTOKEN%', token, 1)
			if '%playlistId=' in url:
				return self.getRelatedUserPL(url, token)
		twAgentGetPage(url, cookieJar=self.keckse, agent=None, headers=self.headers).addCallback(self.genreData).addErrback(self.dataError)

	def getRelatedUserPL(self, url, token):
		pl = re.search('%playlistId=(.*?)%', url).group(1)
		yt_url = re.sub('%playlistId=.*?%', '', url, 1)
		twAgentGetPage(yt_url, cookieJar=self.keckse, agent=None, headers=self.headers).addCallback(self.parseRelatedPL, token, pl).addErrback(self.dataError)

	def parseRelatedPL(self, data, token, pl):
		try:
			data = json.loads(data)
		except:
			pass
		else:
			for item in data.get('items', {}):
				playlist = item['contentDetails']['relatedPlaylists']
				if pl in playlist:
					yt_url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=%s&access_token=%s&order=date' % (str(playlist[pl]), token)
					return twAgentGetPage(yt_url, cookieJar=self.keckse, agent=None, headers=self.headers).addCallback(self.genreData).addErrback(self.dataError)

		reactor.callLater(0, genreData, '')

	def parsePagingUrl(self, data):
		regex = re.compile('data-uix-load-more-href="(.*?)"')
		m = regex.search(data)
		if m:
			if not self.page:
				self.page = 1
			self.c4_browse_ajax = m.group(1).replace('&amp;', '&')
		else:
			if not 'load-more-text' in data:
				self.c4_browse_ajax = ''
				self.pages = self.page

	def parsePagingUrlv3(self, jdata):
		if not self.page:
			self.page = 1
		self.c4_browse_ajax = str(jdata.get('nextPageToken', ''))

	def genreData(self, data):
		if self.apiUrlv3:
			data = json.loads(data)
			self.parsePagingUrlv3(data)

		elif not self.apiUrl:
			try:
				if "load_more_widget_html" in data:
					data = json.loads(data)
					self.parsePagingUrl(data["load_more_widget_html"].replace("\\n","").replace("\\","").encode('utf-8'))
					data = data["content_html"].replace("\\n","").replace("\\","").encode('utf-8')
				else:
					data = json.loads(data)["content_html"].replace("\\n","").replace("\\","").encode('utf-8')
					self.parsePagingUrl(data)
			except:
				self.parsePagingUrl(data)

		elif not self.pages:
			m = re.search('totalResults>(.*?)</', data)
			if m:
				a = int(m.group(1))
				self.pages = a // self.max_res
				if a % self.max_res:
					self.pages += 1
				if self.pages > self.max_pages:
					self.pages = self.max_pages
				self.page = 1

		a = 0
		l = len(data)
		self.filmliste = []
		if self.apiUrlv3:
			listType = re.search('ItemList|subscriptionList|activityList|playlistList|CategoryList', data['kind']) != None
			for item in data.get('items', {}):
				if not listType:
					kind = item['id']['kind']
				else:
					kind = item['kind']
				if kind:
					if 'snippet' in item:
						title = str(item['snippet']['title'])
						if kind.endswith('#video'):
							desc = str(item['snippet']['description'])
							try:
								url = str(item['id']['videoId'])
								img = str(item['snippet']['thumbnails']['default']['url'])
							except:
								pass
							else:
								self.filmliste.append(('', title, url, img, desc, '', ''))
						elif kind.endswith('#playlistItem'):
							desc = str(item['snippet']['description'])
							try:
								url = str(item['snippet']['resourceId']['videoId'])
								img = str(item['snippet']['thumbnails']['default']['url'])
							except:
								pass
							else:
								self.filmliste.append(('', title, url, img, desc, '', ''))
						elif kind.endswith('#channel'):
							desc = str(item['snippet']['description'])
							url = str(item['id']['channelId'])
							img = str(item['snippet']['thumbnails']['default']['url'])
							self.filmliste.append(('', title, url, img, desc, 'CV3', ''))
						elif kind.endswith('#playlist'):
							desc = str(item['snippet']['description'])
							if not listType:
								url = str(item['id']['playlistId'])
							else:
								url = str(item['id'])
							img = str(item['snippet']['thumbnails']['default']['url'])
							self.filmliste.append(('', title, url, img, desc, 'PV3', ''))
						elif kind.endswith('#subscription'):
							desc = str(item['snippet']['description'])
							url = str(item['snippet']['resourceId']['channelId'])
							img = str(item['snippet']['thumbnails']['default']['url'])
							self.filmliste.append(('', title, url, img, desc, 'CV3', ''))
						elif kind.endswith('#guideCategory'):
							desc = ''
							url = str(item['snippet']['channelId'])
							img = ''
							self.filmliste.append(('', title, url, img, desc, 'GV3', ''))
						elif kind.endswith('#activity'):
							desc = str(item['snippet']['description'])
							if item['snippet']['type'] == self.actType:
								try:
									if self.actType == u'upload':
										url = str(item['contentDetails'][self.actType]['videoId'])
									else:
										url = str(item['contentDetails'][self.actType]['resourceId']['videoId'])
									img = str(item['snippet']['thumbnails']['default']['url'])
								except:
									pass
								else:
									self.filmliste.append(('', title, url, img, desc, '', ''))
					elif 'contentDetails' in item:
						details = item['contentDetails']
						if kind.endswith('#channel'):
							if 'relatedPlaylists' in details:
								for k, v in details['relatedPlaylists'].iteritems:
									url = str(v)
									img = ''
									desc = ''
									self.filmliste.append(('', str(k).title(), url, img, desc, 'PV3', ''))

		else:
			data = data.replace('\n', '')
			entrys = None
			list_item_cont = branded_item = shelf_item = yt_pl_thumb = list_item = pl_video_yt_uix_tile = yt_lockup_video = False
			if self.genreName.endswith("Featured Channels") and "branded-page-related-channels-item" in data:
				branded_item = True
				entrys = data.split("branded-page-related-channels-item")
			elif "channels-browse-content-list-item" in data:
				list_item = True
				entrys = data.split("channels-browse-content-list-item")
			elif "browse-list-item-container" in data:
				list_item_cont = True
				entrys = data.split("browse-list-item-container")
			elif re.search('[" ]+shelf-item[" ]+', data):
				shelf_item = True
				entrys = data.split("shelf-item ")
			elif "yt-pl-thumb " in data:
				yt_pl_thumb = True
				entrys = data.split("yt-pl-thumb ")
			elif "pl-video yt-uix-tile " in data:
				pl_video_yt_uix_tile = True
				entrys = data.split("pl-video yt-uix-tile ")
			elif "yt-lockup-video " in data:
				yt_lockup_video = True
				entrys = data.split("yt-lockup-video ")

			if entrys and not self.propertyImageUrl:
				m = re.search('"appbar-nav-avatar" src="(.*?)"', entrys[0])
				property_img = m and m.group(1)
				if property_img:
					if property_img.startswith('//'):
						property_img = 'http:' + property_img
					self.propertyImageUrl = property_img

			if list_item_cont or branded_item or shelf_item or list_item or yt_pl_thumb or pl_video_yt_uix_tile or yt_lockup_video:
				for entry in entrys[1:]:

					if 'data-item-type="V"' in entry:
						vidcnt = '[Paid Content] '
					elif 'data-title="[Private' in entry:
						vidcnt = '[private Video] '
					else:
						vidcnt = ''

					gid = 'S'
					m = re.search('href="(.*?)" class=', entry)
					vid = m and m.group(1).replace('&amp;','&')
					if not vid:
						continue
					if branded_item and not '/SB' in vid:
						continue

					img = title = ''
					if '<span class="" >' in entry:
						m = re.search('<span class="" >(.*?)</span>', entry)
						if m:
							title += decodeHtml(m.group(1))
					elif 'dir="ltr" title="' in entry:
						m = re.search('dir="ltr" title="(.+?)"', entry, re.DOTALL)
						if m:
							title += decodeHtml(m.group(1).strip())
						m = re.search('data-thumb="(.*?)"', entry)
						img = m and m.group(1)
					else:
						m = re.search('dir="ltr".*?">(.+?)</a>', entry, re.DOTALL)
						if m:
							title += decodeHtml(m.group(1).strip())
						m = re.search('data-thumb="(.*?)"', entry)
						img = m and m.group(1)

					if not img:
						img = self.propertyImageUrl

					if img and img.startswith('//'):
						img = 'http:' + img

					desc = ''
					if not vidcnt and 'list=' in vid and not '/videos?' in self.stvLink:
						m = re.search('formatted-video-count-label">\s+<b>(.*?)</b>', entry)
						if m:
							vidcnt = '[%s Videos] ' % m.group(1)
					elif vid.startswith('/watch?'):
						if not vidcnt:
							vid = re.search('v=(.+)', vid).group(1)
							gid = ''
							m = re.search('video-time">(.+?)<', entry)
							if m:
								dura = m.group(1)
								if len(dura)==4:
									vtim = '0:0%s' % dura
								elif len(dura)==5:
										vtim = '0:%s' % dura
								else:
									vtim = dura
								vidcnt = '[%s] ' % vtim

						m = re.search('data-name=.*?>(.*?)</.*?<li>(.*?)</li>\s+</ul>', entry)
						if m:
							desc += 'von ' + decodeHtml(m.group(1)) + ' · ' + m.group(2).replace('</li>', ' ').replace('<li>', '· ') + '\n'

					m = re.search('dir="ltr">(.+?)</div>', entry)

					if (shelf_item or list_item_cont) and not desc and not m:
						m = re.search('shelf-description.*?">(.+?)</div>', entry)

					if m:
						desc += decodeHtml(m.group(1).strip())
						splits = desc.split('<br />')
						desc = ''
						for split in splits:
							if not '<a href="' in split:
								desc += split + '\n'

					if list_item and not vidcnt:
						m = re.search('yt-lockup-meta-info"><li>(.*?)</ul>', entry)
						if m:
							vidcnt = re.sub('<.*?>', '', m.group(1))
							vidcnt = '[%s] ' % vidcnt

					self.filmliste.append((vidcnt, str(title), vid, img, desc, gid, ''))

		reactor.callLater(0, self.checkListe)

	def checkListe(self):
		if len(self.filmliste) == 0:
			self.filmliste.append(('',_('No contents / results found!'),'','','','',''))
			self.keyLocked = True
		else:
			if not self.page:
				self.page = self.pages = 1
			menu_len = len(self.filmliste)
			self.keyLocked = False

		self.ml.setList(map(self.YT_ListEntry, self.filmliste))
		self.th_ThumbsQuery(self.filmliste, 1, 2, 3, None, None, self.page, self.pages, mode=self.modeShowThumb)
		self.showInfos()

	def dataError(self, error):
		self.ml.setList(map(self.YT_ListEntry, [('',_('No contents / results found!'),'','','','','')]))
		self['handlung'].setText("")

	def showInfos(self):
		if self.c4_browse_ajax and not self.pages:
			self['page'].setText("%d" % self.page)
		else:
			self['page'].setText("%d / %d" % (self.page,max(self.page, self.pages)))

		stvTitle = self['liste'].getCurrent()[0][1]
		stvImage = self['liste'].getCurrent()[0][3]
		desc = self['liste'].getCurrent()[0][4]
		self['name'].setText(stvTitle)
		self['handlung'].setText(desc)
		self.coverHelper.getCover(stvImage)

	def youtubeErr(self, error):
		self['handlung'].setText(_("Unfortunately, this video can not be played!\n")+str(error))

	def setVideoPrio(self):
		self.videoPrio = int(config.mediaportal.youtubeprio.value)
		self['vPrio'].setText(self.videoPrioS[self.videoPrio])

	def delFavo(self):

		i = self['liste'].getSelectedIndex()
		c = j = 0
		l = len(self.filmliste)
		try:
			f1 = open(self.favo_path, 'w')
			while j < l:
				if j != i:
					c += 1
					dura = self.filmliste[j][0]
					dhTitle = self.filmliste[j][1]
					dhVideoId = self.filmliste[j][2]
					dhImg = self.filmliste[j][3]
					desc = urllib.quote(self.filmliste[j][4])
					gid = self.filmliste[j][5]
					wdat = '<i>%d</i><n>%s</n><v>%s</v><im>%s</im><d>%s</d><g>%s</g><desc>%s</desc>\n' % (c, dhTitle, dhVideoId, dhImg, dura, gid, desc)
					f1.write(wdat)

				j += 1

			f1.close()
			self.getFavos()

		except IOError, e:
			print "Fehler:\n",e
			print "eCode: ",e
			self['handlung'].setText(_("Error!\n")+str(e))
			f1.close()

	def addFavo(self):
		dhTitle = self['liste'].getCurrent()[0][1]
		dura = self['liste'].getCurrent()[0][0]
		dhImg = self['liste'].getCurrent()[0][3]
		gid = self['liste'].getCurrent()[0][5]
		desc = urllib.quote(self['liste'].getCurrent()[0][4])
		dhVideoId = self['liste'].getCurrent()[0][2]
		if not self.favoGenre and gid in ('S','P','C'):
			dura = ''
			dhTitle = self.genreName + ':' + dhTitle

		try:
			if not fileExists(self.favo_path):
				f1 = open(self.favo_path, 'w')
				f_new = True
			else:
				f_new = False
				f1 = open(self.favo_path, 'a+')

			max_i = 0
			if not f_new:
				data = f1.read()
				for m in re.finditer('<i>(\d*?)</i>.*?<v>(.*?)</v>', data):
					v_found = False
					i, v = m.groups()
					ix = int(i)
					if ix > max_i:
						max_i = ix
					if v == dhVideoId:
						v_found = True
					if v_found:
						f1.close()
						self.session.open(MessageBoxExt, _("Favorite already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
						return

			wdat = '<i>%d</i><n>%s</n><v>%s</v><im>%s</im><d>%s</d><g>%s</g><desc>%s</desc>\n' % (max_i + 1, dhTitle, dhVideoId, dhImg, dura, gid, desc)
			f1.write(wdat)
			f1.close()
			self.session.open(MessageBoxExt, _("Favorite added"), MessageBoxExt.TYPE_INFO, timeout=5)

		except IOError, e:
			print "Fehler:\n",e
			print "eCode: ",e
			self['handlung'].setText(_("Error!\n")+str(e))
			f1.close()

	def getFavos(self):
		self.filmliste = []
		try:
			if not fileExists(self.favo_path):
				f_new = True
			else:
				f_new = False
				f1 = open(self.favo_path, 'r')

			if not f_new:
				data = f1.read()
				f1.close()
				for m in re.finditer('<n>(.*?)</n><v>(.*?)</v><im>(.*?)</im><d>(.*?)</d><g>(.*?)</g><desc>(.*?)</desc>', data):
					n, v, img, dura, gid, desc = m.groups()
					if dura and not dura.startswith('['):
						dura = '[%s] ' % dura.rstrip()
					self.filmliste.append((dura, n, v, img, urllib.unquote(desc), gid, ''))

			if len(self.filmliste) == 0:
				self.pages = self.page = 0
				self.filmliste.append((_('No videos found!'),'','','','','',''))
				self.keyLocked = True
				if not f_new and len(data) > 0:
					os.remove(self.favo_path)

			else:
				self.pages = self.page = 1
				self.keyLocked = False

			self.ml.setList(map(self.YT_ListEntry, self.filmliste))
			self.showInfos()

		except IOError, e:
			print "Fehler:\n",e
			print "eCode: ",e
			self['handlung'].setText(_("Error!\n")+str(e))
			f1.close()

	def changeSort(self):
		list = (
			(_("Date"), ("date", 0)),
			(_("Rating"), ("rating", 1)),
			(_("Relevance"), ("", 2)),
			(_("Title"), ("title", 3)),
			(_("Video count"), ("videoCount", 4)),
			(_("View count"), ("viewCount", 5))
			)
		self.session.openWithCallback(self.cb_handleSortParam, ChoiceBoxExt, title=_("Sort by"), list = list, selection=config.mediaportal.yt_param_time_idx.value)

	def cb_handleSortParam(self, answer):
		p = answer and answer[1]
		if p != None:
			config.mediaportal.yt_param_time_idx.value = p[1]
			self.stvLink = re.sub('order=([a-zA-Z]+)', p[0], self.stvLink)
			self.loadPageData()

	def keyRed(self):
		if not self.key_sort:
			self.keyCancel()
		elif not self.keyLocked:
			self.changeSort()

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.showInfos()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyUp(self):
		if self.keyLocked:
			return
		i = self['liste'].getSelectedIndex()
		if not i:
			self.keyPageDownFast()

		self['liste'].up()
		self.showInfos()

	def keyDown(self):
		if self.keyLocked:
			return
		i = self['liste'].getSelectedIndex()
		l = len(self.filmliste) - 1
		if l == i:
			self.keyPageUpFast()

		self['liste'].down()
		self.showInfos()

	def keyTxtPageUp(self):
		if self.keyLocked:
			return
		self['handlung'].pageUp()

	def keyTxtPageDown(self):
		if self.keyLocked:
			return
		self['handlung'].pageDown()

	def keyPageUpFast(self,step=1):
		if self.keyLocked:
			return
		oldpage = self.page
		if not self.c4_browse_ajax and not self.apiUrlv3:
			if not self.page or not self.pages:
				return
			if (self.page + step) <= self.pages:
				self.page += step
				self.start_idx += self.max_res * step
			else:
				self.page = 1
				self.start_idx = 1
		else:
			self.url_c4_browse_ajax_list.append(self.c4_browse_ajax)
			self.page += 1

		if oldpage != self.page:
			self.loadPageData()

	def keyPageDownFast(self,step=1):
		if self.keyLocked:
			return
		oldpage = self.page
		if not self.c4_browse_ajax and not self.apiUrlv3:
			if not self.page or not self.pages:
				return
			if (self.page - step) >= 1:
				self.page -= step
				self.start_idx -= self.max_res * step
			else:
				self.page = self.pages
				self.start_idx = self.max_res * (self.pages - 1) + 1
		else:
			if self.page == 1:
				return
			self.url_c4_browse_ajax_list.pop()
			self.c4_browse_ajax = self.url_c4_browse_ajax_list[-1]
			self.page -= 1

		if oldpage != self.page:
			self.loadPageData()

	def key_1(self):
		self.keyPageDownFast(2)

	def keyGreen(self):
		if self.keyLocked:
			return
		if self.favoGenre:
			self.delFavo()
		else:
			self.addFavo()

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][2]
		gid = self['liste'].getCurrent()[0][5]
		if gid == 'P' or gid == 'C':
			dhTitle = 'Videos: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			if genreurl.startswith('http'):
				genreurl = genreurl.replace('v=2', '')
			else:
				genreurl = 'https://gdata.youtube.com/feeds/api/playlists/'+self['liste'].getCurrent()[0][2]+'?'
				dhTitle = 'Videos: ' + self['liste'].getCurrent()[0][1]

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif gid == 'CV3':
			dhTitle = 'Ergebnisse: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			genreurl = 'https://www.googleapis.com/youtube/v3/search?part=snippet%2Cid&type=video&order=date&channelId='+self['liste'].getCurrent()[0][2]+'&key=%KEY%'

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif gid == 'GV3':
			dhTitle = 'Ergebnisse: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			hl = param_hl[config.mediaportal.yt_param_meta_idx.value]
			genreurl = 'https://www.googleapis.com/youtube/v3/playlists?part=snippet&channelId='+self['liste'].getCurrent()[0][2]+hl+'&key=%KEY%'

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif gid == 'PV3':
			dhTitle = 'Videos: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			genreurl = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&order=date&playlistId='+self['liste'].getCurrent()[0][2]+'&key=%KEY%'

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif not self.apiUrl or gid == 'S':
			if url.startswith('/playlist?'):
				m = re.search('list=(.+)', url)
				if m:
					url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=%s&order=date&key=' % m.group(1)
					url += '%KEY%'
					dhTitle = 'Playlist: ' + self['liste'].getCurrent()[0][1]
					self.session.open(YT_ListScreen, url, dhTitle)
			elif url.startswith('/user/') or url.startswith('/channel/'):
				url = url.replace('&amp;', '&')
				if '?' in url:
					url += '&'
				else:
					url += '?'
#				url =  self.baseUrl + url + '&flow=list&gl=US'
				url =  self.baseUrl + url
				dhTitle = self.genreName + ':' + self['liste'].getCurrent()[0][1]
				self.session.open(YT_ListScreen, url, dhTitle)
			elif url.startswith('/watch?v='):
				if not 'list=' in url or '/videos?' in self.stvLink:
					url = re.search('v=(.+)', url).group(1)
					listitem = self.filmliste[self['liste'].getSelectedIndex()]
					liste = [(listitem[0], listitem[1], url, listitem[3], listitem[4], listitem[5], listitem[6])]
					self.session.openWithCallback(
						self.setVideoPrio,
						YoutubePlayer,
						liste,
						0,
						playAll = False,
						listTitle = self.genreName,
						plType='local',
						title_inr=1,
						showCover=self.showCover
						)
				else:
					url = re.search('list=(.+)', url).group(1)
					url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=%s&order=date&key=' % url
					url += '%KEY%'
					dhTitle = 'Playlist: ' + self['liste'].getCurrent()[0][1]
					self.session.open(YT_ListScreen, url, dhTitle)
			else:
				self.session.openWithCallback(
					self.setVideoPrio,
					YoutubePlayer,
					self.filmliste,
					self['liste'].getSelectedIndex(),
					playAll = self.playAll,
					listTitle = self.genreName,
					plType='local',
					title_inr=1,
					showCover=self.showCover
					)
		elif not self['liste'].getCurrent()[0][6]:
			self.session.openWithCallback(
				self.setVideoPrio,
				YoutubePlayer,
				self.filmliste,
				self['liste'].getSelectedIndex(),
				playAll = self.playAll,
				listTitle = self.genreName,
				plType='local',
				title_inr=1,
				showCover=self.showCover
				)

	def youtubeExit(self):
		self.keckse.clear()
		del self.filmliste[:]

class YT_Oauth2:
	OAUTH2_URL = 'https://accounts.google.com/o/oauth2'
	CLIENT_ID = 'client_id=322644284204-umqj2oemlr7q2eofu0sv8dff9cvl7c9a.apps.googleusercontent.com'
	CLIENT_SECRET = '&client_secret=dr5Lzk4-VWX7T6PK-dfb21Ic'
	SCOPE = '&scope=https://www.googleapis.com/auth/youtube'
	GRANT_TYPE = '&grant_type=http://oauth.net/grant_type/device/1.0'
	TOKEN_PATH = '/etc/enigma2/mp_yt-access-tokens.json'
	accessToken = None

	def __init__(self):
		import os.path
		self._interval = None
		self._code = None
		self._expiresIn = None
		self._refreshTimer = None
		self.autoRefresh = False
		self.abortPoll = False
		self.waitingBox = None
		self.session = None
		if not config.mediaportal.yt_refresh_token.value:
			self._recoverToken()

	def _recoverToken(self):
		if os.path.isfile(self.TOKEN_PATH):
			with open(self.TOKEN_PATH) as data_file:
				data = json.load(data_file)
				config.mediaportal.yt_refresh_token.value = data['refresh_token'].encode('utf-8')
				config.mediaportal.yt_refresh_token.save()
				return True

	def requestDevCode(self, session):
		self.session = session
		postData = self.CLIENT_ID + self.SCOPE
		twAgentGetPage(self.OAUTH2_URL+'/device/code', method='POST', postdata=postData, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self._cb_requestDevCode, False).addErrback(self._cb_requestDevCode)

	def _cb_requestDevCode(self, data, error=True):
		if error:
			self.session.open(MessageBoxExt, _("Error: Unable to request the Device code"), MessageBoxExt.TYPE_ERROR)
			printl(_("Error: Unable to request the Device code"),self,'E')
			print data
		else:
			googleData = json.loads(data)
			self._interval = googleData['interval']
			self._code = '&code=%s' % googleData['device_code'].encode('utf-8')
			self._expiresIn = googleData['expires_in']
			self.session.openWithCallback(self.cb_request, MessageBoxExt, _("You've to visit:\n{url}\nand enter the code: {code}\nCancel action?").format(url=googleData["verification_url"].encode('utf-8'), code=googleData["user_code"].encode('utf-8')), type = MessageBoxExt.TYPE_YESNO, default = False)

	def cb_request(self, answer):
		if answer is False:
			self.waitingBox = self.session.openWithCallback(self.cb_cancelPoll, MessageBoxExt, _("Waiting for response from the server.\nCancel action?"), type = MessageBoxExt.TYPE_YESNO, default = True, timeout = self._expiresIn - 30)
			self.abortPoll = False
			reactor.callLater(self._interval, self._pollOauth2Server)

	def cb_cancelPoll(self, answer):
		if answer is True:
			self.abortPoll = True

	def _pollOauth2Server(self):
		self._tokenExpired()
		postData = self.CLIENT_ID + self.CLIENT_SECRET + self._code + self.GRANT_TYPE
		twAgentGetPage(self.OAUTH2_URL+'/token', method='POST', postdata=postData, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self._cb_poll, False).addErrback(self._cb_poll)

	def _cb_poll(self, data, error=True):
		if error:
			self.waitingBox.cancel()
			self.session.open(MessageBoxExt, _('Error: Unable to get tokens!'), MessageBoxExt.TYPE_ERROR)
			printl(_('Error: Unable to get tokens!'),self,'E')
			print data
		else:
			try:
				tokenData = json.loads(data)
			except:
				self.waitingBox.cancel()
				self.session.open(MessageBoxExt, _('Error: Unable to get tokens!'), MessageBoxExt.TYPE_ERROR)
				printl('json data error:%s' % str(data),self,'E')
			else:
				if not tokenData.get('error',''):
					self.accessToken = tokenData['access_token'].encode('utf-8')
					config.mediaportal.yt_refresh_token.value = tokenData['refresh_token'].encode('utf-8')
					config.mediaportal.yt_refresh_token.value = tokenData['refresh_token'].encode('utf-8')
					config.mediaportal.yt_refresh_token.save()
					self._expiresIn = tokenData['expires_in']
					self._startRefreshTimer()
					f = open(self.TOKEN_PATH, 'w')
					f.write(json.dumps(tokenData))
					f.close()
					self.waitingBox.cancel()
					self.session.open(MessageBoxExt, _('Access granted :)\nFor safety you should create backup\'s of enigma2 settings and \'/etc/enigma2/mp_yt-access-tokens.json\'.\nThe tokens are valid until they are revoked in Your Google Account.'), MessageBoxExt.TYPE_INFO)
				elif not self.abortPoll:
					print tokenData.get('error','').encode('utf-8')
					reactor.callLater(self._interval, self._pollOauth2Server)

	def refreshToken(self, session, skip=False):
		self.session = session
		if not skip:
			self._tokenExpired()
		if config.mediaportal.yt_refresh_token.value:
			postData = self.CLIENT_ID + self.CLIENT_SECRET + '&refresh_token=%s&grant_type=refresh_token' % config.mediaportal.yt_refresh_token.value

			d = twAgentGetPage(self.OAUTH2_URL+'/token', method='POST', postdata=postData, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self._cb_refresh, False).addErrback(self._cb_refresh)
			return d

	def _cb_refresh(self, data, error=True):
		if error:
			printl(_('Error: Unable to refresh token!'),self,'E')
			print data
			return data
		else:
			try:
				tokenData = json.loads(data)
				self.accessToken = tokenData['access_token'].encode('utf-8')
				self._expiresIn = tokenData['expires_in']
			except:
				printl('json data error!',self,'E')
				print data
				return ""
			else:
				self._startRefreshTimer()
				return self.accessToken

	def revokeToken(self):
		if config.mediaportal.yt_refresh_token.value:
			twAgentGetPage(self.OAUTH2_URL+'/revoke?token=%s' % config.mediaportal.yt_refresh_token.value).addCallback(self._cb_revoke, False).addErrback(self._cb_revoke)

	def _cb_revoke(self, data, error=True):
		if error:
			printl('Error: Unable to revoke!',self,'E')
			print data

	def _startRefreshTimer(self):
		if self._refreshTimer != None and self._refreshTimer.active():
			self._refreshTimer.cancel()
		self._refreshTimer = reactor.callLater(self._expiresIn - 10, self._tokenExpired)

	def _tokenExpired(self):
		if self._refreshTimer != None and self._refreshTimer.active():
			self._refreshTimer.cancel()
		self._expiresIn = 0
		self.accessToken = None

	def getAccessToken(self):
		if self.accessToken == None:
			return ""
		else:
			return self.accessToken

yt_oauth2 = YT_Oauth2()