import json
import os
from solders.keypair import Keypair  # type: ignore
from datetime import datetime
import base58  # type: ignore
from mnemonic import Mnemonic  # type: ignore
import struct  # type: ignore
import hashlib  # type: ignore
import hmac  # type: ignore


def get_wallet_path(user_id: int, wallet_index: int) -> str:
    """Constructs and returns the file path for a user's wallet."""
    return os.path.join("wallets", str(user_id), f"wallet_{wallet_index}.json")


def derive_phantom_key(seed, path="m/44'/501'/0'/0'"):
    """
    Derives private key using Phantom's derivation method
    """
    # Convert path to list of integers
    path_components = []
    for component in path.split("/"):
        if component == "m":
            continue
        if component.endswith("'"):
            component = int(component[:-1]) + 0x80000000
        else:
            component = int(component)
        path_components.append(component)

    # Derive key using path
    key = seed
    for component in path_components:
        # Use proper HMAC-SHA512 for each derivation step
        data = bytearray([0x00]) + key + struct.pack(">L", component)
        hmac_obj = hmac.new(b"ed25519 seed", data, hashlib.sha512)
        key = hmac_obj.digest()[:32]

    return key


async def create_solana_wallet():
    keypair = Keypair()
    print("Keypair:", keypair)

    # Get public key
    public_key = str(keypair.pubkey())
    print("Public Key:", public_key)
    seed = keypair.secret()

    mnemo = Mnemonic("english")
    mnemonic = mnemo.to_mnemonic(seed)
    print("Mnemonic:", mnemonic)
    # Generate seed from mnemonic with empty passphrase
    seed = mnemo.to_seed(mnemonic, passphrase="")

    private_key = derive_phantom_key(seed)
    print("Private Key:", private_key)

    mnemonic_phrase = mnemo.to_mnemonic(private_key)
    print("Mnemonic Phrase:", mnemonic_phrase)

    # Encode private key in base58
    private_key_bytes = bytes(keypair)
    print("Private Key Bytes:", private_key_bytes)
    private_key_b58 = base58.b58encode(private_key_bytes).decode("ascii")
    print("Private Key Base58:", private_key_b58)

    wallet_data = {
        "address": public_key,
        "private_key": private_key_b58,
        "mnemonic": mnemonic_phrase,
        "type": "solana",
    }

    print("Wallet Data:", json.dumps(wallet_data, indent=2))
    return wallet_data


def save_wallet(user_id: int, private_key, wallet_index: int) -> bool:
    """Saves the wallet's private key to a JSON file."""
    directory_path = os.path.join("wallets", str(user_id))
    os.makedirs(directory_path, exist_ok=True)

    file_path = get_wallet_path(user_id, wallet_index)

    try:
        wallet_data = {"private_key": private_key}

        with open(file_path, "w") as f:
            json.dump(wallet_data, f)
        return True
    except Exception as e:
        print(f"Error saving wallet: {e}")  # Basic error handling
        return False


def load_wallets(user_id: int) -> list[Keypair]:
    """Loads all wallets for a given user from the wallets directory."""

    directory_path = os.path.join("wallets", str(user_id))
    loaded_keypairs = []

    # Ensure directory exists
    if not os.path.exists(directory_path):
        print(f"No wallets found for user {user_id}.")
        return loaded_keypairs

    try:
        # Iterate through all wallet JSON files
        for filename in os.listdir(directory_path):
            if filename.startswith("wallet_") and filename.endswith(".json"):
                file_path = os.path.join(directory_path, filename)

                # Load wallet data
                with open(file_path, "r") as f:
                    wallet_data = json.load(f)
                    private_key = wallet_data.get("private_key")
                    print(f"Private_key loaded: {private_key}")

                    # Convert private key list to bytes and create Keypair
                    import base64

                    if private_key:
                        try:
                            # Decode from base64
                            private_key_bytes = base64.b64decode(private_key)
                            private_key_bytes = private_key_bytes[
                                :32
                            ]  # Keep only first 32 bytes

                            # Ensure correct length
                            if len(private_key_bytes) != 32:
                                print(
                                    f"❌ Error: Decoded key length is {len(private_key_bytes)}, expected 32 bytes."
                                )
                            else:
                                # Create Keypair from the private key bytes
                                keypair = Keypair.from_seed(private_key_bytes)
                                print(f"🎃 Keypair successfully created: {keypair}")
                                loaded_keypairs.append(keypair)

                        except Exception as e:
                            print(f"❌ Decoding error: {e}")

                    else:
                        print(f"Invalid private key format in {filename}")

    except Exception as e:
        print(f"Error loading wallets: {e}")  # Basic error handling

    # Return all loaded keypairs
    return loaded_keypairs


def get_next_wallet_index(user_id: int) -> int:
    """Determines the next available wallet index for a user."""
    directory_path = os.path.join("wallets", str(user_id))

    if not os.path.exists(directory_path):
        return 0

    max_index = -1
    try:
        for filename in os.listdir(directory_path):
            if filename.startswith("wallet_") and filename.endswith(".json"):
                try:
                    # Extract index from filename like "wallet_0.json"
                    index_str = filename.split("_")[1].split(".")[0]
                    index = int(index_str)
                    if index > max_index:
                        max_index = index
                except (IndexError, ValueError) as e:
                    print(
                        f"Could not parse wallet index from filename: {filename} due to {e}"
                    )
                    # Continue to next file if parsing fails for one
                    continue
    except Exception as e:
        print(f"Error listing or parsing wallet files: {e}")  # Basic error handling
        return 0  # Fallback to 0 in case of broader error

    return max_index + 1
