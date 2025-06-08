# import asyncio
# from solders.keypair import Keypair
# from solders.pubkey import Pubkey
# from solders.system_program import transfer, TransferParams
# from solana.rpc.async_api import AsyncClient
# from solana.transaction import Transaction
# from solana.rpc.types import TxOpts
# import os
# import json
# import base58


# # Función para cargar wallets desde archivos JSON guardados
# def load_user_wallets(user_id: int, max_wallets: int = 5) -> list[Keypair]:
#     keypairs = []
#     base_path = os.path.join("wallets", str(user_id))

#     for wallet_index in range(max_wallets):
#         wallet_path = os.path.join(base_path, f"wallet_{wallet_index}.json")
#         if not os.path.exists(wallet_path):
#             continue

#         try:
#             with open(wallet_path, "r") as f:
#                 data = json.load(f)
#             private_key_b58 = data.get("private_key")
#             if not private_key_b58:
#                 print(f"❌ Wallet {wallet_index} no tiene private_key")
#                 continue

#             private_key_bytes = base58.b58decode(private_key_b58)

#             # solders.Keypair espera clave secreta de 64 bytes (private + public key concatenadas)
#             # Si tu archivo solo guarda 32 bytes (clave privada), debes reconstruir la keypair
#             # Aquí asumiremos que guardas las 64 bytes, si no, esto da error
#             if len(private_key_bytes) == 64:
#                 keypair = Keypair.from_bytes(private_key_bytes)
#             elif len(private_key_bytes) == 32:
#                 # Derivar keypair si solo tienes 32 bytes de clave privada
#                 # solders no tiene directamente desde 32 bytes, pero se puede usar solana-py Keypair y luego convertir

#                 sol_keypair = Keypair.from_secret_key(private_key_bytes)
#                 keypair = Keypair.from_bytes(bytes(sol_keypair))
#             else:
#                 print(f"❌ Tamaño clave privada inesperado en wallet {wallet_index}")
#                 continue

#             keypairs.append(keypair)
#         except Exception as e:
#             print(f"❌ Error cargando wallet {wallet_index}: {e}")

#     return keypairs


# def is_valid_pubkey(address: str) -> bool:
#     try:
#         pubkey = Pubkey.from_string(address)
#         return pubkey.is_on_curve()
#     except Exception:
#         return False


# async def get_sol_balance(
#     pubkey: Pubkey, rpc_url: str = "https://api.mainnet-beta.solana.com"
# ) -> int:
#     """
#     Retorna el balance en lamports para un pubkey.
#     """
#     async with AsyncClient(rpc_url) as client:
#         try:
#             resp = await client.get_balance(pubkey)
#             return resp.value
#         except Exception as e:
#             print(f"❌ Error obteniendo balance para {pubkey}: {e}")
#             return 0


# async def send_sol_transaction(
#     sender_keypair: Keypair,
#     recipient: str,
#     amount_sol: float,
#     rpc_url: str = "https://api.mainnet-beta.solana.com",
# ) -> str:
#     async with AsyncClient(rpc_url) as client:
#         try:
#             recipient_pubkey = Pubkey.from_string(recipient)
#             lamports = int(amount_sol * 1e9)

#             txn = Transaction()
#             txn.add(
#                 transfer(
#                     TransferParams(
#                         from_pubkey=sender_keypair.pubkey(),
#                         to_pubkey=recipient_pubkey,
#                         lamports=lamports,
#                     )
#                 )
#             )

#             response = await client.send_transaction(
#                 txn,
#                 sender_keypair,
#                 opts=TxOpts(skip_preflight=True, preflight_commitment="processed"),
#             )
#             return response.value
#         except Exception as e:
#             print(f"❌ Error sending transaction from {sender_keypair.pubkey()}: {e}")
#             return ""


# async def perform_sniping(
#     contract_address: str, keypairs: list[Keypair], amount_sol: float = 0.001
# ) -> str:
#     msg = f"🎯 Iniciando sniping para contrato: {contract_address}"
#     print(msg)

