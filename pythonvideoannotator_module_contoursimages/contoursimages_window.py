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

from pythonvideoannotator_models.utils.tools import points_angle, rotate_image





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

        self._datasets_panel= ControlEmptyWidget('Paths')
        self._progress      = ControlProgress('Progress')       
        self._apply         = ControlButton('Apply', checkable=True)

        self._exportimgs    = ControlCheckBox('Export the images')
        self._exportmargin  = ControlSlider('Cutting margin', default=0,  minimum=0, maximum=300)
        self._mask_images   = ControlCheckBox('Use the contour as a mask')
        self._mask_margin   = ControlSlider('Mark margin', default=0,  minimum=0, maximum=100)

        #### draw events ###############################################
        self._export_evts   = ControlCheckBox('Export the events', changed_event=self.__export_evts_changed_evt)
        self._events_lst    = ControlCheckBoxList('Events', enabled=False)
        self._reloadevts_btn= ControlButton('Reload events', enabled=False, default=self.__reload_events_btn_evt)
        ################################################################

        self._maskradius    = ControlCheckBox('Use a circular mask')
        self._radius        = ControlSlider('Mask radius', default=1,  minimum=1, maximum=300)

        self._exportdataset = ControlDir('Export contours to dataset')
        self._rotateimgs    = ControlCheckBox('Rotate the images vertically')
        self._useother_orient = ControlCheckBox('Use the orientation from other contours', enabled=False)

        self._orient_datasets_panel = ControlEmptyWidget('Datasets for the orientation', enabled=False)
        
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
            ('_rotateimgs','_useother_orient'),
            '_orient_datasets_panel',
            ('_maskradius','_radius'),
            '_export_evts',
            ('_events_lst', '_reloadevts_btn'),
            ' ',
            '_apply',
            '_progress'
        ]

        self.load_order = [
            '_datasets_panel', '_exportimgs',
            '_exportdataset',
            '_exportmargin', 
            '_mask_images','_mask_margin',
            '_rotateimgs','_useother_orient',
            '_orient_datasets_panel',
            '_maskradius','_radius', '_export_evts' , '_events_lst'
        ]

        #datasets painel
        self.datasets_dialog = DatasetsDialog(self)
        self.datasets_dialog.datasets_filter = lambda x: isinstance(x, (Contours,Path) )
        self._datasets_panel.value = self.datasets_dialog
        

        self.orientdatasets_dialog = DatasetsDialog(self)
        self.orientdatasets_dialog.datasets_filter = lambda x: isinstance(x, Contours )
        self.orientdatasets_dialog.interval_visible = False
        self._orient_datasets_panel.value = self.orientdatasets_dialog


        self._apply.value       = self.__apply_event
        self._apply.icon        = conf.ANNOTATOR_ICON_PATH

        self._exportimgs.changed_event  = self.__exportimgs_changed_evt
        self._exportimgs.value          = False
        self._mask_images.changed_event = self.__mask_images_changed_evt
        self._mask_images.value         = False
        self._maskradius.changed_event  = self.__maskradius_changed_evt
        self._maskradius.value          = False
        self._rotateimgs.changed_event = self.__rotate_images_changed_evt
        self._useother_orient.changed_event = self.__useother_orient_changed_evt

        self._exportdataset.value = os.getcwd()

        self._progress.hide()

        self.__reload_events_btn_evt()

    ###########################################################################
    ### EVENTS ################################################################
    ###########################################################################

    def __export_evts_changed_evt(self):
        if self._export_evts.value:
            self._events_lst.enabled = True
            self._reloadevts_btn.enabled = True
        else:
            self._events_lst.enabled = False
            self._reloadevts_btn.enabled = False


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

        loaded_events = dict(self._events_lst.items)
        self._events_lst.value = [(e, loaded_events.get(e, False)) for e in events]

    def __rotate_images_changed_evt(self):
        self._useother_orient.enabled = self._rotateimgs.value

        if not self._rotateimgs.value:
            self._useother_orient.value = False
            self._orient_datasets_panel.enabled = False

    def __useother_orient_changed_evt(self):
        self._orient_datasets_panel.enabled = self._useother_orient.value

    def __exportimgs_changed_evt(self):
        if self._exportimgs.value:
            self._exportmargin.enabled  = True
            self._mask_images.enabled   = True
            self._exportdataset.enabled = True
            self._rotateimgs.enabled    = True
        else:
            self._exportmargin.enabled  = False
            self._mask_images.enabled   = False
            self._exportdataset.enabled = False
            self._rotateimgs.enabled    = False


    def __mask_images_changed_evt(self):
        if self._mask_images.value:
            self._mask_margin.enabled   = True
        else:
            self._mask_margin.enabled   = False

    def __maskradius_changed_evt(self):
        if self._maskradius.value:
            self._radius.enabled    = True
        else:
            self._radius.enabled    = False

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

            self._datasets_panel.enabled= False         
            self._exportimgs.enabled    = False
            self._exportmargin.enabled  = False
            self._mask_images.enabled   = False
            self._exportdataset.enabled = False
            self._rotateimgs.enabled    = False
            self._mask_margin.enabled   = False
            self._mask_margin.enabled   = False
            self._useother_orient.enabled = False
            self._orient_datasets_panel.enabled = False
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
            if self._exportimgs.value:
                export_dataset = os.path.join(self._exportdataset.value, 'contours-images')
                if not os.path.exists(export_dataset): os.makedirs(export_dataset)
            else:
                export_dataset = None
            ######################################################################

            if dilate_mask:
                kernel_size = self._mask_margin.value
                if (kernel_size % 2)==0: kernel_size+=1
                kernel = np.ones((kernel_size,kernel_size),np.uint8)
            else:
                kernel = None

            # If the option to use other datasets for the orientation was selected, create a dict variable 
            # with the association between each contour to export and contour to use the orientation
            # the association is used using the object.
            # For each contours to export of an object there should be a contour with orientation from the same object
            if self._useother_orient.value:
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
                            for event_name in self._events_lst.value:
                                path = os.path.join(dataset_export_dataset, event_name)
                                if not os.path.exists(path): os.makedirs(path)
                else:
                    datasets_export_directories = None


                ### calculate the video cuts #############################
                selected_events = self._events_lst.value
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
                            position = dataset.get_position(index)
                            if position is None: continue

                            # Mask the image if the option was selected #####################
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
                            #################################################################
                            
                            # cut the image
                            if self._maskradius.value:
                                x, y, w, h = position[0]-self._radius.value, position[1]-self._radius.value, 2*self._radius.value, 2*self._radius.value
                            elif isinstance(dataset, Contours):
                                # find the cut ######################################
                                bounding_box = dataset.get_bounding_box(index)
                                if bounding_box is None: continue
                                x, y, w, h  = dataset.get_bounding_box(index)
                                #####################################################
                            else:
                                x, y, w, h = position[0], position[1], 1, 1

                            margin = self._exportmargin.value
                            if isinstance(dataset, Contours) and self._rotateimgs.value:
                                margin = 2*self._exportmargin.value

                            x, y, w, h  = x-margin, y-margin, w+margin*2, h+margin*2
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
                                image_dataset = os.path.join(datasets_export_directories[dataset_index], event_name, "{0}.png".format(index) )
                                
                                img_2_save = cut

                                # IF the dataset is a contour
                                if isinstance(dataset, Contours) and self._rotateimgs.value:
                                    
                                    # check which oriention to use
                                    if orient_dict is None:
                                        angle = dataset.get_angle(index)                            
                                    else:
                                        d = orient_dict.get(dataset.object2d, None)
                                        if d is None:
                                            # if no orientation was defined to the object, fallback to the tradictional method
                                            angle = dataset.get_angle(index)
                                        else:
                                            angle = d.get_angle(index)

                                    if angle:
                                        rotation_rad = angle
                                        rotation_deg = math.degrees( rotation_rad )
                                        rotation = rotation_deg
                                        img_2_save = rotate_image(img_2_save, rotation+90)
                                        # we expanded the margin for rotated images so we don't have strange forms exported.
                                        # put it to use for the size
                                        row, col, ch = img_2_save.shape
                                        lx = self._exportmargin.value
                                        rx = col - self._exportmargin.value
                                        ly = self._exportmargin.value
                                        ry = row - self._exportmargin.value
                                        imaux = img_2_save[ly:ry, lx:rx]

                                cv2.imwrite(image_dataset, imaux)

                        self._progress.value = count
                        count += 1

                

            self._datasets_panel.enabled = True 
            self._exportimgs.enabled     = True
            self.__mask_images_changed_evt()
            self.__exportimgs_changed_evt()
            self._apply.label            = 'Apply'
            self._apply.checked          = False

            self._useother_orient.enabled = True
            self._orient_datasets_panel.enabled = True
            self._progress.hide()





    


if __name__ == '__main__': 
    pyforms.startApp(ContoursImagesWindow)
