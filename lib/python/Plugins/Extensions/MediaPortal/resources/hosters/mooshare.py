# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def mooshare(self, data):
		stream_url = None
		stream_url = re.findall('file: "(.*?)"', data, re.S)
		if stream_url:
			url = urllib.unquote(stream_url[-1])
			self._callback(url)
		else:
			self.stream_not_found()