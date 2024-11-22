import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os
import time
from flask import Flask, render_template, url_for, request, redirect, jsonify, session
import random
import psutil
import win32gui
import win32con
import win32process
import webbrowser
import socket
import threading
import keyboard
from protect import *
from termcolor import colored
import colorama
from pos import *
import sqlite3
import textwrap

colorama.init()

if os.name == "nt":
    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
else:
    print(colored("[-] Sorry system is not currently available to not windows user" , "red"))
    exit()

app = Flask(__name__)
app.secret_key = '79123hjuih9'
symbol = "XAUUSD"
msg = ""
# _isProtectCap = input("Do you want to enable proctection capital?: yes/no ")
_isProtectCap = "yes"

word = colored("We stop the odds, you start winning.", "black", "on_light_green")
banner = f"""
   _______
  /\\ o o o\\
 /o \\ o o o\\_______
<    >------>   o /|
 \\ o/  o   /_____/o|         APOLLO
  \\/______/     |oo|         version 0.3.0
        |   o   |o/          Author: Jonathan
        |_______|/           {word}

"""


time.sleep(2)

def databse_connection():
    global conn
    # Connect to or create the SQLite database
    conn = sqlite3.connect("session_db.sqlite")
    cursor = conn.cursor()

    # Create the session table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()


def clean_old_sessions():
    # Define the cutoff time for outdated sessions (24 hours ago)
    cutoff_time = datetime.utcnow() - timedelta(days=1)
    cursor = conn.cursor()
    # Check if there are any active sessions within the last 24 hours
    cursor.execute("SELECT timestamp FROM user_sessions WHERE timestamp >= ?", (cutoff_time.isoformat(),))
    active_sessions = cursor.fetchall()

    if active_sessions:
        print(colored("[-] Program access denied due to an active session.", "black", "on_light_red"))
        return False
    else:
        # Delete entries older than 24 hours
        cursor.execute("DELETE FROM user_sessions WHERE timestamp < ?", (cutoff_time.isoformat(),))
        conn.commit()
        # print(colored("[-] Session within the last 24 hours deleted", "black", "on_light_green"))
        return True

def del_sesh():
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions")
    conn.commit()
    return True


