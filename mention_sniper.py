# import re
# import asyncio
# import json
# import os
# from telegram import Bot # type: ignore
# from tweepy import Client # type: ignore
# import tweepy # type: ignore
# import traceback
# from helper_func import load_wallets
# from sniping_jupiter import execute_sniping_logic
# from solana.rpc.api import Client as SolanaClient # type: ignore

# LINKED_ACCOUNTS_FILE = "data/linked_accounts.json"
# LAST_SNIPED_ID_FILE = "data/last_sniped_mention.txt"

# MENTION_SNIPE_PATTERN = re.compile(
#     r"xeroai_bot snipe sol (\d+(\.\d{1,2})?)", re.IGNORECASE
# )

# CA_PATTERN = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")

# SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
# solana_client = SolanaClient(SOLANA_RPC_URL)


# def load_linked_accounts():
#     if os.path.exists(LINKED_ACCOUNTS_FILE):
#         with open(LINKED_ACCOUNTS_FILE, "r") as f:
#             return json.load(f)
#     return {}


# def load_last_sniped_id():
#     if os.path.exists(LAST_SNIPED_ID_FILE):
#         with open(LAST_SNIPED_ID_FILE, "r") as f:
#             return int(f.read().strip())
#     return None


# def save_last_sniped_id(last_id: int):
#     with open(LAST_SNIPED_ID_FILE, "w") as f:
#         f.write(str(last_id))


# async def handle_sniping_mentions(client: Client, bot: Bot, context, last_id=None):
#     print("🔍 Buscando menciones con comando de sniping...")
#     linked_accounts = load_linked_accounts()

#     try:
#         response = client.get_users_mentions(
#             id=context.bot_data["xeroAi_bot_user_id"],
#             since_id=last_id,
#             tweet_fields=[
#                 "author_id",
#                 "created_at",
#                 "conversation_id",
#                 "in_reply_to_user_id",
#             ],
#             expansions=["author_id"],
#         )
#     except tweepy.TooManyRequests:
#         print("⏳ Rate limit alcanzado en menciones")
#         return last_id
#     except Exception as e:
#         print(f"❌ Error obteniendo menciones: {e}")
#         traceback.print_exc()
#         return last_id

#     if not response.data:
#         print("📭 No hay nuevas menciones relevantes.")
#         return last_id

#     new_last_id = last_id
#     for tweet in reversed(response.data):
#         if not new_last_id or int(tweet.id) > new_last_id:
#             new_last_id = int(tweet.id)

#         text = tweet.text
#         match = MENTION_SNIPE_PATTERN.search(text)
#         if not match:
#             continue

#         amount_sol = float(match.group(1))
#         author_id = tweet.author_id
#         username = None
#         for user in response.includes.get("users", []):
#             if user.id == author_id:
#                 username = user.username.lower()
#                 break

#         if not username or username not in linked_accounts:
#             print(f"⚠️ Usuario @{username} no vinculado.")
#             continue

#         telegram_user_id = linked_accounts[username]

#         try:
#             original_tweet = client.get_tweet(
#                 id=tweet.conversation_id, tweet_fields=["text"]
#             )
#         except Exception as e:
#             print(f"⚠️ No se pudo obtener el tweet original: {e}")
#             continue

#         original_text = getattr(original_tweet.data, "text", "")
#         ca_match = CA_PATTERN.search(original_text)
#         if not ca_match:
#             print("⚠️ El tweet original no contiene un contrato válido.")
#             continue

#         contract_address = ca_match.group(0)
#         wallets = load_wallets(telegram_user_id)

#         if not wallets:
#             print(f"⚠️ No hay wallets registradas para Telegram ID {telegram_user_id}")
#             continue

#         for keypair in wallets:
#             pubkey = keypair.pubkey()
#             try:
#                 balance = solana_client.get_balance(pubkey)["result"]["value"]
#                 if balance < amount_sol * 1_000_000_000:
#                     continue  # Saltar wallets sin fondos suficientes

#                 print(
#                     f"🎯 Intentando snipear {amount_sol} SOL desde {pubkey} en {contract_address}"
#                 )

#                 (
#                     success,
#                     token_name,
#                     token_symbol,
#                     tx_hash,
#                 ) = await execute_sniping_logic(contract_address, keypair, amount_sol)

