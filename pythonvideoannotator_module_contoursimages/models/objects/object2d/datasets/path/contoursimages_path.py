from pysettings import conf
import cv2, numpy as np, os
import base64
from PyQt4 import QtGui, QtCore


class ControursImagesPath(object):

	def __init__(self, name=None):
		super(ControursImagesPath, self).__init__(name)

		self._avg_colors = []
		
	######################################################################
	### EVENTS ###########################################################
	######################################################################

	def name_updated(self, newname):
		super(ControursImagesPath, self).name_updated(newname)
		if hasattr(self,'mainwindow'): self.mainwindow.contoursimages_window.update_datasets()




	def create_contoursimages_tree_nodes(self):

		self.create_group_node('contour > color average', icon=conf.ANNOTATOR_ICON_COLORS)
		
		self.create_data_node('contour > color average > red', 	icon=conf.ANNOTATOR_ICON_COLOR_COMPONENT)
		self.create_data_node('contour > color average > green',icon=conf.ANNOTATOR_ICON_COLOR_COMPONENT)
		self.create_data_node('contour > color average > blue', icon=conf.ANNOTATOR_ICON_COLOR_COMPONENT)
		
	######################################################################
	### FUNCTIONS ########################################################
	######################################################################

	################# CONTOUR #########################################################

	def get_contour_coloraverage_red_value(self, index):
		color = self.get_color_avg(index)
		return None if color is None else color[0]
		
	def get_contour_coloraverage_green_value(self, index):
		color = self.get_color_avg(index)
		return None if color is None else color[1]

	def get_contour_coloraverage_blue_value(self, index):
		color = self.get_color_avg(index)
		return None if color is None else color[2]


	######################################################################
	### DATA ACCESS FUNCTIONS ############################################
	######################################################################

	def get_color_avg(self, index):
		if index<0 or index>=len(self._avg_colors): return None
		return self._avg_colors[index] if self._avg_colors[index] is not None else None

	def set_color_avg(self, index, color):
		if not hasattr(self, 'treenode_contour_coloraverage'): self.create_contoursimages_tree_nodes()
		# add colors in case they do not exists
		if index >= len(self._avg_colors):
			for i in range(len(self._avg_colors), index + 1): self._avg_colors.append(None)
		self._avg_colors[index] = color

	


	######################################################################################
	#### IO FUNCTIONS ####################################################################
	######################################################################################


	def save(self, data, datasets_path=None):
		data = super(ControursImagesPath, self).save(data, datasets_path)
		dataset_path = data['path']
		
		colors_file = os.path.join(dataset_path, 'colors-average.csv')
		with open(colors_file, 'wb') as outfile:
			outfile.write(';'.join(['frame','red','green', 'blue'])+'\n' )
			for index in range(len(self._path)):
				color = self.get_color_avg(index)
				row = [index] + ([None, None, None] if color is None else list(color))
				outfile.write(';'.join( map(str,row) ))
				outfile.write('\n')

		return data

	def load(self, data, dataset_path=None):
		super(ControursImagesPath, self).load(data, dataset_path)
		colors_file = os.path.join(dataset_path, 'colors-average.csv')
		
		if os.path.exists(colors_file):
			with open(colors_file, 'r') as infile:
				infile.readline()
				for i, line in enumerate(infile):
					csvrow = line[:-1].split(';')
					
					frame 	= int(csvrow[0])
					red 	= float(csvrow[1]) if csvrow[1] is not None and csvrow[1]!='None' else None
					green 	= float(csvrow[2]) if csvrow[2] is not None and csvrow[2]!='None' else None
					blue 	= float(csvrow[3]) if csvrow[3] is not None and csvrow[3]!='None' else None

					self.set_color_avg(frame, (red,green,blue))