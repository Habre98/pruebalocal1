# import json
# import os
# from typing import Optional
# from telegram import Bot
# from tweepy import Client
# import traceback
# import tweepy
# import re
# import asyncio

# DATA_DIR = "data"
# os.makedirs(DATA_DIR, exist_ok=True)

# LINKED_ACCOUNTS_FILE = os.path.join(DATA_DIR, "linked_accounts.json")
# LAST_SEEN_ID_FILE = os.path.join(DATA_DIR, "last_seen_id.txt")

# LINK_PATTERN = re.compile(r"@xeroAi_bot\s+link\s+([a-zA-Z0-9]{6,})", re.IGNORECASE)
# LINK_CODES_KEY = "link_codes"


# def load_linked_accounts() -> dict:
#     if os.path.exists(LINKED_ACCOUNTS_FILE):
#         with open(LINKED_ACCOUNTS_FILE, "r") as f:
#             return json.load(f)
#     return {}


# def save_linked_accounts(data: dict):
#     with open(LINKED_ACCOUNTS_FILE, "w") as f:
#         json.dump(data, f, indent=2)


# def load_last_seen_id() -> Optional[int]:
#     if os.path.exists(LAST_SEEN_ID_FILE):
#         with open(LAST_SEEN_ID_FILE, "r") as f:
#             try:
#                 return int(f.read().strip())
#             except ValueError:
#                 return None
#     return None


# def save_last_seen_id(last_seen_id: int):
#     with open(LAST_SEEN_ID_FILE, "w") as f:
#         f.write(str(last_seen_id))


# async def handle_mentions(
#     client: Client, bot: Bot, context, last_seen_id: Optional[int] = None
# ) -> Optional[int]:
#     if "xeroAi_bot_user_id" not in context.bot_data:
#         print("❌ No se ha configurado el ID de usuario del bot de X.")
#         if last_seen_id:
#             return last_seen_id

#     print("🔍 Buscando nuevas menciones...")

#     try:
#         response = client.get_users_mentions(
#             id=context.bot_data["xeroAi_bot_user_id"],
#             since_id=last_seen_id,
#             tweet_fields=["author_id", "created_at"],
#             expansions=["author_id"],
#         )
#     except tweepy.TooManyRequests:
#         print("⚠️ Límite de rate alcanzado. Esperando para reintentar...")
#         for code, telegram_user_id in context.bot_data.get(LINK_CODES_KEY, {}).items():
#             try:
#                 await bot.send_message(
#                     chat_id=telegram_user_id,
#                     text="⚠️ Hemos alcanzado el límite de consultas a X (Twitter). Intentaremos nuevamente en unos minutos.",
#                 )
#             except Exception as e:
#                 print(f"❌ Error al enviar mensaje: {e}")
#         if last_seen_id:
#             return last_seen_id

#     if not response.data:
#         print("📭 No hay nuevas menciones.")
#         if last_seen_id:
#             return last_seen_id

#     users = (
#         {u["id"]: u for u in response.includes.get("users", [])}
#         if response.includes
#         else {}
#     )

#     new_last_seen_id = last_seen_id
#     linked_accounts = load_linked_accounts()
#     link_codes = context.bot_data.get(LINK_CODES_KEY, {})

#     for tweet in reversed(response.data):
#         print(f"📝 Mención recibida: {tweet.text}")
#         match = LINK_PATTERN.search(tweet.text)

#         if match:
#             code = match.group(1)
#             telegram_user_id = link_codes.get(code)

#             if telegram_user_id:
#                 author_id = tweet.author_id
#                 author = users.get(author_id)
#                 username = (
#                     author.username.lower()
#                     if author and hasattr(author, "username")
#                     else str(author_id)
#                 )

#                 # Ignorar si ya está vinculado
#                 if username in linked_accounts:
#                     print(
#                         f"✅ Usuario @{username} ya está vinculado. Ignorando mención."
#                     )
#                     continue

#                 linked_accounts[username] = str(telegram_user_id)
#                 save_linked_accounts(linked_accounts)
#                 del link_codes[code]

#                 await bot.send_message(
#                     chat_id=telegram_user_id,
#                     text=f"✅ Tu cuenta de X (@{username}) ha sido vinculada con éxito.",
#                 )

#                 print(f"🔗 Vinculado: @{username} <-> Telegram ID {telegram_user_id}")
#             else:
#                 print(f"⚠️ Código no válido o ya usado: {code}")
#         else:
#             print(f"⚠️ No se encontró patrón de vinculación en: {tweet.text}")

#         if not new_last_seen_id or int(tweet.id) > new_last_seen_id:
#             new_last_seen_id = int(tweet.id)

