import sys
import time
import multiprocessing
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QSizePolicy, QInputDialog, QMessageBox, QLineEdit, QFileDialog
from PyQt6.QtCore import pyqtSignal
from lib.stageController import StageController
from . import Display

STAGE_X_ID = "27253326"
STAGE_Y_ID = "27253425"
STAGE_Z_ID = "27253356"

class LinearStageControl(QWidget):
    addMotionRequested = pyqtSignal(str, str, str)

    def __init__(self, stage_name, stage_controller, motion_list, parent=None):
        super().__init__(parent)

        self.stage_name = stage_name
        self.stage_controller = stage_controller

        self.stage_label = QLabel(stage_name)
        self.home_button = QPushButton("Home")
        self.velocity_label = QLabel("Velocity (mm/s):")
        self.velocity_edit = QLineEdit()
        self.distance_label = QLabel("Distance (mm):")
        self.distance_edit = QLineEdit()
        self.add_motion_button = QPushButton("Add Motion")
        self.run_motion_button = QPushButton("Run Motion")

        self.motion_list = motion_list

        layout = QVBoxLayout()
        layout.addWidget(self.stage_label)
        layout.addWidget(self.home_button)
        layout.addWidget(self.velocity_label)
        layout.addWidget(self.velocity_edit)
        layout.addWidget(self.distance_label)
        layout.addWidget(self.distance_edit)
        layout.addWidget(self.add_motion_button)
        layout.addWidget(self.run_motion_button)

        self.setLayout(layout)

        self.add_motion_button.clicked.connect(self.emit_add_motion_signal)
        self.run_motion_button.clicked.connect(self.run_motion)
        self.home_button.clicked.connect(self.home)

    def home(self):
        home_thread = threading.Thread(target=self.stage_controller.home)
        home_thread.start()

    def check_input_fields(self):
        velocity_text = self.velocity_edit.text().strip()
        distance_text = self.distance_edit.text().strip()
        
        if not velocity_text or not distance_text:
            QMessageBox.warning(self, "Empty Fields", "Velocity and distance cannot be empty.")
            return None, None

        try:
            velocity = float(velocity_text)
            if velocity < 0:
                QMessageBox.warning(self, "Invalid Velocity", "Velocity cannot be negative.")
                return None, None
            
            distance = float(distance_text)
            return velocity, distance
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numerical values for velocity and distance.")
            return None, None

    def run_motion(self):
        velocity, distance = self.check_input_fields()
        if velocity is not None and distance is not None:
            self.stage_controller.setup_velocity(0, 10, velocity)
            self.stage_controller.move_by(distance)

    def emit_add_motion_signal(self):
        velocity, distance = self.check_input_fields()
        if velocity is not None and distance is not None:
            self.addMotionRequested.emit(self.stage_name, str(velocity), str(distance))

