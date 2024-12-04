#nie usuwałam tego, ale w sumie użyte w planePressure więc już niepotrzebne
import numpy as np
import random
import matplotlib
from matplotlib import pyplot as plt

def main():
    fig, axs = plt.subplots(4, 1, figsize=(45, 30))
    Pa = 33534
    x = []
    fs = []
    ss = []
    ts = []
    for i in range(100):
        x.append(i)
        # firstSensor logic
        if random.randint(0,100) < 96:
            value = random.randint(Pa - 100, Pa + 100)/100
        else:
            value = random.randint(Pa - 400, Pa + 400)/100
        fs.append(value)
        firstSensor = np.array(fs)


        # secondSensor logic
        if random.randint(0, 100) < 92:
            value = random.randint(Pa - 100, Pa + 100) / 100
        else:
            value = random.randint(Pa - 400, Pa + 400) / 100

        ss.append(value)
        secondSensor = np.array(ss)


        # thirdSensor logic
        if random.randint(0, 100) < 87:
            value = random.randint(Pa - 100, Pa + 100) / 100
        else:
            value = random.randint(Pa - 400, Pa + 400) / 100

        ts.append(value)
        thirdSensor = np.array(ts)

    # First plot
    plt.title("Sensor 1")
    axs[0].plot(firstSensor,"o")
    axs[0].set_title("Sensor 1")  # Tytuł wykresu
    axs[0].set_xlabel("Czas [s]")
    axs[0].set_ylabel("Cieśnienie [hPa]")
    axs[0].set_xticks(range(0, 101, 5))
    axs[0].set_ylim((Pa - 500) / 100, (Pa + 500) / 100)

    #Second plot

    plt.title("Sensor 2")
    axs[1].plot(secondSensor, "o")
    axs[1].set_title("Sensor 2")
    axs[1].set_xlabel("Czas [s]")
    axs[1].set_ylabel("Ciśnienie [hPa]")
    axs[1].set_xticks(range(0, 101, 5))
    axs[1].set_ylim((Pa - 500) / 100, (Pa + 500) / 100)

    #Third plot
    axs[2].plot(thirdSensor, "o")
    axs[2].set_title("Sensor 3")
    axs[2].set_xlabel("Czas [s]")
    axs[2].set_ylabel("Ciśnienie [hPa]")
    axs[2].set_ylim((Pa - 500) / 100, (Pa + 500) / 100)
    axs[2].set_xticks(range(0, 101, 5))

    # Fourth plot
    axs[3].scatter(x,firstSensor)
    axs[3].scatter(x,secondSensor)
    axs[3].scatter(x,thirdSensor)
    axs[3].set_title("Wszystkie sensory")
    axs[3].set_xlabel("Czas [s]")
    axs[3].set_ylabel("Ciśnienie [hPa]")
    axs[3].set_xticks(range(0, 101, 5))
    axs[3].set_ylim((Pa - 500) / 100, (Pa + 500) / 100)

    # Show
    plt.subplots_adjust(hspace=0.4)
    plt.show()

    print(firstSensor)
    print(secondSensor)
    print(thirdSensor)


if __name__ == '__main__':
    main()


