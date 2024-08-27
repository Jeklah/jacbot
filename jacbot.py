import time
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from concurrent.futures import ThreadPoolExecutor, as_completed
from telethon.tl.types import User


api_id = 24887943
api_hash = '40d419c51d961cbd3dc173990ef5b858'
phone = '+447816945464'
username = 'jacbotbot_bot'

scrape_from_channel = 'https://t.me/moneymindedprofessional'
channel_to_invite_url = 't.me/jacbot_c'

# Dictionary to keep track of invite attempts per user.
invite_attempts: dict[int, int] = {}
# Maximum number of invite attempts per user.
MAX_INVITES = 5
# Maximum number of workers for concurrent invites.
MAX_WORKERS = 5


def invite_user(client, user_id, channel_to_invite):
    """
    Invite a user to the channel, retrying if a FloodWaitError occurs.
    """
    try:
        # Ensure we have the user entity (this helps with correct invite formatting)
        user_entity = client.get_entity(user_id)

        if not isinstance(user_entity, User):
            print(f'User {user_id} is not a valid user. Skipping invite.')
            return

        # Check how many times the user has been invited
        invite_attempts[user_id] = invite_attempts.get(user_id, 0)

        if invite_attempts[user_id] >= MAX_INVITES:
            print(
                f'User {user_id} has reached the maximum number of invite attempts')
            return

        success = False
        while not success:
            try:
                # Invite the user to the specified channel
                client(InviteToChannelRequest(
                    channel=channel_to_invite, users=[user_id]))
                print(f'Invited user {user_id} to channel {channel_to_invite}')
                invite_attempts[user_id] += 1  # Increment the invite count
                success = True
            except FloodWaitError as e:
                # Handle the FloodWaitError, wait for the required time
                print(
                    f'Waiting for {e.seconds} seconds due to flood wait error')
                time.sleep(e.seconds)  # Sleep and retry after wait time
            except Exception as e:
                # Handle other exceptions
                print(
                    f'Failed to invite user {user_id} to channel {channel_to_invite} due to {e}')
                success = True  # Mark as success to avoid infinite loop
    except Exception as e:
        print(f'Error during processing user {user_id}: {e}')


def process_messages(client):
    """
    Function to process messages and schedule invites in parallel.
    """
    for message in client.iter_messages(scrape_from_channel):
        user_id = message.sender_id

        # Ensure the user is not a bot and is a valid user
        if not message.sender.bot and user_id is not None:
            yield user_id


def main():
    with TelegramClient(username, api_id, api_hash) as client:
        print('Starting JacBot...')
        # Scrape messages from the target channel
        try:
            channel_to_invite = client.get_entity(channel_to_invite_url)
            print(f'Found channel to invite users to: {channel_to_invite_url}')
        except Exception as e:
            print(f'Error while fetching channel to invite: {e}')
            # return

        # Use a ThreadPoolExecutor to invite users in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit tasks for inviting users
            futures = [executor.submit(invite_user, client, user_id, channel_to_invite)
                       for user_id in process_messages(client)]

            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()  # This will re-raise any exception that occurred during the task
                except Exception as e:
                    print(f'Error during invite: {e}')


if __name__ == '__main__':
    main()