#                 if success:
#                     tweet_url = f"https://x.com/{username}/status/{tweet.id}"
#                     solscan_url = f"https://solscan.io/tx/{tx_hash}"
#                     await bot.send_message(
#                         chat_id=telegram_user_id,
#                         text=f"✅ Sniped successfully!\n"
#                         f"🎯 Token: {token_name} (${token_symbol})\n"
#                         f"💰 Amount: {amount_sol} SOL\n"
#                         f"🐦 Tweet: {tweet_url}\n"
#                         f"🔗 Txn: {solscan_url}\n\n"
#                         f"Executed instantly by XERO AI.\nNo tabs. No delays. Just alpha.",
#                     )
#                     break  # Solo un snipe por mención

#             except Exception as e:
#                 print(f"❌ Falló intento de snipe con wallet {pubkey}: {e}")
#                 traceback.print_exc()
#                 continue

#     return new_last_id


# async def mention_sniping_loop(context, interval: int = 30):
#     print("🚀 Iniciando watcher de menciones con comando de sniping")
#     last_id = load_last_sniped_id()

#     bot = context.bot
#     client: Client = context.bot_data["twitter_client"]

#     while True:
#         try:
#             new_last_id = await handle_sniping_mentions(client, bot, context, last_id)
#             if new_last_id and new_last_id != last_id:
#                 save_last_sniped_id(new_last_id)
#                 last_id = new_last_id
#         except Exception as e:
#             print(f"❌ Error en el loop de sniping de menciones: {e}")
#             traceback.print_exc()

#         await asyncio.sleep(interval)


import json
import os
from typing import Optional
from telegram import Bot
from tweepy import Client
import traceback
import tweepy
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime, timedelta


DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

LINKED_ACCOUNTS_FILE = os.path.join(DATA_DIR, "linked_accounts.json")
LAST_SEEN_ID_FILE = os.path.join(DATA_DIR, "last_seen_id.txt")

# Unified patterns for all commands
LINK_PATTERN = re.compile(r"@xeroAi_bot\s+link\s+([a-zA-Z0-9]{6,})", re.IGNORECASE)
SNIPE_PATTERN = re.compile(r"@xeroAi_bot\s+snipe\s+([\d.]+)\s+(\w+)", re.IGNORECASE)
AUTOSNIPE_PATTERN = re.compile(
    r"@xeroAi_bot\s+autosnipe\s+([\d.]+)\s+(\w+)", re.IGNORECASE
)

LINK_CODES_KEY = "link_codes"

# Rate limiting configuration
RATE_LIMIT_DELAY = 15 * 60  # 15 minutes
MAX_CONCURRENT_SNIPES = 10  # Maximum parallel snipes
POLLING_INTERVAL = 15  # More frequent polling for immediate snipes


