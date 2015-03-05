import os
import tempfile
import shutil
import nibabel as nb
import numpy as np
import neurovault.settings
from django.test import TestCase, Client
from neurovault.apps.statmaps.utils import is_thresholded
from neurovault.apps.statmaps.models import Collection,User

class QATest(TestCase):

    def setUp(self):
      self.brain_mask = nb.load(os.path.join(neurovault.settings.STATIC_ROOT,"anatomical","MNI152_mask.nii.gz"))
      self.brain = nb.load(os.path.join(neurovault.settings.STATIC_ROOT,"anatomical","MNI152.nii.gz"))
      # We will fill in brain mask with this percentage of randomly placed values
      self.percentages = [0.0,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.8]
      self.thresholded = [True,True,True,True,True,False,False,False,False,False]
      self.unzip = lambda l:tuple(zip(*l))

    def testThresholded(self):
      for i in range(0,len(self.percentages)):
        p = self.percentages[i]
        t = self.thresholded[i]
        empty_nii = np.zeros(self.brain_mask.shape)
        x,y,z = np.where(self.brain_mask.get_data()==1)
        idx = zip(x,y,z)
        np.random.shuffle(idx) # mix it up! shake it up!
        if p != 0.0:
          number_voxels = int(np.floor(p * len(idx)))
          random_idx = idx[0:number_voxels]
          random_idx = self.unzip(random_idx)
          empty_nii[random_idx] = 1
        empty_nii = nb.Nifti1Image(empty_nii,affine=self.brain_mask.get_affine(),header=self.brain_mask.get_header())
        is_thr, perc_bad = is_thresholded(nii_obj=empty_nii,brain_mask=self.brain_mask)
        print "Filled in %s of values in mask, is thresholded returns [%s:%s]" %(p,is_thr,perc_bad)
        difference = np.abs(p - perc_bad)
        self.assertTrue(difference <= 0.01)
        self.assertEquals(t, is_thr)

