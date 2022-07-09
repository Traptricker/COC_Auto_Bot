from ctypes import windll
from ast import literal_eval
from random import randrange
from training_and_attacking import *
from village_clearing import *
from village_upgrading import *
from account_changing import *
from village_building import *
from interaction_functions import *
from data_storing import *
import cv2 as cv
import numpy as np


def main():
    # Makes program aware of DPI scaling,
    windll.user32.SetProcessDPIAware()
    hwnd = get_hwnd("bluestacks")

    # Resizes and moves the window to the front
    win32gui.MoveWindow(hwnd, 10, 10, 1400, 805, True)
    win32gui.SetForegroundWindow(hwnd)

    # This is how many accounts the bot operates, max is 50
    number_of_accounts = 9

    # The classes that carry out the main functions of the bot
    village_clearer = VillageClearer(win32gui.GetWindowRect(hwnd))
    village_upgrader = VillageUpgrader(win32gui.GetWindowRect(hwnd))
    trainer_and_attacker = TrainerAndAttacker(win32gui.GetWindowRect(hwnd))
    account_changer = AccountChanger(win32gui.GetWindowRect(hwnd), number_of_accounts)
    village_builder = VillageBuilder(win32gui.GetWindowRect(hwnd))
    data_storer = DataStorer(number_of_accounts)

    # Makes sure the csv file has rows for each account
    data_storer.add_new_accounts()

    # Variables used to smoothly move between the functions of the bot
    mode = 1
    tries = 0

    # The images used to deal with various pop-ups
    pop_up_buttons = (
        # Reloads the game if the client and game get de-synced
        (cv.imread("assets/buttons/reload_game_button.jpg", cv.IMREAD_UNCHANGED), .95),
        # Reconnects to the game if connection is lost
        (cv.imread("assets/buttons/try_again_button.jpg", cv.IMREAD_UNCHANGED), .95),
        (cv.imread("assets/buttons/okay_button.jpg", cv.IMREAD_UNCHANGED), .95),
        # Clicks the okay button that appears when you open an account with recently finished upgrades
        (cv.imread("assets/buttons/okay_button_2.jpg", cv.IMREAD_UNCHANGED), .95),
        # Clicks on the okay button that acknowledges you breaking your shield
        (cv.imread("assets/buttons/okay_button_3.jpg", cv.IMREAD_UNCHANGED), .95),
        # Clicks on the okay button when you get treasury loot
        (cv.imread("assets/buttons/okay_button_4.jpg", cv.IMREAD_UNCHANGED), .95),
    )

    pop_up_button_i = 0

    sleep(3)

    # The main loop of the bot
    while True:
        window_rectangle = win32gui.GetWindowRect(hwnd)

        screenshot = get_screenshot(hwnd)
        screenshot = np.array(screenshot)
        screenshot = cv.cvtColor(screenshot, cv.COLOR_RGB2BGR)

        # Deals with various pop-ups that can happen, only does one per frame rather than all of them every frame
        pop_up_button_i += 1
        if pop_up_button_i >= len(pop_up_buttons):
            pop_up_button_i = 0
        button = pop_up_buttons[pop_up_button_i]
        button_rectangle = find_image_rectangle(button, screenshot)
        if button_rectangle:
            x, y = get_center_of_rectangle(button_rectangle)
            click(x, y, window_rectangle)

        if mode == 1:  # Clears the village of obstacles and collects loot
            village_clearer.window_rectangle = window_rectangle
            village_clearer.collect_loot_cart(screenshot)
            village_clearer.collect_resources(screenshot)
            if village_clearer.clear_obstacle(screenshot) or tries >= 6:
                data_storer.update_account_info(account_changer.account_number,
                                                rocks_removed=village_clearer.rocks_removed)
                mode += 1
                tries = 0
        elif mode == 2:  # Upgrades and purchases buildings
            village_upgrader.window_rectangle = window_rectangle
            if (village_upgrader.upgrade_building(
                    screenshot) or tries >= 5) and not village_upgrader.upgrading_building:
                mode += 1
                tries = 0
            village_upgrader.show_suggested_upgrades(screenshot)
        elif mode == 3:  # Trains troops and attacks for loot
            trainer_and_attacker.window_rectangle = window_rectangle
            trainer_and_attacker.train_troops(screenshot)
            if trainer_and_attacker.troops_training and tries > 1:
                trainer_and_attacker.troops_training = False
                mode += 1
                tries = 0
            elif trainer_and_attacker.find_base_to_attack(screenshot) or tries >= 150:
                # Stores the collected account data in a csv file
                data_storer.update_account_info(account_changer.account_number,
                                                total_gold=trainer_and_attacker.total_gold,
                                                total_elixir=trainer_and_attacker.total_elixir,
                                                gold_read=trainer_and_attacker.gold_read,
                                                elixir_read=trainer_and_attacker.elixir_read,
                                                )
                mode += 1
                tries = 0
            elif trainer_and_attacker.attacked:
                trainer_and_attacker.attacked = False
                data_storer.update_account_info(account_changer.account_number,
                                                total_gold=trainer_and_attacker.total_gold,
                                                total_elixir=trainer_and_attacker.total_elixir,
                                                gold_read=trainer_and_attacker.gold_read,
                                                elixir_read=trainer_and_attacker.elixir_read,
                                                )
                mode += 1
                tries = 0
        elif mode == 4:  # Sets base layouts
            # Stores the town hall level for the account in a csv file
            town_hall_level = village_builder.get_town_hall_level(screenshot)
            if town_hall_level > 0:
                data_storer.update_account_info(account_changer.account_number,
                                                town_hall=village_builder.get_town_hall_level(screenshot))
            village_builder.town_hall_level = int(data_storer.get_account_info(account_changer.account_number)[0])
            if village_builder.town_hall_level >= 4 and randrange(0, 11) == 10:
                village_builder.window_rectangle = window_rectangle
                if village_builder.base_link_entered:
                    # Handles base editing and saving
                    if village_builder.handle_base_edit(screenshot):
                        village_builder.base_link_entered = False
                        sleep(1)
                        # Once the process is done, it closes out of the base window
                        x_out()
                        sleep(.5)
                        mode += 1
                        tries = 0
                else:
                    # Opens chrome and enters the base link
                    village_builder.copy_base_layout(screenshot)
            else:
                mode += 1
                tries = 0
        elif mode == 5:  # Changes Supercell ID accounts
            account_changer.window_rectangle = window_rectangle
            account_changer.open_account_menu(screenshot)
            account_changer.select_next_account(screenshot)
            if account_changer.account_changed or tries > 100:
                account_changer.account_changed = False
                # Reads values from csv file for the new account
                village_clearer.rocks_removed = literal_eval(
                    data_storer.get_account_info(account_changer.account_number)[1])
                trainer_and_attacker.total_gold = int(data_storer.get_account_info(account_changer.account_number)[2])
                trainer_and_attacker.total_elixir = int(data_storer.get_account_info(account_changer.account_number)[3])
                trainer_and_attacker.gold_read = int(data_storer.get_account_info(account_changer.account_number)[4])
                trainer_and_attacker.elixir_read = int(data_storer.get_account_info(account_changer.account_number)[5])
                mode += 1
                tries = 0
        else:
            mode = 1

        print(mode)
        tries += 1

        # cv.imshow("What the code sees", screenshot)

        if cv.waitKey(1) == ord("q"):
            cv.destroyWindow()
            break


if __name__ == "__main__":
    main()