#     if not is_valid_pubkey(contract_address):
#         msg = f"❌ Dirección inválida: {contract_address}"
#         print(msg)
#         return msg

#     lamports_needed = int(amount_sol * 1e9)

#     for kp in keypairs:
#         pubkey = kp.pubkey()
#         balance = await get_sol_balance(pubkey)
#         print(f"🔍 Wallet {pubkey} tiene balance: {balance / 1e9} SOL")

#         if balance >= lamports_needed:
#             print(f"🚀 Enviando desde wallet {pubkey} con suficiente balance")
#             tx_signature = await send_sol_transaction(
#                 sender_keypair=kp, recipient=contract_address, amount_sol=amount_sol
#             )
#             if tx_signature:
#                 msg = f"✅ Sniping exitoso desde {pubkey}\n🔗 https://solscan.io/tx/{tx_signature}"
#                 print(msg)
#                 return msg
#             else:
#                 msg = f"⚠️ Falló la transacción con {pubkey}"
#                 print(msg)
#                 return msg

#     msg = "⚠️ Ninguna wallet tiene fondos suficientes para la transacción."
#     print(msg)
#     return msg


# # import asyncio
# from solders.keypair import Keypair  # type: ignore
# from solders.pubkey import Pubkey  # type: ignore
# from solders.system_program import transfer, TransferParams  # type: ignore
# from solana.rpc.async_api import AsyncClient  # type: ignore
# from solders.transaction import VersionedTransaction  # type: ignore
# from solders.message import MessageV0  # type: ignore
# from solders.rpc.config import RpcSendTransactionConfig  # type: ignore
# import os
# import json
# import base58  # type: ignore
# from solders.hash import Hash  # ✅ Import Hash type


# def is_valid_pubkey(address: str) -> bool:
#     try:
#         pubkey = Pubkey.from_string(address)
#         return pubkey.is_on_curve()
#     except Exception:
#         return False


# async def get_sol_balance(
#     pubkey: Pubkey, rpc_url: str = "https://api.mainnet-beta.solana.com"
# ) -> int:
#     """
#     Retorna el balance en lamports para un pubkey.
#     """
#     async with AsyncClient(rpc_url) as client:
#         try:
#             resp = await client.get_balance(pubkey)
#             return resp.value
#         except Exception as e:
#             print(f"❌ Error obteniendo balance para {pubkey}: {e}")
#             return 0


# # Función para cargar wallets desde archivos JSON guardados
# def load_user_wallets(user_id: int, max_wallets: int = 5) -> list[Keypair]:
#     keypairs = []
#     base_path = os.path.join("wallets", str(user_id))

#     for wallet_index in range(max_wallets):
#         wallet_path = os.path.join(base_path, f"wallet_{wallet_index}.json")
#         if not os.path.exists(wallet_path):
#             continue

#         try:
#             with open(wallet_path, "r") as f:
#                 data = json.load(f)
#             private_key_b58 = data.get("private_key")
#             if not private_key_b58:
#                 print(f"❌ Wallet {wallet_index} no tiene private_key")
#                 continue

#             private_key_bytes = base58.b58decode(private_key_b58)

#             if len(private_key_bytes) == 64:
#                 keypair = Keypair.from_bytes(private_key_bytes)
#             elif len(private_key_bytes) == 32:
#                 keypair = Keypair.from_bytes(
#                     Keypair.from_secret_key(private_key_bytes).to_bytes()
#                 )
#             else:
#                 print(f"❌ Tamaño clave privada inesperado en wallet {wallet_index}")
#                 continue

#             keypairs.append(keypair)
#         except Exception as e:
#             print(f"❌ Error cargando wallet {wallet_index}: {e}")

#     return keypairs


# def load_user_private_keys(user_id: int, max_wallets: int = 5) -> list[Keypair]:
#     private_keys = []
#     base_path = os.path.join("wallets", str(user_id))

