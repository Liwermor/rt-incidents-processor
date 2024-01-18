import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QComboBox, QDialog, QRadioButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import closer
import logging
import json
from datetime import datetime

class IncidentProcessorThread(QThread):
    finished_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, rt_url, username, password, answer, link_to_id, incident_ids, selected_status):
        super().__init__()
        self.rt_url = rt_url
        self.username = username
        self.password = password
        self.answer = answer 
        self.link_to_id = link_to_id
        self.incident_ids = incident_ids
        self.selected_status = selected_status

    def run(self):
        try:
            total_incidents = len(self.incident_ids)
            for index, incident_id in enumerate(self.incident_ids, start=1):
                self.log_signal.emit(f"Processing Incident [{index}/{total_incidents}] - ID: {incident_id}")
                closer.process_incident_reports(
                    self.rt_url, self.username, self.password, self.answer, 
                    self.link_to_id, [incident_id], self.selected_status
                )

            #current_time = datetime.now().strftime('[%H:%M] ')
            self.finished_signal.emit(f"solved successfully - 🚀")
        except Exception as e:
            self.finished_signal.emit(f"Error: {e}")


class NumberInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Numbers")
        self.setGeometry(100, 100, 300, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.is_clipboard_connected = False
        layout = QVBoxLayout(self)

        self.number_text_edit = QTextEdit(self)
        layout.addWidget(self.number_text_edit)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.live_capture_radio = QRadioButton("Live capture", self)
        self.live_capture_radio.toggled.connect(self.on_live_capture_toggle)
        layout.addWidget(self.live_capture_radio)

    def on_live_capture_toggle(self, checked):
        clipboard = QApplication.clipboard()
        if checked and not self.is_clipboard_connected:
            clipboard.dataChanged.connect(self.on_clipboard_change)
            self.is_clipboard_connected = True
        elif not checked and self.is_clipboard_connected:
            clipboard.dataChanged.disconnect(self.on_clipboard_change)
            self.is_clipboard_connected = False

    def on_clipboard_change(self):
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        if clipboard_text.isdigit():
            current_text = self.number_text_edit.toPlainText()
            current_lines = current_text.split('\n')
            # Check if the current text is empty before appending
            if not current_lines or clipboard_text != current_lines[-1]:
                new_text = f"{current_text}\n{clipboard_text}".strip() if current_text else clipboard_text
                self.number_text_edit.setText(new_text)


    def get_numbers(self):
        return self.number_text_edit.toPlainText().strip().split('\n')


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 400, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        self.rt_url_entry = QLineEdit(self)
        self.rt_url_entry.setPlaceholderText("https://rt.link/REST/1.0/")
        layout.addWidget(self.create_label_and_widget("RT API URL:", self.rt_url_entry))

        self.rt_username_entry = QLineEdit(self)
        layout.addWidget(self.create_label_and_widget("Username:", self.rt_username_entry))

        self.rt_password_entry = QLineEdit(self)
        self.rt_password_entry.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.create_label_and_widget("Password:", self.rt_password_entry))

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

    def create_label_and_widget(self, label_text, widget):
        container = QWidget()
        container_layout = QVBoxLayout(container)
        label = QLabel(label_text, container)
        container_layout.addWidget(label)
        container_layout.addWidget(widget)
        return container

    def save_settings(self):
        rt_url = self.rt_url_entry.text()
        username = self.rt_username_entry.text()
        password = self.rt_password_entry.text()

        # Save the settings to a JSON file named "profile"
        settings = {
            "rt_url": rt_url,
            "username": username,
            "password": password
        }

        try:
            with open("profile.json", "w") as profile_file:
                json.dump(settings, profile_file, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
            return

        self.accept()


class IncidentProcessorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        #self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        #TODO: Radio button setting always on top
        self.initUI()
        self.incident_ids = []

    def initUI(self):
        self.setWindowTitle("RT Incident Report Processor")
        self.setGeometry(100, 100, 400, 300)

        # Main widget and layout
        widget = QWidget(self)
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        # Settings button
        self.settings_button = QPushButton("Settings", widget)
        self.settings_button.clicked.connect(self.show_settings_dialog)
        layout.addWidget(self.settings_button)

        # Input fields
        self.answer_combo = QComboBox(widget)
        keywords = closer.load_keywords_from_json('answer.json')
        self.answer_combo.addItems(keywords)
        layout.addWidget(self.create_label_and_widget("Answer Keyword:", self.answer_combo))

        # Status dropdown
        self.status_combo = QComboBox(widget)
        self.status_combo.addItem("Close")
        self.status_combo.addItem("Reject")
        layout.addWidget(self.create_label_and_widget("Status:", self.status_combo))

        # Link ID entry
        self.link_id_entry = QLineEdit(widget)
        self.link_id_entry.setPlaceholderText("empty = no link")
        layout.addWidget(self.create_label_and_widget("Link To ID:", self.link_id_entry))

        # Button to open number input dialog        
        self.number_input_button = QPushButton("Enter Numbers", widget)
        self.number_input_button.clicked.connect(self.open_number_input_dialog)
        layout.addWidget(self.number_input_button)

        # Process button
        self.process_button = QPushButton("start process", widget)
        self.process_button.clicked.connect(self.start_process)
        layout.addWidget(self.process_button)

        # Status/Log display
        self.log_text = QTextEdit(widget)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def update_log(self, message):
        self.log_text.append(message)

    def open_number_input_dialog(self):
        dialog = NumberInputDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.incident_ids = dialog.get_numbers()  # Store the IDs in an instance variable

    def create_label_and_widget(self, label_text, widget):
        container = QWidget()
        container_layout = QVBoxLayout(container)
        label = QLabel(label_text, container)
        container_layout.addWidget(label)
        container_layout.addWidget(widget)
        return container

    def show_settings_dialog(self):
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == QDialog.Accepted:
            # Optionally update other UI elements if needed
            pass

#    def start_process(self):       
#        answer_keyword = self.answer_combo.currentText()  # Get the selected keyword
#        try:
#            answer_text = closer.read_answer_from_file('answer.json', answer_keyword)
#            if answer_text is None:
#                raise ValueError(f"No answer found for keyword: {answer_keyword}")
#        except Exception as e:
#            QMessageBox.critical(self, "Error", str(e))
#            return
#
#        link_to_id_text = self.link_id_entry.text()
#        link_to_id = int(link_to_id_text) if link_to_id_text.isdigit() else 0
#
#        self.thread = IncidentProcessorThread(self.rt_url, self.username, self.password, answer_keyword, link_to_id, self.incident_ids, self.status_combo.currentText())  # Pass the selected keyword
#        self.thread.finished_signal.connect(self.on_finish)
#        self.thread.log_signal.connect(self.update_log)  # Connect the signal
#        self.thread.start()

    def start_process(self):
        if not self.incident_ids:
            QMessageBox.warning(self, "Warning", "No incident IDs provided.")
            return

        answer_keyword = self.answer_combo.currentText()  # Get the selected keyword
        try:
            answer_text = closer.read_answer_from_file('answer.json', answer_keyword)
            if answer_text is None:
                raise ValueError(f"No answer found for keyword: {answer_keyword}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        link_to_id_text = self.link_id_entry.text()
        link_to_id = int(link_to_id_text) if link_to_id_text.isdigit() else 0

        # Start the thread with the necessary parameters
        self.thread = IncidentProcessorThread(self.rt_url, self.username, self.password, answer_keyword, link_to_id, self.incident_ids, self.status_combo.currentText())
        self.thread.finished_signal.connect(self.on_finish)
        self.thread.log_signal.connect(self.update_log)
        self.thread.start()



    def on_finish(self, message):
        current_time = datetime.now().strftime('[%H:%M] ')
        formatted_message = f"{current_time}{message}"
        self.log_text.append(formatted_message)
        if "Error" in message:
            QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)

    # Load settings from "profile.json" file if it exists
    settings = {}
    try:
        with open("profile.json", "r") as profile_file:
            settings = json.load(profile_file)
    except FileNotFoundError:
        pass  # File doesn't exist, use default settings

    rt_url = settings.get("rt_url", "")
    username = settings.get("username", "")
    password = settings.get("password", "")

    ex = IncidentProcessorGUI()
    ex.rt_url = rt_url  # Set the rt_url in the GUI
    ex.username = username  # Set the username in the GUI
    ex.password = password  # Set the password in the GUI
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
