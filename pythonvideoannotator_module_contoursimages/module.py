import cv2
from pysettings import conf
from pythonvideoannotator_module_contoursimages.contoursimages_window import ContoursImagesWindow


class Module(object):

	def __init__(self):
		"""
		This implements the Path edition functionality
		"""
		super(Module, self).__init__()

		
		self.contoursimages_window = ContoursImagesWindow(self)


		self.mainmenu[1]['Modules'].append(
			{"Extract the contours' images": self.contoursimages_window.show, 'icon':conf.ANNOTATOR_ICON_IMAGE },			
		)



	
	######################################################################################
	#### IO FUNCTIONS ####################################################################
	######################################################################################

	"""
	def save(self, data, project_path=None):
		#data = super(Module, self).save(data, project_path)
		#data['tracking-settings'] = self.tracking_window.save_form({})
		return data

	def load(self, data, project_path=None):
		super(Module, self).load(data, project_path)
		#if 'tracking-settings' in data: self.tracking_window.load_form(data['tracking-settings'])
		"""