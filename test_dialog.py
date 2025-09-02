import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt5 import QtWidgets
from ui.add_plate_dialog import AddPlateDialog

# A real QWidget-based class to act as a parent for the dialog
class MockMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # These attributes are expected by the dialog's style/font code
        self.button_font_size = 12
        self.table_font_size = 12
        self.input_font_size = 12

# Mock the database functions to avoid actual database dependency during tests
@patch('ui.add_plate_dialog.filter_plate_info', MagicMock(return_value=[]))
class TestAddPlateDialog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the QApplication instance for all tests."""
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)

    def setUp(self):
        """Set up a valid parent and the dialog for each test."""
        self.parent = MockMainWindow()
        self.dialog = AddPlateDialog(parent=self.parent)

    def test_01_widgets_exist(self):
        """Test if the new UI widgets have been added."""
        print("Running test: test_01_widgets_exist")
        self.assertTrue(hasattr(self.dialog, 'results_table'), "results_table widget does not exist.")
        self.assertIsInstance(self.dialog.results_table, QtWidgets.QTableWidget, "results_table is not a QTableWidget.")
        print("...PASSED")

    def test_02_new_methods_exist(self):
        """Test if the new helper methods have been implemented."""
        print("Running test: test_02_new_methods_exist")
        self.assertTrue(hasattr(self.dialog, 'search_plate'), "search_plate method does not exist.")
        self.assertTrue(callable(self.dialog.search_plate), "search_plate is not a callable method.")
        self.assertTrue(hasattr(self.dialog, 'clear_inputs'), "clear_inputs method does not exist.")
        self.assertTrue(callable(self.dialog.clear_inputs), "clear_inputs is not a callable method.")
        print("...PASSED")

    def test_03_clear_inputs_method(self):
        """Test if the clear_inputs method clears all fields and hides the table."""
        print("Running test: test_03_clear_inputs_method")
        # Set some text and make table visible
        self.dialog.plate_part1_line_edit.setText("TEST")
        self.dialog.phone_number_line_edit.setText("12345")
        self.dialog.results_table.setRowCount(1)
        self.dialog.results_table.setVisible(True)

        # Call the method to be tested
        self.dialog.clear_inputs()

        # Check if fields are cleared and table is hidden
        self.assertEqual(self.dialog.plate_part1_line_edit.text(), "")
        self.assertEqual(self.dialog.phone_number_line_edit.text(), "")
        self.assertEqual(self.dialog.results_table.rowCount(), 0)
        self.assertTrue(self.dialog.results_table.isHidden())
        print("...PASSED")

    def test_04_search_plate_method_shows_results(self):
        """Test if search_plate shows and populates the table when results are found."""
        print("Running test: test_04_search_plate_method_shows_results")
        with patch('ui.add_plate_dialog.filter_plate_info') as mock_filter:
            mock_filter.return_value = [("ABC-123", "0912345678", "Test Note")]

            # Set text to simulate user input, which is required to trigger the search logic
            self.dialog.plate_part1_line_edit.setText("ABC")
            self.dialog.search_plate()

            self.assertFalse(self.dialog.results_table.isHidden())
            self.assertEqual(self.dialog.results_table.rowCount(), 1)
            self.assertEqual(self.dialog.results_table.item(0, 0).text(), "ABC-123")
        print("...PASSED")

    def test_05_search_plate_method_hides_results(self):
        """Test if search_plate hides the table when there are no results."""
        print("Running test: test_05_search_plate_method_hides_results")
        with patch('ui.add_plate_dialog.filter_plate_info') as mock_filter:
            mock_filter.return_value = [] # No results

            self.dialog.plate_part1_line_edit.setText("XYZ") # Set text to simulate user typing
            self.dialog.search_plate()

            self.assertTrue(self.dialog.results_table.isHidden())
            self.assertEqual(self.dialog.results_table.rowCount(), 0)
        print("...PASSED")

    def test_06_accept_logic_for_warning_clears_and_refocuses(self):
        """Test on warning rejection, inputs are cleared and focus is reset."""
        print("Running test: test_06_accept_logic_for_warning_clears_and_refocuses")
        with patch('ui.add_plate_dialog.plate_exists', return_value=True), \
             patch('ui.add_plate_dialog.plate_and_phone_exists', return_value=False), \
             patch('PyQt5.QtWidgets.QMessageBox') as mock_msg_box, \
             patch.object(self.dialog, 'done') as mock_done, \
             patch.object(self.dialog, 'clear_inputs') as mock_clear_inputs, \
             patch.object(self.dialog.plate_part1_line_edit, 'setFocus') as mock_set_focus:

            msg_box_instance = mock_msg_box.return_value
            yes_button_mock = MagicMock()
            no_button_mock = MagicMock()
            msg_box_instance.addButton.side_effect = [yes_button_mock, no_button_mock]

            # Simulate the user clicking the "No" button
            msg_box_instance.clickedButton.return_value = no_button_mock

            self.dialog.accept()

            # Assert that the dialog is not closed, inputs are cleared, and focus is reset
            mock_done.assert_not_called()
            mock_clear_inputs.assert_called_once()
            mock_set_focus.assert_called_once()
        print("...PASSED")


if __name__ == '__main__':
    print("Starting programmatic verification of AddPlateDialog...")
    # Use the unittest TestLoader and TextTestRunner to run the tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddPlateDialog)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with a non-zero status code if tests failed
    if not result.wasSuccessful():
        print("\nSome verification tests failed.")
        sys.exit(1)

    print("\nAll verification tests passed!")
