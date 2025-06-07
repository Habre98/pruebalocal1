from telegram import InlineKeyboardMarkup, InlineKeyboardButton  # type: ignore

from telegram.ext import (  # type: ignore
    CallbackContext,
)  # type: ignore
from helper_func import (
    load_wallets,
    create_solana_wallet,
    save_wallet,
    get_next_wallet_index,
)


from solders.pubkey import Pubkey  # type: ignore
from solana.rpc.async_api import AsyncClient  # type: ignore

from linkx import linkx_command

import logging

logger = logging.getLogger(__name__)


async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Manage Wallets", callback_data="manage_wallets")],
        # [InlineKeyboardButton("Add target", callback_data="add_target_command")],
        [InlineKeyboardButton("Link your X account", callback_data="linkx_command")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to the Xero X Sniper Bot! Please choose an option:",
        reply_markup=reply_markup,
    )


async def manage_wallets_command(update, context):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Add New Wallet", callback_data="request_add_wallet")],
        [InlineKeyboardButton("View My Wallets", callback_data="request_my_wallets")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_to_main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(
            text="Manage your wallets:", reply_markup=reply_markup
        )
    else:
        # This case should ideally not be reached if triggered by a button from /start
        await update.message.reply_text(
            text="Manage your wallets:", reply_markup=reply_markup
        )


async def add_wallet_command(update, context):
    keyboard = [
        [
            InlineKeyboardButton(
                "Generate New Wallet", callback_data="generate_new_wallet"
            )
        ],
        # [InlineKeyboardButton("Import Existing Wallet", callback_data="import_existing_wallet")], # Optional for now
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = "To add a new Solana wallet, you can either generate a new one or import an existing one (not yet supported). Would you like to generate a new wallet?"

    query = update.callback_query
    if query:
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)


async def my_wallets_command(update, context):
    user_id = (
        update.callback_query.from_user.id
        if update.callback_query
        else update.message.from_user.id
    )

    loaded_wallets = load_wallets(user_id)

    if not loaded_wallets:
        message_text = (
            "You have no wallets. Use /addwallet or 'Add New Wallet' to create one."
        )
    else:
        wallet_list_str = "Your Wallets:\n"
        for i, wallet_kp in enumerate(loaded_wallets):
            pubkey = wallet_kp.pubkey()
            balance = await get_wallet_balance(str(pubkey))
            wallet_list_str += f"\n🏦 Wallet {i}.\n  PubKey:\n`{str(pubkey)}`\nbalance: `{balance}`\n"  # Using backticks for mono-spaced font
        wallet_list_str += "\nTo select wallets for scanning, use the /selectwallets command (e.g., /selectwallets 0 1 2). You can select up to 5 wallets. (Full selection UI to be implemented later)."
        message_text = wallet_list_str

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message_text, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(text=message_text, parse_mode="Markdown")


async def select_wallets_command(update, context: CallbackContext):
    if context.user_data is None:
        context.user_data = {}
    user_id = update.message.from_user.id
    args = context.args

    if not args:
        await context.bot.send_message(
            chat_id=user_id,
            text="Usage: /selectwallets <index1> <index2> ... (e.g., /selectwallets 0 1). You can select up to 5 wallets.",
        )
        return

    if len(args) > 5:
        await context.bot.send_message(
            chat_id=user_id,
            text="You can select up to 5 wallets. Please provide a list of up to 5 indices.",
        )
        return

    user_wallets = load_wallets(user_id)
    if not user_wallets:
        await update.message.reply_text(
            "You have no wallets to select. Use /addwallet first."
        )
        return

    selected_indices = []
    selected_pubkeys_for_message = []

    try:
        for arg in args:
            idx = int(arg)
            if 0 <= idx < len(user_wallets):
                if idx not in selected_indices:
                    selected_indices.append(idx)
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Wallet index {idx} was already included. Ignoring duplicate.",
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"Invalid wallet index: {idx}. Please use indices from your /mywallets list.",
                )
                return
    except ValueError:
        await context.bot.send_message(
            chat_id=user_id,
            text="Invalid input. Please provide wallet indices as numbers (e.g., /selectwallets 0 1).",
        )
        return

    if not selected_indices:
        await context.bot.send_message(
            chat_id=user_id,
            text="No valid wallets selected. Please check indices from /mywallets.",
        )
        return

    # Store the Keypair objects or just their pubkeys. Storing pubkeys is simpler for now.
    context.user_data["selected_wallets"] = [
        str(user_wallets[i].pubkey()) for i in selected_indices
    ]

    for i in selected_indices:
        pubkey = user_wallets[i].pubkey()
        # balance = await get_wallet_balance(str(pubkey))
        selected_pubkeys_for_message.append(f"🏦 Wallet #{i})\n`{str(pubkey)}`\n")

    await context.bot.send_message(
        chat_id=user_id,
        text="✅  Selected wallets for scanning:\n"
        + "\n".join(selected_pubkeys_for_message)
        + "\nUse /startscanner to begin.",
        parse_mode="Markdown",
    )