#     context.bot_data[LINK_CODES_KEY] = link_codes
#     if new_last_seen_id:
#         return new_last_seen_id


# async def mention_polling_loop(client: Client, bot: Bot, context, interval: int = 30):
#     print("🚀 Iniciando watcher de menciones para vinculación de cuentas")
#     last_seen_id = load_last_seen_id()

#     while True:
#         try:
#             last_seen_id = await handle_mentions(client, bot, context, last_seen_id)
#             if last_seen_id:
#                 save_last_seen_id(last_seen_id)
#         except Exception as e:
#             print(f"❌ Error en handle_mentions: {e}")
#             traceback.print_exc()

#         await asyncio.sleep(interval)


# /////////////////////////////////////////////////////////////////////////////////////////////////////////


# import json
# import os
# from typing import Optional
# from telegram import Bot  # type: ignore
# from tweepy import Client  # type: ignore
# import traceback
# import tweepy  # type: ignore
# import re
# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# import time
# from datetime import datetime, timedelta

# DATA_DIR = "data"
# os.makedirs(DATA_DIR, exist_ok=True)

# LINKED_ACCOUNTS_FILE = os.path.join(DATA_DIR, "linked_accounts.json")
# LAST_SEEN_ID_FILE = os.path.join(DATA_DIR, "last_seen_id.txt")

# LINK_PATTERN = re.compile(r"@xeroAi_bot\s+link\s+([a-zA-Z0-9]{6,})", re.IGNORECASE)
# SNIPE_PATTERN = re.compile(r"@xeroAi_bot\s+snipe\s+([\d.]+)\s+(\w+)", re.IGNORECASE)
# LINK_CODES_KEY = "link_codes"

# # Rate limiting configuration
# RATE_LIMIT_DELAY = 15 * 60  # 15 minutes default delay on rate limit
# MAX_CONCURRENT_TASKS = 5  # Maximum parallel tasks
# POLLING_INTERVAL = 30  # Seconds between polls


# def load_linked_accounts() -> dict:
#     if os.path.exists(LINKED_ACCOUNTS_FILE):
#         with open(LINKED_ACCOUNTS_FILE, "r") as f:
#             return json.load(f)
#     return {}


# def save_linked_accounts(data: dict):
#     with open(LINKED_ACCOUNTS_FILE, "w") as f:
#         json.dump(data, f, indent=2)


# def load_last_seen_id() -> Optional[int]:
#     if os.path.exists(LAST_SEEN_ID_FILE):
#         with open(LAST_SEEN_ID_FILE, "r") as f:
#             try:
#                 return int(f.read().strip())
#             except ValueError:
#                 return None
#     return None


# def save_last_seen_id(last_seen_id: int):
#     with open(LAST_SEEN_ID_FILE, "w") as f:
#         f.write(str(last_seen_id))


# class MentionProcessor:
#     def __init__(self, client: Client, bot: Bot, context):
#         self.client = client
#         self.bot = bot
#         self.context = context
#         self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)
#         self.rate_limit_until = None
#         self.processing_queue = asyncio.Queue()

#     async def process_mention_async(self, tweet, users_dict):
#         """Process a single mention asynchronously"""
#         try:
#             print(f"🔄 Procesando mención: {tweet.text}")

#             # Check for link pattern
#             link_match = LINK_PATTERN.search(tweet.text)
#             snipe_match = SNIPE_PATTERN.search(tweet.text)

#             if link_match:
#                 await self._handle_link_mention(tweet, users_dict, link_match)
#             elif snipe_match:
#                 await self._handle_snipe_mention(tweet, users_dict, snipe_match)
#             else:
#                 print(f"⚠️ Mención sin comando reconocido: {tweet.text}")

#         except Exception as e:
#             print(f"❌ Error procesando mención {tweet.id}: {e}")
#             traceback.print_exc()

#     async def _handle_link_mention(self, tweet, users_dict, match):
#         """Handle account linking mentions"""
#         code = match.group(1)
#         link_codes = self.context.bot_data.get(LINK_CODES_KEY, {})
#         telegram_user_id = link_codes.get(code)

#         if not telegram_user_id:
#             print(f"⚠️ Código no válido o ya usado: {code}")
#             return

#         author_id = tweet.author_id
#         author = users_dict.get(author_id)
#         username = (
#             author.username.lower()
#             if author and hasattr(author, "username")
#             else str(author_id)
#         )

#         linked_accounts = load_linked_accounts()

#         # Check if already linked
#         if username in linked_accounts:
#             print(f"✅ Usuario @{username} ya está vinculado. Ignorando mención.")
#             return

