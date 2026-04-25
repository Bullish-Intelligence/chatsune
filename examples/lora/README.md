# LoRA Example

Configure `config/server-config.yaml`:

```yaml
vllm:
  enable_lora: true
  lora_modules:
    - lint=/models/adapters/lint
```

Then start the stack normally and optionally load more adapters dynamically:
- `python scripts/adapter_manager.py --name lint --path /models/adapters/lint`
