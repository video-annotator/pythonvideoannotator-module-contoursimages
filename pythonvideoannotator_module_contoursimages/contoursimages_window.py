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
from pyforms.Controls import ControlToolBox

from pythonvideoannotator_models_gui.dialogs import DatasetsDialog
from pythonvideoannotator_models_gui.models.video.objects.object2d.datasets.contours import Contours
from pythonvideoannotator_models_gui.models.video.objects.object2d.datasets.path import Path

import simplejson as json

from pythonvideoannotator_models.utils.tools import points_angle, rotate_image





class ContoursImagesWindow(BaseWidget):

    def __init__(self, parent=None):
        super(ContoursImagesWindow, self).__init__('Contours images', parent_win=parent)
        self.mainwindow = parent

        if conf.PYFORMS_USE_QT5:
            self.layout().setContentsMargins(5,5,5,5)
        else:
            self.layout().setMargin(5)

        self.setMinimumHeight(400)
        self.setMinimumWidth(800)

        self._contourspanel = ControlEmptyWidget('Contours datasets')
        self._progress      = ControlProgress('Progress')       
        self._apply         = ControlButton('Apply', checkable=True)
        self._toolbox       = ControlToolBox('Toolbox')

        #### mask ######################################################
        self._usemaskimg       = ControlCheckBox('Apply a mask to the image')
        self._usemaskdilate    = ControlCheckBox('Dilate the mask and apply it to the image')
        self._maskdilatesize   = ControlSlider('Dilate size', default=0, minimum=0, maximum=100)
        self._usemaskellipse   = ControlCheckBox('Apply the min. ellipse as a mask to the image')
        self._usemaskcircular  = ControlCheckBox('Apply a circular mask to the image')
        self._maskcircularsize = ControlSlider('Circular radius', default=0, minimum=0, maximum=100)
        self._usemaskrect      = ControlCheckBox('Apply the min. rect as a mask to the image')
        ################################################################

        #### margin ####################################################
        self._margin = ControlSlider('Margin size', default=0, minimum=0, maximum=100)
        ################################################################

        #### imagesize #################################################
        self._imagesize = ControlSlider('Image size', default=10, minimum=10, maximum=400)
        ################################################################

        #### use stretch ###############################################
        self._usestretch = ControlCheckBox('Stretch image')
        ################################################################

        #### filter per events #########################################
        self._eventslst  = ControlCheckBoxList('Events', enabled=False)
        self._reloadevts = ControlButton('Reload events', enabled=False, default=self.__reload_events_btn_evt)
        ################################################################

        self._exportdataset = ControlDir('Export contours to dataset')
        self._rotateimgs    = ControlCheckBox('Rotate the images vertically')
        self._useotherorient = ControlCheckBox('Use the orientation from other contours', enabled=False)

        self._orient_datasetspanel = ControlEmptyWidget('Datasets for the orientation', enabled=False)
        
        self._formset = [
            '_toolbox',
            '_exportdataset',
            '_apply',
            '_progress'
        ]

        #datasets painel
        self.datasets_dialog = DatasetsDialog(self)
        self.datasets_dialog.datasets_filter = lambda x: isinstance(x, (Contours,Path) )
        self._contourspanel.value = self.datasets_dialog

        self.orientdatasets_dialog = DatasetsDialog(self)
        self.orientdatasets_dialog.datasets_filter = lambda x: isinstance(x, Contours )
        self.orientdatasets_dialog.interval_visible = False
        self._orient_datasetspanel.value = self.orientdatasets_dialog


        self._apply.value       = self.__apply_event
        self._apply.icon        = conf.ANNOTATOR_ICON_PATH

        self._rotateimgs.changed_event = self.__rotate_images_changed_evt
        self._useotherorient.changed_event = self.__useotherorient_changed_evt

        self._exportdataset.value = os.getcwd()

        self._progress.hide()

        self.__reload_events_btn_evt()


        self._toolbox.value = [
            ('Extract from contours',(
                self.datasets_dialog,
            )),
            ('Mask',(
                self._usemaskimg,
                (self._usemaskdilate,self._maskdilatesize),
                (self._usemaskcircular,self._maskcircularsize),
                (self._usemaskellipse,self._usemaskrect),
            )),
            ('Margin, image size & stretch image',(
                self._margin, self._imagesize,
                self._usestretch,
            )),
            ('Rotate images',(
                self._useotherorient,
                self._orient_datasetspanel,
                self._rotateimgs,
            )),
            ('Export images per events',(
                self._reloadevts,
                self._eventslst,
            )),
        ]

    ###########################################################################
    ### EVENTS ################################################################
    ###########################################################################

    def __export_evts_changed_evt(self):
        if self._export_evts.value:
            self._eventslst.enabled = True
            self._reloadevts .enabled = True
        else:
            self._eventslst.enabled = False
            self._reloadevts .enabled = False


    def __reload_events_btn_evt(self):
        """
        Find all the events available on the timeline
        """
        timeline = self.mainwindow.timeline
        rows     = timeline.rows

        events   = {}
        for row in rows:
            for event in row.periods:
                events[event.title] = True

        events = sorted(events.keys())

        loaded_events = dict(self._eventslst.items)
        self._eventslst.value = [(e, loaded_events.get(e, False)) for e in events]

    def __rotate_images_changed_evt(self):
        self._useotherorient.enabled = self._rotateimgs.value

        if not self._rotateimgs.value:
            self._useotherorient.value = False
            self._orient_datasetspanel.enabled = False

    def __useotherorient_changed_evt(self):
        self._orient_datasetspanel.enabled = self._useotherorient.value

  
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

            self._exportmargin.enabled  = False
            self._mask_images.enabled   = False
            self._exportdataset.enabled = False
            self._rotateimgs.enabled    = False
            self._mask_margin.enabled   = False
            self._mask_margin.enabled   = False
            self._useotherorient.enabled = False
            self._orient_datasetspanel.enabled = False
            self._apply.label           = 'Cancel'

            # setup the progress bar
            total_2_analyse  = 0
            for video, (begin, end), datasets in self.datasets_dialog.selected_data:
                capture          = video.video_capture
                total_2_analyse += end-begin

            self._progress.min = 0
            self._progress.max = total_2_analyse
            self._progress.show()



            ######################################################################
            # create a directory to export the images if the option was selected
            export_dataset = os.path.join(self._exportdataset.value, 'contours-images')
            if not os.path.exists(export_dataset): os.makedirs(export_dataset)
            ######################################################################

         

            # If the option to use other datasets for the orientation was selected, create a dict variable 
            # with the association between each contour to export and contour to use the orientation
            # the association is used using the object.
            # For each contours to export of an object there should be a contour with orientation from the same object
            if self._useotherorient.value:
                orient_dict = {}
                for _, _, datasets in self.orientdatasets_dialog.selected_data:
                    orient_dict[datasets[0].object2d] = datasets[0]
            else:
                orient_dict = None

            count = 0
            for video, (begin, end), datasets in self.datasets_dialog.selected_data:
                if len(datasets)==0: continue
                begin, end = int(begin), int(end)+1
                capture.set(cv2.CAP_PROP_POS_FRAMES, begin); 
                
                blobs_datasets = None

                if export_dataset:
                    # create the folders to each video
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

                        if self._export_evts.value:
                            for event_name in self._eventslst.value:
                                path = os.path.join(dataset_export_dataset, event_name)
                                if not os.path.exists(path): os.makedirs(path)
                else:
                    datasets_export_directories = None


                ### calculate the video cuts #############################
                selected_events = self._eventslst.value
                videocuts   = []
                if self._export_evts.value:
                    # use the events to cut the video
                    totalframes = 0
                    timeline = self.mainwindow.timeline
        
                    for row in timeline.rows:
                        for event in row.periods:
                            if event.end<=begin: continue
                            if event.begin>=end: continue
                            if event.title not in selected_events: continue
                            b = int(event.begin if event.begin>=begin else begin)
                            e = int(event.end   if event.end<=end else end)
                            totalframes += e-b
                            videocuts.append( (b, e, event.title) )
                    videocuts = sorted(videocuts, key = lambda x: x[0])
                else:
                    # no events were selected
                    totalframes = end-begin
                    videocuts   = [(int(begin), int(end), None)]
                ##########################################################

                # start the loop that will create the video files
                for b, e, event_name in videocuts:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, b)

                    for index in range(b, e):
                        res, frame = capture.read()
                        if not res: break
                        if not self._apply.checked: break

                        for dataset_index, dataset in enumerate(datasets):
                            pass

                        self._progress.value = count
                        count += 1

                

            self._apply.label            = 'Apply'
            self._apply.checked          = False

            self._useotherorient.enabled = True
            self._orient_datasetspanel.enabled = True
            self._progress.hide()





    


if __name__ == '__main__': 
    pyforms.startApp(ContoursImagesWindow)
