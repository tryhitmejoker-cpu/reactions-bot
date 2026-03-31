#!/usr/bin/env python3
import asyncio
import os
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

API_ID       = int(os.environ["API_ID"])
API_HASH     = os.environ["API_HASH"]
PHONE        = os.environ["PHONE"]
ADMIN_ID     = int(os.environ["ADMIN_ID"])

client = TelegramClient("session", API_ID, API_HASH)

pending = {}  # store forwarded message info per user

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handler(event):
    user_id = event.sender_id

    if user_id != ADMIN_ID:
        return

    # Step 1 — forwarded message received
    if event.forward and user_id not in pending:
        pending[user_id] = {
            "chat_id": event.forward.chat_id,
            "msg_id": event.forward.channel_post or event.forward.saved_from_msg_id
        }
        await event.reply(
            "✅ Post received!\n\n"
            "Now send me the emoji you want to react with (e.g. 🔥)"
        )
        return

    # Step 2 — emoji received
    if user_id in pending and "emoji" not in pending[user_id]:
        emoji = event.text.strip()
        if not emoji:
            await event.reply("Please send a valid emoji.")
            return
        pending[user_id]["emoji"] = emoji
        await event.reply(f"Got it! {emoji}\n\nNow how many reactions do you want to add?")
        return

    # Step 3 — amount received
    if user_id in pending and "emoji" in pending[user_id] and "amount" not in pending[user_id]:
        try:
            amount = int(event.text.strip())
            if amount < 1 or amount > 100:
                await event.reply("Please send a number between 1 and 100.")
                return
        except ValueError:
            await event.reply("Please send a valid number.")
            return

        pending[user_id]["amount"] = amount
        data = pending[user_id]

        await event.reply(
            f"⏳ Adding {data['amount']} x {data['emoji']} reactions...\n"
            f"This may take a moment!"
        )

        try:
            for i in range(data["amount"]):
                await client(SendReactionRequest(
                    peer=data["chat_id"],
                    msg_id=data["msg_id"],
                    reaction=[ReactionEmoji(emoticon=data["emoji"])]
                ))
                await asyncio.sleep(0.5)

            await event.reply(
                f"✅ Done! Added {data['amount']} x {data['emoji']} reactions!"
            )
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")

        del pending[user_id]
        return

    await event.reply(
        "👋 Welcome to the Reactions Bot!\n\n"
        "Forward me a post from your channel or group to get started."
    )

async def main():
    await client.start(phone=PHONE)
    print("Reactions bot running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
