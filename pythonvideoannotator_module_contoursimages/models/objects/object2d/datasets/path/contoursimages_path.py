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
		self.treenode_avgcolor = self.tree.create_child('Color average', icon=conf.ANNOTATOR_ICON_COLORS, parent=self.treenode_countour )
		self.treenode_avgcolor.win = self

		
		self.treenode_avgred = self.tree.create_child('Red', icon=conf.ANNOTATOR_ICON_COLOR_COMPONENT, parent=self.treenode_avgcolor )
		self.treenode_avgred.win = self
		self.tree.add_popup_menu_option(label='View on the timeline', 
			function_action=self.__send_red_avg_to_timeline_event, item=self.treenode_avgred, 
			icon=conf.ANNOTATOR_ICON_TIMELINE)
		
		self.treenode_avggreen = self.tree.create_child('Green', icon=conf.ANNOTATOR_ICON_COLOR_COMPONENT, parent=self.treenode_avgcolor )
		self.treenode_avggreen.win = self
		self.tree.add_popup_menu_option(label='View on the timeline', 
			function_action=self.__send_green_avg_to_timeline_event, item=self.treenode_avggreen, 
			icon=conf.ANNOTATOR_ICON_TIMELINE)
		
		self.treenode_avgblue = self.tree.create_child('Blue', icon=conf.ANNOTATOR_ICON_COLOR_COMPONENT, parent=self.treenode_avgcolor )
		self.treenode_avgblue.win = self
		self.tree.add_popup_menu_option(label='View on the timeline', 
			function_action=self.__send_blue_avg_to_timeline_event, item=self.treenode_avgblue, 
			icon=conf.ANNOTATOR_ICON_TIMELINE)

		self.treenode_avgcolor.win = self.treenode_avgred.win = \
		self.treenode_avggreen.win = self.treenode_avgblue.win = self


	######################################################################
	### FUNCTIONS ########################################################
	######################################################################

	################# CONTOUR #########################################################
		
	def __send_red_avg_to_timeline_event(self):
		data = [(i,self.get_redcolor_avg(i)) for i in range(len(self)) if self.get_redcolor_avg(i) is not None]
		self.mainwindow.add_graph('{0} red color average'.format(self.name), data)

	def __send_green_avg_to_timeline_event(self):
		data = [(i,self.get_greencolor_avg(i)) for i in range(len(self)) if self.get_greencolor_avg(i) is not None]
		self.mainwindow.add_graph('{0} green color average'.format(self.name), data)

	def __send_blue_avg_to_timeline_event(self):
		data = [(i,self.get_bluecolor_avg(i)) for i in range(len(self)) if self.get_bluecolor_avg(i) is not None]
		self.mainwindow.add_graph('{0} blue color average'.format(self.name), data)


	######################################################################
	### DATA ACCESS FUNCTIONS ############################################
	######################################################################

	def get_color_avg(self, index):
		if index<0 or index>=len(self._avg_colors): return None
		return self._avg_colors[index] if self._avg_colors[index] is not None else None

	def set_color_avg(self, index, color):
		if not hasattr(self, 'treenode_avgcolor'): self.create_contoursimages_tree_nodes()
		# add colors in case they do not exists
		if index >= len(self._avg_colors):
			for i in range(len(self._avg_colors), index + 1): self._avg_colors.append(None)
		self._avg_colors[index] = color

	def set_redcolor_avg(self, index, red):
		color = self.get_color_avg(index)
		if color is None: 
			color = red, None, None
		else:
			color = red, color[1], color[2]
		self.set_color_avg(index, color)



	def get_redcolor_avg(self, index):
		color = self.get_color_avg(index)
		return None if color is None else color[0]

	def set_redcolor_avg(self, index, red):
		color = self.get_color_avg(index)
		if color is None: 
			color = red, None, None
		else:
			color = red, color[1], color[2]
		self.set_color_avg(index, color)



	def get_greencolor_avg(self, index):
		color = self.get_color_avg(index)
		return None if color is None else color[0]

	def set_greencolor_avg(self, index, green):
		color = self.get_color_avg(index)
		if color is None: 
			color = None, green, None
		else:
			color = color[0], green, color[2]
		self.set_color_avg(index, color)



	def get_bluecolor_avg(self, index):
		color = self.get_color_avg(index)
		return None if color is None else color[0]

	def set_bluecolor_avg(self, index, blue):
		color = self.get_color_avg(index)
		if color is None: 
			color = None, None, blue
		else:
			color = color[0], color[1], blue
		self.set_color_avg(index, color)
	


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