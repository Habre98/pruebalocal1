# import asyncio

# from telegram.ext import (  # type: ignore
#     CommandHandler,
#     CallbackQueryHandler,
#     PicklePersistence,
#     ApplicationBuilder,
#     ContextTypes,
#     JobQueue,
# )
# from wallets import (
#     start,
#     add_wallet_command,
#     my_wallets_command,
#     select_wallets_command,
#     button_callback,
# )
# from x_monitor import (
#     add_target_command,
#     list_targets_command,
#     removetarget_command,
#     handle_remove_target_callback,
#     monitor_users,
# )
# from mention_linker import (
#     mention_polling_loop,
# )
# from linkx import (
#     linkx_command,
#     linked_command,
#     unlinkx_command,
# )
# from x_utils import (
#     fetch_bot_x_id,
#     start_mention_watcher,
# )
# from mention_sniper import (
#     mention_sniping_loop,
# )
# import logging
# import os
# import tweepy  # type: ignore
# import requests
# from dotenv import load_dotenv  # type: ignore

# # Logging config
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# load_dotenv()
# BOT_TOKEN = os.getenv("BOT_TOKEN")
# TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAP%2Fp2AEAAAAAVCOvKnfqBTAs4gm5BRNkOc2vAAE%3DDOXuPDaIj2E3dt78ke9UkVeUlGz4nIOXMc5aN09k9V7rQjSPMV"


# if BOT_TOKEN is None:
#     print("Please set the BOT_TOKEN environment variable.")
#     exit(1)


# twitter_client = tweepy.Client(
#     bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True
# )


# async def start_monitoring(context: ContextTypes.DEFAULT_TYPE):
#     application = context.application

#     def get_all_targets():
#         all_targets = []
#         for chat_id, chat_data in application.chat_data.items():
#             for target in chat_data.get("targets", []):
#                 all_targets.append(
#                     {
#                         "username": target["username"],
#                         "chat_id": chat_id,
#                     }
#                 )
#         print("DEBUG - get_all_targets() →", all_targets)
#         return all_targets

#     await monitor_users(get_all_targets, application)


# def main():
#     print(">>> Iniciando bot...")
#     persistence = PicklePersistence(filepath="bot_data.pickle")
#     application = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

#     # Obtener el Bot de Telegram para pasarlo al mention_polling_loop
#     telegram_bot = application.bot

#     # Handlers
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("addwallet", add_wallet_command))
#     application.add_handler(CommandHandler("mywallets", my_wallets_command))
#     application.add_handler(CommandHandler("selectwallets", select_wallets_command))
#     application.add_handler(CommandHandler("addtarget", add_target_command))
#     application.add_handler(CommandHandler("listtargets", list_targets_command))
#     application.add_handler(CommandHandler("removetarget", removetarget_command))
#     application.add_handler(
#         CallbackQueryHandler(handle_remove_target_callback, pattern=r"^remove_target:")
#     )
#     application.add_handler(CallbackQueryHandler(button_callback))
#     application.add_handler(CommandHandler("linkx", linkx_command))
#     application.add_handler(CommandHandler("linked", linked_command))
#     application.add_handler(CommandHandler("unlinkx", unlinkx_command))

#     application.job_queue.run_repeating(start_monitoring, interval=60, first=0)

#     async def init_bot_data(context):
#         context.bot_data["twitter_client"] = twitter_client
#         await fetch_bot_x_id(context)

#     application.job_queue.run_once(
#         lambda context: asyncio.create_task(init_bot_data(context)), when=5
#     )

#     application.job_queue.run_once(
#         lambda context: asyncio.create_task(start_mention_watcher(context)), when=10
#     )

#     application.job_queue.run_once(
#         lambda context: asyncio.create_task(mention_sniping_loop(context)), when=15
#     )

#     print(">>> Bot en ejecución...")
#     application.run_polling()


# if __name__ == "__main__":
#     main()

# //////////////////////////////////////////////////////////////////////////////


# //////////////////////////////////////////////////////////////////////////
import asyncio
import telegram

print("TELEGRAM: ", dir(telegram))

from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    PicklePersistence,
    ApplicationBuilder,
    ContextTypes,
)
from wallets import (
    start,
    add_wallet_command,
    my_wallets_command,
    select_wallets_command,
    button_callback,
)
from x_monitor import (
    add_target_command,
    list_targets_command,
    removetarget_command,
    handle_remove_target_callback,
    monitor_users,
)
from mention_linker import (
    mention_polling_loop,
)
from linkx import (
    linkx_command,
    linked_command,
    unlinkx_command,
)
from x_utils import (
    fetch_bot_x_id,
    # start_mention_watcher,
)
from mention_sniper import (
    mention_sniping_loop,
)
import logging
import os
import tweepy  # type: ignore

