#!/usr/bin/env python3

#****************************************************************************
# bases.py, provides conversions of number bases and fractions
#
# ConvertAll, a units conversion program
# Copyright (C) 2019, Douglas W. Bell
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License, either Version 2 or any later
# version.  This program is distributed in the hope that it will be useful,
# but WITTHOUT ANY WARRANTY.  See the included LICENSE file for details.
#*****************************************************************************

import math
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (QCheckBox, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSpinBox,
                             QVBoxLayout)


class BasesDialog(QDialog):
    """A dialog for conversion of number bases.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint |
                            Qt.WindowSystemMenuHint)
        self.setWindowTitle(_('Base Conversions'))
        self.value = 0
        self.numBits = 32
        self.twosComplement = False
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.addSpacing(3)
        decimalLabel = QLabel(_('&Decmal'))
        layout.addWidget(decimalLabel)
        decimalEdit = QLineEdit()
        decimalLabel.setBuddy(decimalEdit)
        decimalEdit.base = 10
        decRegEx = QRegularExpression('[-0-9]*')
        decimalEdit.setValidator(QRegularExpressionValidator(decRegEx))
        layout.addWidget(decimalEdit)
        layout.addSpacing(8)
        hexLabel = QLabel(_('&Hex'))
        layout.addWidget(hexLabel)
        hexEdit = QLineEdit()
        hexLabel.setBuddy(hexEdit)
        hexEdit.base = 16
        hexRegEx = QRegularExpression('[-0-9a-fA-F]*')
        hexEdit.setValidator(QRegularExpressionValidator(hexRegEx))
        layout.addWidget(hexEdit)
        layout.addSpacing(8)
        octalLabel = QLabel(_('&Octal'))
        layout.addWidget(octalLabel)
        octalEdit = QLineEdit()
        octalLabel.setBuddy(octalEdit)
        octalEdit.base = 8
        octRegEx = QRegularExpression('[-0-7]*')
        octalEdit.setValidator(QRegularExpressionValidator(octRegEx))
        layout.addWidget(octalEdit)
        layout.addSpacing(8)
        binaryLabel = QLabel(_('&Binary'))
        layout.addWidget(binaryLabel)
        binaryEdit = QLineEdit()
        binaryLabel.setBuddy(binaryEdit)
        binaryEdit.base = 2
        binRegEx = QRegularExpression('[-01]*')
        binaryEdit.setValidator(QRegularExpressionValidator(binRegEx))
        layout.addWidget(binaryEdit)
        layout.addSpacing(8)
        self.bitsButton = QPushButton('')
        self.setButtonLabel()
        layout.addWidget(self.bitsButton)
        self.bitsButton.clicked.connect(self.changeBitSettings)
        layout.addSpacing(8)
        closeButton = QPushButton(_('&Close'))
        layout.addWidget(closeButton)
        closeButton.clicked.connect(self.close)
        layout.addSpacing(3)
        self.editors = (decimalEdit, hexEdit, octalEdit, binaryEdit)
        for editor in self.editors:
            editor.textEdited.connect(self.updateValue)

    def updateValue(self):
        """Update the current number base and then the other editors.
        """
        activeEditor = self.focusWidget()
        text = activeEditor.text()
        if text:
            try:
                self.value = baseNum(text, activeEditor.base, self.numBits,
                                     self.twosComplement)
            except ValueError:
                QMessageBox.warning(self, 'ConvertAll', _('Number overflow'))
                activeEditor = None
        else:
            self.value = 0
        for editor in self.editors:
            if editor is not activeEditor:
                editor.setText(baseNumStr(self.value, editor.base,
                                          self.numBits, self.twosComplement))

    def changeBitSettings(self):
        """Show the dialog to update bit settings.
        """
        dlg = QDialog(self)
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint |
                           Qt.WindowSystemMenuHint)
        dlg.setWindowTitle(_('Bit Settings'))
        topLayout = QVBoxLayout(dlg)
        dlg.setLayout(topLayout)
        bitLayout = QHBoxLayout()
        topLayout.addLayout(bitLayout)
        bitSizeBox = QSpinBox(dlg)
        bitSizeBox.setMinimum(1)
        bitSizeBox.setMaximum(256)
        bitSizeBox.setSingleStep(16)
        bitSizeBox.setValue(self.numBits)
        bitLayout.addWidget(bitSizeBox)
        label = QLabel(_('&bit overflow limit'), dlg)
        label.setBuddy(bitSizeBox)
        bitLayout.addWidget(label)
        twoCompBox = QCheckBox(_("&Use two's complement\n"
                                 "for negative numbers"), dlg)
        twoCompBox.setChecked(self.twosComplement)
        topLayout.addWidget(twoCompBox)

        ctrlLayout = QHBoxLayout()
        topLayout.addLayout(ctrlLayout)
        ctrlLayout.addStretch(0)
        okButton = QPushButton(_('&OK'), dlg)
        ctrlLayout.addWidget(okButton)
        okButton.clicked.connect(dlg.accept)
        cancelButton = QPushButton(_('&Cancel'), dlg)
        ctrlLayout.addWidget(cancelButton)
        cancelButton.clicked.connect(dlg.reject)
        if dlg.exec_() == QDialog.Accepted:
            self.numBits = bitSizeBox.value()
            self.twosComplement = twoCompBox.isChecked()
            self.setButtonLabel()

    def setButtonLabel(self):
        """Set the text label on the bitsButton to match settings.
        """
        text = '{0} {1}, '.format(self.numBits, _('bit'))
        if self.twosComplement:
            text += _('&two\'s complement')
        else:
            text += _('no &two\'s complement')
        self.bitsButton.setText(text)


class FractionDialog(QDialog):
    """A dialog for conversion of numbers into fractions.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint |
                            Qt.WindowSystemMenuHint)
        self.setWindowTitle(_('Fraction Conversions'))
        layout = QVBoxLayout(self)


