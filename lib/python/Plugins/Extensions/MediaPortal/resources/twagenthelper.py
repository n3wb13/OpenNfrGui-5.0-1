# -*- coding: utf-8 -*-

from twisted import __version__
__TW_VER__ = tuple([int(x) for x in __version__.split('.')])

try:
	from urlparse import urlunparse, urljoin, urldefrag
	from urllib import splithost, splittype
except ImportError:
	from urllib.parse import splithost, splittype, urljoin, urldefrag
	from urllib.parse import urlunparse as _urlunparse

	def urlunparse(parts):
		result = _urlunparse(tuple([p.decode("charmap") for p in parts]))
		return result.encode("charmap")
from imports import *
import base64
from twisted.internet.ssl import ClientContextFactory

MDEBUG = False

if __TW_VER__ < (13, 1, 0):
	from twisted.python import failure
	from twisted.web._newclient import ResponseFailed

	class RedirectAgent(object):
		"""
		An L{Agent} wrapper which handles HTTP redirects.

		The implementation is rather strict: 301 and 302 behaves like 307, not
		redirecting automatically on methods different from I{GET} and I{HEAD}.

		See L{BrowserLikeRedirectAgent} for a redirecting Agent that behaves more
		like a web browser.

		@param redirectLimit: The maximum number of times the agent is allowed to
			follow redirects before failing with a L{error.InfiniteRedirection}.

		@cvar _redirectResponses: A L{list} of HTTP status codes to be redirected
			for I{GET} and I{HEAD} methods.

		@cvar _seeOtherResponses: A L{list} of HTTP status codes to be redirected
			for any method and the method altered to I{GET}.

		@since: 11.1
		"""

		_redirectResponses = [http.MOVED_PERMANENTLY, http.FOUND,
							http.TEMPORARY_REDIRECT]
		_seeOtherResponses = [http.SEE_OTHER]

		def __init__(self, agent, redirectLimit=20):
			self._agent = agent
			self._redirectLimit = redirectLimit


		def request(self, method, uri, headers=None, bodyProducer=None):
			"""
			Send a client request following HTTP redirects.

			@see: L{Agent.request}.
			"""
			deferred = self._agent.request(method, uri, headers, bodyProducer)
			return deferred.addCallback(
				self._handleResponse, method, uri, headers, 0)


		def _resolveLocation(self, requestURI, location):
			"""
			Resolve the redirect location against the request I{URI}.

			@type requestURI: C{bytes}
			@param requestURI: The request I{URI}.

			@type location: C{bytes}
			@param location: The redirect location.

			@rtype: C{bytes}
			@return: Final resolved I{URI}.
			"""
			return _urljoin(requestURI, location)


		def _handleRedirect(self, response, method, uri, headers, redirectCount):
			"""
			Handle a redirect response, checking the number of redirects already
			followed, and extracting the location header fields.
			"""
			if redirectCount >= self._redirectLimit:
				err = error.InfiniteRedirection(
					response.code,
					'Infinite redirection detected',
					location=uri)
				raise ResponseFailed([failure.Failure(err)], response)
			locationHeaders = response.headers.getRawHeaders('location', [])
			if not locationHeaders:
				err = error.RedirectWithNoLocation(
					response.code, 'No location header field', uri)
				raise ResponseFailed([failure.Failure(err)], response)
			location = self._resolveLocation(uri, locationHeaders[0])
			deferred = self._agent.request(method, location, headers)
			return deferred.addCallback(
				self._handleResponse, method, uri, headers, redirectCount + 1)


		def _handleResponse(self, response, method, uri, headers, redirectCount):
			"""
			Handle the response, making another request if it indicates a redirect.
			"""
			if response.code in self._redirectResponses:
				if method not in ('GET', 'HEAD'):
					err = error.PageRedirect(response.code, location=uri)
					raise ResponseFailed([failure.Failure(err)], response)
				return self._handleRedirect(response, method, uri, headers,
											redirectCount)
			elif response.code in self._seeOtherResponses:
				return self._handleRedirect(response, 'GET', uri, headers,
											redirectCount)
			return response

	class BrowserLikeRedirectAgent(RedirectAgent):
		"""
		An L{Agent} wrapper which handles HTTP redirects in the same fashion as web
		browsers.

		Unlike L{RedirectAgent}, the implementation is more relaxed: 301 and 302
		behave like 303, redirecting automatically on any method and altering the
		redirect request to a I{GET}.

		@see: L{RedirectAgent}

		@since: 13.1
		"""
		_redirectResponses = [http.TEMPORARY_REDIRECT]
		_seeOtherResponses = [http.MOVED_PERMANENTLY, http.FOUND, http.SEE_OTHER]

	def _urljoin(base, url):
		"""
		Construct a full ("absolute") URL by combining a "base URL" with another
		URL. Informally, this uses components of the base URL, in particular the
		addressing scheme, the network location and (part of) the path, to provide
		missing components in the relative URL.

		Additionally, the fragment identifier is preserved according to the HTTP
		1.1 bis draft.

		@type base: C{bytes}
		@param base: Base URL.

		@type url: C{bytes}
		@param url: URL to combine with C{base}.

		@return: An absolute URL resulting from the combination of C{base} and
			C{url}.

		@see: L{urlparse.urljoin}

		@see: U{https://tools.ietf.org/html/draft-ietf-httpbis-p2-semantics-22#section-7.1.2}
		"""
		base, baseFrag = urldefrag(base)
		url, urlFrag = urldefrag(urljoin(base, url))
		return urljoin(url, b'#' + (urlFrag or baseFrag))
