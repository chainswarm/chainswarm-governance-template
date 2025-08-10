# Miner Registry

Add a file at `registry/miners/{github}.yaml`:

```yaml
github: your-handle
hotkey_ss58: 5Fabc...
nonce: 82a0b7f8e2f1... (32 bytes hex)
signature_b64: z1aK... (ed25519 over (nonce || hotkey_ss58))
```

Generate nonce randomly.

Sign nonce || hotkey_ss58 with your hotkey.

Submit PR; CI will verify the signature and label your PR verified.
Once merged, your GitHub ↔ hotkey mapping is active.
