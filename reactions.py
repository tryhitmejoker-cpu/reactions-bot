#!/usr/bin/env python3
import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji, PeerChannel

API_ID       = int(os.environ["API_ID"])
API_HASH     = os.environ["API_HASH"]
SESSION      = os.environ["SESSION_STRING"]
ADMIN_ID     = int(os.environ["ADMIN_ID"])

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

pending = {}

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handler(event):
    user_id = event.sender_id

    if user_id != ADMIN_ID:
        return

    if event.forward and user_id not in pending:
        fwd = event.forward
        msg_id = fwd.channel_post or fwd.saved_from_msg_id or event.id
        chat_id = fwd.saved_from_peer or fwd.chat_id

        # Debug info
        await event.reply(
            f"🔍 Debug info:\n"
            f"chat_id: {chat_id}\n"
            f"msg_id: {msg_id}\n"
            f"channel_post: {fwd.channel_post}\n"
            f"saved_from_msg_id: {fwd.saved_from_msg_id}\n"
            f"saved_from_peer: {fwd.saved_from_peer}"
        )

        pending[user_id] = {
            "chat_id": chat_id,
            "msg_id": int(msg_id)
        }
        await event.reply("Now send emoji:")
        return

    if user_id in pending and "emoji" not in pending[user_id]:
        emoji = event.text.strip()
        pending[user_id]["emoji"] = emoji
        await event.reply(f"Got it! {emoji}\n\nHow many?")
        return

    if user_id in pending and "emoji" in pending[user_id] and "amount" not in pending[user_id]:
        try:
            amount = int(event.text.strip())
        except ValueError:
            await event.reply("Please send a valid number.")
            return

        pending[user_id]["amount"] = amount
        data = pending[user_id]

        await event.reply(f"⏳ Adding {data['amount']} x {data['emoji']} reactions...")

        try:
            for i in range(data["amount"]):
                await client(SendReactionRequest(
                    peer=data["chat_id"],
                    msg_id=data["msg_id"],
                    reaction=[ReactionEmoji(emoticon=data["emoji"])]
                ))
                await asyncio.sleep(0.5)

            await event.reply(f"✅ Done!")
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")

        del pending[user_id]
        return

async def main():
    await client.start()
    print("Reactions bot running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
