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

2) Add a file
Create registry/miners/<your-github-handle>.yaml with the content above and open a PR.
The registry CI will verify your signature and label your PR verified. Once merged, your mapping is active.



# 2) `tools/generate_registry_entry.py` (Bittensor wallet → nonce + signature)

> Works with the modern **`bittensor`** SDK wallet. It loads your **hotkey** from `--wallet.name/--wallet.hotkey/--wallet.path`, signs `nonce||hotkey_ss58` with **ed25519**, and prints the YAML for `registry/miners/*.yaml`. If your local install differs, you can alternatively use `btcli wallet sign` (official) — kept in the comments. :contentReference[oaicite:1]{index=1}

```python
#!/usr/bin/env python3
import os, sys, base64, binascii, argparse, secrets, textwrap

def main():
    ap = argparse.ArgumentParser(description="Generate miner registry YAML using your Bittensor hotkey")
    ap.add_argument("--github", required=True, help="your GitHub handle (without @)")
    ap.add_argument("--wallet.name", dest="wname", required=True, help="Bittensor coldkey name")
    ap.add_argument("--wallet.hotkey", dest="whot", required=True, help="Bittensor hotkey name")
    ap.add_argument("--wallet.path", dest="wpath", default="~/.bittensor/wallets", help="Wallet path (default: ~/.bittensor/wallets)")
    ap.add_argument("--nonce", help="optional 32-byte hex nonce; if omitted, a secure random nonce is generated")
    args = ap.parse_args()

    try:
        import bittensor as bt
    except Exception as e:
        print("ERROR: `bittensor` package not found. Install with: pip install bittensor", file=sys.stderr)
        sys.exit(2)

    # Resolve path & load wallet
    wpath = os.path.expanduser(args.wpath)
    wallet = bt.wallet(name=args.wname, hotkey=args.whot, path=wpath)  # wallet loader; will prompt if encrypted

    # obtain hotkey address
    try:
        hotkey_ss58 = wallet.hotkey.ss58_address
    except Exception as e:
        print(f"ERROR: could not read hotkey ss58 address from wallet: {e}", file=sys.stderr)
        sys.exit(3)

    # nonce: 32 random bytes hex if not provided
    if args.nonce:
        try:
            nonce_bytes = binascii.unhexlify(args.nonce)
            if len(nonce_bytes) != 32:
                raise ValueError("nonce must be exactly 32 bytes in hex")
        except Exception as e:
            print(f"ERROR: invalid --nonce: {e}", file=sys.stderr)
            sys.exit(4)
    else:
        nonce_bytes = secrets.token_bytes(32)

    # message = nonce || hotkey_ss58 (UTF-8)
    msg = nonce_bytes + hotkey_ss58.encode("utf-8")

    # sign with hotkey
    try:
        # modern Bittensor wallet hotkey exposes ed25519 signing via .sign()
        signature_bytes = wallet.hotkey.sign(msg)
    except Exception as e:
        print(f"ERROR: failed to sign with wallet hotkey: {e}", file=sys.stderr)
        print("\nIf your environment differs, you can sign with the official CLI instead:\n"
              "  btcli wallet sign --message <hex_of_msg> --address <hotkey_ss58>\n"
              "Where <hex_of_msg> is hex(nonce||hotkey_ss58).", file=sys.stderr)
        sys.exit(5)

    sig_b64 = base64.b64encode(signature_bytes).decode("utf-8")
    nonce_hex = binascii.hexlify(nonce_bytes).decode("utf-8")

    yaml = textwrap.dedent(f"""\
    github: {args.github}
    hotkey_ss58: {hotkey_ss58}
    nonce: {nonce_hex}
    signature_b64: {sig_b64}
    """)
    print(yaml)

    # helper: also print the exact hex message for manual verification if needed
    print("# message_hex:", (binascii.hexlify(msg).decode("utf-8")), file=sys.stderr)

if __name__ == "__main__":
    main()
```

If your local wallet prompts for a passphrase, unlock it when asked. The CLI btcli wallet sign can also verify the signature; see official docs. 
docs.learnbittensor.org