def can_use_program():

    cursor = conn.cursor()

    if not has_position() and not clean_old_sessions():
        print(colored("[-] Error no active position but there's a session created on database", "black", "on_light_red"))
        print(colored("Clearing sessions on database", "yellow"))
        del_sesh()
        print(colored("Sessions removed", "green"))
        return False

    else:
        # Fetch the most recent session timestamp
        cursor.execute("SELECT timestamp FROM user_sessions ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()

        if result:
            last_session_time = datetime.fromisoformat(result[0])
            time_since_last = datetime.utcnow() - last_session_time

            # Check if the last session was within the last 24 hours
            if time_since_last < timedelta(days=1):
                print(colored(f"[-] Trade is on going check dashboard for position http://{ipv4}:5000", "black", "on_light_red"))
                print(colored("[-] Program access denied. Last session is still within 24 hours.", "red"))
                is_protect_capital()
                return False
            else:
                print(colored("[+] Program access granted. Last session was more than 24 hours ago.", "green"))
                is_protect_capital()
                return True
        else:
            print(colored("[-] No previous session found. Access granted.", "green"))

        # Insert a new session entry since access is allowed
        print(colored("[!] Inserting new session on database.", "yellow"))
        cursor.execute("INSERT INTO user_sessions (timestamp) VALUES (?)", (datetime.utcnow().isoformat(),))
        conn.commit()
        print(colored("[+] New session created.", "black", "on_light_green"))
        is_protect_capital()
        return True

def mt5_login():
    login = "24401976"
    password = "lohjILDM_.42!"
    server = "FivePercentOnline-Real"
    mt5.login(login, password, server)

    return True


def init_mt():
    if not mt5.initialize():
        print(colored("[-] initialize() failed", "red"))
        return False
        mt5.shutdown()
        exit()
    else:
        mt5_login()
    return True

@app.route('/')
def index():
    mt5_login()
    symbol = "XAUUSD"
    positions = mt5.positions_get(symbol=symbol)
    status = None
    pos_profit = 0
    msg = session.get('msg', None)  # Retrieve msg from session (if any)
    position_ticket = 0


    if can_place_order():
        status = "You can place a new order."
    else:
        status = "You already have an open position for this. Please wait 24 hours to place another order."
        # Get the profit of the current position
        if positions:
            for position in positions:
                pos_profit = position.profit
                position_ticket = position.ticket


    response = render_template('index.html', status=status, pos_profit=pos_profit, msg=msg, position = position_ticket)

    # Clear the message from the session AFTER rendering the page
    session.pop('msg', None)
    return response

@app.route('/check_quota')
def check_quota():
    # print(colored("Hello from ajax", "black", "on_light_green"))
    mt5_login()
    # Get open positions for the specific symbol
    positions = mt5.positions_get(symbol=symbol)
    pos_profit = None

    if positions is None or len(positions) == 0:
        return jsonify({"msg": "No open positions", "redirect": False})

    # Loop through the positions to check profit (assuming only one position per symbol)
    for position in positions:
        pos_profit = position.profit

    # Check if capital protection is active
    if _isProtectCap.lower() == "yes":
        is_protect_capital()

        # If quota hit (pos_profit == 100)
        if pos_profit == 100.00 or pos_profit == 100:
            return jsonify({"msg": "Quota hit", "redirect": True})

        # check for BE to be fixed soon
        # elif pos_profit == 50.00 or pos_profit == 50:
        #     msg = "Position is set to BE hitted mark profit for breakeven"
        #     return jsonify({"msg": msg, "redirect": "be"})

            # print("Position is set to BE hitted mark profit for breakeven")
            # return redirect('/set_be_ajax')
        else:
            print(colored("[-] Profit is not at quota yet", "red"))
            return jsonify({"msg": "Profit is not at quota yet", "redirect": False})
    else:
        # If quota hit (pos_profit == 100)
        if pos_profit == 100:
            msg = "Position Close quota hit"
            return jsonify({"msg": msg, "redirect": True})
        else:
            return jsonify({"msg": "Profit is not at quota yet", "redirect": False})
    return jsonify({"msg": msg})

@app.route('/close_position')
def close_position():
    mt5_login()
    _isProtectCap
    global msg
    positions = mt5.positions_get(symbol=symbol)
    position_counts = []
    postion_tic = None
    position_sym = None

    if positions:
        for position in positions:
            position_counts.append(position)
            postion_tic = position.ticket
            position_sym = position.symbol

        pos_num = len(position_counts)

        # Handle multiple positions
        if pos_num > 1:
            if _isProtectCap.lower() == "yes":
                is_protect_capital()
                msg = "Protection Capital triggered."
                return jsonify({'msg': msg})
            else:
                msg = "[!]You've had multiple positions and Protection Capital is not on; cannot perform this protocol."
                print(colored(msg, "yellow"))
                return jsonify({'msg': msg})

        else:
            # Only one position to close
            try:
                # Determine the order type based on the current position's type
                close_type = mt5.ORDER_TYPE_SELL if positions[0].type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

                # Prepare the close request
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": postion_tic,
                    "symbol": position_sym,
                    "volume": positions[0].volume,  # Use the exact volume of the open position
                    "type": close_type,  # Determine if it's a buy or sell close
                }

                # Send the close request
                result = mt5.order_send(close_request)

                # Check the result
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    msg = f"Position {postion_tic} closed successfully."
                    print(msg)
                    return jsonify({'msg': msg})
                else:
                    msg = f"Failed to close position {postion_tic}. Error code: {result.retcode}."
                    print(msg)
                    return jsonify({'msg': msg})

            except Exception as e:
                msg = f"An error occurred: {str(e)}"
                print(msg)
                return jsonify({'msg': msg})

    else:
        msg = "No Running positions."
        print(msg)

    return jsonify({'msg': msg})

@app.route('/clear_msg')
def clear_msg():
    _msg = True
    return jsonify({'msg':_msg})


