import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QWidget
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

Pa = 33534  # Base pressure

#funckja generująca odcyzty barometrów
def generate_sensor_reading(reliability):
    if random.randint(0, 100) < reliability:
        return random.randint(Pa - 100, Pa + 100) / 100
    else:
        return random.randint(Pa - 400, Pa + 400) / 100


######################## algorytmy głosowania ###########################

#Mediananowy algorytm głosowania z adaptacyjnym oknem tolerancji
def median_voting(readings):
    def calculate_median(values):
        sorted_values = sorted(values)
        n = len(sorted_values)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_values[mid - 1] + sorted_values[mid]) / 2
        else:
            return sorted_values[mid]

    median = calculate_median(readings)

    #tablica odchyleń od mediany każdej wartośći
    deviations = [abs(r - median) for r in readings]

    # mediana z odchyleń, będzie stanowić margines odchylenia
    # (tj. mediana +-median_deviation)
    median_deviation = calculate_median(deviations)

    selected_readings = [r for r in readings if abs(r-median) <= median_deviation]

    if selected_readings:
        return calculate_median(selected_readings)

    return None


#Głosowanie większościowe z głosowaniem średnim
def majority_voting(readings):
    ERROR_MARGIN = 1.0  # 1% margines błędu

    def within_margin(value1, value2, margin):
        return abs(value1 - value2)/value1*100 <= margin

    # Sprawdzenie wszystkich kombinacji 2 lub 3 wartości
    matching_readings = []
    n = len(readings)

    # Iteracja po wszystkich parach, aby znaleźć największą grupę zgodnych wartości
    for i in range(n):
        current_group = [readings[i]]  # Zaczynamy od jednego elementu
        for j in range(n):
            if i != j and within_margin(readings[i], readings[j], ERROR_MARGIN):
                current_group.append(readings[j])

        # Jeśli znaleźliśmy większą grupę, zastępujemy obecną
        if len(current_group) > len(matching_readings):
            matching_readings = current_group

    # Sprawdzamy, czy liczba zgodnych wartości jest większa niż połowa
    if len(matching_readings) > n / 2:
        return sum(matching_readings) / len(matching_readings)  # Średnia zgodnych wartości

    # W przeciwnym razie zwróć None
    return None


#Głosowanie ważone
def weighted_voting(readings):
    weights = [0.5, 0.3, 0.2]  # Wagi barometrów
    weights_sum = sum(weights)

    # Średnia ważona
    weighted_average = sum(w * r for w, r in zip(weights, readings)) / weights_sum
    return weighted_average

##################################################################

#definiowanie wyglądu okna
class SensorPlot(QWidget):
    def __init__(self, reliability, parent=None):
        super().__init__(parent)

        self.reliability = reliability
        self.data = []
        self.time = []

        # Set up the layout and figure
        layout = QVBoxLayout()
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("czas [s]", fontsize=8)
        self.ax.set_ylabel("ciśnienie [hPa]", fontsize=8)
        self.ax.set_ylim(325, 345)
        self.ax.set_xlim(0, 100)
        self.ax.grid()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Initialize the line plot
        self.line, = self.ax.plot([], [], color="b")  # No label here

        # Initialize with a few data points (time 0 to 100 seconds) - stan początkowy
        for i in range(100):
            self.time.append(i)
            self.data.append(generate_sensor_reading(self.reliability))

        # Initialize the plot with data
        self.line.set_data(self.time, self.data)
        self.ax.relim()
        self.ax.set_xlim(self.time[0], self.time[-1])

        self.figure.subplots_adjust(bottom=0.30)
        self.canvas.draw()

    def update_plot(self, time_step):
        # Generate and store new data
        self.time.append(time_step)
        self.data.append(generate_sensor_reading(self.reliability))

        # Limit to last 100 points
        if len(self.time) > 100:
            self.time.pop(0)
            self.data.pop(0)

        # Update the line plot
        self.line.set_data(self.time, self.data)
        self.ax.relim()

        # Set the time range to the last 100 time steps (or fewer if less data)
        self.ax.set_xlim(self.time[0], self.time[-1])
        self.figure.subplots_adjust(hspace=0.1)
        self.canvas.draw()

    def get_latest_value(self):
        return self.data[-1] if self.data else None


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main widget
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Create sensor plots
        self.sensor1 = SensorPlot(96, self)
        self.sensor2 = SensorPlot(92, self)
        self.sensor3 = SensorPlot(87, self)

        # Create table for latest values
        self.table = QTableWidget(3, 6)
        self.table.setHorizontalHeaderLabels(["Barometr", "Ciśnienie [hPa]","", "Majority Voter", "Median Voter", "Weighted Voter"])
        self.table.setVerticalHeaderLabels(["Barometr 1", "Barometr 2", "Barometr 3"])
        self.table.setFixedHeight(150)

        # Add plots and table to layout
        layout.addWidget(self.sensor1)
        layout.addWidget(self.sensor2)
        layout.addWidget(self.sensor3)
        layout.addWidget(QLabel("Bierzące odczyty:"))
        layout.addWidget(self.table)

        # Set up the timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(500)  # Update every 500 ms (0.5 second)

        self.time_step = 100  # Start time from 100 seconds, since we already populated initial data

    def update_plots(self):
        self.time_step += 1

        # Update individual plots
        self.sensor1.update_plot(self.time_step)
        self.sensor2.update_plot(self.time_step)
        self.sensor3.update_plot(self.time_step)

        # Pobierz odczyty z sensorów
        readings = [
            self.sensor1.get_latest_value(),
            self.sensor2.get_latest_value(),
            self.sensor3.get_latest_value(),
        ]

        # Wyniki algorytmów głosowania
        maj_result = majority_voting(readings)
        med_result = median_voting(readings)
        weight_result = weighted_voting(readings)

        # Update table with latest values
        sensors = [self.sensor1, self.sensor2, self.sensor3]
        for i, sensor in enumerate(sensors):
            latest_value = sensor.get_latest_value()
            self.table.setItem(i, 0, QTableWidgetItem(f"Sensor {i + 1}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{latest_value:.2f}"))

        # Wyświetl wyniki algorytmów głosowania w ostatnim wierszu
        self.table.setItem(0, 3, QTableWidgetItem(f"{maj_result:.2f}" if maj_result is not None else "N/A"))
        self.table.setItem(0, 4, QTableWidgetItem(f"{med_result:.2f}" if med_result is not None else "N/A"))
        self.table.setItem(0, 5, QTableWidgetItem(f"{weight_result:.2f}"))

        self.table.setItem(0, 2, QTableWidgetItem("wynik głosowania [hPa]:"))
        self.table.setColumnWidth(2, 160)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.setWindowTitle("Pomiar wysokości w samolocie")
    window.resize(1200, 1000)
    window.show()
    sys.exit(app.exec_())
