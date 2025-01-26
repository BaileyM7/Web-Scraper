from twilio.rest import Client

def getKey():

    #trying to grab the key
    try:
        file = open("smsInfo.txt", "r")
        key = file.readline()
        sid = file.readline()
        number = file.readline()
        file.close()
        return key, sid, number
    
    # handling errors
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")

key, sid, number = getKey

account_sid = sid
auth_token = f'[{key}]'
client = Client(account_sid, auth_token)
message = client.messages.create(
    to= f'[{number}]'
)

print(message.sid)