#         # Link the account
#         linked_accounts[username] = str(telegram_user_id)
#         save_linked_accounts(linked_accounts)
#         del link_codes[code]
#         self.context.bot_data[LINK_CODES_KEY] = link_codes

#         try:
#             await self.bot.send_message(
#                 chat_id=telegram_user_id,
#                 text=f"✅ Tu cuenta de X (@{username}) ha sido vinculada con éxito.",
#             )
#             print(f"🔗 Vinculado: @{username} <-> Telegram ID {telegram_user_id}")
#         except Exception as e:
#             print(f"❌ Error enviando confirmación de vinculación: {e}")

#     async def _handle_snipe_mention(self, tweet, users_dict, match):
#         """Handle snipe command mentions"""
#         amount = float(match.group(1))
#         token = match.group(2).upper()

#         author_id = tweet.author_id
#         author = users_dict.get(author_id)
#         username = (
#             author.username.lower()
#             if author and hasattr(author, "username")
#             else str(author_id)
#         )

#         linked_accounts = load_linked_accounts()

#         if username not in linked_accounts:
#             print(f"⚠️ Usuario @{username} no está vinculado para snipe")
#             return

#         telegram_user_id = linked_accounts[username]

#         print(f"🎯 Procesando snipe: {amount} {token} para @{username}")

#         try:
#             # Send confirmation to user
#             await self.bot.send_message(
#                 chat_id=telegram_user_id,
#                 text=f"🎯 Procesando snipe: {amount} {token}\n⏳ Ejecutando transacción...",
#             )

#             # Here you would integrate your actual snipe logic
#             # For now, just simulating processing
#             await asyncio.sleep(1)  # Simulate processing time

#             await self.bot.send_message(
#                 chat_id=telegram_user_id,
#                 text=f"✅ Snipe ejecutado: {amount} {token}",
#             )

#             print(f"✅ Snipe completado para @{username}: {amount} {token}")

#         except Exception as e:
#             print(f"❌ Error procesando snipe para @{username}: {e}")
#             try:
#                 await self.bot.send_message(
#                     chat_id=telegram_user_id,
#                     text=f"❌ Error ejecutando snipe: {amount} {token}",
#                 )
#             except Exception as e:
#                 print(f"❌ Error enviando notificación de error: {e}")
#                 pass

#     async def fetch_mentions(self, last_seen_id: Optional[int] = None):
#         """Fetch mentions from X API with rate limit handling"""
#         if "xeroAi_bot_user_id" not in self.context.bot_data:
#             print("❌ No se ha configurado el ID de usuario del bot de X.")
#             return None, last_seen_id

#         # Check if we're still in rate limit cooldown
#         if self.rate_limit_until and datetime.now() < self.rate_limit_until:
#             remaining = (self.rate_limit_until - datetime.now()).seconds
#             print(f"⏳ Esperando rate limit: {remaining} segundos restantes")
#             return None, last_seen_id

#         try:
#             print("🔍 Buscando nuevas menciones...")
#             response = self.client.get_users_mentions(
#                 id=self.context.bot_data["xeroAi_bot_user_id"],
#                 since_id=last_seen_id,
#                 tweet_fields=["author_id", "created_at"],
#                 expansions=["author_id"],
#                 max_results=100,  # Fetch more mentions at once
#             )

#             # Clear rate limit if successful
#             self.rate_limit_until = None
#             return response, last_seen_id

#         except tweepy.TooManyRequests as e:
#             print("⚠️ Límite de rate alcanzado.")

#             # Set rate limit cooldown
#             self.rate_limit_until = datetime.now() + timedelta(seconds=RATE_LIMIT_DELAY)

#             # Notify all linked users about rate limit
#             await self._notify_rate_limit()

#             return None, last_seen_id

#         except Exception as e:
#             print(f"❌ Error fetching mentions: {e}")
#             traceback.print_exc()
#             return None, last_seen_id

#     async def _notify_rate_limit(self):
#         """Notify all users with pending link codes about rate limit"""
#         link_codes = self.context.bot_data.get(LINK_CODES_KEY, {})

#         for code, telegram_user_id in link_codes.items():
#             try:
#                 await self.bot.send_message(
#                     chat_id=telegram_user_id,
#                     text="⚠️ Hemos alcanzado el límite de consultas a X (Twitter). El bot continuará procesando automáticamente en unos minutos.",
#                 )
#             except Exception as e:
#                 print(f"❌ Error enviando notificación de rate limit: {e}")


# async def handle_mentions(
#     client: Client, bot: Bot, context, last_seen_id: Optional[int] = None
# ) -> Optional[int]:
#     """Enhanced mention handler with parallel processing"""

