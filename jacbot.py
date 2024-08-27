import time
import concurrent.futures
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
import pandas as pd


api_id = 24887943
api_hash = str('
phone= '+
username='jacbotbot_bot'

scrape_from_channel='https://t.me/clickhouse_en'
channel_to_invite='t.me/jacbot_c'

data=[]
invite_attempts={}  # Dictionary to keep track of invite attempts per user.
MAX_INVITES=5       # Maximum number of invite attempts per user.
MAX_WORKERS=5       # Maximum number of workers for concurrent invites.


def invite_user(client, user_id):
    """
    Invite a user to the channel, retrying if a FloodWaitError occurs.
    """
    invite_attempts[user_id]=invite_attempts.get(user_id, 0)

    if invite_attempts[user_id] >= MAX_INVITES:
        print(
            f'User {user_id} has reached the maximum number of invite attempts')
        return False

    success=False
    while not success:
        try:
            # Invite the user to the specified channel
            client(InviteToChannelRequest(
                channel=channel_to_invite, users=[user_id]))
            print(f'Invited user {user_id} to channel {channel_to_invite}')
            invite_attempts[user_id] += 1  # Increment the invite count
            success=True
        except FloodWaitError as e:
            # Handle the FloodWaitError, wait for the required time
            print(f'Waiting for {e.seconds} seconds due to flood wait error')
            time.sleep(e.seconds)  # Sleep and retry after wait time
        except Exception as e:
            # Handle other exceptions
            print(
                f'Failed to invite user {user_id} to channel {channel_to_invite} due to {e}')
            return False
    return True


def main():
    with TelegramClient(username, api_id, api_hash) as client:
        print('Starting JacBot...')
        # Scrape messages from the target channel
        for message in client.iter_messages(scrape_from_channel):
            # print(message.sender_id, ':', message.text, message.date)
            data.append([message.sender_id, message.text, message.date, message.id,
                         message.post_author, message.views, message.peer_id.channel_id])

            # Save data to CSV
            df=pd.DataFrame(data, columns=['sender_id', 'text', 'date', 'message.id',
                              'message.post_author', 'message.views', 'message.peer_id.channel_id'])
            df.to_csv('./scraped_data.csv', encoding='utf-8')

            # Get user details and invite them to the target channel in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures=[]

                # Schedule invites for each user
                for message in data:
                    user_id=message[0]  # sender_id

                    # Ensure the user is not a bot and is a valid user
                    if user_id and not message[0]:
                        futures.append(executor.submit(
                            invite_user, client, user_id))

                # Wait for all the invites to complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()  # Check if any exceptions occurred
                    except Exception as e:
                        print(f'An error occurred: {e}')


if __name__ == '__main__':
    main()
