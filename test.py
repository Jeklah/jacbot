import asyncio
import time
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import User


api_id = ''
api_hash = ''
phone = ''
username = 'jacbotbot_bot'

channel_to_invite_url = 't.me/jacbot_c'

invite_attempts = {}
MAX_INVITES = 5
MAX_CONCURRENT_INVITES = 5


async def invite_user(client, user_id, channel_to_invite):
    try:
        user_entity = await client.get_entity(user_id)

        if not isinstance(user_entity, User):
            print(f'user {user_id} is not a valid user. Skipping invite.')
            return

        invite_attempts[user_id] = invite_attempts.get(user_id, 0)

        if invite_attempts[user_id] >= MAX_INVITES:
            print(
                f'user {user_id} has reached the maximum number of invite attempts')
            return

        success = False
        while not success:
            try:
                await client(InviteToChannelRequest(channel=channel_to_invite, users=[user_entity]))
                print(
                    f'invited user {user_id} to channel {channel_to_invite.title}')
                invite_attempts[user_id] += 1
                success = True
            except FloodWaitError as e:
                print(
                    f'waiting for {e.seconds} seconds due to flood wait error')
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f'error inviting user {user_id}: {e}')
                success = True
