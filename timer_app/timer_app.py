from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QInputDialog, QSlider, QFormLayout, QComboBox, QDialog, QLineEdit, QSpinBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
import sys
import time
import math
import random
import json

class TimerConfigWindow(QDialog):
    def __init__(self, num_timers, saved_configs):
        super().__init__()
        self.setWindowTitle("Configure Timers")
        self.saved_configs = saved_configs
        self.timer_configs = []

        layout = QVBoxLayout()
        self.inputs = []

        for i in range(num_timers):
            row_layout = QVBoxLayout()

            # Timer preset dropdown
            preset_combo = QComboBox(self)
            preset_combo.addItem("New Timer")
            preset_combo.addItems([config["title"] for config in self.saved_configs])
            preset_combo.currentIndexChanged.connect(lambda index, i=i: self.populate_preset(index, i))
            row_layout.addWidget(preset_combo)

            # Timer name input
            name_input = QLineEdit(self)
            name_input.setPlaceholderText(f"Timer {i + 1} Name")
            row_layout.addWidget(name_input)

            # Hours, minutes, seconds inputs
            hour_input = QSpinBox(self)
            hour_input.setRange(0, 99)
            hour_input.setPrefix("H: ")
            row_layout.addWidget(hour_input)

            minute_input = QSpinBox(self)
            minute_input.setRange(0, 59)
            minute_input.setPrefix("M: ")
            row_layout.addWidget(minute_input)

            second_input = QSpinBox(self)
            second_input.setRange(0, 59)
            second_input.setPrefix("S: ")
            row_layout.addWidget(second_input)

            self.inputs.append((preset_combo, name_input, hour_input, minute_input, second_input))
            layout.addLayout(row_layout)

        confirm_button = QPushButton("Confirm", self)
        confirm_button.clicked.connect(self.collect_inputs)
        layout.addWidget(confirm_button)
        self.setLayout(layout)

    def populate_preset(self, index, timer_index):
        if index == 0:  # "New Timer" selected
            return

        preset = self.saved_configs[index - 1]  # Adjust for "New Timer"
        _, name_input, hour_input, minute_input, second_input = self.inputs[timer_index]

        name_input.setText(preset["title"])
        plan_time = preset["plan_time"]
        hours, remainder = divmod(plan_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        hour_input.setValue(hours)
        minute_input.setValue(minutes)
        second_input.setValue(seconds)

    def collect_inputs(self):
        for preset_combo, name_input, hour_input, minute_input, second_input in self.inputs:
            title = name_input.text() if name_input.text() else "Unnamed Timer"
            plan_time = hour_input.value() * 3600 + minute_input.value() * 60 + second_input.value()
            self.timer_configs.append({"title": title, "plan_time": plan_time})

            if preset_combo.currentText() == "New Timer":
                save, ok = QInputDialog.getItem(self, "Save Timer", f"Save {title} as a new preset?", ["Yes", "No"], editable=False)
                if ok and save == "Yes":
                    self.saved_configs.append({"title": title, "plan_time": plan_time})
        self.accept()

class TimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hang in there!")
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Always on top

        # Load saved configurations
        self.saved_configs = self.load_configs()

        # Initialize timers
        self.num_timers, ok = QInputDialog.getInt(self, "Timers", "Enter number of timers:", min=1, max=10)
        if not ok:
            sys.exit()

        config_window = TimerConfigWindow(self.num_timers, self.saved_configs)
        if config_window.exec_() == QDialog.Accepted:
            self.timer_configs = config_window.timer_configs
            self.save_configs()  # Save updated presets
        else:
            sys.exit()

        self.is_running = [False] * self.num_timers
        self.start_time = [0] * self.num_timers
        self.elapsed_time = [0] * self.num_timers
        self.pie_angles = [0] * self.num_timers

        self.colors = [QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(self.num_timers)]
        self.labels = []

        # Build UI
        layout = QVBoxLayout()

        # Transparency slider
        transparency_layout = QFormLayout()
        self.transparency_slider = QSlider(Qt.Horizontal, self)
        self.transparency_slider.setMinimum(50)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setValue(90)
        self.transparency_slider.valueChanged.connect(self.adjust_transparency)
        transparency_layout.addRow("Transparency:", self.transparency_slider)
        layout.addLayout(transparency_layout)

        timer_layout = QHBoxLayout()

        for i, config in enumerate(self.timer_configs):
            single_timer_layout = QVBoxLayout()

            # Add timer title
            label_title = QLabel(f"{config['title']} (Plan: {self.format_time(config['plan_time'])})", self)
            label_title.setAlignment(Qt.AlignCenter)
            single_timer_layout.addWidget(label_title)

            # Add timer display
            label = QLabel("00:00:00", self)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 24px;")
            single_timer_layout.addWidget(label)
            self.labels.append(label)

            # Add reset button
            reset_button = QPushButton("Reset", self)
            reset_button.clicked.connect(lambda checked, i=i: self.reset_timer(i))
            single_timer_layout.addWidget(reset_button)

            timer_layout.addLayout(single_timer_layout)

        layout.addLayout(timer_layout)
        self.setLayout(layout)

        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(100)

    def reset_timer(self, index):
        self.is_running[index] = False
        self.elapsed_time[index] = 0
        self.pie_angles[index] = 0
        self.labels[index].setText("00:00:00")

    def toggle_timer(self, index):
        # Stop all other timers
        for i in range(self.num_timers):
            if i != index:
                self.is_running[i] = False

        # Start or pause the selected timer
        if self.is_running[index]:
            self.is_running[index] = False
        else:
            self.is_running[index] = True
            self.start_time[index] = time.time() - self.elapsed_time[index]

    def mousePressEvent(self, event):
        # Detect clicks on pie charts to start/stop timers
        width = self.width() // self.num_timers
        height = self.height()
        for i in range(self.num_timers):
            center_x = width * i + width // 2
            center_y = height // 2
            radius = min(width, height) // 4
            distance = math.sqrt((event.x() - center_x) ** 2 + (event.y() - center_y) ** 2)
            if distance <= radius:
                self.toggle_timer(i)
                break

    def adjust_transparency(self):
        value = self.transparency_slider.value()
        self.setWindowOpacity(value / 100)

    def update_timer(self):
        for i in range(self.num_timers):
            if self.is_running[i]:
                self.elapsed_time[i] = time.time() - self.start_time[i]
                mins, secs = divmod(int(self.elapsed_time[i]), 60)
                hours, mins = divmod(mins, 60)
                self.labels[i].setText(f"{hours:02}:{mins:02}:{secs:02}")
                self.pie_angles[i] = min(360 * self.elapsed_time[i] / self.timer_configs[i]["plan_time"], 360)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        width = self.width() // self.num_timers
        height = self.height()

        for i in range(self.num_timers):
            center_x = width * i + width // 2
            center_y = height // 2
            radius = min(width, height) // 4

            # Draw full circle background
            painter.setBrush(QBrush(Qt.lightGray))
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

            # Draw pie segment
            painter.setBrush(QBrush(self.colors[i]))
            painter.drawPie(center_x - radius, center_y - radius, radius * 2, radius * 2, 90 * 16, -int(self.pie_angles[i] * 16))

    def format_time(self, seconds):
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def load_configs(self):
        try:
            with open("timer_configs.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_configs(self):
        with open("timer_configs.json", "w") as f:
            json.dump(self.saved_configs, f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec_())

