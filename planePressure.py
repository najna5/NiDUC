import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QWidget, QDialog, QPushButton,
    QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QLabel
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

Pa = 33534  # Base pressure in Pa

# Funkcja generująca odczyty barometrów w hPa
def generate_sensor_reading(reliability):
    if random.randint(0, 100) < reliability:
        return random.randint(Pa - 20, Pa + 20) / 100
    else:
        return random.randint(Pa - 100, Pa + 100) / 100


######################## Algorytmy głosowania ###########################

# Medianowy algorytm głosowania z adaptacyjnym oknem tolerancji
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

    # Tablica odchyleń od mediany
    deviations = [abs(r - median) for r in readings]
    median_deviation = calculate_median(deviations)

    selected_readings = [r for r in readings if abs(r - median) <= median_deviation]

    if selected_readings:
        return calculate_median(selected_readings)
    return None


# Głosowanie większościowe z głosowaniem średnim
def majority_voting(readings):
    ERROR_MARGIN = 1.0  # 1% margines błędu

    def within_margin(value1, value2, margin):
        return abs(value1 - value2) / value1 * 100 <= margin

    matching_readings = []
    n = len(readings)

    for i in range(n):
        current_group = [readings[i]]
        for j in range(n):
            if i != j and within_margin(readings[i], readings[j], ERROR_MARGIN):
                current_group.append(readings[j])

        if len(current_group) > len(matching_readings):
            matching_readings = current_group

    if len(matching_readings) > n / 2:
        return sum(matching_readings) / len(matching_readings)
    return None


# Głosowanie ważone
def weighted_voting(readings):
    weights = [0.5, 0.3, 0.2]  # Wagi barometrów
    weights_sum = sum(weights)
    weighted_average = sum(w * r for w, r in zip(weights, readings)) / weights_sum
    return weighted_average

##################################################################

# Funkcja zapisu danych do pliku
def save_to_file(time_step, filename, majority, median, weighted):
    with open(filename, "a") as file:
        file.write(f"{time_step};{majority:.2f};{median:.2f};{weighted:.2f}\n")

# Funkcja obliczania wysokosci na podstawie cisnienia atmosferycznego

def height(pressure):
    return 44330 * (1-(pressure/1013.25)**(1/5.255))

################ okno do wyboru pogody ##########################

class WeatherConditionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybór warunków pogodowych")
        self.resize(400, 300)

        # Układ dialogu
        layout = QVBoxLayout(self)

        # Dodanie etykiety z opisem
        layout.addWidget(QLabel("Wybierz warunki pogodowe:"))

        # Opcje warunków pogodowych
        self.clear_radio = QRadioButton("Bezchmurnie")
        self.cloudy_radio = QRadioButton("Pochmurno")
        self.stormy_radio = QRadioButton("Burzowo")
        self.clear_radio.setChecked(True)  # Domyślna opcja

        layout.addWidget(self.clear_radio)
        layout.addWidget(self.cloudy_radio)
        layout.addWidget(self.stormy_radio)

        # Przyciski OK/Anuluj
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_selected_conditions(self):
        """Zwraca wybrane warunki pogodowe."""
        if self.clear_radio.isChecked():
            return "clear"
        elif self.cloudy_radio.isChecked():
            return "cloudy"
        elif self.stormy_radio.isChecked():
            return "stormy"
        return "clear"

class SensorPlot(QWidget):
    def __init__(self, reliability, parent=None):
        super().__init__(parent)
        self.reliability = reliability
        self.data = []
        self.time = []

        layout = QVBoxLayout()
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("czas [0.5 s]", fontsize=8)
        self.ax.set_ylabel("ciśnienie [hPa]", fontsize=8)
        self.ax.set_ylim(325, 345)
        self.ax.set_xlim(0, 100)
        self.ax.grid()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.line, = self.ax.plot([], [], color="b")
        for i in range(100):
            self.time.append(i)
            self.data.append(generate_sensor_reading(self.reliability))
        self.line.set_data(self.time, self.data)
        self.ax.relim()
        self.ax.set_xlim(self.time[0], self.time[-1])

        self.figure.subplots_adjust(bottom=0.30)
        self.canvas.draw()

    def update_plot(self, time_step):
        self.time.append(time_step)
        self.data.append(generate_sensor_reading(self.reliability))

        if len(self.time) > 100:
            self.time.pop(0)
            self.data.pop(0)

        self.line.set_data(self.time, self.data)
        self.ax.relim()
        self.ax.set_xlim(self.time[0], self.time[-1])
        self.canvas.draw()

    def get_latest_value(self):
        return self.data[-1] if self.data else None

