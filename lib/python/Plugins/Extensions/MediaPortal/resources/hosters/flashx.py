# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def flashx(self, data):
	getSmilUrl = re.search('file: "(http:.*?\.smil)"', data, re.S)
	if not getSmilUrl:
		get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
		if get_packedjava:
			sJavascript = get_packedjava[0]
			sUnpacked = unpack(sJavascript)
			if sUnpacked:
				getSmilUrl = re.search('file:"(http:.*?\.smil)"', sUnpacked, re.S)
				filecodeid = re.search('file_code=(.*?)&', sUnpacked, re.S)
				if filecodeid:
					filecode = "http://flashx.tv/dl?%s" % filecodeid.group(1)
				else:
					filecode = ""
	if getSmilUrl:
		getPage(getSmilUrl.group(1), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.flashxSmilData, filecode).addErrback(self.errorload)
	else:
		self.stream_not_found()

def flashxSmilData(self, data, filecode):
	rtmp_server = re.findall('meta base="(rtmp://.*?)"', data, re.S)
	file = re.findall('video src="(.*?)".*?height="(.*?)"', data, re.S)
	bestHight = 0
	for path,height in file:
		if height > bestHight:
			bestHight = height
			bestpath = path
	if rtmp_server and file:
		stream_url = "%s app=vod/ pageUrl=%s swfUrl=http://static.flashx.tv/player6/jwplayer.flash.swf playpath=%s live=1" % (rtmp_server[0], filecode, bestpath)
		self._callback(stream_url)
	else:
		self.stream_not_found()