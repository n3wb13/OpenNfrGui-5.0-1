from MenuList import MenuList
from Tools.Directories import SCOPE_ACTIVE_SKIN, resolveFilename
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists
import skin
from enigma import getDesktop

def ChoiceEntryComponent(key="", text=None):
    if getDesktop(0).size().width() == 1920:
	if not text: text = ["--"]
	res = [ text ]
	if text[0] == "--":
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 00, 1000, 25, 0, RT_HALIGN_LEFT, "-"*200))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 65, 2, 1000, 40, 0, RT_HALIGN_LEFT, text[0]))
		pngfile = resolveFilename(SCOPE_ACTIVE_SKIN, "buttons/key_" + key + ".png")
		if fileExists(pngfile):
			png = LoadPixmap(pngfile)
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 35, 35, png))
	return res
    if getDesktop(0).size().width() == 1280:
	if not text: text = ["--"]
	res = [ text ]
	if text[0] == "--":
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 00, 800, 25, 0, RT_HALIGN_LEFT, "-"*200))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 45, 00, 800, 25, 0, RT_HALIGN_LEFT, text[0]))
		pngfile = resolveFilename(SCOPE_ACTIVE_SKIN, "buttons/key_" + key + ".png")
		if fileExists(pngfile):
			png = LoadPixmap(pngfile)
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 5, 0, 35, 30, png))
	return res
class ChoiceList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=False):
            if getDesktop(0).size().width() == 1920:	
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font = skin.fonts["ChoiceList"]
		self.l.setFont(0, gFont("Regular", 28))
		self.l.setFont(1, gFont("Regular", 22))
		self.l.setItemHeight(font[2])
		self.selection = selection
            else:
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font = skin.fonts["ChoiceList"]
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])
		self.selection = selection
                            
	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)
		self.instance.setWrapAround(True)