#################### okno z wykresem wysokości ##########################
class HeightPlot(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wykres wysokości")
        self.resize(1200, 800)
        self.time = []

        # Ustawienie układu i wykresu
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("czas [0.5 s]", fontsize=8)
        self.ax.set_ylabel("wysokość [m n.p.m.]", fontsize=8)
        self.ax.grid()

        # Przygotowanie danych
        self.heights_voting1 = [] # Wysokości dla sensora 1
        self.heights_voting2 = [] # Wysokości dla sensora 2
        self.heights_voting3 = [] # Wysokości dla sensora 3
        self.heights_pa = [] # Wysokości dla głównej zmiennej `Pa`

        for i in range(100):
            self.time.append(i)
            one = generate_sensor_reading(98)
            two = generate_sensor_reading(96)
            three = generate_sensor_reading(90)
            self.heights_voting1.append(height(majority_voting([one,two,three])))
            self.heights_voting2.append(height(median_voting([one,two,three])))
            self.heights_voting3.append(height(weighted_voting([one,two,three])))
            self.heights_pa.append(height(Pa/100))

        # Dodanie linii dla każdego źródła danych
        self.line_sensor1, = self.ax.plot(self.time, self.heights_voting1, label="Majority voting", color="b")
        self.line_sensor2, = self.ax.plot(self.time, self.heights_voting2, label="Median voting", color="r")
        self.line_sensor3, = self.ax.plot(self.time, self.heights_voting3, label="Weighted voting", color="g")
        self.line_pa, = self.ax.plot(self.time, self.heights_pa, label="Bazowa wysokość", color="k", linestyle="--")

        # Ustawienie legendy
        self.ax.legend()

        # Dynamiczne osie
        self.ax.set_xlim(self.time[0], self.time[-1])
        self.ax.set_ylim(0, 10)  # Początkowy zakres osi Y
        layout.addWidget(self.canvas)

    def update_plot(self, time_step, heights):
        # `heights` to słownik zawierający wartości dla każdej serii danych
        voting1_height = heights["sensor1"]
        voting2_height = heights["sensor2"]
        voting3_height = heights["sensor3"]
        pa_height = heights["pa"]

        # Aktualizacja danych dla każdej linii
        self.time.append(time_step)
        self.time.pop(0)

        self.heights_voting1.append(voting1_height)
        self.heights_voting1.pop(0)

        self.heights_voting2.append(voting2_height)
        self.heights_voting2.pop(0)

        self.heights_voting3.append(voting3_height)
        self.heights_voting3.pop(0)

        self.heights_pa.append(pa_height)
        self.heights_pa.pop(0)

        # Aktualizacja linii wykresu
        self.line_sensor1.set_data(self.time, self.heights_voting1)
        self.line_sensor2.set_data(self.time, self.heights_voting2)
        self.line_sensor3.set_data(self.time, self.heights_voting3)
        self.line_pa.set_data(self.time, self.heights_pa)

        # Dynamiczne skalowanie osi
        self.ax.set_ylim(height(Pa/100)-30, height(Pa/100)+30)
        self.ax.set_xlim(self.time[0], self.time[-1])
        self.canvas.draw()

######################## okno główne wyświetlające odczyty baromatrów ##########################

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Wywołanie okna wyboru warunków pogodowych
        dialog = WeatherConditionsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_conditions = dialog.get_selected_conditions()
        else:
            # Domyślnie "bezchmurnie", jeśli użytkownik zamknie dialog
            selected_conditions = "clear"

        # Ustawienie niezawodności na podstawie wybranych warunków
        if selected_conditions == "clear":
            self.filename = "clear.txt"
            reliability1, reliability2, reliability3 = 98, 96, 94
        elif selected_conditions == "cloudy":
            self.filename = "cloudy.txt"
            reliability1, reliability2, reliability3 = 90, 85, 80
        elif selected_conditions == "stormy":
            self.filename = "stormy.txt"
            reliability1, reliability2, reliability3 = 75, 70, 65
        else:
            reliability1, reliability2, reliability3 = 98, 96, 94  # Domyślnie

        with open(self.filename, "w") as file:
            file.write("czas;majority_voter;median_voter;weighted_voter\n")
        # Tworzenie sensorów z przypisaną niezawodnością
        self.sensor1 = SensorPlot(reliability1, self)
        self.sensor2 = SensorPlot(reliability2, self)
        self.sensor3 = SensorPlot(reliability3, self)

        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.table = QTableWidget(3, 6)
        self.table.setHorizontalHeaderLabels(["Barometr", "Ciśnienie [hPa]", "", "Majority Voter", "Median Voter", "Weighted Voter"])
        self.table.setVerticalHeaderLabels(["Barometr 1", "Barometr 2", "Barometr 3"])
        self.table.setFixedHeight(150)

        layout.addWidget(self.sensor1)
        layout.addWidget(self.sensor2)
        layout.addWidget(self.sensor3)
        layout.addWidget(QLabel("Bierzące odczyty:"))
        layout.addWidget(self.table)

        self.open_height_plot_button = QPushButton("Pokaż wykres wysokości")
        self.open_height_plot_button.clicked.connect(self.open_height_plot)
        layout.addWidget(self.open_height_plot_button)

        # Utwórz instancję HeightPlot
        self.height_plot = HeightPlot(self)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(500)

        self.time_step = 100

    def open_height_plot(self):
        # Pokaż już istniejący i aktualizowany w tle wykres
        self.height_plot.show()

    def update_plots(self):
        self.time_step += 1

        # Aktualizacja danych ciśnienia na wykresach sensorów
        self.sensor1.update_plot(self.time_step)
        self.sensor2.update_plot(self.time_step)
        self.sensor3.update_plot(self.time_step)

        # Odczyty z sensorów
        readings = [
            self.sensor1.get_latest_value(),
            self.sensor2.get_latest_value(),
            self.sensor3.get_latest_value(),
        ]

        # Obliczenia metodami głosowania
        maj_result = majority_voting(readings)
        med_result = median_voting(readings)
        weight_result = weighted_voting(readings)

        # Obliczanie wysokości
        heights = {
            "sensor1": height(maj_result),
            "sensor2": height(med_result),
            "sensor3": height(weight_result),
            "pa": height(Pa/100),
        }

        # Aktualizacja tabeli
        sensors = [self.sensor1, self.sensor2, self.sensor3]
        for i, sensor in enumerate(sensors):
            latest_value = sensor.get_latest_value()
            self.table.setItem(i, 0, QTableWidgetItem(f"Sensor {i + 1}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{latest_value:.2f}"))

        self.table.setItem(0, 3, QTableWidgetItem(f"{maj_result:.2f}" if maj_result is not None else "N/A"))
        self.table.setItem(0, 4, QTableWidgetItem(f"{med_result:.2f}" if med_result is not None else "N/A"))
        self.table.setItem(0, 5, QTableWidgetItem(f"{weight_result:.2f}"))
        self.table.setItem(1, 3,
                           QTableWidgetItem(f"{height(maj_result):.2f}" if height(maj_result) is not None else "N/A"))
        self.table.setItem(1, 4,
                           QTableWidgetItem(f"{height(med_result):.2f}" if height(med_result) is not None else "N/A"))
        self.table.setItem(1, 5, QTableWidgetItem(f"{height(weight_result):.2f}"))
        self.table.setItem(0, 2, QTableWidgetItem("wynik głosowania [hPa]:"))
        self.table.setItem(1, 2, QTableWidgetItem("wysokość [m n.p.m.]:"))
        self.table.setColumnWidth(2, 200)

        # Aktualizacja wykresu wysokości
        if not self.height_plot:
            self.height_plot = HeightPlot(self)
        self.height_plot.update_plot(self.time_step, heights)

        # Zapis do pliku
        save_to_file(self.time_step, self.filename, maj_result or 0, med_result or 0, weight_result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.setWindowTitle("Pomiar wysokości w samolocie")
    window.resize(1200, 1000)
    window.show()
    sys.exit(app.exec_())