class MainWindow(QWidget):
    def __init__(self, signal, logging_queue):
        super().__init__()

        self.setWindowTitle("Linear Stage Control")
        self.setMinimumWidth(800)

        self.motion_list = QListWidget()
        self.motion_list.setMinimumWidth(340)

        self.stageX_controller = StageController(STAGE_X_ID)
        self.stageY_controller = StageController(STAGE_Y_ID)
        self.stageZ_controller = StageController(STAGE_Z_ID)

        self.stage1_control = LinearStageControl("X_Stage", self.stageX_controller, self.motion_list)
        self.stage2_control = LinearStageControl("Y_Stage", self.stageY_controller, self.motion_list)
        self.stage3_control = LinearStageControl("Z_Stage", self.stageZ_controller, self.motion_list)

        self.stage1_control.addMotionRequested.connect(self.add_motion)
        self.stage2_control.addMotionRequested.connect(self.add_motion)
        self.stage3_control.addMotionRequested.connect(self.add_motion)

        self.pause_button = QPushButton("Add Pause")
        self.pause_button.clicked.connect(self.add_pause)

        self.sequence_name_input = QLineEdit()
        self.sequence_name_input.setPlaceholderText("Sequence Name")
        self.sequence_name_input.setMaximumWidth(200)
        self.sequence_name = ""

        self.run_sequence_button = QPushButton("Run Sequence")
        self.run_sequence_button.setCheckable(True)
        self.run_sequence_button.clicked.connect(self.toggle_sequence)

        self.load_sequence_button = QPushButton("Load Sequence")
        self.load_sequence_button.clicked.connect(self.load_sequence)
        self.load_sequence_button.setMaximumWidth(100)

        self.save_sequence_button = QPushButton("Save Sequence")
        self.save_sequence_button.clicked.connect(self.save_sequence)
        self.save_sequence_button.setMaximumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.sequence_name_input)
        button_layout.addWidget(self.run_sequence_button)
        button_layout.addWidget(self.load_sequence_button)
        button_layout.addWidget(self.save_sequence_button)

        layout = QHBoxLayout()
        layout.addWidget(self.stage1_control)
        layout.addWidget(self.stage2_control)
        layout.addWidget(self.stage3_control)
        layout.addWidget(self.motion_list)
        layout.addWidget(self.pause_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.signal = signal
        self.logging_queue = logging_queue
        self.sequence_thread = None
        self.sequence_active = False

    def toggle_sequence(self):
        if self.sequence_active:
            self.stop_sequence()
        else:
            self.start_sequence()

    def start_sequence(self):
        self.sequence_active = True
        self.sequence_name = self.sequence_name_input.text()
        self.sequence_thread = threading.Thread(target=self.run_sequence)
        self.sequence_thread.start()

    def stop_sequence(self):
        self.sequence_active = False
        if self.sequence_thread and self.sequence_thread.is_alive():
            self.sequence_thread.join()

    def load_sequence(self):
        self.motion_list.clear()
        sequence_file, _ = QFileDialog.getOpenFileName(self, "Load Sequence", "sequences/", "Text Files (*.txt)")

        if sequence_file:
            with open(sequence_file, "r") as file:
                for line in file:
                    split_text = line.split()
                    stage_name = split_text[0]
                    if stage_name == "Pause":
                        motion_info = f"Time: {split_text[2]} seconds"
                    else:
                        velocity = split_text[2].rstrip(',')
                        distance = split_text[4]
                        motion_info = f"Velocity: {velocity}, Distance: {distance}"
                    stage_name = f"<b>{stage_name}</b>"
                    self.config_sequence_item(stage_name, motion_info)

    def save_sequence(self):
        sequence_file = QInputDialog.getText(self, "Save Sequence", "Enter sequence file name:")
        if sequence_file[1]:
            with open(f"sequences/{sequence_file[0]}.txt", "w") as file:
                for index in range(self.motion_list.count()):
                    item_widget = self.motion_list.itemWidget(self.motion_list.item(index))
                    split_text = item_widget.layout().itemAt(0).widget().text().split()
                    stage_name = split_text[0].strip('<b>').strip('</b>')
                    if stage_name == "Pause":
                        motion_info = f"Time: {split_text[2]}"
                    else:
                        velocity = split_text[2].rstrip(',')
                        distance = split_text[4]
                        motion_info = f"Velocity: {velocity}, Distance: {distance}"
                    file.write(f"{stage_name} {motion_info}\n")

    def config_sequence_item(self, motion_type, motion_info):
        item = QListWidgetItem()
        self.motion_list.addItem(item)

        remove_button = QPushButton("Remove")
        remove_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        remove_button.clicked.connect(lambda _, i=item: self.remove_motion(i))

        motion_item_text = f"<b>{motion_type}</b> {motion_info}"
        motion_label = QLabel(motion_item_text)
        motion_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        widget = QWidget()
        widget_layout = QHBoxLayout()
        widget_layout.addWidget(motion_label)
        widget_layout.addWidget(remove_button)
        widget.setLayout(widget_layout)

        item.setSizeHint(widget.sizeHint())

        self.motion_list.setItemWidget(item, widget)

    def add_motion(self, stage_name, velocity, distance):
        motion_info = f"Velocity: {velocity}, Distance: {distance}"
        self.config_sequence_item(stage_name, motion_info)

    def add_pause(self):
        pause_time, ok = QInputDialog.getDouble(self, "Pause Time", "Enter pause time (seconds):", 1.0, 0.1, 100.0, 1)
        if ok:
            motion_info = f"Time: {pause_time} seconds"
            self.config_sequence_item("Pause", motion_info)

    def remove_motion(self, item):
        row = self.motion_list.row(item)
        self.motion_list.takeItem(row)

    def run_sequence(self):
        self.set_logging_active(True, self.sequence_name)
        for index in range(self.motion_list.count()):
            item_widget = self.motion_list.itemWidget(self.motion_list.item(index))
            split_text = item_widget.layout().itemAt(0).widget().text().split()
            stage_name = split_text[0].strip('<b>').strip('</b>')
            item_widget.layout().itemAt(0).widget().setStyleSheet("background-color: lightgrey;")

            if stage_name == "Pause":
                pause_time_index = split_text.index("Time:")
                pause_time = float(split_text[pause_time_index + 1])
                print("Pausing for", pause_time, "seconds")
                time.sleep(pause_time)
            else:
                velocity_index = split_text.index("Velocity:")
                velocity = float(split_text[velocity_index + 1].rstrip(','))

                distance_index = split_text.index("Distance:")
                distance = float(split_text[distance_index + 1])

                if stage_name == "X_Stage":
                    controller = self.stageX_controller
                elif stage_name == "Y_Stage":
                    controller = self.stageY_controller
                elif stage_name == "Z_Stage":
                    controller = self.stageZ_controller

                controller.setup_velocity(0, 10, velocity)
                controller.move_by(distance)

                while controller.is_moving():
                    if self.sequence_active == False:
                        controller.stop()
                        break

            if self.sequence_active == False:
                break
            
            item_widget.layout().itemAt(0).widget().setStyleSheet("")

        self.set_logging_active(False, self.sequence_name)
        self.sequence_active = False
        self.run_sequence_button.setChecked(False)

    def set_logging_active(self, logging_flag, sequence_name):
        self.logging_queue.put((logging_flag, sequence_name))
        print("Logging set to", logging_flag)

    def closeEvent(self, event):
        self.signal.terminate()
        super().closeEvent(event)

def run_Display(logging_queue):
    Display.main(logging_queue)

def main():
    logging_queue = multiprocessing.Queue()
    signal = multiprocessing.Process(target=run_Display, args=(logging_queue,))
    signal.start()
    
    app = QApplication(sys.argv)
    window = MainWindow(signal, logging_queue)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())