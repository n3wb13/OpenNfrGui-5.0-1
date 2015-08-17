# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def videomega(self, data):
	unescape = re.findall('unescape."(.*?)"', data, re.S)
	if len(unescape) == 3:
		javadata = urllib2.unquote(unescape[2])
		if javadata:
			stream_url = re.findall('file:"(http.*?)"', javadata, re.S)
			if stream_url:
				self._callback(stream_url[0])
			else:
				self.stream_not_found()
		else:
			self.stream_not_found()
	else:
		stream_url = re.findall('<source src="(.*?)" type="video/mp4"/>', data)
		if stream_url:
			self._callback(stream_url[0])
		else:
			self.stream_not_found()