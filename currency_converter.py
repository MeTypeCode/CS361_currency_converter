import zmq
import time
import re

conversions = {
    'CAD': 1.40898,
    'EUR': .944,
    'USD': 1
}
default_from_currency = 'USD' # Input type is assumed to be this currency when no currency is given 2

def convert(amount, from_currency, to_currency):
    conversion_rate = conversions[to_currency] if from_currency == 'USD' else 1.0 / conversions[from_currency]
    return round(amount * conversion_rate, 2)

'''
    Process the request message and return the parameters
    Message should have the variable name and value seperated by a colon
        amount:FLOAT
        amount_list:str(LIST) 
        from_currency:(EUR|CAD|USD)
        to_currency: (EUR|CAD|USD)

    Message should only have either amount or amount_list, but not both
    from_currency is optional and will default to USD

    EX: "amount:100.30 from_currency:CAD to_currency:USD"
        or "amount:[102.44, 200, 302.3, 10.99] to_currency:CAD"
'''
def process(message):
    # Get amount
    amount_match = re.search(r'amount:(\d+\.\d+|\d+)', message)
    amount = float(amount_match.group(1)) if amount_match else None

    # Get amount list
    amount_list_match = re.search(r"amount_list:\[([^\]]+)\]", message)
    if amount_list_match:
        amount_list_str = amount_list_match.group(1)
        amount_list = [float(x.strip()) for x in amount_list_str.split(',')]
    else: 
        amount_list = None

    # Get from_currency
    from_currency_match = re.findall(r"from_currency:(EUR|CAD|USD)", message)
    from_currency = from_currency_match[0] if from_currency_match else default_from_currency

    # Get to_currency
    to_currency_match = re.findall(r"to_currency:(EUR|CAD|USD)", message)
    to_currency = to_currency_match[0] if to_currency_match else None

    # value will return as None if it was not in message string
    return amount, amount_list, from_currency, to_currency



def main():
    context = zmq.Context()

    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        print("Listening for messages:")
        message = socket.recv()
        print(f"Received: {message.decode()}")

        if len(message) > 0:
            if message.decode() == "Q":     # Send Q to automatically close the microservice
                break

            amount, amount_list, from_currency, to_currency = process(message.decode())

            # if did not include a to_currency
            if to_currency is None:
                print("error: must include a to_currency")
                reply = "error: must include a to_currency"

            # if sent a single value to convert
            elif amount is not None:
                reply = str(convert(amount, from_currency, to_currency))

            # if sent list of value to convert
            elif amount_list is not None: 
                reply = str([convert(x, from_currency, to_currency) for x in amount_list])

            # if did not include amount or amount_list
            else: 
                print("error: must include an amount or amount_list")
                reply = "error: must include an amount or amount_list"

            # Wait to ensure client is listening
            time.sleep(.01)

            print(f"Replied: {reply}")
            socket.send_string(reply)

    # exit
    context.destroy()

if __name__ == "__main__":
    main()