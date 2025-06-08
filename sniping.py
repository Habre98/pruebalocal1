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