#     for wallet_index in range(max_wallets):
#         wallet_path = os.path.join(base_path, f"wallet_{wallet_index}.json")
#         if not os.path.exists(wallet_path):
#             continue

#         try:
#             with open(wallet_path, "r") as f:
#                 data = json.load(f)
#             private_key_b58 = data.get("private_key")
#             if not private_key_b58:
#                 print(f"❌ Wallet {wallet_index} no tiene private_key")
#                 continue

#             private_keys.append(private_key_b58)
#         except Exception as e:
#             print(f"❌ Error cargando wallet {wallet_index}: {e}")

#     return private_keys


# async def send_sol_transaction(
#     sender_keypair: Keypair,
#     recipient: str,
#     amount_sol: float,
#     rpc_url: str = "https://api.mainnet-beta.solana.com",
# ) -> str:
#     async with AsyncClient(rpc_url) as client:
#         try:
#             recipient_pubkey = Pubkey.from_string(recipient)
#             lamports = int(amount_sol * 1e9)

#             instructions = [
#                 transfer(
#                     TransferParams(
#                         from_pubkey=sender_keypair.pubkey(),
#                         to_pubkey=recipient_pubkey,
#                         lamports=lamports,
#                     )
#                 )
#             ]

#             blockhash_response = await client.get_latest_blockhash()
#             blockhash = Hash.from_string(
#                 blockhash_response.value
#             )  # ✅ Correctly convert

#             message = MessageV0.try_compile(
#                 sender_keypair.pubkey(),
#                 instructions,
#                 [],
#                 blockhash,
#             )
#             tx = VersionedTransaction(message, [sender_keypair])

#             response = await client.send_transaction(
#                 tx, RpcSendTransactionConfig(skip_preflight=True)
#             )
#             return response.value
#         except Exception as e:
#             print(f"❌ Error sending transaction from {sender_keypair.pubkey()}: {e}")
#             return ""


# async def sort_selected_wallets_for_sniping(update, context):
#     user_private_keys = load_user_private_keys(update.effective_user.id)
#     selected_wallets = context.bot_data.get("selected_wallets", {})

#     for wallet_index, private_key in enumerate(user_private_keys):
#         if wallet_index in selected_wallets:
#             context.bot_data["selected_wallets"][wallet_index] = private_key
#         # from the selected wallets select the one with most balance and do the sniping
#         # - Check wallet balance


# async def get_highest_balance_wallet(keypairs: list[Keypair]) -> Keypair:
#     """Returns the wallet with the highest balance."""
#     wallet_balances = {}

#     for kp in keypairs:
#         pubkey = kp.pubkey()
#         balance = await get_sol_balance(pubkey)  # Fetch SOL balance
#         wallet_balances[kp] = balance
#         print(f"🔍 Wallet {pubkey} tiene balance: {balance / 1e9} SOL")

#     # Select the wallet with the highest balance
#     best_wallet = max(wallet_balances, key=lambda x: wallet_balances[x])

#     print(
#         f"💰 Wallet seleccionada: {best_wallet.pubkey()} con balance: {wallet_balances[best_wallet] / 1e9} SOL"
#     )
#     return best_wallet


# async def perform_sniping(
#     contract_address: str, keypairs: list[Keypair], amount_sol: float = 0.001
# ) -> str:
#     """Selects the wallet with the most balance and performs a sniping transaction."""

#     contract_address = await validate_contract_address(
#         contract_address
#     )  # Validate contract
#     msg = f"🎯 Iniciando sniping para contrato: {contract_address}"
#     print(msg)

#     lamports_needed = int(amount_sol * 1e9)

#     # Get the wallet with the highest balance
#     best_wallet = await get_highest_balance_wallet(keypairs)

#     # Check balance
#     best_balance = await get_sol_balance(best_wallet.pubkey())

