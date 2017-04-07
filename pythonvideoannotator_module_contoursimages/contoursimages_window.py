import pyforms, math, cv2, os, numpy as np
from pysettings import conf
from pyforms import BaseWidget
from pyforms.Controls import ControlNumber
from pyforms.Controls import ControlList
from pyforms.Controls import ControlCombo
from pyforms.Controls import ControlDir
from pyforms.Controls import ControlSlider
from pyforms.Controls import ControlButton
from pyforms.Controls import ControlCheckBox
from pyforms.Controls import ControlCheckBoxList
from pyforms.Controls import ControlEmptyWidget
from pyforms.Controls import ControlProgress

from pythonvideoannotator_models_gui.dialogs import DatasetsDialog
from pythonvideoannotator_models_gui.models.video.objects.object2d.datasets.contours import Contours
from pythonvideoannotator_models_gui.models.video.objects.object2d.datasets.path import Path

import simplejson as json

def points_angle(p1, p2): 
	x1, y1 = p1
	x2, y2 = p2
	rads = math.atan2(-(y2-y1),x2-x1)
	rads %= 2*np.pi
	return rads

def getTranslationMatrix2d(dx, dy):
	"""
	Returns a numpy affine transformation matrix for a 2D translation of
	(dx, dy)
	"""
	return np.matrix([[1, 0, dx], [0, 1, dy], [0, 0, 1]])

def rotate_image(image, angle):
	"""
	Rotates the given image about it's centre
	"""

	image_size = (image.shape[1], image.shape[0])
	image_center = tuple(np.array(image_size) / 2)

	rot_mat = np.vstack([cv2.getRotationMatrix2D(image_center, angle, 1.0), [0, 0, 1]])
	trans_mat = np.identity(3)

	w2 = image_size[0] * 0.5
	h2 = image_size[1] * 0.5

	rot_mat_notranslate = np.matrix(rot_mat[0:2, 0:2])

	tl = (np.array([-w2, h2]) * rot_mat_notranslate).A[0]
	tr = (np.array([w2, h2]) * rot_mat_notranslate).A[0]
	bl = (np.array([-w2, -h2]) * rot_mat_notranslate).A[0]
	br = (np.array([w2, -h2]) * rot_mat_notranslate).A[0]

	x_coords = [pt[0] for pt in [tl, tr, bl, br]]
	x_pos = [x for x in x_coords if x > 0]
	x_neg = [x for x in x_coords if x < 0]

	y_coords = [pt[1] for pt in [tl, tr, bl, br]]
	y_pos = [y for y in y_coords if y > 0]
	y_neg = [y for y in y_coords if y < 0]

	right_bound = np.max(x_pos)
	left_bound = np.min(x_neg)
	top_bound = np.max(y_pos)
	bot_bound = np.min(y_neg)

	new_w = int(np.abs(right_bound - left_bound))
	new_h = int(np.abs(top_bound - bot_bound))
	new_image_size = (new_w, new_h)

	new_midx = new_w * 0.5
	new_midy = new_h * 0.5

	dx = int(new_midx - w2)
	dy = int(new_midy - h2)

	trans_mat = getTranslationMatrix2d(dx, dy)
	affine_mat = (np.matrix(trans_mat) * np.matrix(rot_mat))[0:2, :]
	result = cv2.warpAffine(image, affine_mat, new_image_size, flags=cv2.INTER_LINEAR)

	return result

