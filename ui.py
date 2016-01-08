#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ui.py - simple console UI using Blessings
#
# Copyright (c) 2013 András Veres-Szentkirályi
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function
from blessings import Terminal
from itertools import izip

T = Terminal()
COLORS = [T.cyan, T.green, T.yellow, T.red, T.magenta, T.blue]
width = T.width
if width is None:
	import os
	width = int(os.environ.get('COLUMNS', '80'))

def horizontal_separator():
	print(T.bold_black('-' * (width - 1)))

def print_input_filenames(filenames):
	print('Input files:')
	for color, fn in izip(COLORS, filenames):
		print(' -', color(fn))