#     if best_balance >= lamports_needed:
#         print(f"🚀 Enviando desde wallet {best_wallet.pubkey()} con suficiente balance")
#         tx_signature = await send_sol_transaction(
#             sender_keypair=best_wallet,
#             recipient=contract_address,
#             amount_sol=amount_sol,
#         )
#         if tx_signature:
#             msg = f"✅ Sniping exitoso desde {best_wallet.pubkey()}\n🔗 https://solscan.io/tx/{tx_signature}"
#             print(msg)
#             return msg
#         else:
#             msg = f"⚠️ Falló la transacción con {best_wallet.pubkey()}"
#             print(msg)
#             return msg

#     msg = "⚠️ La wallet seleccionada no tiene suficiente balance para la transacción."
#     print(msg)
#     return msg

# import base64
# import requests
# from solders.keypair import Keypair  # type: ignore
# from solders.pubkey import Pubkey  # type: ignore
# from solana.rpc.async_api import AsyncClient  # type: ignore
# from solders.transaction import VersionedTransaction  # type: ignore
# from solana.rpc.api import Client
# from jupiter_python_sdk.jupiter import Jupiter  # ✅ Import Jupiter SDK

# import json
# import os
# import base58  # type: ignore

# JUPITER_QUOTE_API = "https://quote-api.jup.ag/v6/quote"
# JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"
# SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

# solana_client = Client(SOLANA_RPC_URL)
# jupiter = Jupiter(SOLANA_RPC_URL,keypair= None)


# def is_valid_pubkey(address: str) -> bool:
#     try:
#         pubkey = Pubkey.from_string(address)
#         return pubkey.is_on_curve()
#     except Exception:
#         return False


# async def get_sol_balance(pubkey: Pubkey, rpc_url: str = SOLANA_RPC_URL) -> int:
#     async with AsyncClient(rpc_url) as client:
#         try:
#             resp = await client.get_balance(pubkey)
#             return resp.value
#         except Exception as e:
#             print(f"❌ Error obteniendo balance para {pubkey}: {e}")
#             return 0


# async def validate_contract_address(contract_address: str) -> str:
#     if not is_valid_pubkey(contract_address):
#         raise ValueError(f"Invalid contract address: {contract_address}")
#     return contract_address


# def load_user_wallets(user_id: int, max_wallets: int = 5) -> list[Keypair]:
#     keypairs = []
#     base_path = os.path.join("wallets", str(user_id))
#     for wallet_index in range(max_wallets):
#         wallet_path = os.path.join(base_path, f"wallet_{wallet_index}.json")
#         if not os.path.exists(wallet_path):
#             continue
#         try:
#             with open(wallet_path, "r") as f:
#                 data = json.load(f)
#             private_key_b58 = data.get("private_key")
#             if not private_key_b58:
#                 print(f"❌ Wallet {wallet_index} no tiene private_key")
#                 continue
#             private_key_bytes = base58.b58decode(private_key_b58)
#             keypair = Keypair.from_bytes(
#                 private_key_bytes[:64]
#             )  # Ensure correct length
#             keypairs.append(keypair)
#         except Exception as e:
#             print(f"❌ Error cargando wallet {wallet_index}: {e}")
#     return keypairs


# async def get_best_quote(input_mint: str, output_mint: str, amount_lamports: int):
#     try:
#         return await jupiter.get_quote(
#             input_mint, output_mint, amount_lamports, slippage_bps=1000
#         )
#     except Exception as e:
#         print(f"❌ Error obteniendo quote de Jupiter: {e}")
#         return None


# async def get_swap_transaction(route, user_pubkey: str):
#     try:
#         return await jupiter.get_swap_transaction(route, user_pubkey)
#     except Exception as e:
#         print(f"❌ Error al obtener transacción de swap: {e}")
#         return None


# async def get_highest_balance_wallet(keypairs: list[Keypair]) -> Keypair:
#     """Returns the wallet with the highest balance."""
#     wallet_balances = {}
#     for kp in keypairs:
#         pubkey = kp.pubkey()
#         balance = await get_sol_balance(pubkey)
#         wallet_balances[kp] = balance
#         print(f"🔍 Wallet {pubkey} tiene balance: {balance / 1e9} SOL")
#     best_wallet = max(wallet_balances, key=lambda x: wallet_balances[x])
#     print(
#         f"💰 Wallet seleccionada: {best_wallet.pubkey()} con balance: {wallet_balances[best_wallet] / 1e9} SOL"
#     )
#     return best_wallet


