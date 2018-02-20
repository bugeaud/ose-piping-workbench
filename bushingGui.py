# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 January 2018
# Create a bushing-fitting.

import math
import os.path

from PySide import QtCore, QtGui
import FreeCAD

import OSEBase
from bushing import *
from piping import *
import pipingGui


class MainDialog(QtGui.QDialog):
	QSETTINGS_APPLICATION = "OSE piping workbench"
	QSETTINGS_NAME = "bushing user input"
	def __init__(self, document, table):
		super(MainDialog, self).__init__()
		self.document = document
		self.table = table
		self.initUi()
	def initUi(self): 
		Dialog = self # Added 
		self.result = -1 
		self.setupUi(self)
		# Fill table with dimensions. 
		self.initTable()

		# Restore previous user input. Ignore exceptions to prevent this part
		# part of the code to prevent GUI from starting, once settings are broken.
		try:
			self.restoreInput()
		except Exception as e:
			print ("Could not restore old user input!")
			print(e)
		self.show()

# The following lines are from QtDesigner .ui-file processed by pyside-uic
# pyside-uic --indent=0 create-bushing.ui -o tmp.py
#
# The file paths needs to be adjusted manually. For example
# os.path.join(OSEBase.IMAGE_PATH, "bushing-dimensions.png")
	def setupUi(self, Dialog):
		Dialog.setObjectName("Dialog")
		Dialog.resize(803, 666)
		self.verticalLayout = QtGui.QVBoxLayout(Dialog)
		self.verticalLayout.setObjectName("verticalLayout")
		self.checkBoxCreateSolid = QtGui.QCheckBox(Dialog)
		self.checkBoxCreateSolid.setChecked(True)
		self.checkBoxCreateSolid.setObjectName("checkBoxCreateSolid")
		self.verticalLayout.addWidget(self.checkBoxCreateSolid)
		self.tableViewParts = QtGui.QTableView(Dialog)
		self.tableViewParts.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.tableViewParts.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableViewParts.setObjectName("tableViewParts")
		self.verticalLayout.addWidget(self.tableViewParts)
		self.label_2 = QtGui.QLabel(Dialog)
		self.label_2.setTextFormat(QtCore.Qt.AutoText)
		self.label_2.setWordWrap(True)
		self.label_2.setObjectName("label_2")
		self.verticalLayout.addWidget(self.label_2)
		self.label = QtGui.QLabel(Dialog)
		self.label.setText("")
		self.label.setPixmap(os.path.join(OSEBase.IMAGE_PATH, "bushing-dimensions.png"))
		self.label.setAlignment(QtCore.Qt.AlignCenter)
		self.label.setObjectName("label")
		self.verticalLayout.addWidget(self.label)
		self.buttonBox = QtGui.QDialogButtonBox(Dialog)
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		self.verticalLayout.addWidget(self.buttonBox)

		self.retranslateUi(Dialog)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
		QtCore.QMetaObject.connectSlotsByName(Dialog)

	def retranslateUi(self, Dialog):
		Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create Bushing", None, QtGui.QApplication.UnicodeUTF8))
		self.checkBoxCreateSolid.setText(QtGui.QApplication.translate("Dialog", "Create Solid", None, QtGui.QApplication.UnicodeUTF8))
		self.label_2.setText(QtGui.QApplication.translate("Dialog", "<html><head/><body><p>To construct a part, only these dimensions are used: L, N, POD, PID1, and POD1. All other dimensions are used for inromation.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))


	def initTable(self):
		# Read table data from CSV
		self.model = pipingGui.PartTableModel(self.table.headers, self.table.data)
		self.tableViewParts.setModel(self.model)
		
	def getSelectedPartName(self):
		sel = self.tableViewParts.selectionModel()
		if sel.isSelected:
			if len(sel.selectedRows())> 0:
				rowIndex = sel.selectedRows()[0].row()
				return self.model.getPartName(rowIndex)
		return None

	def selectPartByName(self, partName):
		"""Select first row with a part with a name partName."""
		if partName is not None:
			row_i = self.model.getPartRowIndex(partName)
			if row_i >= 0:
				self.tableViewParts.selectRow(row_i)

	def accept(self):
		"""User clicked OK"""
		# If there is no active document, show a warning message and do nothing.
		if self.document is None:
			text = "I have not found any active document were I can create a corner fitting.\n"\
				"Use menu File->New to create a new document first, "\
				"then try to create the corner fitting again."
			msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the corner fitting failed.", text)
			msgBox.exec_()
			super(MainDialog, self).accept()
			return

		# Get suitable row from the the table.
		partName = self.getSelectedPartName()
		createSolid = self.checkBoxCreateSolid.isChecked()
		if partName is not None:
			bushing = BushingFromTable(self.document, self.table)
			bushing.create(partName, createSolid)
			self.document.recompute()
			# Save user input for the next dialog call.
			self.saveInput()
			# Call parent class.
			super(MainDialog, self).accept()
		else:
			msgBox = QtGui.QMessageBox()
			msgBox.setText("Select part")
			msgBox.exec_()

	def saveInput(self):
		"""Store user input for the next run."""
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)
		check = self.checkBoxCreateSolid.checkState()
		settings.setValue("checkBoxCreateSolid", int(check))
		settings.setValue("LastSelectedPartName", self.getSelectedPartName())
		settings.sync()

	def restoreInput(self):
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)
		checkState = QtCore.Qt.CheckState(int(settings.value("checkBoxCreateSolid")))
		self.checkBoxCreateSolid.setCheckState(checkState)
		self.selectPartByName(settings.value("LastSelectedPartName"))

# Before working with macros, try to load the dimension table.
def GuiCheckTable():
	# Check if the CSV file exists.
	if os.path.isfile(CSV_TABLE_PATH) == False:
		text = "This macro requires %s  but this file does not exist."%(CSV_TABLE_PATH)
		msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the bushing failed.", text)
		msgBox.exec_()
		exit(1) # Error

        FreeCAD.Console.PrintMessage("Trying to load CSV file with dimensions: %s"%CSV_TABLE_PATH) 
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)

	if table.hasValidData == False:
		text = 'Invalid %s.\n'\
			'It must contain columns %s.'%(CSV_TABLE_PATH, ", ".join(DIMENSIONS_USED))
		msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the bushing failed.", text)
		msgBox.exec_()
		exit(1) # Error

	return table

#doc=FreeCAD.activeDocument()
#table = GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#form = MainDialog(doc, table)

