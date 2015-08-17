# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def vkme(self, data):
	stream_urls = re.findall('url[0-9]+=(http(s)?://.*?.vk.me/.*?/videos/.*?[0-9]+.mp4)', data)
	if stream_urls:
		stream_url = stream_urls[-1][0]
		self._callback(stream_url)
		return
	else:
		stream_urls = re.findall('url[0-9]+\\\\":\\\\"(http(s)?:.*?/videos.*?[0-9]+.mp4)', data)
		if stream_urls:
			stream_url = stream_urls[-1][0].replace('\\','')
			self._callback(stream_url)
			return
		else:
			stream_urls = re.findall('"url[0-9]+":"(http(s)?:.*?videos.*?)"', data)
			if stream_urls:
				self._callback(stream_urls[-1][0].replace("\/","/"))
				return
	self.stream_not_found()
