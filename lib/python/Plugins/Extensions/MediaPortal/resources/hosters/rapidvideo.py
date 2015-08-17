﻿# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def rapidvideo(self, data):
	get_packedjava = re.findall("<script type=.text.javascript.*?(eval.function.*?)</script>", data, re.S)
	if get_packedjava and detect(get_packedjava[0]):
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			stream_url = None
			stream_url = re.findall('file:"(.*?)"', sUnpacked, re.S)
			if stream_url:
				url = urllib.unquote(stream_url[-1])
				self._callback(url)
				return
	self.stream_not_found()