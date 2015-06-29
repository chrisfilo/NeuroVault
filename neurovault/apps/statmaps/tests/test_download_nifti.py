from django.test import TestCase, Client
from neurovault.apps.statmaps.models import Collection,User, StatisticMap
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from neurovault.apps.statmaps.forms import StatisticMapForm
from .utils import clearDB

class AddStatmapsTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('NeuroGuy')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user)
        self.coll = Collection(owner=self.user, name="Test Collection")
        self.coll.save()
        
    def tearDown(self):
        clearDB()

    def testDownload(self):

            post_dict = {
                'name': "test map",
                'cognitive_paradigm_cogatlas': 'trm_4f24126c22011',
                'modality':'fMRI-BOLD',
                'map_type': 'T',
                'collection':self.coll.pk,
            }
            testpath = os.path.abspath(os.path.dirname(__file__))
            Image1 = StatisticMap(name='Image1', collection=self.coll, file='motor_lips.nii.gz', map_type="Z")
            Image1.file = SimpleUploadedFile('motor_lips.nii.gz', file(os.path.join(testpath,'test_data/statmaps/motor_lips.nii.gz')).read())
            Image1.save()
            
            
            response = self.client.get("/images/" + str(Image1.id) + "/download")
            self.assertEqual(response.status_code, 200)
            
            print result