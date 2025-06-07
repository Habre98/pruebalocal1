# import httpx

# input_mint = "So11111111111111111111111111111111111111112"
# output_mint = "BteyF35oaTPAqrQLj6W1ExYaEKs7Fgg162wTzpT7pump"  # Example token mint
# amount = str(100_000)  # lamports
# slippage_bps = 50

# url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={slippage_bps}"

# print(f"Requesting quote URL:\n{url}")

# response = httpx.get(url)
# print(f"Status: {response.status_code}")
# print(f"Content:\n{response.text}")

# try:
#     data = response.json()
#     print("JSON response:", data)
# except Exception as e:
#     print("JSON decode error:", e)


import aiohttp


async def debug_jupiter_api():
    url = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint": token_in,
        "outputMint": contract_address,
        "amount": amount_lamports,
        "slippageBps": slippage_bps,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Response: {text}")
