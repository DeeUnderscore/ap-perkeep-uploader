import unittest
import pathlib
from perkeepap.ap_importer import MissingAsDataError, ApData, ApOutbox

# testdata directory is a sibling of the test files
TESTDATA_DIR=pathlib.Path(__file__).resolve().parent / 'testdata'

class ImporterTest(unittest.TestCase):
    """
    Test JSON-LD reading and processing

    """

    def setUp(self):
        self.importer = ApData.from_dir(TESTDATA_DIR)

    def test_json_loading(self):
        for item in self.importer.jsons:
            if ('id' in item 
                and item['id'] == 'https://localhost/Alice'):

                self.assertIn('type', item)
                self.assertEqual(item['type'], 'Person')
                return

        self.fail('Did not find the expected json in loaded jsons')


    def test_get_by_id(self):
        item = self.importer.get_by_id('https://localhost/Alice')

        self.assertEqual(item['id'], 'https://localhost/Alice')
        self.assertEqual(item['name'], 'Alice')

    def test_get_by_id_missing(self):
        self.assertIsNone( self.importer.get_by_id('nosuchid') )

    def test_outbox(self):
        outbox = ApOutbox(self.importer, 'https://localhost/Alice')
        
        self.assertEqual(outbox.outbox[0]['id'],
                         'https://localhost/Alice/activities/1')

    def test_outbox_missing(self):

        with self.assertRaises(MissingAsDataError, msg='Tried invalid actor id'):
            ApOutbox(self.importer, 'nosuchid')

        with self.assertRaises(MissingAsDataError, 
            msg='Tried actor with missing outbox file'):

            ApOutbox(self.importer, 'https://localhost/bt_mcexample')

    def test_outbox_iteration(self):
        outbox = ApOutbox(self.importer, 'https://localhost/Alice')

        wanted_ids = ('https://localhost/Alice/activities/1',
            'https://localhost/Alice/activities/2',
            'https://localhost/Alice/activities/3')

        for (got, want) in zip((node['id'] for node in outbox), wanted_ids):
            self.assertEqual(got, want)


    def test_outbox_note_only_iteration(self):
        outbox = ApOutbox(self.importer, 'https://localhost/Alice')

        wanted_ids = ('https://localhost/Alice/activities/1',
            'https://localhost/Alice/activities/3')

        zipped = zip((node['id'] for node in outbox.notes_only()), wanted_ids)

        for (got, want) in zipped:
            self.assertEqual(got, want)

        