# async def perform_sniping(
#     contract_address: str, keypairs: list[Keypair], amount_sol: float = 0.001
# ) -> str:
#     """Selects the wallet with the most balance and performs a sniping transaction using Jupiter."""
#     contract_address = await validate_contract_address(contract_address)
#     print(f"🎯 Iniciando sniping para contrato: {contract_address}")

#     best_wallet = await get_highest_balance_wallet(keypairs)
#     user_pubkey = best_wallet.pubkey()
#     amount_lamports = int(amount_sol * 1e9)

#     print(
#         f"🚀 Obteniendo mejor ruta para swap SOL ➝ {contract_address} por {amount_sol} SOL"
#     )
#     route = await get_best_quote(
#         "So11111111111111111111111111111111111111112", contract_address, amount_lamports
#     )
#     if not route:
#         return "❌ No se encontraron rutas de swap válidas."

#     print("📦 Obteniendo transacción de swap desde Jupiter...")
#     tx_bytes = await get_swap_transaction(route, str(user_pubkey))
#     if not tx_bytes:
#         return "❌ Error al obtener transacción de swap."

#     tx = VersionedTransaction.from_bytes(tx_bytes)
#     tx.sign([best_wallet])

#     print("📤 Enviando transacción a la red...")
#     tx_sig = solana_client.send_raw_transaction(
#         tx.serialize(), opts={"skip_preflight": True}
#     )
#     tx_hash = str(tx_sig.value)

#     print(f"✅ Sniping exitoso. Tx: {tx_hash}")
#     return f"✅ Sniping exitoso. Tx: {tx_hash}"


# /////////////////////////////////////////////////////////////////////////////////
import base64
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solana.rpc.async_api import AsyncClient  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Processed
from jupiter_python_sdk.jupiter import Jupiter  # ✅ Import Jupiter SDK
from telegram._bot import Bot  # ✅ Use the private `_bot` module from v22.1


import json
import os
import base58  # type: ignore
import aiohttp

from dotenv import load_dotenv  # type: ignore
import asyncio

import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN) if BOT_TOKEN else None


JUPITER_QUOTE_API = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

async_solana_client = AsyncClient(SOLANA_RPC_URL)


# async def keypair_for_jup_access(user_id: int) -> Keypair:
#     """Use a fixed raw base58 private key."""
#     raw_key = "2m9FwarnAA8tgHzzBRQyFUcqoq2e5h1EDYWAemmppKPaCqpNFxDhcCYVu4dmdij1hJ7Q4RFSkAdk1ekSuFT5PWkT"  # Replace with actual valid key
#     decoded_key = base58.b58decode(raw_key)
#     if not (32 <= len(decoded_key) <= 64):
#         raise ValueError(f"Invalid key length: {len(decoded_key)} (Expected 32 or 64)")
#     return Keypair.from_bytes(decoded_key)


async def load_user_private_keys(user_id: int, max_wallets: int = 5) -> list[str]:
    private_keys = []
    base_path = os.path.join("wallets", str(user_id))
    for wallet_index in range(max_wallets):
        wallet_path = os.path.join(base_path, f"wallet_{wallet_index}.json")
        if not os.path.exists(wallet_path):
            continue
        try:
            with open(wallet_path, "r") as f:
                data = json.load(f)
            private_key_b58 = data.get("private_key")
            if not private_key_b58:
                print(f"❌ Wallet {wallet_index} no tiene private_key")
                continue
            private_keys.append(private_key_b58)
        except Exception as e:
            print(f"❌ Error cargando wallet {wallet_index}: {e}")
    return private_keys