# import requests
from dotenv import load_dotenv  # type: ignore

# Logging config
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAADA%2F2QEAAAAAbdPtND6eKQ%2Fg%2F%2FwMkg1LgiSH1%2Bs%3DYO3SNao3wKaGFL5sCmtqn4d8c13K8DwHRvadTKD42AkR0ajw4D"

if BOT_TOKEN is None:
    print("Please set the BOT_TOKEN environment variable.")
    exit(1)

twitter_client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=False
)

# Global variable to store background tasks
background_tasks = set()


async def start_monitoring(context: ContextTypes.DEFAULT_TYPE):
    application = context.application

    def get_all_targets():
        all_targets = []
        for chat_id, chat_data in application.chat_data.items():
            for target in chat_data.get("targets", []):
                all_targets.append(
                    {
                        "username": target["username"],
                        "chat_id": chat_id,
                    }
                )
        print("DEBUG - get_all_targets() →", all_targets)
        return all_targets

    await monitor_users(context, get_all_targets, application)


async def start_unified_mention_system(context: ContextTypes.DEFAULT_TYPE):
    """Start the unified mention system as a single background task"""
    print("🚀 Starting unified mention system...")

    # Initialize bot data first
    context.bot_data["twitter_client"] = twitter_client
    await fetch_bot_x_id(context)

    # Import here to avoid circular imports
    from mention_linker import unified_mention_loop

    # Create single background task for all mention processing
    task = asyncio.create_task(
        unified_mention_loop(twitter_client, context.application.bot, context)
    )

    # Keep reference to prevent garbage collection
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    print("✅ Unified mention system started - handles linking AND sniping!")


async def start_background_mention_watcher(context: ContextTypes.DEFAULT_TYPE):
    """Start the mention watcher as a background task"""
    print("🚀 Starting mention watcher as background task...")

    # Initialize bot data first
    context.bot_data["twitter_client"] = twitter_client
    await fetch_bot_x_id(context)

    # Create background task for mention polling
    task = asyncio.create_task(
        mention_polling_loop(
            twitter_client, context.application.bot, context, interval=30
        )
    )

    # Keep reference to prevent garbage collection
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    print("✅ Mention watcher background task started")


async def start_background_mention_sniper(context: ContextTypes.DEFAULT_TYPE):
    """Start the mention sniper as a background task"""
    print("🚀 Starting mention sniper as background task...")

    # Create background task for mention sniping
    task = asyncio.create_task(mention_sniping_loop(context))

    # Keep reference to prevent garbage collection
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    print("✅ Mention sniper background task started")


async def initialize_bot_systems(context: ContextTypes.DEFAULT_TYPE):
    """Initialize all bot systems in sequence"""
    try:
        print("🔧 Initializing bot systems...")

        # Step 1: Initialize Twitter client and fetch bot ID
        context.bot_data["twitter_client"] = twitter_client
        await fetch_bot_x_id(context)
        print("✅ Twitter client initialized")

        # Step 2: Start mention watcher (non-blocking)
        await start_background_mention_watcher(context)

        # Step 3: Start mention sniper (non-blocking)
        await start_background_mention_sniper(context)

        print("🎉 All bot systems initialized successfully!")

    except Exception as e:
        print(f"❌ Error initializing bot systems: {e}")
        import traceback

        traceback.print_exc()


def main():
    print(">>> Iniciando bot...")
    persistence = PicklePersistence(filepath="bot_data.pickle")
    application = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addwallet", add_wallet_command))
    application.add_handler(CommandHandler("mywallets", my_wallets_command))
    application.add_handler(CommandHandler("selectwallets", select_wallets_command))
    application.add_handler(CommandHandler("addtarget", add_target_command))
    application.add_handler(CommandHandler("listtargets", list_targets_command))
    application.add_handler(CommandHandler("removetarget", removetarget_command))
    application.add_handler(
        CallbackQueryHandler(handle_remove_target_callback, pattern=r"^remove_target:")
    )
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("linkx", linkx_command))
    application.add_handler(CommandHandler("linked", linked_command))
    application.add_handler(CommandHandler("unlinkx", unlinkx_command))

    # Schedule the monitoring job (this one can stay as is)
    application.job_queue.run_repeating(start_monitoring, interval=60, first=0)

    # Initialize all bot systems as a single background task
    application.job_queue.run_once(initialize_bot_systems, when=5)

    print(">>> Bot en ejecución...")
    application.run_polling()


if __name__ == "__main__":
    main()