def baseNumStr(number, base, numBits=32, twosComplement=False):
    """Return string of number in given base (2-16).

    Arguments:
        base -- the number base to convert to
        numBits -- the number of bits available for the result
        twosComplement -- if True, use two's complement for negative numbers
    """
    digits = '0123456789abcdef'
    number = int(round(number))
    result = ''
    sign = ''
    if number == 0:
        return '0'
    if twosComplement:
        if number >= 2**(numBits - 1) or \
                number < -2**(numBits - 1):
            return 'overflow'
        if number < 0:
            number = 2**numBits + number
    else:
        if number < 0:
            number = abs(number)
            sign = '-'
        if number >= 2**numBits:
            return 'overflow'
    while number:
        number, remainder = divmod(number, base)
        result = '{0}{1}'.format(digits[remainder], result)
    return '{0}{1}'.format(sign, result)


def baseNum(numStr, base, numBits=32, twosComplement=False):
    """Convert number string to an integer using given base.

    Arguments:
        base -- the number base to convert from
        numBits -- the number of bits available for the numStr
        twosComplement -- if True, use two's complement for negative numbers
    """
    numStr = numStr.replace(' ', '')
    if numStr == '-':
        return 0
    num = int(numStr, base)
    if num >= 2**numBits:
        raise ValueError
    if base != 10 and twosComplement and num >= 2**(numBits - 1):
        num = num - 2**numBits
    return num


def calcFraction(num, precision, powerOfTwo=False):
    """Return a tuple of mixed number, numerator and denominator.

    Raise a ValueError if no fraction is found.
    Arguments:
        precision -- num of decimal places for result accuracy
        powerOfTwo -- if True, restrict the denominator to powers of 2
    """
    isNegative = num < 0
    num = math.fabs(num)
    mixed = math.floor(num)
    num -= mixed
    denom = 2
    denomLimit = 10**precision
    accuracy = 0.6 / 10**precision
    while denom < denomLimit:
        numer = round(num * denom)
        if numer > 0 and abs(num - numer / denom) < accuracy:
            if isNegative:
                mixed = -mixed
                numer = -numer
            return (mixed, numer, denom)
        denom = denom + 1 if not powerOfTwo else denom * 2
    raise ValueError

def listFractions(decimal):
    """Return a list of numerator, denominator tuples.

    The tuples approximate the decimal, becoming more accurate.
    Arguments:
        decimal -- a real number to approximate as a fraction
    """
    results = []
    denom = 2
    denomLimit = 1000000
    minDelta = denomLimit
    numer = round(decimal * denom)
    delta = abs(decimal - numer / denom)
    while denom < denomLimit:
        if numer != 0:
            nextNumer = round(decimal * (denom + 1))
            nextDelta = abs(decimal - nextNumer / (denom + 1))
            if delta < minDelta and delta <= nextDelta:
                results.append((numer, denom))
                if delta == 0.0:
                    break
                minDelta = delta
            numer = nextNumer
            delta = nextDelta
        denom += 1
    if results:  # handle when first result is a whole num (2/2, 4/2, etc.)
        numer, denom = results[0]
        if denom == 2 and numer / denom == round(numer / denom):
            results[0] = (round(numer / denom), 1)
    return results
