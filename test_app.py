"""Exercise real Streamlit rendering and shared-filter state."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class DashboardTests(unittest.TestCase):
    def test_views_filters_and_details(self):
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=60)
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.tabs),4)
        initial=app.metric[0].value
        app.multiselect(key='channels').set_value(['Paid Search']).run(timeout=60)
        self.assertEqual(len(app.exception),0)
        self.assertNotEqual(app.metric[0].value,initial)
        for table in app.dataframe:
            if 'channel' in table.value.columns:
                self.assertEqual(set(table.value['channel']),{'Paid Search'})
        app.radio[0].set_value('Weekly').run(timeout=60)
        self.assertEqual(len(app.exception),0)
        app.selectbox(key='detail_campaign').select_index(1).run(timeout=60)
        self.assertEqual(len(app.exception),0)
        app.multiselect(key='channels').set_value([]).run(timeout=60)
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('No records match' in item.value for item in app.warning))
        self.assertEqual(len(app.metric),0)

if __name__ == '__main__': unittest.main()