#     processor = MentionProcessor(client, bot, context)
#     response, last_seen_id = await processor.fetch_mentions(last_seen_id)

#     if not response or not response.data:
#         if not response:
#             print("📭 No se pudieron obtener menciones (rate limit o error).")
#         else:
#             print("📭 No hay nuevas menciones.")
#         return last_seen_id

#     # Prepare user data
#     users = (
#         {u["id"]: u for u in response.includes.get("users", [])}
#         if response.includes
#         else {}
#     )

#     # Process mentions in parallel
#     tasks = []
#     new_last_seen_id = last_seen_id

#     for tweet in reversed(response.data):
#         # Update last seen ID
#         if not new_last_seen_id or int(tweet.id) > new_last_seen_id:
#             new_last_seen_id = int(tweet.id)

#         # Create async task for parallel processing
#         task = asyncio.create_task(processor.process_mention_async(tweet, users))
#         tasks.append(task)

#     # Wait for all mentions to be processed
#     if tasks:
#         print(f"🚀 Procesando {len(tasks)} menciones en paralelo...")
#         await asyncio.gather(*tasks, return_exceptions=True)
#         print("✅ Todas las menciones procesadas")

#     return new_last_seen_id


# async def mention_polling_loop(
#     client: Client, bot: Bot, context, interval: int = POLLING_INTERVAL
# ):
#     """Enhanced polling loop with better error handling and recovery"""
#     print("🚀 Iniciando watcher de menciones mejorado con procesamiento paralelo")
#     last_seen_id = load_last_seen_id()
#     consecutive_errors = 0
#     max_consecutive_errors = 5

#     try:
#         while True:
#             try:
#                 start_time = time.time()

#                 last_seen_id = await handle_mentions(client, bot, context, last_seen_id)
#                 if last_seen_id:
#                     save_last_seen_id(last_seen_id)

#                 # Reset error counter on success
#                 consecutive_errors = 0

#                 # Calculate dynamic sleep time
#                 processing_time = time.time() - start_time
#                 sleep_time = max(1, interval - processing_time)

#                 print(f"⏳ Esperando {sleep_time:.1f}s hasta próxima verificación...")
#                 await asyncio.sleep(sleep_time)

#             except asyncio.CancelledError:
#                 print("🛑 Mention polling loop cancelled")
#                 break

#             except Exception as e:
#                 consecutive_errors += 1
#                 error_delay = min(300, 30 * consecutive_errors)  # Max 5 minutes

#                 print(f"❌ Error en polling loop (#{consecutive_errors}): {e}")
#                 traceback.print_exc()

#                 if consecutive_errors >= max_consecutive_errors:
#                     print(
#                         f"🔥 Demasiados errores consecutivos. Pausando {error_delay}s..."
#                     )

#                 await asyncio.sleep(error_delay)

#     except Exception as e:
#         print(f"❌ Fatal error in mention polling loop: {e}")
#         traceback.print_exc()
#     finally:
#         print("🔚 Mention polling loop ended")


# ////////////////////////////////////////////////////////////////////////////

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

# from helper_func import wallet_path
from sniping import perform_sniping

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

LINKED_ACCOUNTS_FILE = os.path.join(DATA_DIR, "linked_accounts.json")
LAST_SEEN_ID_FILE = os.path.join(DATA_DIR, "last_seen_id.txt")