def load_linked_accounts() -> dict:
    if os.path.exists(LINKED_ACCOUNTS_FILE):
        with open(LINKED_ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_linked_accounts(data: dict):
    with open(LINKED_ACCOUNTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_last_seen_id() -> Optional[int]:
    if os.path.exists(LAST_SEEN_ID_FILE):
        with open(LAST_SEEN_ID_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None
    return None


def save_last_seen_id(last_seen_id: int):
    with open(LAST_SEEN_ID_FILE, "w") as f:
        f.write(str(last_seen_id))


class UnifiedMentionProcessor:
    def __init__(self, client: Client, bot: Bot, context):
        self.client = client
        self.bot = bot
        self.context = context
        self.snipe_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SNIPES)
        self.rate_limit_until = None
        self.is_running = True

    async def process_mention_batch(self, tweets, users_dict):
        """Process multiple mentions in parallel"""
        if not tweets:
            return

        # Create tasks for parallel processing
        tasks = []
        for tweet in tweets:
            task = asyncio.create_task(self._process_single_mention(tweet, users_dict))
            tasks.append(task)

        # Execute all mentions in parallel
        if tasks:
            print(f"🚀 Procesando {len(tasks)} menciones en paralelo...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ Error procesando mención {tweets[i].id}: {result}")

    async def _process_single_mention(self, tweet, users_dict):
        """Process a single mention with all command types"""
        try:
            tweet_text = tweet.text
            print(f"📝 Procesando mención: {tweet_text}")

            # Check for different command patterns
            link_match = LINK_PATTERN.search(tweet_text)
            snipe_match = SNIPE_PATTERN.search(tweet_text)
            autosnipe_match = AUTOSNIPE_PATTERN.search(tweet_text)

            if link_match:
                await self._handle_link_command(tweet, users_dict, link_match)
            elif snipe_match:
                await self._handle_snipe_command(
                    tweet, users_dict, snipe_match, is_auto=False
                )
            elif autosnipe_match:
                await self._handle_snipe_command(
                    tweet, users_dict, autosnipe_match, is_auto=True
                )
            else:
                print(f"⚠️ Mención sin comando reconocido: {tweet_text}")

        except Exception as e:
            print(f"❌ Error procesando mención {tweet.id}: {e}")
            traceback.print_exc()

    async def _handle_link_command(self, tweet, users_dict, match):
        """Handle account linking"""
        code = match.group(1)
        link_codes = self.context.bot_data.get(LINK_CODES_KEY, {})
        telegram_user_id = link_codes.get(code)

        if not telegram_user_id:
            print(f"⚠️ Código de vinculación no válido: {code}")
            return

        author_id = tweet.author_id
        author = users_dict.get(author_id)
        username = (
            author.username.lower()
            if author and hasattr(author, "username")
            else str(author_id)
        )

        linked_accounts = load_linked_accounts()

        if username in linked_accounts:
            print(f"✅ Usuario @{username} ya vinculado")
            try:
                await self.bot.send_message(
                    chat_id=telegram_user_id,
                    text=f"ℹ️ Tu cuenta @{username} ya está vinculada.",
                )
            except Exception as e:
                print(f"❌ Error enviando mensaje de cuenta ya vinculada: {e}")
            return

        # Link the account
        linked_accounts[username] = str(telegram_user_id)
        save_linked_accounts(linked_accounts)
        del link_codes[code]
        self.context.bot_data[LINK_CODES_KEY] = link_codes

        try:
            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=f"✅ Cuenta vinculada exitosamente!\n🐦 X: @{username}\n📱 Telegram: Usuario vinculado",
            )
            print(f"🔗 Vinculación exitosa: @{username} ↔ Telegram {telegram_user_id}")
        except Exception as e:
            print(f"❌ Error enviando confirmación de vinculación: {e}")

    async def _handle_snipe_command(self, tweet, users_dict, match, is_auto=False):
        """Handle snipe commands (immediate execution)"""
        amount = float(match.group(1))
        token = match.group(2).upper()
        command_type = "autosnipe" if is_auto else "snipe"

        author_id = tweet.author_id
        author = users_dict.get(author_id)
        username = (
            author.username.lower()
            if author and hasattr(author, "username")
            else str(author_id)
        )

        linked_accounts = load_linked_accounts()

        if username not in linked_accounts:
            print(f"⚠️ Usuario @{username} no vinculado para {command_type}")
            return

        telegram_user_id = linked_accounts[username]

        print(f"🎯 SNIPE INMEDIATO: {amount} {token} para @{username}")

        # Execute snipe immediately in background
        asyncio.create_task(
            self._execute_snipe(
                self, telegram_user_id, username, amount, token, is_auto
            )
        )

    async def _execute_snipe(self, telegram_user_id, username, amount, token, is_auto):
        """Execute the actual snipe operation"""
        command_type = "AutoSnipe" if is_auto else "Snipe"

        try:
            # Immediate confirmation
            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=f"🚀 {command_type} INICIADO!\n💰 Cantidad: {amount} {token}\n⚡ Ejecutando transacción...",
            )

            print(
                f"🎯 Ejecutando {command_type.lower()}: {amount} {token} para @{username}"
            )

            # TODO: Replace this with your actual snipe logic
            # This is where you'd integrate with your trading system
            await self._simulate_snipe_execution(
                self, telegram_user_id, username, amount, token
            )

            # Success notification
            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=f"✅ {command_type} EXITOSO!\n💰 {amount} {token}\n🎉 Transacción completada",
            )

            print(f"✅ {command_type} completado para @{username}: {amount} {token}")

        except Exception as e:
            print(f"❌ Error ejecutando {command_type.lower()}: {e}")
            try:
                await self.bot.send_message(
                    chat_id=telegram_user_id,
                    text=f"❌ Error en {command_type}\n💰 {amount} {token}\n⚠️ Transacción falló: {str(e)[:100]}",
                )
            except Exception as e:
                print(f"❌ Error enviando notificación de error: {e}")
                pass

    async def _simulate_snipe_execution(
        self, telegram_user_id, username, amount, token
    ):
        from sniping import perform_sniping, load_user_wallets

        """Simulate snipe execution - replace with your actual logic"""
        # Simulate processing time
        await asyncio.sleep(0.5)  # Very fast execution for demo

        # TODO: Replace with your actual snipe logic:
        # - Validate token contract
        # - Check wallet balance
        # - Execute trade
        # - Return transaction details
        keypairs = await load_user_wallets(telegram_user_id)
        if not keypairs:
            print(f"⚠️ No keypairs found for user {telegram_user_id}")
            return

        await perform_sniping(telegram_user_id, token, keypairs, amount)

        print(f"💎 sniping: {amount} {token}")

    async def fetch_mentions(self, last_seen_id: Optional[int] = None):
        """Fetch mentions with enhanced rate limit handling"""
        if "xeroAi_bot_user_id" not in self.context.bot_data:
            print("❌ Bot X ID no configurado")
            return None, last_seen_id

        # Check rate limit
        if self.rate_limit_until and datetime.now() < self.rate_limit_until:
            remaining = (self.rate_limit_until - datetime.now()).seconds
            if remaining % 60 == 0:  # Log every minute
                print(f"⏳ Rate limit activo: {remaining // 60}m restantes")
            return None, last_seen_id

        try:
            print("🔍 Buscando menciones...")
            response = self.client.get_users_mentions(
                id=self.context.bot_data["xeroAi_bot_user_id"],
                since_id=last_seen_id,
                tweet_fields=["author_id", "created_at"],
                expansions=["author_id"],
                max_results=100,
            )

            self.rate_limit_until = None  # Clear rate limit
            return response, last_seen_id

        except tweepy.TooManyRequests:
            print("⚠️ Rate limit alcanzado - continuando en background...")
            self.rate_limit_until = datetime.now() + timedelta(seconds=RATE_LIMIT_DELAY)
            return None, last_seen_id

        except Exception as e:
            print(f"❌ Error fetching menciones: {e}")
            return None, last_seen_id