# async def initialize_jupiter_client(user_id: int) -> Jupiter:
#     keypair = await keypair_for_jup_access(user_id)
#
#     return Jupiter(
#         async_client=async_solana_client,
#         keypair=keypair,
#         quote_api_url="https://quote-api.jup.ag/v6/quote",  # NO trailing '?'
#         swap_api_url="https://quote-api.jup.ag/v6/swap",
#     )


async def get_sol_balance(pubkey: Pubkey, rpc_url: str = SOLANA_RPC_URL) -> int:
    async with AsyncClient(rpc_url) as client:
        try:
            resp = await client.get_balance(pubkey)
            return resp.value
        except Exception as e:
            print(f"❌ Error obteniendo balance para {pubkey}: {e}")
            return 0


def load_user_wallets(user_id: int, max_wallets: int = 5) -> list[Keypair]:
    keypairs = []
    base_path = os.path.join("wallets", str(user_id))
    for wallet_index in range(max_wallets):
        wallet_path = os.path.join(base_path, f"wallet_{wallet_index}.json")
        if not os.path.exists(wallet_path):
            continue
        try:
            with open(wallet_path, "r") as f:
                data = json.load(f)
            private_key_b58 = data.get("private_key")
            if not private_key_b58:
                print(f"❌ Wallet {wallet_index} no tiene private_key")
                continue
            private_key_bytes = base58.b58decode(private_key_b58)
            keypair = Keypair.from_bytes(private_key_bytes[:64])
            keypairs.append(keypair)
        except Exception as e:
            print(f"❌ Error cargando wallet {wallet_index}: {e}")
    return keypairs


async def get_highest_balance_wallet(keypairs: list[Keypair] | Keypair) -> Keypair:
    wallet_balances = {}
    if isinstance(keypairs, list):
        for kp in keypairs:
            pubkey = kp.pubkey()
            balance = await get_sol_balance(pubkey)
            wallet_balances[kp] = balance
            print(f"🔍 Wallet {pubkey} tiene balance: {balance / 1e9} SOL")
        best_wallet = max(wallet_balances, key=wallet_balances.get)
    elif isinstance(keypairs, Keypair):
        pubkey = keypairs.pubkey()
        balance = await get_sol_balance(pubkey)
        wallet_balances[keypairs] = balance
        print(f"🔍 Wallet {pubkey} tiene balance: {balance / 1e9} SOL")
        best_wallet = keypairs
    else:
        raise TypeError("Invalid type for keypairs. Expected list[Keypair] or Keypair.")

    print(
        f"💰 Wallet seleccionada: {best_wallet.pubkey()} con balance: {wallet_balances[best_wallet] / 1e9} SOL"
    )
    return best_wallet