# Unified patterns for all commands
LINK_PATTERN = re.compile(r"@xeroAi_bot\s+link\s+([a-zA-Z0-9]{6,})", re.IGNORECASE)
SNIPE_PATTERN = re.compile(r"@xeroAi_bot\s+snipe\s+([\d.]+)\s+(\w+)", re.IGNORECASE)
BUY_PATTERN = re.compile(r"@xeroAi_bot\s+buy\s+([\d.]+)\s+(\w+)", re.IGNORECASE)

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
            buy_match = BUY_PATTERN.search(tweet_text)

            if link_match:
                await self._handle_link_command(tweet, users_dict, link_match)
            elif snipe_match:
                await self._handle_snipe_command(
                    tweet, users_dict, snipe_match, is_auto=False
                )
            elif buy_match:
                await self._handle_snipe_command(
                    tweet, users_dict, buy_match, is_auto=True
                )
            else:
                print(f"⚠️ Mención sin comando reconocido: {tweet_text}")

        except Exception as e:
            print(f"❌ Error procesando mención {tweet.id}: {e}")
            traceback.print_exc()

    async def _handle_link_command(self, tweet, users_dict, match):
        """Handle account linking"""
        code = match.group(1)
        author_id = tweet.author_id
        author = users_dict.get(author_id)
        username = (
            author.username.lower()
            if author and hasattr(author, "username")
            else str(author_id)
        )
        print(f"[LINK_DEBUG] _handle_link_command triggered. Code: {code}, Author ID: {author_id}, Username: {username}")

        link_codes = self.context.bot_data.get(LINK_CODES_KEY, {})
        telegram_user_id = link_codes.get(code)
        print(f"[LINK_DEBUG] Telegram User ID from code '{code}': {telegram_user_id}")

        if not telegram_user_id:
            print(f"[LINK_DEBUG] Invalid or used code detected: {code}")
            print(f"⚠️ Código de vinculación no válido: {code}")
            return

        linked_accounts = load_linked_accounts()
        print(f"[LINK_DEBUG] Checking username '{username}'. Current linked_accounts: {linked_accounts}")

        if username in linked_accounts:
            print(f"[LINK_DEBUG] Account already linked for username '{username}' to Telegram ID '{linked_accounts[username]}'")
            print(f"✅ Usuario @{username} ya vinculado")
            try:
                await self.bot.send_message(
                    chat_id=telegram_user_id,
                    text=f"ℹ️ Tu cuenta @{username} ya está vinculada.",
                )
            except Exception as e:
                print(f"[LINK_DEBUG] Error sending 'already linked' message: {e}")
                print(f"❌ Error enviando mensaje de cuenta ya vinculada: {e}")
            return

        print(f"[LINK_DEBUG] Establishing new link for username '{username}' to Telegram ID '{telegram_user_id}'")
        # Link the account
        linked_accounts[username] = str(telegram_user_id)
        save_linked_accounts(linked_accounts)
        del link_codes[code]
        self.context.bot_data[LINK_CODES_KEY] = link_codes
        print(f"[LINK_DEBUG] Account for '{username}' saved and code '{code}' deleted.")

        try:
            print(f"[LINK_DEBUG] Sending success message to Telegram ID '{telegram_user_id}' for username '{username}'")
            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=f"✅ Cuenta vinculada exitosamente!\n🐦 X: @{username}\n📱 Telegram: Usuario vinculado",
            )
            print(f"🔗 Vinculación exitosa: @{username} ↔ Telegram {telegram_user_id}")
        except Exception as e:
            print(f"[LINK_DEBUG] Error sending success confirmation message: {e}")
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
            self._execute_snipe(telegram_user_id, username, amount, token, is_auto)
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
            await self._simulate_snipe_execution(amount, token)

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
                pass

    async def _simulate_snipe_execution(self, amount, token):
        """Simulate snipe execution - replace with your actual logic"""
        # Simulate processing time
        await asyncio.sleep(0.5)  # Very fast execution for demo

        # TODO: Replace with your actual snipe logic:
        try:
            await self.bot.send_message(
                chat_id=self.context.bot_data["xeroAi_bot_user_id"],
                text=f"🎯 Ejecutando snipe: {amount} {token}",
            )
            await perform_sniping(token, amount)
        except Exception as e:
            print(f"❌ Error enviando mensaje de snipe: {e}")

        print(f"💎 Simulated snipe: {amount} {token}")

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
            print("😎Since id:", last_seen_id)

            # response = self.client.get_users_mentions(
            #     id=self.context.bot_data["xeroAi_bot_user_id"],
            #     since_id=last_seen_id,
            #     tweet_fields=["author_id", "created_at"],
            response = self.client.get_users_mentions(
                id=self.context.bot_data["xeroAi_bot_user_id"],
                since_id=last_seen_id,
                tweet_fields=["author_id", "created_at"],
                expansions=["author_id"],
                max_results=100,
            )
            # response = self.client.get_users_mentions(
            #     id=self.context.bot_data["xeroAi_bot_user_id"], max_results=100
            # )  # ✅ No since_id
            print(response.data)

            if response.data:
                new_last_seen_id = last_seen_id
                for tweet in response.data:
                    if not new_last_seen_id or int(tweet.id) > new_last_seen_id:
                        new_last_seen_id = int(tweet.id)  # ✅ Update to latest mention

                if new_last_seen_id != last_seen_id:
                    print(
                        f"📝 Updating last_seen_id from {last_seen_id} → {new_last_seen_id}"
                    )
                    last_seen_id = new_last_seen_id  # ✅ Assign new ID
                    save_last_seen_id(last_seen_id)  # ✅ Persist the latest ID

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

                    # Process all mentions in parallel
                    await processor.process_mention_batch(
                        list(reversed(response.data)), users
                    )

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