else:
	from twisted.web.client import BrowserLikeRedirectAgent

class GetResource(Protocol):
	def __init__(self, status, message, finished):
		self.finished = finished
		self.buffer = []
		self.status = status
		self.message = message

	def dataReceived(self, data):
		self.buffer.append(data)

	def connectionLost(self, reason):
		d_print( "connectionLost: ", reason)
		if reason.check(ResponseDone):
			self.finished.callback(b''.join(self.buffer))
		elif reason.check(http.PotentialDataLoss):
			self.finished.callback(b''.join(self.buffer))
		else:
			self.finished.errback(reason)

class StringProducer:
	implements(IBodyProducer)

	def __init__(self, body):
		self.body = body
		self.length = len(body)

	def startProducing(self, consumer):
		consumer.write(self.body)
		return succeed(None)

	def pauseProducing(self):
		pass

	def stopProducing(self):
		pass

class WebClientContextFactory(ClientContextFactory): #do not verify https requests
	def getContext(self, hostname, port):
		return ClientContextFactory.getContext(self)

class TwAgentRedirectAgent(BrowserLikeRedirectAgent):
	def __init__(self, agent, redirectLimit=20):
		BrowserLikeRedirectAgent.__init__(self, agent, redirectLimit)

	def _handleResponse(self, response, method, uri, headers, redirectCount):
		locationHeaders = response.headers.getRawHeaders('location', [])
		if locationHeaders:
			location = self._resolveLocation(uri, locationHeaders[0])
			headers.addRawHeader('location', location)
		else:
			headers.addRawHeader('location', uri)

		return BrowserLikeRedirectAgent._handleResponse(self, response, method, uri, headers, redirectCount)

