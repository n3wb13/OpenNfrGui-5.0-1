# -*- coding: utf-8 -*-
from imports import *
import mp_globals
from Components.ActionMap import HelpableActionMap
from Components.Sources.StaticText import StaticText
from Screens.HelpMenu import HelpableScreen

class VirtualKeyBoardExtInputHelpDialog(NumericalTextInputHelpDialog):

	def __init__(self, session, textinput):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/InputHelpDialog.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/InputHelpDialog.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		NumericalTextInputHelpDialog.__init__(self, session, textinput)

class VirtualKeyBoardExt(Screen, NumericalTextInput, HelpableScreen):

	def __init__(self, session, title="", text="", captcha=None, is_dialog=False):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/VirtualKeyBoardExt.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/VirtualKeyBoardExt.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		NumericalTextInput.__init__(self, nextFunc=self.nextFunc, handleTimeout=True)
		HelpableScreen.__init__(self)
		self.sms_txt = None
		self.keys_list = []
		self.shiftkeys_list = []
		self.lang = language.getLanguage()
		self.nextLang = None
		self.shiftMode = False
		self.cursor = "XcursorX"
		self.gui_cursor = "|"
		self.text = text + self.cursor
		self.selectedKey = 0
		self.cursor_show = True
		self.cursor_time = 1000
		self.cursorTimer = eTimer()
		if mp_globals.isDreamOS:
			self.cursorTimer_conn = self.cursorTimer.timeout.connect(self.toggleCursor)
		else:
			self.cursorTimer.callback.append(self.toggleCursor)
		self.cursorTimer.start(self.cursor_time, True)
		self.captcha = captcha
		self.picload = ePicLoad()

		self['captcha'] = Pixmap()
		self["country"] = StaticText("")
		self["header"] = Label(title)
		self["text"] = Label()
		self['title'] = Label()
		self.ml = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
		self["list"] = self.ml

		self["actions"] = ActionMap(["KeyboardInputActions", "InputAsciiActions"],
			{
				"gotAsciiCode": self.keyGotAscii,
				"deleteBackward": self.backClicked
			}, -2)
		self["InputBoxActions"] = HelpableActionMap(self, "InputBoxActions",
			{
				"deleteBackward": (self.cursorLeft, _("Move cursor left")),
				"deleteForward": (self.cursorRight, _("Move cursor right"))
			}, -2)
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"ok": (self.okClicked, _("Select key")),
				"cancel": (self.exit, _("Cancel"))
			},-2)
		self["ShortcutActions"] = HelpableActionMap(self, "ShortcutActions",
			{
				"red": (self.backClicked, _("Delete (left of the cursor)")),
				"blue": (self.backSpace, _("Delete (right of the cursor)")),
				"green": (self.ok, _("Save")),
				"yellow": (self.switchLang, _("Switch keyboard layout"))
			}, -2)
		self["WizardActions"] = HelpableActionMap(self, "WizardActions",
			{
				"left": (self.left, _("Left")),
				"right": (self.right, _("Right")),
				"up": (self.up, _("Up")),
				"down": (self.down, _("Down"))
			},-2)
		self["SeekActions"] = HelpableActionMap(self, "SeekActions",
			{
				"seekBack": (self.move_to_begin, _("Move to begin")),
				"seekFwd": (self.move_to_end, _("Move to end"))
			},-2)
		self["NumberActions"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal
		})

		self.set_GUI_Text()
		self.setLang()
		self.buildVirtualKeyBoard()
		self.onExecBegin.append(self.setKeyboardModeAscii)
		self.onLayoutFinish.append(self.__onLayoutFinish)
		self.onClose.append(self.__onClose)

	def __onLayoutFinish(self):
		self['title'].setText("MediaPortal KeyBoard")
		self.setTitle("MediaPortal KeyBoard")
		self.help_window = self.session.instantiateDialog(VirtualKeyBoardExtInputHelpDialog, self)
		self.help_window.show()
		if self.captcha == None:
			self['captcha'].hide()
		else:
			if fileExists(self.captcha):
				self['captcha'].instance.setPixmap(gPixmapPtr())
				self.scale = AVSwitch().getFramebufferScale()
				size = self['captcha'].instance.size()
				if mp_globals.fakeScale:
					self.picload.setPara((size.width(), size.height(), self.scale[0], self.scale[1], False, 1, "#00000000"))
				else:
					self.picload.setPara((size.width(), size.height(), self.scale[0], self.scale[1], False, 1, "#FF000000"))
				if mp_globals.isDreamOS:
					if self.picload.startDecode(self.captcha, False) == 0:
						ptr = self.picload.getData()
						if ptr != None:
							self['captcha'].instance.setPixmap(ptr)
							self['captcha'].show()
				else:
					if self.picload.startDecode(self.captcha, 0, 0, False) == 0:
						ptr = self.picload.getData()
						if ptr != None:
							self['captcha'].instance.setPixmap(ptr)
							self['captcha'].show()

	def __onClose(self):
		self.session.deleteDialog(self.help_window)
		self.help_window = None

	def switchLang(self):
		self.lang = self.nextLang
		self.setLang()
		self.buildVirtualKeyBoard()

	def setLang(self):
		if self.lang == 'de_DE':
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"ü", u"+",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"ö", u"ä", u"#",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"@", u"ß", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"Ü", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"Ö", u"Ä", u"'",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"?", u"\\", u"OK"]
			self.nextLang = 'es_ES'
		elif self.lang == 'es_ES':
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"ú", u"+",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"ó", u"á", u"#",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"@", u"Ł", u"ŕ", u"é", u"č", u"í", u"ě", u"ń", u"ň", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"Ú", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"Ó", u"Á", u"'",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"?", u"\\", u"Ŕ", u"É", u"Č", u"Í", u"Ě", u"Ń", u"Ň", u"OK"]
			self.nextLang = 'fi_FI'
		elif self.lang == 'fi_FI':
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"é", u"+",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"ö", u"ä", u"#",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"@", u"ß", u"ĺ", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"É", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"Ö", u"Ä", u"'",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"?", u"\\", u"Ĺ", u"OK"]
			self.nextLang = 'sv_SE'
		elif self.lang == 'sv_SE':
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"é", u"+",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"ö", u"ä", u"#",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"@", u"ß", u"ĺ", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"É", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"Ö", u"Ä", u"'",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"?", u"\\", u"Ĺ", u"OK"]
			self.nextLang = 'sk_SK'
		elif self.lang =='sk_SK':
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"ú", u"+",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"ľ", u"@", u"#",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"š", u"č", u"ž", u"ý", u"á", u"í", u"é", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"ť", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"ň", u"ď", u"'",
				u"Á", u"É", u"Ď", u"Í", u"Ý", u"Ó", u"Ú", u"Ž", u"Š", u"Č", u"Ť", u"Ň",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"?", u"\\", u"ä", u"ö", u"ü", u"ô", u"ŕ", u"ĺ", u"OK"]
			self.nextLang = 'cs_CZ'
		elif self.lang == 'cs_CZ':
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"ú", u"+",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"ů", u"@", u"#",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"ě", u"š", u"č", u"ř", u"ž", u"ý", u"á", u"í", u"é", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"ť", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"ň", u"ď", u"'",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"?", u"\\", u"Č", u"Ř", u"Š", u"Ž", u"Ú", u"Á", u"É", u"OK"]
			self.nextLang = 'en_EN'
		else:
			self.keys_list = [
				u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE",
				u"q", u"w", u"e", u"r", u"t", u"z", u"u", u"i", u"o", u"p", u"+", u"@",
				u"a", u"s", u"d", u"f", u"g", u"h", u"j", u"k", u"l", u"#", u"\\",
				u"<", u"y", u"x", u"c", u"v", u"b", u"n", u"m", u",", ".", u"-", u"CLEAR",
				u"SHIFT", u"SPACE", u"OK"]
			self.shiftkeys_list = [
				u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE",
				u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"*",
				u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"'", u"?",
				u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR",
				u"SHIFT", u"SPACE", u"OK"]
			self.lang = 'en_EN'
			self.nextLang = 'de_DE'
		self.keys_list = self.buildKeyBoardLayout(self.keys_list)
		self.shiftkeys_list = self.buildKeyBoardLayout(self.shiftkeys_list)
		self["country"].setText(self.lang)

	def buildVirtualKeyBoard(self, selectedKey=0):
		list = []
		self.max_key = -1
		if self.shiftMode:
			self.k_list = self.shiftkeys_list
			for keys in self.k_list:
				keyslen = len(keys)
				self.max_key += keyslen
				if selectedKey < keyslen and selectedKey > -1:
					list.append((keys, selectedKey, True))
				else:
					list.append((keys, -1, True))
				selectedKey -= keyslen
		else:
			self.k_list = self.keys_list
			for keys in self.k_list:
				keyslen = len(keys)
				self.max_key += keyslen
				if selectedKey < keyslen and selectedKey > -1:
					list.append((keys, selectedKey, False))
				else:
					list.append((keys, -1, False))
				selectedKey -= keyslen
		self.ml.setList(map(self.VirtualKeyBoardEntryComponent, list))
		self.first_line_len = len(self.k_list[0])
		self.no_of_lines = len(self.k_list)

	def buildKeyBoardLayout(self, key_list):
		line_len = 12
		if self["list"].skinAttributes:
			for (attrib, value) in self["list"].skinAttributes:
				if attrib == "linelength":
					line_len = int(value)
		k_list = []
		line = []
		i = 0
		for key in key_list:
			i += 1
			line.append(key)
			if i == line_len:
				k_list.append(line)
				i = 0
				line = []
		k_list.append(line)
		return k_list

	def toggleCursor(self):
		whitespace = " " * len(self.gui_cursor)
		if self.cursor_show:
			self.cursor_show = False
			txt = self.text.replace(self.cursor, whitespace)
		else:
			self.cursor_show = True
			txt = self.text.replace(self.cursor, self.gui_cursor)
		self["text"].setText(txt)
		self.cursorTimer.start(self.cursor_time, True)

	def set_GUI_Text(self):
		txt = self.text.replace(self.cursor, "|")
		self["text"].setText(txt)

	def backClicked(self):
		txt = self.text.split(self.cursor)
		del_len = self.checkUnicode(txt[0][-1:])
		self.text = txt[0][:-del_len] + self.cursor + txt[1]
		self.set_GUI_Text()

	def backSpace(self):
		txt = self.text.split(self.cursor)
		del_len = self.checkUnicode(txt[1][:1])
		self.text = txt[0] + self.cursor + txt[1][del_len:]
		self.set_GUI_Text()

	def cursorLeft(self):
		self.moveCursor(-1)

	def cursorRight(self):
		self.moveCursor(+1)

	def checkUnicode(self, char):
		try:
			len(u'%s' % char)
		except UnicodeDecodeError:
			return 2
		return 1

	def moveCursor(self, direction):
		txt = self.text.split(self.cursor)
		if direction < 0:
			direction *= self.checkUnicode(txt[0][-1:])
		elif direction > 0:
			direction *= self.checkUnicode(txt[1][:1])
		pos = self.text.find(self.cursor) + direction
		clean_txt = self.text.replace(self.cursor, "")
		if pos > len(clean_txt):
			self.text = self.cursor + clean_txt
		elif pos < 0:
			self.text = clean_txt + self.cursor
		else:
			self.text = clean_txt[:pos] + self.cursor + clean_txt[pos:]
		self.set_GUI_Text()

	def move_to_begin(self):
		clean_txt = self.text.replace(self.cursor, "")
		self.text = self.cursor + clean_txt

	def move_to_end(self):
		clean_txt = self.text.replace(self.cursor, "")
		self.text = clean_txt + self.cursor

	def toggleShift(self):
		if self.shiftMode:
			self.shiftMode = False
		else:
			self.shiftMode = True
		self.buildVirtualKeyBoard(self.selectedKey)

	def keyNumberGlobal(self, number):
		self.cursorTimer.stop()
		if number != self.lastKey and self.lastKey != -1:
			self.nextChar()
		txt = self.getKey(number).encode("utf-8")
		self.sms_txt = self.text.replace(self.cursor, txt +  self.cursor)
		self.got_sms_key(txt)
		txt = self.sms_txt.replace(self.cursor, "|")
		self["text"].setText(txt)

	def nextFunc(self):
		if self.sms_txt:
			self.text = self.sms_txt
		self.sms_txt = None
		self.set_GUI_Text()
		self.cursorTimer.start(self.cursor_time, True)

	def okClicked(self):
		if self.shiftMode:
			list = self.shiftkeys_list
		else:
			list = self.keys_list
		selectedKey = self.selectedKey

		text = None

		for x in list:
			xlen = len(x)
			if selectedKey < xlen:
				if selectedKey < len(x):
					text = x[selectedKey]
				break
			else:
				selectedKey -= xlen

		if text is None:
			return

		text = text.encode("utf-8")

		if text == "EXIT":
			self.exit()
		elif text == "BACKSPACE":
			self.backClicked()
		elif text == "CLEAR":
			self.text = "" + self.cursor
			self.set_GUI_Text()
		elif text == "SHIFT":
			self.toggleShift()
		elif text == "SPACE":
			self.text = self.text.replace(self.cursor, " " + self.cursor)
			self.set_GUI_Text()
		elif text == "OK":
			self.ok()
		elif text == "LEFT":
			self.cursorLeft()
		elif text == "RIGHT":
			self.cursorRight()
		else:
			self.text = self.text.replace(self.cursor, text + self.cursor)
			self.set_GUI_Text()

	def ok(self):
		text = self.text.encode("utf-8")
		text = text.replace(self.cursor, "")
		self.close(text)

	def exit(self):
		self.close(None)

	def moveActiveKey(self, direction):
		self.selectedKey += direction
		for k in range(0, self.no_of_lines, 1):
			no_of_chars = k * self.first_line_len
			if direction == -1:
				if self.selectedKey == no_of_chars - 1:
					self.selectedKey = no_of_chars - 1 + self.first_line_len
					if self.selectedKey > self.max_key:
						self.selectedKey = self.max_key
					break
			elif direction == 1:
				if self.selectedKey == no_of_chars + self.first_line_len:
					self.selectedKey = no_of_chars
					break
				if self.selectedKey > self.max_key:
					self.selectedKey = (self.no_of_lines -1) * self.first_line_len
					break
			elif direction == -self.first_line_len:
				if self.selectedKey < 0:
					self.selectedKey = (self.no_of_lines -1) * self.first_line_len + self.first_line_len + self.selectedKey
					if self.selectedKey > self.max_key:
						self.selectedKey = self.selectedKey - self.first_line_len
				break
			elif direction == self.first_line_len:
				tmp_key = self.selectedKey - self.first_line_len
				if self.selectedKey > self.max_key:
					line_no = k + 1
					if line_no * self.first_line_len > tmp_key:
						self.selectedKey = tmp_key - (line_no - 1) * self.first_line_len
						break
				elif self.selectedKey <= self.max_key:
					break
		self.showActiveKey()

	def left(self):
		self.moveActiveKey(-1)

	def right(self):
		self.moveActiveKey(+1)

	def up(self):
		self.moveActiveKey(-self.first_line_len)

	def down(self):
		self.moveActiveKey(+self.first_line_len)

	def showActiveKey(self):
		self.buildVirtualKeyBoard(self.selectedKey)

	def inShiftKeyList(self,key):
		for KeyList in self.shiftkeys_list:
			for char in KeyList:
				if char == key:
					return True
		return False

	def got_sms_key(self, char):
		return
		if self.inShiftKeyList(char):
			self.shiftMode = True
			list = self.shiftkeys_list
		else:
			self.shiftMode = False
			list = self.keys_list
		selkey = 0
		for keylist in list:
			for key in keylist:
				if key == char:
					self.selectedKey = selkey
					self.showActiveKey()
					return
				else:
					selkey += 1

	def keyGotAscii(self):
		try:
			from Components.config import getCharValue
			char = getCharValue(getPrevAsciiCode())
		except:
			char = unichr(getPrevAsciiCode())
		if len(str(char)) == 1:
			char = char.encode("utf-8")
		if self.inShiftKeyList(char):
			self.shiftMode = True
			list = self.shiftkeys_list
		else:
			self.shiftMode = False
			list = self.keys_list
		if char == " ":
			char = "SPACE"
		selkey = 0
		for keylist in list:
			for key in keylist:
				if key == char:
					self.selectedKey = selkey
					self.okClicked()
					self.showActiveKey()
					return
				else:
					selkey += 1

	def VirtualKeyBoardEntryComponent(self, entry):
		keys = entry[0]
		selectedKey = entry[1]
		shiftMode = entry[2]

		plugin_path = mp_globals.pluginPath
		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		vkeys = ["backspace", "bg", "clr", "esc", "ok", "sel", "shift", "shift_sel", "space"]
		for vkey in vkeys:
			path = "%s/%s/images/vkey_%s.png" % (skin_path, config.mediaportal.skin.value, vkey)
			if not fileExists(path):
				path = skin_path + mp_globals.skinFallback + "/images/vkey_%s.png" % vkey
			if not fileExists(path):
				path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/vkey_%s.png" % vkey)
			globals()['key_%s' % vkey] = LoadPixmap(cached=True, path=path)
		res = [ (keys) ]

		x = 0
		count = 0
		if shiftMode:
			shiftkey_png = key_shift_sel
		else:
			shiftkey_png = key_shift
		for key in keys:
			width = None
			height = None
			if key == "EXIT":
				width = key_esc.size().width()
				height = key_esc.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_esc))
			elif key == "BACKSPACE":
				width = key_backspace.size().width()
				height = key_backspace.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_backspace))
			elif key == "CLEAR":
				width = key_clr.size().width()
				height = key_clr.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_clr))
			elif key == "SHIFT":
				width = shiftkey_png.size().width()
				height = shiftkey_png.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=shiftkey_png))
			elif key == "SPACE":
				width = key_space.size().width()
				height = key_space.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_space))
			elif key == "OK":
				width = key_ok.size().width()
				height = key_ok.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_ok))
			else:
				width = key_bg.size().width()
				height = key_bg.size().height()
				res.extend((
					MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_bg),
					MultiContentEntryText(pos=(x, 0), size=(width, height), font=0, text=key.encode("utf-8"), flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER)
				))

			if selectedKey == count:
				width = key_sel.size().width()
				height = key_sel.size().height()
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, 0), size=(width, height), png=key_sel))

			if width is not None:
				x += width
			else:
				x += 45
			count += 1
			if height is not None:
				if config.mediaportal.skin.value == "clean_fhd":
					self.ml.l.setFont(0, gFont('mediaportal_clean', height - 15))
				else:
					self.ml.l.setFont(0, gFont('mediaportal', height - 15))
		return res