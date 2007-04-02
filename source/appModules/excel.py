#appModules/excel.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 Michael Curran <mick@kulgan.net>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import time
import re
import ctypes
import pythoncom
import win32com.client
import comtypes.automation
import IAccessibleHandler
import audio
import debug
from keyUtils import sendKey, key
import NVDAObjects
import appModuleHandler

re_dollaredAddress=re.compile(r"^\$?([a-zA-Z]+)\$?([0-9]+)")

class appModule(appModuleHandler.appModule):

	def __init__(self,appName,appWindow):
		appModuleHandler.appModule.__init__(self,appName,appWindow)
		NVDAObjects.IAccessible.registerNVDAObjectClass(self,"EXCEL6",IAccessibleHandler.ROLE_SYSTEM_CLIENT,NVDAObject_excelEditableCell)
		NVDAObjects.IAccessible.registerNVDAObjectClass(self,"EXCEL7",IAccessibleHandler.ROLE_SYSTEM_CLIENT,NVDAObject_excelTable)

	def __del__(self):
		NVDAObjects.IAccessible.unregisterNVDAObjectClass(self,"EXCEL6",IAccessibleHandler.ROLE_SYSTEM_CLIENT)
		NVDAObjects.IAccessible.unregisterNVDAObjectClass(self,"EXCEL7",IAccessibleHandler.ROLE_SYSTEM_CLIENT)
		appModuleHandler.appModule.__del__(self)

class NVDAObject_excelEditableCell(NVDAObjects.winEdit.NVDAObject_winEdit):

	def _get_role(self):
		return IAccessibleHandler.ROLE_SYSTEM_TEXT

class NVDAObject_excelTable(NVDAObjects.IAccessible.NVDAObject_IAccessible):

	def __init__(self,*args,**vars):
		NVDAObjects.IAccessible.NVDAObject_IAccessible.__init__(self,*args,**vars)
		ptr=ctypes.c_void_p()
		if ctypes.windll.oleacc.AccessibleObjectFromWindow(self.windowHandle,IAccessibleHandler.OBJID_NATIVEOM,ctypes.byref(comtypes.automation.IDispatch._iid_),ctypes.byref(ptr))!=0:
			raise OSError("No native object model")
		#We use pywin32 for large IDispatch interfaces since it handles them much better than comtypes
		o=pythoncom._univgw.interface(ptr.value,pythoncom.IID_IDispatch)
		t=o.GetTypeInfo()
		a=t.GetTypeAttr()
		oleRepr=win32com.client.build.DispatchItem(attr=a)
		self.excelObject=win32com.client.CDispatch(o,oleRepr)

	def _get_role(self):
		return IAccessibleHandler.ROLE_SYSTEM_TABLE

	def getSelectedRange(self):
		return self.excelObject.Selection
	selectedRange=property(fget=getSelectedRange)

	def getActiveCell(self):
		time.sleep(0.01)
		return self.excelObject.ActiveCell
	activeCell=property(fget=getActiveCell)

	def getCellAddress(self,cell):
		return re_dollaredAddress.sub(r"\1\2",cell.Address)

	def getCellText(self,cell):
		return cell.Text

	def cellHasFormula(self,cell):
		return cell.HasFormula

	def speakSelection(self):
		try:
			cells=self.getSelectedRange()
			if cells.Count>1:
				first=cells.Item(1)
				last=cells.Item(cells.Count)
				audio.speakMessage((_("selected")+" %s %s "+_("through")+" %s %s")%(self.getCellAddress(first),self.getCellText(first),self.getCellAddress(last),self.getCellText(last)))
			else:
				text=self.getCellAddress(self.getActiveCell())
				if self.cellHasFormula(self.getActiveCell()):
					text+=" "+_("has formula")
				text+=" %s"%self.getCellText(self.getActiveCell())
				audio.speakMessage(text)
		except:
			pass

	def getFontName(self,cell):
		return cell.Font.Name

	def getFontSize(self,cell):
		return int(cell.Font.Size)

	def isBold(self,cell):
		return cell.Font.Bold

	def isItalic(self,cell):
		return cell.Font.Italic

	def isUnderline(self,cell):
		return cell.Font.Underline

	def event_gainFocus(self):
		self.speakObject()
		self.speakSelection()

	def script_moveByCell(self,keyPress,nextScript):
		"""Moves to a cell and speaks its coordinates and content"""
		sendKey(keyPress)
		self.speakSelection()
	script_moveByCell.__doc__=_("Moves to a cell and speaks its coordinates and content")

	def text_reportPresentation(self,offset):
		"""Reports the current font name, font size, font attributes of the active cell"""
		audio.speakMessage(_("font")+": %s"%self.getFontName(self.getActiveCell()))
		audio.speakMessage("%s %s"%(self.getFontSize(self.getActiveCell()),_("point")))
		if self.isBold(self.getActiveCell()):
			audio.speakMessage(_("bold"))
		if self.isItalic(self.getActiveCell()):
			audio.speakMessage(_("italic"))
		if self.isUnderline(self.getActiveCell()):
			audio.speakMessage(_("underline"))

[NVDAObject_excelTable.bindKey(keyName,scriptName) for keyName,scriptName in [
	("ExtendedUp","moveByCell"),
	("ExtendedDown","moveByCell"),
	("ExtendedLeft","moveByCell"),
	("ExtendedRight","moveByCell"),
	("Control+ExtendedUp","moveByCell"),
	("Control+ExtendedDown","moveByCell"),
	("Control+ExtendedLeft","moveByCell"),
	("Control+ExtendedRight","moveByCell"),
	("ExtendedHome","moveByCell"),
	("ExtendedEnd","moveByCell"),
	("Control+ExtendedHome","moveByCell"),
	("Control+ExtendedEnd","moveByCell"),
	("Shift+ExtendedUp","moveByCell"),
	("Shift+ExtendedDown","moveByCell"),
	("Shift+ExtendedLeft","moveByCell"),
	("Shift+ExtendedRight","moveByCell"),
	("Shift+Control+ExtendedUp","moveByCell"),
	("Shift+Control+ExtendedDown","moveByCell"),
	("Shift+Control+ExtendedLeft","moveByCell"),
	("Shift+Control+ExtendedRight","moveByCell"),
	("Shift+ExtendedHome","moveByCell"),
	("Shift+ExtendedEnd","moveByCell"),
	("Shift+Control+ExtendedHome","moveByCell"),
	("Shift+Control+ExtendedEnd","moveByCell"),
]]