@app.route('/set_new_tp/<int:id>', methods=["POST"])
def new_tp(id):
    new_tp = request.form.get('new_tp')
    mt5_login()
    try:
        new_tp_float = float(new_tp)  # Convert to float
    except ValueError:
        return jsonify({'msg': 'Invalid TP value, must be a number'}), 400

    ticket = id
    symbol = "XAUUSD"
    positions = mt5.positions_get(symbol=symbol)
    usr_position = None
    usr_position_counter = 0
    msg = None
    print(colored(f"[+] Received ticket ID: {id}, new TP: {new_tp}", "green"))

    if not new_tp:
        return jsonify({'msg': 'Error: Missing new_tp value'}), 400

    try:
        for position in positions:
            usr_position = position
            usr_position_counter += 1
    except Exception as e:
        print(colored(f"[-] An error occurred: {e}", "red"))

    if usr_position_counter > 1:
        msg = "You've had multiple positions and Protection Capital is not on; cannot perform this protocol."
        return jsonify({'msg':msg})
    else:
        if usr_position:
            print("Updating Take Profit")

            modify_request = {
                "action": mt5.TRADE_ACTION_SLTP,  # Modify Stop Loss / Take Profit
                "position": usr_position.ticket,
                "sl": usr_position.sl,  # Keep SL as is if you're only updating TP
                "tp": new_tp_float,      # Use the float value directly
                "volume": usr_position.volume  # Volume is required
            }

            print("Modify request:", modify_request)

            # Check the order
            # check_order = mt5.order_check(modify_request)
            # print("Check order result:", check_order)
            result = mt5.order_send(modify_request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print("Order send result:", result)
                if result.retcode == mt5.TRADE_RETCODE_NO_CHANGES:
                    msg = "Unable to change since previous TP is same with the current set TP"
                    return jsonify({'msg':msg})
                else:
                    msg = f"Take Profit modified for position {usr_position.ticket}."
                    return jsonify({'msg':msg})

            else:
                msg = f"Invalid order: Error code: ."
                return jsonify({'msg':msg})

        else:
                msg = "No positions found to modify."
                return jsonify({'msg':msg})

     # Print the message for debugging
    print(f"Response Message: {msg}")
    return redirect('/')

@app.route('/set_be_ajax')
def set_be_ajax():
    mt5_login()
    symbol = "XAUUSD"
    positions = mt5.positions_get(symbol=symbol)
    # print(positions)
    origin_entry = None
    usr_position = None
    usr_position_counter = 0

    try:
        for position in positions:
            # print(position.price_open)
            origin_entry = position.price_open
            usr_position = position
            usr_position_counter += 1
    except Exception as e:
        print(colored("[-] Error no available positions","red"))


    if usr_position_counter > 1:
        if _isProtectCap.lower() == "yes":
            msg = "You've enabled Safety Protocol. You cannot stack new positions."
        else:
            msg = "You've had multiple positions and Protection Capital is not on; cannot perform this protocol."
    else:

        if usr_position:

            msg = f"User position found: Ticket: {usr_position.ticket}, Current SL: {usr_position.sl}, Volume: {usr_position.volume}\n"

            # check if profit is positive before setting a breakeven
            if usr_position.profit > 0.00:

                # # Prepare the modify request
                modify_request = {
                    "action": mt5.TRADE_ACTION_SLTP,  # Modify Stop Loss / Take Profit
                    "position": usr_position.ticket,
                    "sl": origin_entry,
                    "tp": usr_position.tp,  # Keep the existing TP
                    "volume": usr_position.volume  # Volume is required
                }

                # Send the modify request
                result = mt5.order_send(modify_request)

                if result is not None and result.retcode == mt5.TRADE_RETCODE_DONE:
                    msg = f"Stop loss set to breakeven successfully for position {usr_position.ticket}.\n"
                else:
                    msg = f"Failed to modify stop loss for position {usr_position.ticket}. Error code: {result.retcode if result else 'Unknown'}.\n"
            else:
                msg = "Position is currently on drawdown cannot set to breakeven "

        else:
            msg = "No positions found to modify."

    return jsonify({'msg': msg})  # Return JSON with the message


#ajax shit
@app.route('/get_profit')
def get_profit():
    mt5_login()
    # Get current positions
    positions = mt5.positions_get(symbol=symbol)
    position_profit = 0


    if positions:
        for position in positions:
            # Access profit from the correct index
            position_profit += position.profit
    else:
        return jsonify({'profit': 'No active positions', 'is_negative': False})

    # Simulate profit changes
    # simulated_change = random.uniform(1, 100)  # Simulating profit changes
    # position_profit += simulated_change  # change sa actual profit


    is_negative = position_profit < 0

    if is_negative:
        formatted_profit = f"- ${abs(position_profit):.2f}"
    else:
        formatted_profit = f"+ ${position_profit:.2f}"

    return jsonify({'profit': formatted_profit, 'is_negative': is_negative})


def get_ipv4_address():
    hostname = socket.gethostname()
    ipv4_address = socket.gethostbyname(hostname)
    return ipv4_address

ipv4 = get_ipv4_address()

def open_browser(ipv4):
    print(ipv4_address)
    time.sleep(2)
    webbrowser.open(f"http://{ipv4_address}:5000")



if __name__ == "__main__":
    print(textwrap.dedent(banner))
    databse_connection()

    try:
        can_use_program()
        print(colored(f"[!] initializing MT5", "yellow"))
        init_mt()
        print(colored(f"[+] MT5 initialized", "green"))
        print(colored(f"[+] Open dashboard http://{ipv4}:5000", "black", "on_light_green"))
        app.run(debug=False, host=ipv4, port=5000)
    except Exception as e:
        print(colored(f"[-] An error occured: {e}", "black", "on_light_red"))
        mt5.shutdown()
        conn.close()
        print("Exited program.")
