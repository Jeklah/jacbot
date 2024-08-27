import asyncio
import time
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import User


api_id = 24887943
api_hash = '40d419c51d961cbd3dc173990ef5b858'
phone = '+447816945464'
username = 'jacbotbot_bot'

channel_to_invite_url = 't.me/jacbot_c'

invite_attempts = {}  # Dictionary to keep track of invite attempts per user
MAX_INVITES = 5  # Maximum number of times to invite a user
MAX_CONCURRENT_INVITES = 5  # Maximum number of concurrent invites


async def invite_user(client, user_id, channel_to_invite):
    """Function to invite a single user to the channel asynchronously."""
    try:
        # Ensure we have the user entity (this helps with correct invite formatting)
        user_entity = await client.get_entity(user_id)

        if not isinstance(user_entity, User):
            print(f"User {user_id} is not a valid user entity. Skipping.")
            return

        # Check how many times the user has been invited
        invite_attempts[user_id] = invite_attempts.get(user_id, 0)

        if invite_attempts[user_id] >= MAX_INVITES:
            print(f"User {user_id} has already been invited {invite_attempts[user_id]} times. Skipping.")
            return

        success = False
        while not success:
            try:
                # Invite the user to the specified channel
                await client(InviteToChannelRequest(channel=channel_to_invite, users=[user_entity]))
                print(f"Invited user {user_id} to {channel_to_invite.title}")
                invite_attempts[user_id] += 1  # Increment invite count
                success = True
            except FloodWaitError as e:
                # Handle the FloodWait error
                print(f"Flood wait error for user {user_id}: Need to wait for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                # Handle any other errors
                print(f"Failed to invite user {user_id}: {e}")
                success = True  # Prevent infinite loop on unexpected errors

    except Exception as e:
        print(f"Error processing user {user_id}: {e}")


async def process_messages(client):
    """Function to process messages and yield users to invite."""
    async for message in client.iter_messages("https://t.me/clickhouse_en"):
        user_id = message.sender_id

        # Ensure the user is not a bot and is a valid user
        if not message.sender.bot and user_id is not None:
            yield user_id


async def invite_users_concurrently(client, user_ids, channel_to_invite):
    """Invite users concurrently with a limit on max concurrency."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_INVITES)

    async def sem_invite_user(user_id):
        async with semaphore:
            await invite_user(client, user_id, channel_to_invite)

    # Schedule and run all invitations concurrently
    await asyncio.gather(*[sem_invite_user(user_id) for user_id in user_ids])


async def main():
    async with TelegramClient(username, api_id, api_hash) as client:
        # Get the entity of the channel where you want to send invites
        try:
            channel_to_invite = await client.get_entity(channel_to_invite_url)
            print(f"Channel to invite users to: {channel_to_invite.title}")
        except Exception as e:
            print(f"Error fetching target channel entity: {e}")
            return

        # Gather user IDs from messages
        user_ids = [user_id async for user_id in process_messages(client)]

        # Invite users concurrently
        await invite_users_concurrently(client, user_ids, channel_to_invite)


if __name__ == "__main__":
    asyncio.run(main())
