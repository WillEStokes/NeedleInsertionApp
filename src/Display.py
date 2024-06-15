import sys
import multiprocessing
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtCore import Qt, QThread
from lib.K64F import K64F

class MainWindow(QMainWindow):
    def __init__(self, logging_queue):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Sensor Display")
        self.setGeometry(100, 100, 800, 600)

        # Data initialisation
        # self.data_labels = {'fx', 'fy', 'fz', 'tx', 'ty', 'tz'}
        self.data_labels = ['fx', 'fy', 'fz', 'tx', 'ty', 'tz']
        self.data = tuple([0] * 9)

        # Chart
        self.chart = QChart()
        self.chart.setTitle("FT Data")
        self.chart_view = QChartView()
        self.chart_view.setChart(self.chart)

        # Axes
        self.axisY = QValueAxis()
        self.axisY.setTitleText("Force/Torque")
        self.axisY.setRange(-20, 20)
        self.chart.addAxis(self.axisY, Qt.AlignmentFlag.AlignLeft)
        self.axisX = QValueAxis()
        self.axisX.setRange(0, 1)
        self.axisX.setLabelFormat("%u")
        self.axisX.setTickType(QValueAxis.TickType.TicksDynamic)
        self.axisX.setTickInterval(10)
        self.chart.addAxis(self.axisX, Qt.AlignmentFlag.AlignBottom)

        # Add series to chart
        for name in self.data_labels:
            series = QLineSeries()
            series.setName(name)
            self.chart.addSeries(series)
            series.attachAxis(self.axisX)
            series.attachAxis(self.axisY)

        # Buttons
        self.acquire_button = QPushButton("Acquire")
        self.acquire_button.setCheckable(True)
        self.acquire_button.clicked.connect(self.toggle_acquisition)
        self.zero_button = QPushButton("Zero Data")
        self.zero_button.clicked.connect(self.zero_data)

        # Recording indicator
        self.recording_indicator = QLabel("Not Recording")
        self.recording_indicator.setStyleSheet("background-color: white; color: black; padding: 5px;")
        self.recording_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Layout
        self.layout = QVBoxLayout()
        indicators_layout = QVBoxLayout()
        self.indicators = []
        for i in range(9):
            indicator_label = QLabel()
            self.indicators.append(indicator_label)
            indicators_layout.addWidget(indicator_label)
        indicators_layout.addWidget(self.zero_button)
        indicators_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.indicators[0].setText(f"fx: {0:.3f}")
        self.indicators[1].setText(f"fy: {0:.3f}")
        self.indicators[2].setText(f"fz: {0:.3f}")
        self.indicators[3].setText(f"tx: {0:.3f}")
        self.indicators[4].setText(f"ty: {0:.3f}")
        self.indicators[5].setText(f"tz: {0:.3f}")
        self.indicators[6].setText(f"px: {0:.3f}")
        self.indicators[7].setText(f"py: {0:.3f}")
        self.indicators[8].setText(f"pz: {0:.3f}")
        chart_layout = QHBoxLayout()
        chart_layout.addLayout(indicators_layout)
        chart_layout.addWidget(self.chart_view)
        self.layout.addLayout(chart_layout)
        self.layout.addWidget(self.acquire_button)
        self.layout.addWidget(self.recording_indicator)

        # Set central widget
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Class instances
        self.K64F = K64F()
        self.K64F.init_ethernet()

        # Variables
        self.acquisition_active = False
        self.read_counter = 0
        self.mean_ft_data = [0] * 6
        self.max_x = 0
        self.logging_queue = logging_queue

        # Logging thread
        self.logging_thread = LoggingListener(self, logging_queue, self.K64F)
        self.logging_thread.start()
    
    def toggle_acquisition(self):
        if self.acquisition_active:
            self.stop_acquisition()
        else:
            self.start_acquisition()

    def start_acquisition(self):
        self.K64F.start_acquisition()
        self.K64F.data_stream.data_received.connect(self.update_chart)
        self.acquisition_active = True

    def stop_acquisition(self):
        self.K64F.stop_acquisition()
        self.acquisition_active = False

    def update_chart(self, data):
        self.data = data
        fx, fy, fz, tx, ty, tz, px, py, pz = self.data

        self.mean_ft_data[0] += fx
        self.mean_ft_data[1] += fy
        self.mean_ft_data[2] += fz
        self.mean_ft_data[3] += tx
        self.mean_ft_data[4] += ty
        self.mean_ft_data[5] += tz

        self.indicators[6].setText(f"px: {px:.3f}")
        self.indicators[7].setText(f"py: {py:.3f}")
        self.indicators[8].setText(f"pz: {pz:.3f}")

        self.read_counter += 1
        
        if self.read_counter == 5:
            mean_ft_data = [value / 5 for value in self.mean_ft_data]

            self.indicators[0].setText(f"fx: {mean_ft_data[0]:.3f}")
            self.indicators[1].setText(f"fy: {mean_ft_data[1]:.3f}")
            self.indicators[2].setText(f"fz: {mean_ft_data[2]:.3f}")
            self.indicators[3].setText(f"tx: {mean_ft_data[3]:.3f}")
            self.indicators[4].setText(f"ty: {mean_ft_data[4]:.3f}")
            self.indicators[5].setText(f"tz: {mean_ft_data[5]:.3f}")

            for i, series in enumerate(self.chart.series()):
                series.append(self.max_x, mean_ft_data[i])

            self.max_x += 1
            self.min_x = max(0, self.max_x - 100)
            self.axisX.setRange(self.min_x, self.max_x)

            for series in self.chart.series():
                while len(series.points()) > 100:
                    series.remove(0)
            
            self.chart_view.update()

            self.read_counter = 0
            self.mean_ft_data = [0] * 6

    def zero_data(self):
        self.K64F.set_data_offset()

    def closeEvent(self, event):
        super().closeEvent(event)

class LoggingListener(QThread):
    def __init__(self, main_window, logging_queue, K64F):
        super().__init__()
        self.main_window = main_window
        self.logging_queue = logging_queue
        self.K64F = K64F

    def run(self):
        while True:
            logging_flag, sequence_name = self.logging_queue.get() # listen for logging flag and sequence name
            if logging_flag is True:
                self.K64F.set_sequence_name(sequence_name)
                self.K64F.enable_logging()
                self.main_window.recording_indicator.setText("Recording")
                self.main_window.recording_indicator.setStyleSheet("background-color: green; color: black; padding: 5px;")
            else:
                self.K64F.disable_logging()
                self.main_window.recording_indicator.setText("Not Recording")
                self.main_window.recording_indicator.setStyleSheet("background-color: white; color: black; padding: 5px;")

def main(logging_queue):
    app = QApplication(sys.argv)
    window = MainWindow(logging_queue)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    logging_queue = multiprocessing.Queue()
    main(logging_queue)