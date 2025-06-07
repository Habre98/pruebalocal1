from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
from telegram.ext import ContextTypes  # type: ignore


# from types import SimpleNamespace
import re
import aiohttp  # type: ignore
import tweepy  # type: ignore
import os
import asyncio
from dotenv import load_dotenv  # type: ignore

load_dotenv()
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAADA%2F2QEAAAAAK6ET5SPdyvYphvuiDpBxhHs%2Fctk%3D5PskJkXhMLfxH7xScbF5kayEVjPAn0SBRiQ2l8KQx87ZEUTG02"
if BEARER_TOKEN is None:
    print("Please set the BEARER_TOKEN environment variable.")
    exit(1)

client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)


SOL_ADDRESS_REGEX = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")


async def add_target_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usa /addtarget <username>")
        return

    username = context.args[0].lstrip("@").lower()
    chat_id = update.effective_chat.id

    targets = context.chat_data.setdefault("targets", [])

    if any(t["username"] == username for t in targets):
        await update.message.reply_text(f"⚠️ Ya estás siguiendo a @{username}")
        return

    targets.append({"username": username, "chat_id": chat_id})
    await update.message.reply_text(f"✅ Ahora estás siguiendo a @{username}")
    print("DEBUG - Nuevos targets guardados:", context.chat_data["targets"])


async def list_targets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    targets = context.chat_data.get("targets", [])

    if not targets:
        await update.message.reply_text(
            "📭 You haven't added any X (Twitter) accounts to monitor.\n"
            "Use /addtarget <username> to start tracking tweets from someone."
        )
        return

    formatted_targets = "\n".join([f"• @{t['username']}" for t in targets])
    await update.message.reply_text(
        f"📡 You're currently monitoring the following accounts:\n\n{formatted_targets}"
    )


async def removetarget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    targets = context.chat_data.get("targets", [])

    if not targets:
        await update.message.reply_text("You have no targets to remove.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                f"🗑️ @{t['username']}", callback_data=f"remove_target:{t['username']}"
            )
        ]
        for t in targets
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select a target to remove:", reply_markup=reply_markup
    )


async def handle_remove_target_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    username = query.data.split(":")[1]
    targets = context.chat_data.get("targets", [])

    new_targets = [t for t in targets if t["username"] != username]
    context.chat_data["targets"] = new_targets

    await query.edit_message_text(f"🗑️ Unfollowed @{username}")


last_seen_tweet = {}


async def check_new_tweets(context, username, chat_id, application, chat_data):
    try:
        # Obtener usuario (sin await porque es síncrono)
        user = client.get_user(username=username)

        if not user.data:
            print(f"⚠️ User {username} not found or error fetching user data.")
            return
        user_id = user.data.id

        print(f"👀 Buscando tweets recientes para @{username} (user_id: {user_id})...")

        # Obtener tweets (síncrono)
        tweets = client.get_users_tweets(
            id=user_id, max_results=5, tweet_fields=["created_at"]
        )

        if tweets.data:
            print(f"📄 Últimos tweets de @{username}: {[t.text for t in tweets.data]}")
            latest_tweet = tweets.data[0]

            last_seen_id = chat_data.get(f"last_seen_{username}")
            if last_seen_id != latest_tweet.id:
                chat_data[f"last_seen_{username}"] = latest_tweet.id

                found_addresses = SOL_ADDRESS_REGEX.findall(latest_tweet.text)

                for address in found_addresses:
                    from sniping import load_user_wallets, perform_sniping

                    if await is_valid_pumpfun_contract(address):
                        tweet_url = f"https://x.com/{username}/status/{latest_tweet.id}"
                        pump_url = f"https://pump.fun/{address}"

                        text = (
                            f"🧵 New Pump.fun token from @{username}:\n\n"
                            f"{latest_tweet.text}\n\n"
                            f"🔗 {tweet_url}\n"
                            f"🚀 Pump.fun: {pump_url}"
                        )

                        print(f"🔔 {text}")
                        await application.bot.send_message(chat_id=chat_id, text=text)
                        selected_keypairs = load_user_wallets(chat_id)

                        if not selected_keypairs:
                            print(
                                f"⚠️ There are no wallets selected for the user {chat_id}, incompleted sniping."
                            )
                        else:
                            print(
                                f"🎯 Running sniping for {len(selected_keypairs)} wallet(s) from {username} in {address}"
                            )
                            contract_address = address
                            keypairs = selected_keypairs
                            print("👁‍🗨Context data:", context.chat_data)
                            amount_sol = context.chat_data.get("amount", 0.0001)
                            sniping_result = await perform_sniping(
                                user_id, contract_address, keypairs, amount_sol
                            )

                            await application.bot.send_message(
                                chat_id=chat_id, text=sniping_result
                            )
                        return

    except tweepy.TooManyRequests as e_rate_limit:
        print(
            f"❌ Rate limit error in check_new_tweets for @{username}: {e_rate_limit}"
        )
    except Exception as e:
        print(f"❌ Query error @{username}: {e}")


async def is_valid_pumpfun_contract(address: str) -> bool:
    url = f"https://pump.fun/{address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                return response.status == 200
    except Exception as e:
        print(f"⚠️ Error verifying Pump.fun for {address}: {e}")
        return False


async def monitor_users(context, get_all_targets, application):
    for target in get_all_targets():
        username = target["username"]
        chat_id = target["chat_id"]
        chat_data = application.chat_data.get(chat_id, {})
        await check_new_tweets(context, username, chat_id, application, chat_data)
