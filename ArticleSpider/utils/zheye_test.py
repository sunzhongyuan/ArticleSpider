# -*- coding: utf-8 -*-
__author__ = 'zyzy'

from zheye import zheye


z = zheye()
positions = z.Recognize('a.gif')
print(positions)
