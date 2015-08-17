# -*- coding: utf-8 -*-

from imports import *
from twagenthelper import twAgentGetPage

class Client:
	USER_AGENT = '1.2.3.1 (Nexus 2; Android 4.2.2; de_DE)'
	RESULTDELAY = 2

	MV_DEFINITIONS_v12 = {
		"request_base_url": "http://www.myvideo.de/gateway.php?SITE=cellular&format=json",
		"request_get_connect_token": "&method=GetConnectToken&token=%TOKEN%&player_type=ANDROID",
		"request_navigation": "&method=Navigation&token=%TOKEN%",
		"request_home": "&method=get&id=%ID%&token=%TOKEN%&searchOrder=0&type=video_charts&size=%SIZE%&offset=%OFFSET%",
		"request_videodetails": "&method=GetVideoDetails&id=%ID%&token=%TOKEN%&player_type=ANDROID&playlistContext=true",
		"request_videodetails_playlist": "&method=GetVideoDetails&id=%ID%&token=%TOKEN%&player_type=ANDROID&playlistID=%PLAYLIST_ID%&size=%SIZE%&offset=%OFFSET%",
		"request_playlist": "&method=get&id=%ID%&token=%TOKEN%&type=play_list&size=%SIZE%&offset=%OFFSET%",
		"request_video_comments": "&method=get&id=%ID%&token=%TOKEN%&type=video_comments",
		"request_group_playlists": "&method=get&id=%ID%&token=%TOKEN%&searchOrder=%SEARCHORDER%&type=%GROUPTYPE%&size=%SIZE%&offset=%OFFSET%",
		"request_group_videos": "&method=get&id=%ID%&token=%TOKEN%&searchOrder=%SEARCHORDER%&type=group_videos&size=%SIZE%&offset=%OFFSET%",
		"request_group_video_search": "&method=get&id=%ID%&token=%TOKEN%&searchOrder=%SEARCHORDER%&type=group_video_search&size=%SIZE%&offset=%OFFSET%"
		}

	SESSION_TIMEOUT = 1800

	def __init__(self):
		self.mDeviceUID = ""
		self.mSecretKey = "1c8a2a7c1511c01ee5158ec2ed99b7498eb58dd5e328e978169c7b0cbd30d43f"
		self.agent_headers = {'Cookie2': ['$Version=1']}
		self.cookies = CookieJar()
		self.current_milli_time = lambda: int(round(time() * 1000))
		self.cnt = 0
		self.clearSession()

		self._sessionTimeoutTimer = eTimer()
		if mp_globals.isDreamOS:
			self._sessionTimeoutTimer_conn = self._sessionTimeoutTimer.timeout.connect(self._setSessionTimeout)
		else:
			self._sessionTimeoutTimer.callback.append(self._setSessionTimeout)

		self.stopSessionTimer = lambda: self._sessionTimeoutTimer.stop()
		self.requestID = lambda x: str(x.get('id', 0))
		self.requestPlaylistID = lambda x: str(x.get('playListID', 0))
		self.requestType = lambda x: str(x.get('type', ''))
		self.requestSearchOrder = lambda x: str(x.get('searchOrder', 5))
		self.requestSearchWord = lambda x: x.get('searchWord', '')
		self.requestSearchFilter = lambda x: x.get('searchFilter', 0)
		self.requestFilterData = lambda x: x.get('filterData', 0)
		self._createUrl = lambda x: self.MV_DEFINITIONS_v12.get("request_base_url", "") + self.MV_DEFINITIONS_v12.get(x, "")

	def clearSession(self):
		self.connected = False
		self.connect_pending = False
		self.initialToken = ""
		self.mDeviceToken = ""
		self.recievedConnectToken = ""
		self.session_token = ""
		self.session = None
		self.mDeviceUID = ""
		self.cookies.clear()

	def refreshToken(self):
		if not self.connected and not self.connect_pending:
			self.connect_pending = True
			return self.__connect()

	def _setSessionTimeout(self):
		self.connected = False

	def _getJson(self, data):
		try:
			jsonData = json.loads(data)
		except:
			printl('Error: No JSON object could be decoded!:',self,'E')
			self.connected = False
			self.connect_pending = False
			return {}
		else:
			return jsonData

	def connect(self, session):
		self.session = session
		self.cnt = 0
		self.connect_pending = True
		return self.__connect()

	def __connect(self):
		if self.cnt >= 3:
			msg = _("MyVideoClient Error:\nCannot connect to server!")
			self.session.open(MessageBoxExt, msg, type = MessageBoxExt.TYPE_ERROR)
			raise Exception(msg)

		self.cnt += 1
		self.clearSession()
		self.initialToken = self.getDeviceToken()
		url = self._createUrl('request_get_connect_token')
		url = url.replace('%TOKEN%', self.initialToken)
		d = self._getWebPage(None, url, False)
		d.addCallback(self._getJson)
		d.addCallback(self._getConnectToken)
		d2 = defer.Deferred()
		d.addCallback(self._delayResult, d2)
		d.addErrback(self._connectError)
		return d2

	def _delayResult(self, result, d):
		reactor.callLater(self.RESULTDELAY, d.callback, result)

	def _getConnectToken(self, jsonData):
		self.recievedConnectToken = jsonData.get("result", "")
		self._generateSessionTokens()
		self.connected = True
		self.cnt = 0
		self.connect_pending = False
		self._sessionTimeoutTimer.start(1000*self.SESSION_TIMEOUT, True)
		return self.session_token

	def _connectError(self, error):
		self.connect_pending = False
		printl("MyVideoClient: Error on Connect!:\n",self,'E')
		printl(error.getErrorMessage(),self,'E')

	def requestNavigation(self):
		url = self._createUrl('request_navigation')
		d = self._getWebPage(None, url)
		d.addCallback(self._getJson)
		return d

	def requestPlaylist(self, request_data, sz=20, ofs=0):
		sz = min(sz, 200)
		url = self._createUrl('request_playlist')
		url = url.replace('%ID%', self.requestPlaylistID(request_data))
		url = url.replace('%SIZE%',str(sz))
		url = url.replace('%OFFSET%',str(ofs))
		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def requestVideodetailsPlaylist(self, request_data, sz=20, ofs=0):
		sz = min(sz, 200)
		url = self._createUrl('request_videodetails_playlist')
		url = url.replace('%ID%', self.requestID(request_data))
		url = url.replace('%PLAYLIST_ID%', self.requestPlaylistID(request_data))
		url = url.replace('%SIZE%',str(sz))
		url = url.replace('%OFFSET%',str(ofs))
		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def requestVideodetails(self, request_data):
		url = self._createUrl('request_videodetails')
		url = url.replace('%ID%', self.requestID(request_data))
		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def getVideodetailsPlaylist(self, jsonData):
		video=jsonData['resultList']['video']['init']['resultList'][0]
		curl = video['connectionurl']
		url = re.search('vurl=(.*?m3u8)', curl).group(1)
		url = unquote(url)
		return url

	def requestGroupPlaylists(self, request_data, filter_data={}, sz=20, ofs=0):
		sz = min(sz, 200)
		url = self._createUrl('request_group_playlists')
		url = url.replace('%ID%', self.requestID(request_data))
		url = url.replace('%GROUPTYPE%', self.requestType(request_data))
		url = url.replace('%SEARCHORDER%', self.requestSearchOrder(request_data))
		url = url.replace('%SIZE%',str(sz))
		url = url.replace('%OFFSET%',str(ofs))
		filterData = self.requestFilterData(filter_data)
		if filterData and filterData[0].get('searchWord',''):
			url = self.appendFilterToUrl(url, filterData)
		else:
			searchFilter = self.requestSearchFilter(request_data)
			if searchFilter:
				url = self.appendFilterToUrl(url, searchFilter)

		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def requestHome(self, request_data, sz=20, ofs=0):
		sz = min(sz, 200)
		url = self._createUrl('request_home')
		url = url.replace('%ID%', self.requestID(request_data))
		url = url.replace('%SIZE%',str(sz))
		url = url.replace('%OFFSET%',str(ofs))
		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def requestGroupVideos(self, request_data, filter_data={}, sz=20, ofs=0):
		sz = min(sz, 200)
		url = self._createUrl('request_group_videos')
		url = url.replace('%ID%', self.requestID(request_data))
		url = url.replace('%SEARCHORDER%', self.requestSearchOrder(request_data))
		url = url.replace('%SIZE%',str(sz))
		url = url.replace('%OFFSET%',str(ofs))
		filterData = self.requestFilterData(filter_data)
		if filterData and filterData[0].get('searchWord',''):
			url = self.appendFilterToUrl(url, filterData)
		else:
			searchFilter = self.requestSearchFilter(request_data)
			if searchFilter:
				url = self.appendFilterToUrl(url, searchFilter)

		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def requestGroupVideoSearch(self, request_data, sz=20, ofs=0):
		sz = min(sz, 200)
		url = self._createUrl('request_group_video_search')
		url = url.replace('%ID%', self.requestID(request_data))
		url = url.replace('%SEARCHORDER%', self.requestSearchOrder(request_data))
		url = url.replace('%SIZE%',str(sz))
		url = url.replace('%OFFSET%',str(ofs))
		url = self.appendFilterToUrl(url, request_data['searchFilter'])
		d = defer.maybeDeferred(self.refreshToken)
		d.addCallback(self._getWebPage, url)
		d.addCallback(self._getJson)
		return d

	def appendFilterToUrl(self, url, filter_data):
		i = 0
		for filter in filter_data:
			searchType = str(filter.get('searchType',0))
			searchWord = str(filter.get('searchWord',''))
			url += '&searchFilter[%d][searchType]=%s&searchFilter[%d][searchWord]=%s' % (i, searchType, i, searchWord)
			i += 1

		return url

	def requestM3U8(self, url):
		d = twAgentGetPage(str(url), agent=self.USER_AGENT)
		d.addCallback(self._getM3U8List)
		d.addCallback(self._getBestVideoUrl, url).addErrback(self.dataError)
		return d

	def _getM3U8List(self, data):
		m3ulist=re.findall('BANDWIDTH=(\d+)\s+\w+(_\d+p[\.|\_]\S*m3u8)', data)
		return m3ulist

	def _getBandwidth(self, videoPrio):
		videoPrio = int(config.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = 1000000
		elif videoPrio == 1:
			bw = 500000
		else:
			bw = 175000

		return bw

	def _getBestVideoUrl(self, m3ulist, url):
		bw = self._getBandwidth(1)
		last_bw=0
		for _bw, uext in m3ulist:
			test_bw = int(_bw)
			if test_bw >= last_bw and test_bw <= bw:
				last_bw = test_bw
				return url.replace('.m3u8', '') + uext

		return None

	def getMD5Hash(self, paramString):
		try:
			str = hashlib.md5(paramString).hexdigest()
		except:
			printl("MyVideoClient: Could not generate MD5-Hash",self,'E')
			return None
		else:
			return str

	def generateSessionPasswd(self):
		return self.getMD5Hash(self.mSecretKey + self.getMD5Hash(self.recievedConnectToken))

	def getConnectToken(self):
		return self.recievedConnectToken

	def getDeviceToken(self):
		if not self.mDeviceToken:
			self.mDeviceToken = self.getMD5Hash(self.mDeviceUID + str(self.current_milli_time()))

		return self.mDeviceToken

	def _getDeviceUID(self):
		return "1"

	def _clearAccessToken(self):
		self._setSessionToken("");

	def _clearCookies(self):
		self.cookies.clear()

	def _generateSessionTokens(self):
		self._setSessionToken(self.getSessionToken(self.getDeviceToken(), self.recievedConnectToken));

	def getSessionState(self):
		return self.getSessionState()

	def rc4_crypt(self, data, key):
		x = 0
		box = range(256)
		for i in range(256):
			x = (x + box[i] + ord(key[i % len(key)])) % 256
			box[i], box[x] = box[x], box[i]
		x = y = 0
		out = []
		for char in data:
			x = (x + 1) % 256
			y = (y + box[x]) % 256
			box[x], box[y] = box[y], box[x]
			out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

		return ''.join(out)

	def encryptRC4(self, data , key , encode = hexlify):
		data = self.rc4_crypt(data , key)
		if encode:
			data = encode(data)

		return data

	def getSessionToken(self, paramString1, paramString2):
		str1 = self.getMD5Hash(paramString2)
		str2 = self.encryptRC4(paramString1, self.getMD5Hash(self.mSecretKey + str1))
		return str2

	def _setSessionToken(self, paramString):
		self.session_token = paramString

	def _getSessionToken(self):
		return self.session_token

	def dataError(self, error):
		printl("MyVideoClient: Error!:\n",self,'E')
		printl(error.getErrorMessage(),self,'E')
		if not config.mediaportal.sp_show_errors.value:
			self.session.open(MessageBoxExt, _("MyVideoClient Error:\n") + str(error.getErrorMessage()), type = MessageBoxExt.TYPE_ERROR)
		return error

	def _getWebPage(self, result, url, no_token=True):
		if no_token:
			if self.connected:
				self._sessionTimeoutTimer.start(1000*self.SESSION_TIMEOUT, True)
			url = url.replace('%TOKEN%', self.session_token)
		return twAgentGetPage(url, agent=self.USER_AGENT, cookieJar=self.cookies, headers=Headers(self.agent_headers), timeout=15)
		
mvClient = Client()