import MetaTrader5 as mt5
from main import *


def mt5_login():
    login = ""
    password = ""
    server = ""
    mt5.login(login, password, server)

    return True

def is_protect_capital():
    # You can define the symbol here if you want, or pass it as a parameter
    mt5_login()
    symbol = "XAUUSD"  # Update this as needed
    positions = mt5.positions_get(symbol=symbol)
    flag = False

    # Loop to continuously check and close positions
    while True:

        # Retrieve current positions
        positions = mt5.positions_get(symbol=symbol)  # Refresh positions
        if not positions:
            print("No open positions found.")
            break  # Exit if no positions are found

        losing_position = []
        position_counter = len(positions)  # Count the current positions
        most_negative_pos_ticket = []
        most_negative_pos = None

        # Exit the outer loop if no positions remain
        if position_counter == 1:
            print("All positions closed except 1.")
            break
        else:

            # Determine the most negative position
            for position in positions:
                if most_negative_pos is None or position.profit < most_negative_pos.profit:
                    most_negative_pos = position
                    most_negative_pos_ticket = [position.ticket]  # Reset the ticket list
                elif position.profit == most_negative_pos.profit:
                    most_negative_pos_ticket.append(position.ticket)  # Append if equal profit

            # Loop through the most negative positions and attempt to close them
            for ticket in most_negative_pos_ticket:
                for position in positions:
                    if position.ticket == ticket:
                        # Create close request
                        close_request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": position.symbol,
                            "volume": position.volume,  # Volume must match the opened position
                            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                            "position": ticket,
                        }

                        print(f"Attempting to close position {ticket} with request: {close_request}")
                        result = mt5.order_send(close_request)

                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            print(f"Position {ticket} closed successfully.")
                            position_counter -= 1
                            flag = True  # Set flag to indicate a position was closed
                            break  # Exit the inner loop after closing a position
                        else:
                            print(f"Failed to close position {ticket}. Error code: {result.retcode}.")
                            print(f"Result: {result}")  # Print additional details



    return flag