async def perform_sniping(
    user_id: int,
    contract_address: str,
    keypairs: list[Keypair],
    amount_sol: float = 0.001,
) -> str:
    print(f"🎯 Iniciando sniping para contrato: {contract_address}")

    best_wallet = await get_highest_balance_wallet(keypairs)
    logger.info(f"Sniping attempt: User's best_wallet selected for Jupiter ops: {best_wallet.pubkey()}")
    user_pubkey = best_wallet.pubkey()
    amount_lamports = int(amount_sol * 1_000_000_000)

    # Fix slippage calculation
    slippage_percent = 10  # 10% max slippage
    slippage_percent = max(0.1, min(slippage_percent, 50))  # cap between 0.1% and 50%
    slippage_bps = int(slippage_percent * 100)  # Convert to basis points

    print(f"🎯 Slippage set to: {slippage_percent}% ({slippage_bps} BPS)")

    token_in = "So11111111111111111111111111111111111111112"  # SOL

    print(f"🚀 Requesting quote with amount {amount_lamports} lamports")
    print("DEBUG: quote params:")
    print(f"  - input_mint: {token_in}")
    print(f"  - output_mint: {contract_address}")
    print(f"  - amount: {amount_lamports}")
    print(f"  - slippage_bps: {slippage_bps}")

    # Try Jupiter SDK first, fallback to direct API if needed
    quote = None
    transaction_data_base64 = None

    async with AsyncClient("https://api.mainnet-beta.solana.com") as async_client:
        # Method 1: Try Jupiter SDK first
        try:
            print("🔄 Trying Jupiter SDK...")

            jupiter = Jupiter(
                async_client=async_client,
                keypair=best_wallet,
                quote_api_url="https://quote-api.jup.ag/v6/quote",
                swap_api_url="https://quote-api.jup.ag/v6/swap",
            )

            # Quick test with short timeout
            quote = await asyncio.wait_for(
                jupiter.quote(
                    input_mint=str(token_in),
                    output_mint=str(contract_address),
                    amount=int(amount_lamports),
                    slippage_bps=int(slippage_bps),
                ),
                timeout=10.0,
            )

            if quote and isinstance(quote, dict) and "inAmount" in quote:
                print("✅ Jupiter SDK quote successful")

                # Try swap with SDK
                amount_to_swap = int(quote["inAmount"])
                transaction_data_base64 = await asyncio.wait_for(
                    jupiter.swap(
                        input_mint=token_in,
                        output_mint=contract_address,
                        amount=amount_to_swap,
                        slippage_bps=slippage_bps,
                    ),
                    timeout=10.0,
                )

                if transaction_data_base64:
                    print("✅ Jupiter SDK swap successful")
                else:
                    print("⚠️ Jupiter SDK swap returned empty, trying direct API...")
                    quote = None  # Reset to try direct API
            else:
                print("⚠️ Jupiter SDK quote failed or empty, trying direct API...")
                quote = None

        except Exception as e:
            print(f"⚠️ Jupiter SDK failed: {e}")
            print("🔄 Falling back to direct API...")
            quote = None

        # Method 2: Direct API fallback
        if not quote or not transaction_data_base64:
            print("🔄 Using direct Jupiter API...")

            async with aiohttp.ClientSession() as session:
                try:
                    # Step 1: Get Quote via direct API
                    quote_url = "https://quote-api.jup.ag/v6/quote"
                    quote_params = {
                        "inputMint": token_in,
                        "outputMint": contract_address,
                        "amount": amount_lamports,
                        "slippageBps": slippage_bps,
                        "onlyDirectRoutes": "false",
                        "asLegacyTransaction": "false",
                    }

                    async with session.get(quote_url, params=quote_params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            print(f"❌ Quote API error {response.status}: {error_text}")
                            return f"❌ No se encontraron rutas de swap válidas: {error_text}"

                        quote_text = await response.text()
                        quote = json.loads(quote_text)

                    if "error" in quote:
                        print(f"❌ Quote error: {quote['error']}")
                        return "❌ No se encontraron rutas de swap válidas."

                    print("✅ Direct API quote successful")

                    # Step 2: Get Swap Transaction via direct API
                    swap_url = "https://quote-api.jup.ag/v6/swap"

                    # Try different configurations to avoid AMM compatibility issues
                    swap_configs = [
                        # Config 1: No shared accounts (for simple AMMs)
                        {
                            "quoteResponse": quote,
                            "userPublicKey": str(user_pubkey),
                            "wrapAndUnwrapSol": True,
                            "useSharedAccounts": False,  # Disable for simple AMMs
                            "prioritizationFeeLamports": "auto",
                            "asLegacyTransaction": False,
                        },
                        # Config 2: Shared accounts enabled (for complex AMMs)
                        {
                            "quoteResponse": quote,
                            "userPublicKey": str(user_pubkey),
                            "wrapAndUnwrapSol": True,
                            "useSharedAccounts": True,
                            "prioritizationFeeLamports": "auto",
                            "asLegacyTransaction": False,
                        },
                        # Config 3: Basic configuration
                        {
                            "quoteResponse": quote,
                            "userPublicKey": str(user_pubkey),
                            "wrapAndUnwrapSol": True,
                            "asLegacyTransaction": False,
                        },
                    ]

                    # Try each configuration until one works
                    for i, config in enumerate(swap_configs):
                        try:
                            print(f"🔄 Trying swap config {i + 1}/3...")

                            async with session.post(
                                swap_url,
                                json=config,
                                headers={"Content-Type": "application/json"},
                            ) as response:
                                if response.status == 200:
                                    swap_text = await response.text()
                                    swap_response = json.loads(swap_text)

                                    if "error" not in swap_response:
                                        transaction_data_base64 = swap_response.get(
                                            "swapTransaction"
                                        )
                                        if transaction_data_base64:
                                            print(
                                                f"✅ Swap successful with config {i + 1}"
                                            )
                                            break
                                else:
                                    error_text = await response.text()
                                    print(f"⚠️ Config {i + 1} failed: {error_text}")
                                    continue

                        except Exception as config_error:
                            print(f"⚠️ Config {i + 1} exception: {config_error}")
                            continue

                    if not transaction_data_base64:
                        return "❌ Error al obtener transacción de swap con todas las configuraciones."

                except Exception as e:
                    print(f"❌ Direct API error: {e}")
                    return f"❌ Error: {str(e)}"

        # Validate we have everything needed
        if not quote:
            return "❌ No se pudo obtener cotización."

        if not transaction_data_base64:
            return "❌ Error al obtener transacción de swap."

        print(f"✅ Quote: {quote}")
        print(f"✅ Transaction prepared: {transaction_data_base64[:50]}...")

        # Continue with transaction signing and sending
        try:
            versioned_tx = VersionedTransaction.from_bytes(
                base64.b64decode(transaction_data_base64)
            )

            logger.info(f"Sniping attempt: Signing transaction with wallet: {best_wallet.pubkey()}")
            signed_tx = VersionedTransaction(versioned_tx.message, [best_wallet])

            print("📤 Enviando transacción a la red...")
            opts = TxOpts(skip_preflight=True, preflight_commitment=Processed)

            tx_resp = await async_client.send_raw_transaction(
                bytes(signed_tx), opts=opts
            )

            tx_hash = None
            if hasattr(tx_resp, "value"):
                tx_hash = tx_resp.value
            elif isinstance(tx_resp, dict) and "result" in tx_resp:
                tx_hash = tx_resp["result"]
            elif isinstance(tx_resp, str):
                tx_hash = tx_resp
            else:
                raise Exception(f"Unexpected tx_resp type: {type(tx_resp)}")

            print(f"✅ Sniping exitoso. Tx hash: {tx_hash}")
            await message_for_user(
                user_id, amount_to_swap, tx_hash, user_pubkey, contract_address
            )
            return tx_hash

        except Exception as e:
            # print(f"❌ Error enviando transacción: {e}")
            return


async def message_for_user(user_id, amount, tx_hash, user_pubkey, contract_address):
    message = (
        f"🚀 **Sniping Success!** 🎉\n\n"
        f"🎯 You just executed a perfect **sniping trade**!\n"
        f"📍 **Contract Address:** `{contract_address}`\n"
        f"💰 **Amount:** `{amount} SOL`\n"
        f"🔗 **Transaction:** [View on Solscan](https://solscan.io/tx/{tx_hash})\n"
        f"🛠 **Wallet Used:** `{user_pubkey}`\n\n"
        f"🔥 You're making big moves in DeFi—keep going! 💎🚀"
    )

    await bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
    return message


# /////////////////////////////////////////


#async def mock_bot():
    raw_key = base58.b58decode(
        "2m9FwarnAA8tgHzzBRQyFUcqoq2e5h1EDYWAemmppKPaCqpNFxDhcCYVu4dmdij1hJ7Q4RFSkAdk1ekSuFT5PWkT"
    )
    keypair = Keypair.from_bytes(raw_key)
    keypairs = [keypair]

    contract_address = "BteyF35oaTPAqrQLj6W1ExYaEKs7Fgg162wTzpT7pump"

    amount_sol = 0.0001
    user_id = 6858772436

    result = await perform_sniping(user_id, contract_address, keypairs, amount_sol)
    print(result)


#if __name__ == "__main__":
    asyncio.run(mock_bot())
