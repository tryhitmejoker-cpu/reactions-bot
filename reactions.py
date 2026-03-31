#!/usr/bin/env python3
import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

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

    # Handle forwarded post
    if event.forward and user_id not in pending:
        fwd = event.forward
        chat_id = fwd.chat_id or fwd.saved_from_peer
        msg_id = fwd.channel_post or fwd.saved_from_msg_id

        if not msg_id:
            await event.reply(
                "❌ Could not get message ID automatically.\n\n"
                "Please copy the post link from your channel and send it here.\n"
                "Example: https://t.me/c/1234567890/123"
            )
            pending[user_id] = {"waiting_for_link": True, "chat_id": chat_id}
            return

        pending[user_id] = {
            "chat_id": chat_id,
            "msg_id": int(msg_id)
        }
        await event.reply("✅ Post received!\n\nNow send me the emoji you want to react with (e.g. 🔥)")
        return

    # Handle post link
    if user_id in pending and pending[user_id].get("waiting_for_link"):
        text = event.text.strip()
        if "t.me/c/" in text:
            parts = text.split("/")
            msg_id = int(parts[-1])
            pending[user_id]["msg_id"] = msg_id
            pending[user_id].pop("waiting_for_link")
            await event.reply("✅ Got it!\n\nNow send me the emoji you want to react with (e.g. 🔥)")
        else:
            await event.reply("Please send a valid post link (t.me/c/...)")
        return

    # Handle emoji
    if user_id in pending and "emoji" not in pending[user_id] and not pending[user_id].get("waiting_for_link"):
        emoji = event.text.strip()
        if not emoji:
            await event.reply("Please send a valid emoji.")
            return
        pending[user_id]["emoji"] = emoji
        await event.reply(f"Got it! {emoji}\n\nNow how many reactions do you want to add?")
        return

    # Handle amount
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
        "Forward me a post from your channel or group to get started.\n"
        "Or send a post link directly (https://t.me/c/...)"
    )

async def main():
    await client.start()
    print("Reactions bot running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