class ContoursImagesWindow(BaseWidget):

	def __init__(self, parent=None):
		super(ContoursImagesWindow, self).__init__('Contours images', parent_win=parent)
		self.mainwindow = parent

		if conf.PYFORMS_USE_QT5:
			self.layout().setContentsMargins(5,5,5,5)
		else:
			self.layout().setMargin(5)

		#self.layout().setMargin(5)
		self.setMinimumHeight(400)
		self.setMinimumWidth(800)

		self._datasets_panel	= ControlEmptyWidget('Paths')
		self._progress  	= ControlProgress('Progress')		
		self._apply 		= ControlButton('Apply', checkable=True)

		self._exportimgs    = ControlCheckBox('Export the images')
		self._exportmargin  = ControlSlider('Cutting margin', 0, 0, 300)
		self._mask_images   = ControlCheckBox('Use the contour as a mask')
		self._mask_margin   = ControlSlider('Mark margin', 0, 0, 100)

		self._maskradius	= ControlCheckBox('Use a circular mask')
		self._radius 		= ControlSlider('Mask radius', 1, 1, 300)

		self._exportdataset    = ControlDir('Export contours to dataset')
		self._rotateimgs    = ControlCheckBox('Rotate the images vertically')

		
		self._formset = [
			'info: This module add to the contour properties extrated from its image',
			'_datasets_panel',
			'=',
			' ',
			'Export the contours images',
			'_exportimgs',
			'_exportdataset',
			'_exportmargin', 
			('_mask_images','_mask_margin'),
			'_rotateimgs',
			('_maskradius','_radius'),
			' ',
			'_apply',
			'_progress'
		]

		self.load_order = ['_datasets_panel']

		self.datasets_dialog 		= DatasetsDialog(self)
		self._datasets_panel.value = self.datasets_dialog
		self.datasets_dialog.datasets_filter = lambda x: isinstance(x, (Contours,Path) )

		self._apply.value		= self.__apply_event
		self._apply.icon 		= conf.ANNOTATOR_ICON_PATH

		self._exportimgs.changed_event 	= self.__exportimgs_changed_evt
		self._exportimgs.value 			= False
		self._mask_images.changed_event = self.__mask_images_changed_evt
		self._mask_images.value			= False
		self._maskradius.changed_event  = self.__maskradius_changed_evt
		self._maskradius.value 			= False

		self._exportdataset.value = os.getcwd()

		self._progress.hide()

	def init_form(self):
		super(ContoursImagesWindow, self). init_form()
		self.datasets_dialog.project = self.mainwindow.project

	###########################################################################
	### EVENTS ################################################################
	###########################################################################


	def __exportimgs_changed_evt(self):
		if self._exportimgs.value:
			self._exportmargin.enabled  = True
			self._mask_images.enabled   = True
			self._exportdataset.enabled    = True
			self._rotateimgs.enabled   	= True
		else:
			self._exportmargin.enabled  = False
			self._mask_images.enabled   = False
			self._exportdataset.enabled    = False
			self._rotateimgs.enabled   	= False


	def __mask_images_changed_evt(self):
		if self._mask_images.value:
			self._mask_margin.enabled 	= True
		else:
			self._mask_margin.enabled	= False

	def __maskradius_changed_evt(self):
		if self._maskradius.value:
			self._radius.enabled 	= True
		else:
			self._radius.enabled	= False

	###########################################################################
	### PROPERTIES ############################################################
	###########################################################################

	@property
	def datasets(self): return self.datasets_dialog.datasets
	

	@property
	def player(self): return self._filter._player
	
	def __apply_event(self):

		if self._apply.checked:
			dilate_mask = self._mask_margin.enabled and self._mask_margin.value>0

			self._datasets_panel.enabled 	= False			
			self._exportimgs.enabled    = False
			self._exportmargin.enabled  = False
			self._mask_images.enabled   = False
			self._exportdataset.enabled    = False
			self._rotateimgs.enabled   	= False
			self._mask_margin.enabled	= False
			self._mask_margin.enabled   = False
			self._apply.label 			= 'Cancel'

			total_2_analyse  = 0
			for video, (begin, end), datasets in self.datasets_dialog.selected_data:
				capture 		 = video.video_capture
				total_2_analyse += end-begin

			self._progress.min = 0
			self._progress.max = total_2_analyse
			self._progress.show()

			if self._exportimgs.value:
				export_dataset = os.path.join(self._exportdataset.value, 'contours-images')
				if not os.path.exists(export_dataset): os.makedirs(export_dataset)
			else:
				export_dataset = None

			if dilate_mask:
				kernel_size = self._mask_margin.value
				if (kernel_size % 2)==0: kernel_size+=1
				kernel = np.ones((kernel_size,kernel_size),np.uint8)
			else:
				kernel = None

			count = 0
			for video, (begin, end), datasets in self.datasets_dialog.selected_data:
				if len(datasets)==0: continue
				begin, end = int(begin), int(end)+1
				capture.set(cv2.CAP_PROP_POS_FRAMES, begin); 
				
				blobs_datasets = None

				if export_dataset:
					video_export_dataset = os.path.join(export_dataset, video.name)
					if not os.path.exists(video_export_dataset): os.makedirs(video_export_dataset)
				else:
					video_export_dataset = None

				if video_export_dataset:
					datasets_export_directories = []
					for dataset in datasets:
						dataset_export_dataset = os.path.join(video_export_dataset, dataset.name)
						if not os.path.exists(dataset_export_dataset): os.makedirs(dataset_export_dataset)
						datasets_export_directories.append(dataset_export_dataset)
				else:
					datasets_export_directories = None


				



				for index in range(begin, end+1):
					res, frame = capture.read()
					if not res: break
					if not self._apply.checked: break

					for dataset_index, dataset in enumerate(datasets):
						position = dataset.get_position(index)
						if position is None: continue

						mask = np.zeros_like(frame)
						if self._mask_images.value:
							#create the mask
							# if the dataset is a contour
							if isinstance(dataset, Contours):
								contour = dataset.get_contour(index)
								cv2.drawContours( mask, np.array( [contour] ), -1, (255,255,255), -1 )
								if dilate_mask: mask = cv2.dilate(mask,kernel,iterations=1)
							if self._maskradius.value:
								cv2.circle(mask, position, self._radius.value, (255,255,255), -1)
							frame = cv2.bitwise_and(mask, frame)
						else:
							mask[:,:,:] = 255
						
						# cut the image
						if self._maskradius.value:
							x, y, w, h = position[0]-self._radius.value, position[1]-self._radius.value, 2*self._radius.value, 2*self._radius.value
						elif isinstance(dataset, Contours):
							# find the cut ######################################
							bounding_box = dataset.get_bounding_box(index)
							if bounding_box is None: continue
							x, y, w, h 	= dataset.get_bounding_box(index)
							#####################################################
						else:
							x, y, w, h = position[0], position[1], 1, 1

						x, y, w, h  = x-self._exportmargin.value, y-self._exportmargin.value, w+self._exportmargin.value*2, h+self._exportmargin.value*2
						if x<0: x=0
						if y<0: y=0
						if (x+w)>frame.shape[1]: w = frame.shape[1]-x
						if (y+h)>frame.shape[0]: h = frame.shape[0]-y

						cut = frame[y:y+h, x:x+w]
						
						# calculate colors average ############################
						cut_b, cut_g, cut_r = cv2.split(cut)
						gray = cv2.cvtColor(cut, cv2.COLOR_BGR2GRAY)
						boolean_mask = (mask[y:y+h, x:x+w,0]!=255)
	
						# average the colors using a mask to remove the non contours areas
						r_avg, g_avg, b_avg = \
							np.ma.average(np.ma.array(cut_r, mask=boolean_mask)), \
							np.ma.average(np.ma.array(cut_g, mask=boolean_mask)), \
							np.ma.average(np.ma.array(cut_b, mask=boolean_mask)) 

						dataset.set_color_avg(index, (r_avg, g_avg, b_avg) )

						gray_avg = np.ma.average(np.ma.array(gray, mask=boolean_mask))
						dataset.set_gray_avg(index, gray_avg )						
						#####################################################

						if datasets_export_directories:
							image_dataset = os.path.join(datasets_export_directories[dataset_index], "{0}.png".format(index) )
							
							img_2_save = cut

							# IF the dataset is a contour
							if isinstance(dataset, Contours) and self._rotateimgs.value:
								head, tail = dataset.get_extreme_points(index)
								if head and tail:
									rotation_rad = points_angle( tail, head )
									rotation_deg = math.degrees( rotation_rad )
									rotation = 90-rotation_deg
									img_2_save = rotate_image(img_2_save, rotation)

							cv2.imwrite(image_dataset, img_2_save)

					self._progress.value = count
					count += 1

				

			self._datasets_panel.enabled 	= True	
			self._exportimgs.enabled    = True
			self.__mask_images_changed_evt()
			self.__exportimgs_changed_evt()
			self._apply.label 			= 'Apply'
			self._apply.checked 		= False
			self._progress.hide()





	


if __name__ == '__main__': 
	pyforms.startApp(ContoursImagesWindow)
