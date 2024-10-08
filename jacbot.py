#!/usr/bin/env python3
"""
A Telegram bot that scrapes a channel for users and invites them to another channel.

The channels are specified by the username or URL.
The bot processes messages 10 at a time.
The bot will wait after multiple invite attempts to avoid being rate-limited.


Instructions:
Install Python 3.7 or higher.

Ensure you have installed the required dependencies:
$ pip install -r requirements.txt

Run the script with the following command:
$ python3 jacbot.py

or:
$ ./jacbot.py

Author: Jeklah
Date: 28/08/2024
"""
import asyncio
from collections.abc import AsyncGenerator
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import User, Channel, Chat

api_id: int = 24887943
api_hash: str = '40d419c51d961cbd3dc173990ef5b858'
phone: str = '+447816945464'
username: str = 'jacbotbot_bot'

channel_to_invite_url: str = 't.me/jacbot_c'
channel_to_scrape2: str = 't.me/+C9wUqflM_vg0NGVk'
channel_to_scrape: str = 't.me/clickhouse_en'

# Dictionary to keep track of invite attempts per user
invite_attempts: dict[int, int] = {}
MAX_INVITES: int = 5  # Maximum number of times to invite a user
MAX_CONCURRENT_INVITES: int = 10  # Maximum number of concurrent invites


async def invite_user(client: TelegramClient, user_id: int, channel_to_invite: Channel) -> None:
    """
    Function to invite a single user to the channel asynchronously.

    :param client: The TelegramClient instance.
    :param user_id: The ID of the user to invite.
    :param channel_to_invite: The Channel entity to invite the user to.
    """
    try:
        # Ensure we have the user entity (this helps with correct invite formatting)
        user_entity = await client.get_entity(user_id)

        if not isinstance(user_entity, User):
            print(f"User {user_id} is not a valid user entity. Skipping.")
            return

        # Check how many times the user has been invited
        invite_attempts[user_id] = invite_attempts.get(user_id, 0)

        if invite_attempts[user_id] >= MAX_INVITES:
            print(
                f"User {user_id} has already been invited {invite_attempts[user_id]} times. Skipping.")
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
                print(
                    f"Flood wait error for user {user_id}: Need to wait for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                # Handle any other errors
                print(f"Failed to invite user {user_id}: {e}")
                success = True  # Prevent infinite loop on unexpected errors

    except Exception as e:
        print(f"Error processing user {user_id}: {e}")


async def process_messages(client: TelegramClient) -> AsyncGenerator[int, None]:
    """
    Function to process messages and yield users to invite.

    :param client: The TelegramClient instance.

    :return: An asyncgenerator yielding user IDs to invite.
    """
    async for message in client.iter_messages(channel_to_scrape):
        # Check if the sender is a User and not a Channel/Chat
        if isinstance(message.sender, User):
            user_id = message.sender_id

            # Ensure user is not a bot
            if not message.sender.bot and user_id is not None:
                yield user_id

        # Check if the sender is a Channel or Chat
        elif isinstance(message.sender, (Channel, Chat)):
            try:
                # Join the channel or chat if necessary
                channel = await client.get_entity(message.sender_id)
                print(f'Joined channel: {channel.title}')

                # Iterate over the participants of the channel
                async for participant in client.iter_participants(channel):
                    if isinstance(participant, User) and not participant.bot:
                        yield participant.id
            except Exception as e:
                print(f"Error processing channel {message.sender_id}: {e}")
                return


async def invite_users_concurrently(client: TelegramClient, user_ids: list, channel_to_invite: Channel) -> None:
    """
    Invite users concurrently with a limit on max concurrency.

    :param client: The TelegramClient instance.
    :param user_ids: List of user IDs to invite.
    :param channel_to_invite: The Channel entity to invite the users to.
    """
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
            print('Starting JacBot...')
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
