from ctypes import windll
from obstacle_clearing import *
from interaction_functions import *
import cv2 as cv
import numpy as np


def main():
    # Make program aware of DPI scaling,
    windll.user32.SetProcessDPIAware()
    hwnd = get_hwnd("bluestacks")
    win32gui.SetForegroundWindow(hwnd)

    obstacle_clearer = ObstacleClearer(.97)

    while True:
        screenshot = get_screenshot(hwnd)
        screenshot = np.array(screenshot)
        screenshot = cv.cvtColor(screenshot, cv.COLOR_RGB2BGR)

        obstacle_clearer.find_obstacle_rectangles(screenshot)
        obstacle_clearer.show_obstacle_locations(screenshot)

        cv.imshow('Matches', screenshot)

        if cv.waitKey(1) == ord("q"):
            cv.destroyWindow()
            break


if __name__ == '__main__':
    main()