class TwAgentHelper(object):

	DEBUG_HEADER = False

	def __init__(self, proxy_host=None, proxy_port=None, use_proxy=False, p_user='', p_pass='',  gzip_decoding=False, redir_agent=False, use_tls=False, cookieJar=None, redirectLimit=20, headers=None, connectTimeout=None):
		d_print( "Twisted Agent in use", __TW_VER__)
		if not headers:
			self.headers = Headers()
		elif  isinstance(headers, Headers):
			self.headers = headers
		else:
			self.headers = Headers()
			for k,v in headers.iteritems():
				self.headers.setRawHeaders(k, [v])

		self.useProxy = use_proxy
		self.body = None
		if self.useProxy:
			if use_tls:
				from twisted.internet import ssl
				options = ssl.CertificateOptions()
				self.endpoint = SSL4ClientEndpoint(reactor, proxy_host, proxy_port, options)
			else:
				self.endpoint = TCP4ClientEndpoint(reactor, proxy_host, proxy_port)
			if cookieJar != None:
				self.agent = CookieAgent(ProxyAgent(self.endpoint), cookieJar)
			else:
				self.agent = ProxyAgent(self.endpoint)
			auth = base64.b64encode("%s:%s" % (p_user, p_pass))
			self.headers.addRawHeader('Proxy-Authorization', 'Basic ' + auth.strip())
		else:
			if cookieJar != None:
				self.agent = CookieAgent(Agent(reactor, connectTimeout=connectTimeout, contextFactory=WebClientContextFactory()), cookieJar)
			else:
				self.agent = Agent(reactor, connectTimeout=connectTimeout, contextFactory=WebClientContextFactory())

		if gzip_decoding and __TW_VER__ >= (11, 1, 0):
			d_print( 'Tw agent: Using gzip decoder')
			from twisted.web.client import ContentDecoderAgent, GzipDecoder
			self.agent = ContentDecoderAgent(self.agent, [('gzip', GzipDecoder)])

		self._agent = self.agent
		if redir_agent:
			self.agent = TwAgentRedirectAgent(self.agent, redirectLimit=redirectLimit)

	def getRedirectedUrl(self, url, redir=True):
		d_print( "getRedirectedUrl: ", url)
		return self._agent.request('HEAD', url, headers=self.headers).addCallback(self._getResponse, url, redir)

	def _getResponse(self, response, url, redir):
		d_print( "_getResponse:")
		d_print( "Status code: ", response.phrase)
		import mp_globals

		if self.DEBUG_HEADER:
			for header, value in response.headers.getAllRawHeaders():
				d_print( header, value)

		r = response.headers.getRawHeaders("location")
		if r:
			r_url = r[0]
			p = self._parse(r_url)
			if b'http' not in p[0]:
				d_print( "Rel. URL correction")
				scheme, host, port, path = self._parse(url)
				r_url = b'%s://%s/%s' % (scheme, host, r_url)
			d_print( "Location: ", r_url)
		else:
			r_url = url

		if 'Forbidden' in response.phrase and not redir:
			return response.phrase
		elif redir:
			return r_url
		else: return response

	def getWebPage(self, url, method='GET', postdata=None, addlocation=False):
		d_print( "getWebPage:")
		if postdata:
			body = StringProducer(postdata)
		else: body = None

		return self.agent.request(method, url, headers=self.headers, bodyProducer=body).addCallback(self._getResource, addlocation)

	def _getResource(self, response, addlocation=False):
		finished = Deferred()
		response.deliverBody(GetResource(response.code, response.phrase, finished))
		if addlocation:
			finished.addCallback(self._addLocation2Body)

		return finished

	def _addLocation2Body(self, body):
		if body:
			return succeed("".join((body, "twLocation=\"", self.headers.getRawHeaders("location", [""])[0], '"')))
		else:
			return succeed(body)

	@staticmethod
	def _parse(url, defaultPort=None):
		from urlparse import urlunparse
		url = url.strip()
		parsed = http.urlparse(url)
		scheme = parsed[0]
		path = urlunparse(('', '') + parsed[2:])

		if defaultPort is None:
			if scheme == 'https':
				defaultPort = 443
			else:
				defaultPort = 80

		host, port = parsed[1], defaultPort
		if ':' in host:
			host, port = host.split(':')
			try:
				port = int(port)
			except ValueError:
				port = defaultPort

		if path == '':
			path = '/'

		return scheme, host, port, path

class TwAgentFactory(TwAgentHelper):
    def __init__(self, method='GET', postdata=None, headers=None,
                 agent="Twisted PageGetter", timeout=None, cookieJar=None,
                 followRedirect=True, redirectLimit=20, gzip_decoding=True, addlocation=False):
		self.method = method
		self.postdata = postdata
		self.addlocation = addlocation

		TwAgentHelper.__init__(self, gzip_decoding=gzip_decoding, redir_agent=followRedirect, cookieJar=cookieJar, redirectLimit=redirectLimit, headers=headers, connectTimeout=timeout)
		if agent:
			self.headers.setRawHeaders('User-Agent', [agent])

def twAgentGetPage(url, **kwargs):
	twAgent = TwAgentFactory(**kwargs)
	if twAgent.postdata:
		body = StringProducer(twAgent.postdata)
	else: body = None
	if twAgent.method != 'HEAD':
		return twAgent.agent.request(twAgent.method, url, headers=twAgent.headers, bodyProducer=body).addCallback(twAgent._getResource, twAgent.addlocation)
	else:
		return twAgent._agent.request(twAgent.method, url, headers=twAgent.headers, bodyProducer=body).addCallback(twAgent._getResponse, url, True)

