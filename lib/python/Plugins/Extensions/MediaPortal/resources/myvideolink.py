# -*- coding: utf-8 -*-
from imports import *
from playrtmpmovie import PlayRtmpMovie

class MyvideoLink:

	MASTER_KEY = "c8407a08b3c71ea418ec9dc662f2a56e40cbd6d5a114aa50fb1e1079e17f2b83"
	MV_BASE_URL = 'http://www.myvideo.at/'

	def __init__(self, session, bufferingOpt = 'none'):
		print "MyvideoLink:"
		self.session = session
		self._callback = None
		self._errback = None
		self.bufferingOpt = bufferingOpt
		self.special_headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31',
			'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
			'Referer': ''
		}

	def getLink(self, cb_play, cb_err, title, url, token, imgurl=''):
		self._callback = cb_play
		self._errback = cb_err
		self.title = title
		self.imgurl = imgurl
		self.special_headers['Referer'] = self.MV_BASE_URL
		vpage_url = self.MV_BASE_URL + 'watch/%s' % token
		getPage(vpage_url, headers=self.special_headers).addCallback(self.get_video, token).addErrback(cb_err)

	def __md5(self, s):
		return hashlib.md5(s).hexdigest()

	def __rc4crypt(self, data, key):
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

	def get_video(self, html, video_id):
		try:
			params = {}
			encxml = ''
			sec = re.search('var\sflashvars=\{(.*?)\}', html)
			
			for (a, b) in re.findall('(.*?):\'(.*?)\',?', sec.group(1)):
				if not a == '_encxml':
					params[a] = b
				else:
					encxml = unquote(b)
			if not params.get('domain'):
				params['domain'] = 'www.myvideo.at'
			xmldata_url = '%s?%s' % (encxml, urlencode(params))
			if 'flash_playertype=MTV' in xmldata_url:
				xmldata_url = (
					'http://www.myvideo.at/dynamic/get_player_video_xml.php?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes'
				) % video_id
		except:
			xmldata_url = (
				'http://www.myvideo.at/dynamic/get_player_video_xml.php?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes'
			) % video_id
		print 'xmldata_url:',xmldata_url
		getPage(xmldata_url, headers=self.special_headers).addCallback(self.get_enc_data, video_id).addErrback(self._errback)

	def get_enc_data(self, enc_data, video_id):
		print 'get_enc_data:'
		video = {}
		video['videopage'] = self.MV_BASE_URL + 'watch/%s' % video_id
		video['token'] = ''
		enc_data = enc_data.replace("_encxml=","")
		try:
			enc_data_b = unhexlify(enc_data)
			sk = self.__md5(self.MASTER_KEY + self.__md5(str(video_id)))
			dec_data = self.__rc4crypt(enc_data_b, sk)
#			print 'dec_data:',dec_data
			if '%3Ftoken' in dec_data:
				rtmpurl = re.search('connectionurl=\'(.*?)%3Ftoken', dec_data).group(1)
				token = re.search('%3Ftoken%3D(.*?)\'', dec_data).group(1)
				video['token'] = '?token=' + unquote(token)
			else:
				rtmpurl = re.search('connectionurl=\'(.*?)\'', dec_data).group(1)
			video['rtmpurl'] = unquote(rtmpurl)
			playpath = re.search('source=\'(.*?)\'', dec_data).group(1)
			video['file'] = unquote(playpath)
			m_filepath = re.search('path=\'(.*?)\'', dec_data)
			video['filepath'] = m_filepath.group(1)
			if not video['file'].endswith('f4m'):
				ppath, prefix = unquote(playpath).split('.')
				video['playpath'] = '%s:%s' % (prefix,ppath)
			else:
				video['hls_playlist'] = (video['filepath'] + video['file']).replace('.f4m', '.m3u8')

			if 'hls_playlist' in video:
				video_url = video['hls_playlist']
			elif not video['rtmpurl']:
				video_url = video['filepath'] + video['file']
			else:
				video['rtmpurl'] = video['rtmpurl'].replace('rtmpe://', 'rtmp://')
				video_url = ('%(rtmpurl)s playpath=%(playpath)s%(token)s pageUrl=%(videopage)s swfUrl=http://is1.myvideo.de/at/player/mingR14b/ming.swf swfVfy=1') % video
		except:
			print 'http fallback'
			path = source = ''
			try:
				path = re.search("path=\'(.*?)'", dec_data).group(1)
				source = unquote(re.search("source=\'(.*?)'", dec_data).group(1))
			except:
				pass

			if not path or not source or source.endswith('black_clip.flv'):
				emsg = 'Das Video "%s" ist leider nicht verfügbar!' % self.title
				if self._errback:
					self._errback(emsg)
				else:
					print 'Fehler:',emsg
				return
			video_url = path + source

		title = self.title
		pos = title.find('. ', 0, 5)
		if pos > 0:
			pos += 2
			title = title[pos:]

		scArtist = ''
		scTitle = title
		p = title.find(' -- ')
		if p > 0:
			scArtist = title[:p].strip()
			scTitle = title[p+4:].strip()

		if config.mediaportal.useRtmpDump.value and self.bufferingOpt == 'rtmpbuffering':
			if video_url.startswith('rtmp'):
				final = "%(rtmpurl)s' --swfVfy=1 --playpath=%(playpath)s%(token)s --pageUrl=%(videopage)s  --tcUrl=%(rtmpurl)s --swfUrl=http://is1.myvideo.de/at/player/mingR14b/ming.swf'" % video
				movieinfo = [final,scTitle,self.imgurl]
				self.session.open(PlayRtmpMovie, movieinfo, scTitle, playCallback=self._callback)
			else:
				self._callback(scTitle, video_url, self.imgurl, http_fallback=True)
		else:
			self._callback(scTitle, video_url, imgurl=self.imgurl, artist=scArtist)