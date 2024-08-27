import time
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
import pandas as pd


api_id = 24887943
api_hash = str('
phone= '+
username='jacbotbot_bot'

channel_to_invite='t.me/jacbot_c'

data=[]
invite_attempts={}  # Dictionary to keep track of invite attempts per user.
MAX_INVITES=5       # Maximum number of invite attempts per user.
with TelegramClient(username, api_id, api_hash) as client:
    print('Starting JacBot...')
    for message in client.iter_messages("https://t.me/clickhouse_en"):
        # print(message.sender_id, ':', message.text, message.date)
        data.append([message.sender_id, message.text, message.date, message.id,
                    message.post_author, message.views, message.peer_id.channel_id])

        df=pd.DataFrame(data, columns=["sender_id", "text", "date",
                                         "message.id", "message.post_author",
                                         "message.views", "message.peer_id.channel_id"])
        df.to_csv("./filename.csv", encoding='utf-8')

        # Get user details and invite them to the target channel
        user_id=message.sender_id

        # Ensure the user is not a bot and is a valid user
        if not message.sender.bot and user_id is not None:
            # Check how many times the user has been invited
            invite_attempts[user_id]=invite_attempts.get(user_id, 0)

            if invite_attempts[user_id] >= MAX_INVITES:
                print(
                    f'User {user_id} has reached the maximum number of invite attempts')
                continue

            # Success loop to handle flood wait errors
            success=False
            while not success:
                try:
                    # Invite the user to the specified channel
                    client(InviteToChannelRequest(
                        channel=channel_to_invite, users=[user_id]))
                    print(
                        f'Invited user {user_id} to channel {channel_to_invite}')
                    invite_attempts[user_id] += 1  # Increment the invite count
                    success=True
                except FloodWaitError as e:
                    # Handle flood wait errors by waiting for the specified time
                    print(
                        f'Waiting for {e.seconds} seconds due to flood wait error')
                    time.sleep(e.seconds)
                except Exception as e:
                    print(
                        f'Failed to invite user {user_id} to channel {channel_to_invite} due to {e}')
                    success=True  # Prevents infinite loop in case of other errors
