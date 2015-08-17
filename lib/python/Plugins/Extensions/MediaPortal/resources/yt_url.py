# -*- coding: utf-8 -*-

from messageboxext import MessageBoxExt
import mp_globals
from twagenthelper import TwAgentHelper, TwDownloadAgent

try:
	from cvevosignalgoextractor import decryptor
except:
	isVEVODecryptor = False
else:
	isVEVODecryptor = True

from imports import *

class youtubeUrl(object):

  def __init__(self, session):
	self.__callBack = None
	self.errBack = None
	self.session = session
	self.error = ""
	self.playing = False
	#self.useProxy = config.mediaportal.premiumize_use.value and config.mediaportal.sp_use_yt_with_proxy.value and mp_globals.premium_yt_proxy_host
	self.useProxy = config.mediaportal.premiumize_use.value and config.mediaportal.sp_use_yt_with_proxy.value
	if mp_globals.yt_dwnld_agent:
		mp_globals.yt_dwnld_agent.cancelDownload(self.initDownloadAgent)
	else:
		self.initDownloadAgent()

	self.tw_agent_hlp = TwAgentHelper(gzip_decoding=True, redir_agent=True)
	mp_globals.premiumize = self.useProxy
	self.retryParse = False

  def initDownloadAgent(self):
	print 'initDownloadAgent:'
	mp_globals.yt_dwnld_agent = None
	if self.useProxy:
		#proxyhost = mp_globals.premium_yt_proxy_host
		#proxyport = mp_globals.premium_yt_proxy_port
		proxyhost = 'nl.premiumize.me'
		proxyport = 82
		puser = config.mediaportal.premiumize_username.value
		ppass = config.mediaportal.premiumize_password.value
		mp_globals.yt_dwnld_agent = TwDownloadAgent(use_proxy=self.useProxy, proxy_host=proxyhost, proxy_port=proxyport, p_user=puser, p_pass=ppass, gzip_decoding=True, redir_agent=True)
	else:
		mp_globals.yt_dwnld_agent = TwDownloadAgent(gzip_decoding=True, redir_agent=True)

  def callBack(self, url):
	print 'callBack:'
	self.error = '[YoutubeURL] Playback error:'
	self.tw_agent_hlp.getRedirectedUrl(url, True).addCallback(self.getRedirect).addErrback(self.dataError)

  def getRedirect(self, url):
	print 'getRedirect:'
	if mp_globals.yt_dwnld_agent and url and 'Forbidden' in url and self.video_url.startswith('http'):
		if  config.mediaportal.premiumize_yt_buffering_opt.value != 'off':
			self.downloadStream()
		else:
			self.dataError(url)
	elif mp_globals.yt_dwnld_agent and config.mediaportal.premiumize_yt_buffering_opt.value == 'all':
		self.downloadStream()
	else:
		self.__callBack(url)

  def downloadStream(self):
	print 'downloadStream:'
	self.error = '[YoutubeURL] Buffering error:'
	mp_globals.yt_dwnld_lastnum = (mp_globals.yt_dwnld_lastnum + 1) % 2
	mp_globals.yt_dwnld_agent.downloadPage(self.video_url, 'yt_downloaded_file_%d' % mp_globals.yt_dwnld_lastnum, self.playFile).addCallback(self.playFile).addErrback(self.dataError)

  def playFile(self, data):
	print 'playFile:',data
	if data:
		m = re.search('File="(.*?)" buffering="(.*?)"', data)
		if m:
			filepath = m.group(1)
			buffering = m.group(2)
			if buffering:
				if 'canceled' == buffering:
					print 'Buffering canceled'
					self.session.open(MessageBoxExt, _('Buffering canceled'), MessageBoxExt.TYPE_INFO, timeout=3)
				elif 'ready' != buffering:
					print 'Buffering finished'
			if filepath and not self.playing:
				self.playing = True
				self.__callBack(filepath)

  def addCallback(self, cbFunc):
	self.__callBack = cbFunc

  def addErrback(self, errFunc):
	self.errBack = errFunc

  def dataError(self, error):
	print 'dataError:'
	self.error += str(error)
	self.errReturn()

  def errReturn(self, url=None):
	mp_globals.yt_dwnld_agent = None
	if self.errBack == None:
		self.session.openWithCallback(self.cbYTErr, MessageBoxExt,str(self.error), MessageBoxExt.TYPE_INFO, timeout=10)
	else:
		self.errBack(self.error)

  def cbYTErr(self, res):
	return

  def getVideoUrl(self, url, videoPrio=2):
	# portions of this part is from mtube plugin

	if not self.__callBack:
		self.error = '[YoutubeURL] Error: no callBack set'
		self.errReturn()

	if videoPrio == 0:
		self.VIDEO_FMT_PRIORITY_MAP = {
			'38' : 5, #MP4 Original (HD)
#			'37' : 5, #MP4 1080p (HD)
			'22' : 4, #MP4 720p (HD)
			'35' : 2, #FLV 480p
			'18' : 1, #MP4 360p
			'34' : 3, #FLV 360p
		}
	elif videoPrio == 1:
		self.VIDEO_FMT_PRIORITY_MAP = {
			'38' : 5, #MP4 Original (HD)
#			'37' : 5, #MP4 1080p (HD)
			'22' : 4, #MP4 720p (HD)
			'35' : 1, #FLV 480p
			'18' : 2, #MP4 360p
			'34' : 3, #FLV 360p
		}
	else:
		self.VIDEO_FMT_PRIORITY_MAP = {
			'38' : 2, #MP4 Original (HD)
#			'37' : 1, #MP4 1080p (HD)
			'22' : 1, #MP4 720p (HD)
			'35' : 3, #FLV 480p
			'18' : 4, #MP4 360p
			'34' : 5, #FLV 360p
		}

	self.video_url = None
	self.video_id = url
	self.videoPrio = videoPrio

	# Getting video webpage
	#URLs for YouTube video pages will change from the format http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
	#watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&safeSearch=none&noredirect=1'%self.video_id
	watch_url = 'http://www.youtube.com/watch?v=%s&gl=US'%self.video_id
	self.error = "[YoutubeURL] Error: Unable to retrieve watchpage:\n%s\n" % watch_url
	print watch_url
	if mp_globals.yt_dwnld_agent:
		mp_globals.yt_dwnld_agent.getWebPage(watch_url).addCallback(self.parseVInfo, watch_url).addErrback(self.dataError)
	else:
		self.tw_agent_hlp.getWebPage(watch_url).addCallback(self.parseVInfo, watch_url).addErrback(self.dataError)

  def parseVInfo(self, videoinfo, watch_url):
	flashvars = self.extractFlashVars(videoinfo, 0)
	if not flashvars.has_key(u"url_encoded_fmt_stream_map"):
		if self.useProxy and not self.retryParse:
			self.retryParse = True
			self.tw_agent_hlp.getWebPage(watch_url).addCallback(self.parseVInfo, watch_url).addErrback(self.dataError)
		else:
			self.checkFlashvars(flashvars, videoinfo, True)
	else:
		links = {}
		for url_desc in flashvars[u"url_encoded_fmt_stream_map"].split(u","):
			url_desc_map = parse_qs(url_desc)
			if not (url_desc_map.has_key(u"url") or url_desc_map.has_key(u"stream")):
				continue

			key = int(url_desc_map[u"itag"][0])
			url = u""

			if url_desc_map.has_key(u"url"):
				url = urllib.unquote(url_desc_map[u"url"][0])
			elif url_desc_map.has_key(u"conn") and url_desc_map.has_key(u"stream"):
				url = urllib.unquote(url_desc_map[u"conn"][0])
				if url.rfind("/") < len(url) -1:
					url = url + "/"
				url = url + urllib.unquote(url_desc_map[u"stream"][0])
			elif url_desc_map.has_key(u"stream") and not url_desc_map.has_key(u"conn"):
				url = urllib.unquote(url_desc_map[u"stream"][0])

			if url_desc_map.has_key(u"sig"):
				url = url + u"&signature=" + url_desc_map[u"sig"][0]
			elif url_desc_map.has_key(u"s"):
				sig = url_desc_map[u"s"][0]
				flashvars = self.extractFlashVars(videoinfo, 1)
				if isVEVODecryptor:
					signature = decryptor.decryptSignature(sig, flashvars[u"js"])
				else:
					signature = None
				if not signature:
					self.error = "[YoutubeURL] Error: cannot decrypt signature!"
					self.errReturn(None)
					return
				else:
					url += u"&signature=" + signature

			try:
				links[self.VIDEO_FMT_PRIORITY_MAP[str(key)]] = url
			except KeyError:
				print 'skipping',key,'fmt not in priority videos'
				continue

		if not links:
			url = flashvars.get('hlsvp','')
			print 'hlsvp:',str(url)
			if url:
				links[0] = url

		try:
			self.video_url = links[sorted(links.iterkeys())[0]].encode('utf-8')
			self.callBack(self.video_url)
		except (KeyError,IndexError):
			self.error = "[YoutubeURL] Error: no video url found"
			self.errReturn(self.video_url)

  def parseVInfo2(self, videoinfo):
	print 'parseVInfo2:'
	flashvars = parse_qs(videoinfo)
	if not flashvars.has_key(u"url_encoded_fmt_stream_map"):
		self.checkFlashvars(flashvars, videoinfo)
	else:
		print 'parsing...'
		video_fmt_map = {}
		fmt_infomap = {}
		tmp_fmtUrlDATA = flashvars['url_encoded_fmt_stream_map'][0].split(',')
		for fmtstring in tmp_fmtUrlDATA:
			fmturl = fmtid = fmtsig = ""
			if flashvars.has_key('url_encoded_fmt_stream_map'):
				try:
					for arg in fmtstring.split('&'):
						if arg.find('=') >= 0:
							key, value = arg.split('=')
							if key == 'itag':
								if len(value) > 3:
									value = value[:2]
								fmtid = value
							elif key == 'url':
								fmturl = value
							elif key == 'sig':
								fmtsig = value

					if fmtid != "" and fmturl != "" and self.VIDEO_FMT_PRIORITY_MAP.has_key(fmtid):
						video_fmt_map[self.VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl), 'fmtsig': fmtsig }
						fmt_infomap[int(fmtid)] = "%s&signature=%s" %(unquote_plus(fmturl), fmtsig)
					fmturl = fmtid = fmtsig = ""

				except:
					self.error = "[YoutubeURL] Error parsing fmtstring: %s" % fmtstring
					self.errReturn(self.video_url)
					return

			else:
				(fmtid,fmturl) = fmtstring.split('|')

			if self.VIDEO_FMT_PRIORITY_MAP.has_key(fmtid) and fmtid != "":
				video_fmt_map[self.VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl) }
				fmt_infomap[int(fmtid)] = unquote_plus(fmturl)

		if video_fmt_map and len(video_fmt_map):
			print "[youtubeUrl] found best available video format:",video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]['fmtid']
			best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
			if best_video['fmtsig']:
				self.video_url = "%s&signature=%s" %(best_video['fmturl'].split(';')[0], best_video['fmtsig'])
			else:
				self.video_url = "%s" %(best_video['fmturl'].split(';')[0])
			self.callBack(self.video_url)
		else:
			self.error = "[YoutubeURL] Error: no video url found"
			self.errReturn(self.video_url)

  def checkFlashvars(self, flashvars, videoinfo, get_info2=False):
	# Attempt to see if YouTube has issued an error message
	if not flashvars.has_key(u"reason"):
		from imports import decodeHtml
		pc = False
		if 'ypc-offer-title' in videoinfo:
			msg = re.search('ypc-offer-title">.*?<a.*?">(.*?)</a', videoinfo, re.S)
			if msg:
				pc = True
				self.error = '[YoutubeURL] Error: Paid Content'
				self.error += '\n: "%s"' % msg.group(1)
		elif 'itemprop="paid" content="True"' in videoinfo:
			msg = re.search('dir="ltr" title="(.*?)"', videoinfo, re.S)
			if msg:
				pc = True
				self.error = '[YoutubeURL] Error: Paid Content'
				self.error += ':\n"%s"' % decodeHtml(msg.group(1))

		msg = re.search('class="message">(.*?)</', videoinfo, re.S)
		if msg:
			txt = msg.group(1).strip()
			msg = re.search('class="submessage">(.*?)</', videoinfo, re.S)
			if msg:
				txt += '\n' + msg.group(1).strip()

			if not pc:
				self.error = '[YoutubeURL] Error: %s' % txt
			else:
				self.error += txt
		elif not pc:
			print 'videoinfo:',videoinfo
			self.error = '[YoutubeURL] Error: unable to extract "url_encoded_fmt_stream_map" parameter for unknown reason'

		if not pc and get_info2 and 'og:restrictions:age' in videoinfo:
			el = '&el=embedded'
			info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (self.video_id, el))
			self.error = "[YoutubeURL] Error: Unable to retrieve videoinfo page:\n%s\n" % info_url
			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.getWebPage(info_url).addCallback(self.parseVInfo2).addErrback(self.dataError)
			else:
				self.tw_agent_hlp.getWebPage(info_url).addCallback(self.parseVInfo2).addErrback(self.dataError)
			return
	else:
		reason = unquote_plus(flashvars['reason'][0])
		self.error = '[YoutubeURL] Error: YouTube said: %s' % reason.decode('utf-8')

	self.errReturn(self.video_url)

  def removeAdditionalEndingDelimiter(self, data):
	pos = data.find("};")
	if pos != -1:
		data = data[:pos + 1]
	return data

  def normalizeUrl(self, url):
	if url[0:2] == "//":
		url = "http:" + url
	return url

  def extractFlashVars(self, data, assets):
	flashvars = {}
	found = False

	for line in data.split("\n"):
		if line.strip().find(";ytplayer.config = ") > 0:
			found = True
			p1 = line.find(";ytplayer.config = ") + len(";ytplayer.config = ") - 1
			p2 = line.rfind(";")
			if p1 <= 0 or p2 <= 0:
				continue
			data = line[p1 + 1:p2]
			break
	data = self.removeAdditionalEndingDelimiter(data)

	if found:
		data = json.loads(data)
		if assets:
			flashvars = data["assets"]
		else:
			flashvars = data["args"]

		for k in ["html", "css", "js"]:
			if k in flashvars:
				flashvars[k] = self.normalizeUrl(flashvars[k])

	return flashvars