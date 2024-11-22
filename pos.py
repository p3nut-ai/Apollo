import MetaTrader5 as mt5
from termcolor import colored
import colorama
from main import *

colorama.init()

def mt5_login():
    login = ""
    password = ""
    server = ""
    mt5.login(login, password, server)

    return True


def has_position():
    mt5_login()
    symbol = "XAUUSD"  # Update this as needed
    positions = mt5.positions_get(symbol=symbol)
    flag = False
    position_counter = 0

    if not positions:
        print(colored("[-] No active positions", "red"))
        return False
    else:
        for position in positions:
            position_counter += 1


    if position_counter >= 1:
        print("You cannot trade today please wait for another 24 hrs")

        return False

    else:
        print("You're able to trade")
        return True

    return False

def can_place_order():
    if has_position():
        return True

    return False


def has_running_pos():
    print("You have a running position")
    process_name = "terminal64.exe"  # Your MT5 process name
    time.sleep(2)
    counter = 0
    while counter <= 3:
        if _isProtectCap.lower() == 'yes':
            hide_window(process_name)
            is_protect_capital()
            app.run(debug=False, host=ipv4, port=5000)
            return True
        elif _isProtectCap.lower() == 'no':
            print("Turning off Capital Protection Protocol")
            hide_window(process_name)
            app.run(debug=False, host=ipv4, port=5000)
            return True
        else:
            print("Invalid input. Try again.")
            counter += 1
    return False