async def unified_mention_loop(client: Client, bot: Bot, context):
    """Single unified loop for all mention processing"""
    print("🚀 INICIANDO MONITOR UNIFICADO DE MENCIONES")
    print("📡 Comandos soportados: link, snipe, autosnipe")

    processor = UnifiedMentionProcessor(client, bot, context)
    last_seen_id = load_last_seen_id()
    consecutive_errors = 0
    max_errors = 5

    try:
        while processor.is_running:
            try:
                start_time = time.time()

                # Fetch new mentions
                response, last_seen_id = await processor.fetch_mentions(last_seen_id)

                if response and response.data:
                    # Prepare user data
                    users = (
                        {u["id"]: u for u in response.includes.get("users", [])}
                        if response.includes
                        else {}
                    )

                    # Update last seen ID
                    new_last_seen_id = last_seen_id
                    for tweet in response.data:
                        if not new_last_seen_id or int(tweet.id) > new_last_seen_id:
                            new_last_seen_id = int(tweet.id)

                    # Process all mentions in parallel
                    await processor.process_mention_batch(
                        list(reversed(response.data)), users
                    )

                    # Save progress
                    if new_last_seen_id and new_last_seen_id != last_seen_id:
                        save_last_seen_id(new_last_seen_id)
                        last_seen_id = new_last_seen_id

                # Reset error counter on success
                consecutive_errors = 0

                # Dynamic sleep
                processing_time = time.time() - start_time
                sleep_time = max(1, POLLING_INTERVAL - processing_time)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                print("🛑 Monitor de menciones cancelado")
                break

            except Exception as e:
                consecutive_errors += 1
                error_delay = min(300, 30 * consecutive_errors)

                print(f"❌ Error en monitor (#{consecutive_errors}): {e}")

                if consecutive_errors >= max_errors:
                    print(f"🔥 Demasiados errores. Pausa: {error_delay}s")

                await asyncio.sleep(error_delay)

    except Exception as e:
        print(f"❌ Error fatal en monitor: {e}")
        traceback.print_exc()
    finally:
        processor.is_running = False
        print("🔚 Monitor de menciones terminado")


# Legacy functions for backward compatibility
async def mention_polling_loop(client: Client, bot: Bot, context, interval: int = 30):
    """Legacy function - redirects to unified loop"""
    print("🔄 Redirigiendo a monitor unificado...")
    await unified_mention_loop(client, bot, context)


async def start_mention_watcher(context):
    """Updated to use unified system"""
    bot = context.bot
    bot_x_id = context.bot_data.get("xeroAi_bot_user_id")
    twitter_client = context.bot_data.get("twitter_client")

    if not twitter_client:
        print("❌ Cliente de Twitter no encontrado")
        return

    if not bot_x_id:
        print("❌ Bot X ID no encontrado")
        return

    print("🚀 Iniciando monitor unificado de menciones")
    await unified_mention_loop(twitter_client, bot, context)


async def mention_sniping_loop(context, interval: int = 30):
    """Legacy function - now handled by unified loop"""
    print("ℹ️ Sniping ahora manejado por el monitor unificado")
    # This function is now obsolete as sniping is handled in the unified loop
    return