class DownloadResource(Protocol):

	def __init__(self, status, message, finished, callback, file, filepath, event):
		d_print( "DownloadResource:")
		import mp_globals
		self.data = ""
		self.finished = finished
		self._callback = callback
		self.status = status
		self.message = message

		s = config.mediaportal.premiumize_use_yt_buffering_size.value
		if 'Whole' in s:
			self.buff_threshold = 2000000000
		else:
			self.buff_threshold = int(s)*1024*1024

		self.file = file
		self.filepath = filepath
		mp_globals.yt_bytes_downloaded = 0L
		self.buffer_ready = False
		self.cancel = False
		self.cancel_event = event
		self.cancel_event.addCallback(self.cancelConnection)
		mp_globals.yt_download_runs = True

	def dataReceived(self, data):
		import mp_globals
		self.file.write(data)
		mp_globals.yt_bytes_downloaded += len(data)

		if self.cancel:
			if __TW_VER__ >= (11, 1, 0):
				self.transport.abortConnection()
			else:
				self.transport.loseConnection()
		elif not self.buffer_ready and mp_globals.yt_bytes_downloaded >= self.buff_threshold:
			self.buffer_ready = True
			self._callback('File="%s" buffering="ready"' % self.filepath)

	def connectionLost(self, reason):
		d_print( "connectionLost:")
		import mp_globals
		mp_globals.yt_download_runs = False
		self.file.close()
		if self.cancel:
			self.finished.callback('File="%s" buffering="canceled"' % self.filepath)
		elif reason.check(ResponseDone):
			self.finished.callback('File="%s" buffering="%s"' % (self.filepath, self.message))
		elif reason.check(http.PotentialDataLoss):
			self.finished.callback('File="%s" buffering="%s"' % (self.filepath, self.message))
		else:
			self.finished.errback(reason)

	def cancelConnection(self):
		import mp_globals
		self.cancel = True
		mp_globals.yt_download_runs = False
		self.cancel_event.reset()

class TwDownloadAgent(TwAgentHelper):

	def __init__(self, *args, **kw_args):
		TwAgentHelper.__init__(self, *args, **kw_args)
		import mp_globals
		from simpleevent import SimpleEvent

		self.length = 0
		self.cancel_event = SimpleEvent()
		self.downloadTimer = eTimer()
		if mp_globals.isDreamOS:
			self.downloadTimer_conn = self.downloadTimer.timeout.connect(self.__updateProgress)
		else:
			self.downloadTimer.callback.append(self.__updateProgress)

	def downloadPage(self, url, file_nm, pre_callback):
		d_print( "downloadPage: ", url)
		import mp_globals
		self.filepath = config.mediaportal.storagepath.value + file_nm
		try:
			self.file = open(self.filepath, 'wb')
		except:
			err = 'downloadPage: Cannot create:\n%s' % self.filepath

		mp_globals.yt_tmp_storage_dirty |= True
		self.downloadTimer.start(1000, False)
		return self.agent.request('GET', url, headers=self.headers).addCallback(self.__downloadResource, pre_callback, self.file, self.filepath, self.cancel_event).addCallback(self.__downloadFinished)

	def __downloadResource(self, response, callback, file, filepath, event):
		self.length = response.length
		finished = Deferred()
		response.deliverBody(DownloadResource(response.code, response.phrase, finished, callback, file, filepath, event))
		return finished

	def cancelDownload(self, callback=None):
		import mp_globals
		self.downloadTimer.stop()
		if mp_globals.yt_download_runs:
			self.cancel_event.genEvent(callback)
		elif callback:
			callback()

	def __downloadFinished(self, data):
		import re
		import mp_globals
		m = re.search('(File=".*?") buffering="(.*?)"', data)
		if m:
			d_print( '%s downloaded, "%s": %d of %d bytes loaded' % (m.group(1), m.group(2), mp_globals.yt_bytes_downloaded, self.length))
			self.downloadTimer.stop()
			if mp_globals.yt_download_progress_widget:
				reactor.callLater(1, self.__updateProgressbar, mp_globals.yt_bytes_downloaded, self.length)
			return data

	def __updateProgress(self):
		import mp_globals
		#d_print( 'Download-Stat: %d of %d bytes' % (mp_globals.yt_bytes_downloaded, self.length))
		if mp_globals.yt_download_progress_widget:
			reactor.callLater(0, self.__updateProgressbar, mp_globals.yt_bytes_downloaded, self.length)

	def __updateProgressbar(self, size_downloaded, size):
		import mp_globals
		if size > 0 and size_downloaded >= 0:
			progress = int(100 * round(float(size_downloaded) / size, 2))
			if progress > 100:
				progress = 100
			mp_globals.yt_download_progress_widget.setValue(progress)

def d_print(*args):
	if MDEBUG:
		s = ''
		for arg in args:
			s += str(arg)
		print s

__all__ = ["__TW_VER__", "TwAgentHelper", "twAgentGetPage", "TwDownloadAgent"]