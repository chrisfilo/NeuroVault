from django.test import TestCase, Client
from neurovault.apps.statmaps.models import Collection,User
import tempfile
import os
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from neurovault.apps.statmaps.nidm_results import NIDMUpload
from neurovault.apps.statmaps.forms import NIDMResultsForm
from .utils import clearDB


class NIDMResultsTest(TestCase):

    def setUp(self):
        testpath = os.path.abspath(os.path.dirname(__file__))
        self.files = {
            'fsl_course_av': {
                'file': os.path.join(testpath,'test_data/nidm/fsl_course_av.nidm.zip'),
                'output_row': {'type': u'T','name': u'Statistic Map: Visual',},
                'num_statmaps': 4,
            },
            'fsl_course_fluency2': {
                'file': os.path.join(testpath,'test_data/nidm/fsl_course_fluency2.nidm.zip'),
                'output_row': {'type': u'F','name': u'Statistic Map: Generation F',},
                'num_statmaps': 12,
            },
            'spm_example': {
                'file': os.path.join(testpath,'test_data/nidm/spm_example.nidm.zip'),
                'output_row': {'type': u'T', 'name': u'Statistic Map: passive listening > rest', },
                'num_statmaps': 1,
            },
            'fsl_course_ptt_ac_left': {
                'file': os.path.join(testpath,'test_data/nidm/fsl_course_ptt_ac_left.nidm.zip'),
                'output_row': {'type': u'F','name': u'Statistic Map: index F',},
                'num_statmaps': 12,
            },
            'ds000001_Con1_nidm_001': {
                'file': os.path.join(testpath,'test_data/nidm/ds000001_Con1_nidm_001.nidm.zip'),
                'output_row': {'type': u'F','name': u'Statistic Map: Con1: pumps realRT - ctrl realRT',},
                'num_statmaps': 1,
            },
        }

        self.failing_files = {
             'spm_bad_ttl':   os.path.join(testpath,'test_data/nidm/spm_bad_ttl.nidm.zip'),
        }

        self.tmpdir = tempfile.mkdtemp()
        self.user = User.objects.create_user('NeuroGuy')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user)
        #we us private collection to avoid running the comparisons
        self.coll = Collection(owner=self.user, name="Test Collection", private=True, private_token="XBOLFOFU")
        self.coll.save()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        clearDB()

    def testParseNIDMZip(self):
        contrasts = {}
        turtles = {}  # I like turtles.
        uploads = {}
        statmaps = {}

        for name in self.files:
            uploads[name] = NIDMUpload(self.files[name]['file'],tmp_dir=self.tmpdir,load=False)
            turtles[name] = uploads[name].parse_metafiles(extract_ttl=True)
            contrasts[name] = uploads[name].parse_contrasts()
            statmaps[name] = uploads[name].get_statmaps()

        """
        assert known bad file throws parsing error
        """
        for key in self.failing_files:
            with self.assertRaises(NIDMUpload.ParseException):
                print NIDMUpload(self.failing_files[key])

        """
        assert output matches expected output
        """
        for name, info in self.files.items():
            first_map = sorted(statmaps[name])[0]
            for field in 'name','type':
                self.assertEquals(first_map[field],info['output_row'][field])
            self.assertEquals(len(statmaps[name]), info['num_statmaps'])

    def testUploadNIDMZip(self):

        for name, info in self.files.items():
            zip_file = open(info['file'], 'rb')
            post_dict = {
                'name': name,
                'description':'{0} upload test'.format(name),
                'collection':self.coll.pk,
            }

            fname = os.path.basename(info['file'])
            file_dict = {'zip_file': SimpleUploadedFile(fname, zip_file.read())}
            form = NIDMResultsForm(post_dict, file_dict)

            self.assertTrue(form.is_valid())

            nidm = form.save()

            self.assertEquals(len(nidm.nidmresultstatisticmap_set.all()),info['num_statmaps'])

            map_type = info['output_row']['type'][0]
            map_img = nidm.nidmresultstatisticmap_set.filter(map_type=map_type).first()

            self.assertEquals(map_img.name,info['output_row']['name'])
