from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QInputDialog, QSlider, QFormLayout, QComboBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
import sys
import time
import math
import random
import json

class TimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customizable Timers with Pie Charts")
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Always on top

        # Load saved configurations
        self.saved_configs = self.load_configs()

        # Initialize timers
        self.num_timers, ok = QInputDialog.getInt(self, "Timers", "Enter number of timers:", min=1, max=10)
        if not ok:
            sys.exit()

        self.titles = []
        self.plan_time = []
        self.colors = []

        for i in range(self.num_timers):
            title, plan_time = self.get_timer_config(i)
            self.titles.append(title)
            self.plan_time.append(plan_time)

            # Generate a random color for each timer
            self.colors.append(QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

        self.is_running = [False] * self.num_timers
        self.start_time = [0] * self.num_timers
        self.elapsed_time = [0] * self.num_timers
        self.pie_angles = [0] * self.num_timers

        self.labels = []
        self.reset_buttons = []

        main_layout = QVBoxLayout()

        # Transparency slider
        self.transparency_slider = QSlider(Qt.Horizontal, self)
        self.transparency_slider.setMinimum(50)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setValue(90)
        self.transparency_slider.valueChanged.connect(self.adjust_transparency)
        transparency_layout = QFormLayout()
        transparency_layout.addRow("Transparency:", self.transparency_slider)
        main_layout.addLayout(transparency_layout)

        timer_layout = QHBoxLayout()

        for i in range(self.num_timers):
            single_timer_layout = QVBoxLayout()

            # Add timer title
            label_title = QLabel(f"{self.titles[i]} (Plan: {self.format_time(self.plan_time[i])})", self)
            label_title.setAlignment(Qt.AlignCenter)
            label_title.setStyleSheet("font-size: 18px; font-weight: bold;")
            single_timer_layout.addWidget(label_title)

            # Add timer label
            label = QLabel("00:00:00", self)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 24px;")
            single_timer_layout.addWidget(label)
            self.labels.append(label)

            reset_button = QPushButton("Reset", self)
            reset_button.clicked.connect(lambda checked, i=i: self.reset_timer(i))
            single_timer_layout.addWidget(reset_button)
            self.reset_buttons.append(reset_button)

            timer_layout.addLayout(single_timer_layout)

        main_layout.addLayout(timer_layout)
        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(100)

    def get_timer_config(self, index):
        preset_names = [config["title"] for config in self.saved_configs]
        preset_names.append("New Timer")

        title, ok = QInputDialog.getItem(self, f"Timer {index+1}", "Choose a timer preset or create a new one:", preset_names, editable=True)
        if not ok:
            sys.exit()

        if title == "New Timer" or title not in preset_names:
            title, ok = QInputDialog.getText(self, f"Timer {index+1}", f"Enter name for timer {index+1}:")
            if not ok:
                sys.exit()

            hours, ok = QInputDialog.getInt(self, f"Timer {index+1}", f"Enter hours for {title}:", min=0, max=99)
            if not ok:
                sys.exit()

            minutes, ok = QInputDialog.getInt(self, f"Timer {index+1}", f"Enter minutes for {title}:", min=0, max=59)
            if not ok:
                sys.exit()

            seconds, ok = QInputDialog.getInt(self, f"Timer {index+1}", f"Enter seconds for {title}:", min=0, max=59)
            if not ok:
                sys.exit()

            plan_time = hours * 3600 + minutes * 60 + seconds

            save, ok = QInputDialog.getItem(self, f"Save Timer {index+1}", "Save this timer as a preset?", ["Yes", "No"], editable=False)
            if ok and save == "Yes":
                self.save_timer_config(title, plan_time)
        else:
            for config in self.saved_configs:
                if config["title"] == title:
                    plan_time = config["plan_time"]
                    break

        return title, plan_time

    def save_timer_config(self, title, plan_time):
        if len(self.saved_configs) >= 5:
            self.saved_configs.pop(0)  # Keep only the 5 most recent presets
        self.saved_configs.append({"title": title, "plan_time": plan_time})
        self.save_configs()

    def adjust_transparency(self):
        value = self.transparency_slider.value()
        self.setWindowOpacity(value / 100)

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

    def reset_timer(self, index):
        self.is_running[index] = False
        self.elapsed_time[index] = 0
        self.pie_angles[index] = 0
        self.labels[index].setText("00:00:00")

    def update_timer(self):
        for i in range(self.num_timers):
            if self.is_running[i]:
                self.elapsed_time[i] = time.time() - self.start_time[i]
                mins, secs = divmod(int(self.elapsed_time[i]), 60)
                hours, mins = divmod(mins, 60)
                self.labels[i].setText(f"{hours:02}:{mins:02}:{secs:02}")

                # Update pie angle based on elapsed time and plan time
                self.pie_angles[i] = min(360 * self.elapsed_time[i] / self.plan_time[i], 360)

                # Mark timer as complete if it exceeds plan time
                if self.elapsed_time[i] >= self.plan_time[i]:
                    self.is_running[i] = False
                    self.pie_angles[i] = 360

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

            # Draw timer title and planned time above the clock
            painter.setPen(QPen(Qt.black))
            painter.drawText(center_x - radius, center_y - radius - 30, radius * 2, 20, Qt.AlignCenter, f"{self.titles[i]}")
            painter.drawText(center_x - radius, center_y - radius - 10, radius * 2, 20, Qt.AlignCenter, f"Plan: {self.format_time(self.plan_time[i])}")


    def format_time(self, seconds):
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def load_configs(self):
        try:
            with open("timer_configs.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_configs(self):
        with open("timer_configs.json", "w") as f:
            json.dump(self.saved_configs, f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec_())

