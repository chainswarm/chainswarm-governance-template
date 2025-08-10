# Miner Registry

Register your GitHub ↔ Hotkey mapping so your merged PRs can receive emissions.

## 1) Generate your nonce + signature (Python, uses your Bittensor wallet)

Run this locally (NOT in CI):

```bash
python tools/generate_registry_entry.py \
  --github your-github-handle \
  --wallet.name <coldkey_name> \
  --wallet.hotkey <hotkey_name> \
  --wallet.path ~/.bittensor/wallets
```

It prints a YAML block like:

```yaml
github: your-github-handle
hotkey_ss58: 5Fabc...            # your hotkey address
nonce: 82a0b7...                 # 32 bytes hex
signature_b64: z1aK...           # ed25519 over (nonce || hotkey_ss58), base64
```

Tip: you can verify the signature yourself with the official CLI:

```bash
btcli wallet verify \
  --message "$(python -c 'import sys,base64;import binascii;print(\"\" )')" # see script usage below
```

(We also verify automatically in CI on your registry PR.)

# 2) Add a file
Create registry/miners/<your-github-handle>.yaml with the content above and open a PR.
The registry CI will verify your signature and label your PR verified. Once merged, your mapping is active.

```https://github.com/chainswarm/chainswarm-governance-template/tree/main/tools```

If your local wallet prompts for a passphrase, unlock it when asked. The CLI btcli wallet sign can also verify the signature; see official docs. 
docs.learnbittensor.org
