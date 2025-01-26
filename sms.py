from twilio.rest import Client
account_sid = 'ACb3dc08d81fb79500ac745b1f431dd02e'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)
message = client.messages.create(
    to='[HandsetNumber]'
)
print(message.sid)