async def prompt_generate_new_wallet(update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        wallet_index = get_next_wallet_index(user_id)
        wallet_data = await create_solana_wallet()
        if wallet_data is None:
            raise Exception("Failed to generate wallet data.")
        private_key = wallet_data["private_key"]
        public_key = wallet_data["address"]
        logger.info(
            f"Secret Key: `{private_key}`\nPublic Key: `{public_key}`\nWallet Index: `{wallet_index}`"
        )

        if save_wallet(user_id, private_key, wallet_index):
            message_text = f"✅ Successfully generated new wallet #{wallet_index} \nPublic Key: `{public_key}`.\nPrivate Key: `{private_key}`.\n⚠️Store your keys safely and do not share with anyone"
        else:
            message_text = "Failed to save the new wallet. Please try again."

    except Exception as e:
        print(f"Error in prompt_generate_new_wallet: {e}")
        message_text = (
            "An error occurred while generating the wallet. Please try again."
        )

    await query.edit_message_text(text=message_text, parse_mode="Markdown")


async def get_wallet_balance(wallet_address):
    try:
        # Validate wallet_address
        if (
            wallet_address is None
            or not isinstance(wallet_address, str)
            or wallet_address.strip() == ""
        ):
            logger.error("Invalid or None wallet address provided.")
            return 0

        # Log wallet address for debugging
        logger.debug(f"Received wallet address: {wallet_address}")

        # Convert Base58 wallet address to Pubkey object
        pubkey = Pubkey.from_string(wallet_address)

        # TODO: TOGGLE DEV/MAINNET
        # Initialize Solana Async Client
        async_client = AsyncClient("https://api.mainnet-beta.solana.com")
        # async_client = AsyncClient("https://api.devnet.solana.com")

        # Fetch balance
        response = await async_client.get_balance(pubkey)
        await async_client.close()  # Close connection to avoid resource leaks

        # Extract balance value
        if response.value is not None:
            print(f"Wallet balance: {response.value} lamports")
            return response.value / 1_000_000_000  # Convert lamports to SOL
        else:
            logger.error("Failed to fetch wallet balance: Balance value is None.")
            return 0
    except Exception as e:
        logger.error(f"Exception in check_wallet_balance: {e}")
        return 0


async def button_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "manage_wallets":
        await manage_wallets_command(update, context)
    elif query.data == "request_add_wallet":
        await add_wallet_command(update, context)
    elif query.data == "request_my_wallets":
        await my_wallets_command(update, context)
    elif query.data == "generate_new_wallet":
        await prompt_generate_new_wallet(update, context)
    elif query.data == "linkx_command":
        await linkx_command(update, context)

    elif query.data == "back_to_main_menu":
        await start(update, context)
