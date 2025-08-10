# Miner Registry

Add a file at `registry/miners/{github}.yaml`:

```yaml
github: your-handle
hotkey_ss58: 5Fabc...
nonce: 82a0b7f8e2f1... (32 bytes hex)
signature_b64: z1aK... (ed25519 over (nonce || hotkey_ss58))
