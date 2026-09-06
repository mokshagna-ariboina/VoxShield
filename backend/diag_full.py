import torch
import numpy as np
import json
import librosa
from aasist.models.AASIST import Model

# === 1. WEIGHT LOADING CHECK ===
with open('aasist/config/AASIST.conf', 'r') as f:
    config = json.load(f)
d_args = config.get('model_config', {})

model = Model(d_args)
state_dict = torch.load('weights/AASIST.pth', map_location='cpu')

# Check for missing and unexpected keys
model_keys = set(model.state_dict().keys())
ckpt_keys = set(state_dict.keys())

missing = model_keys - ckpt_keys
unexpected = ckpt_keys - model_keys

print('=== WEIGHT LOADING ===')
print(f'Model parameters: {sum(p.numel() for p in model.parameters())}')
print(f'Checkpoint parameters: {sum(v.numel() for v in state_dict.values())}')
print(f'Model keys: {len(model_keys)}')
print(f'Checkpoint keys: {len(ckpt_keys)}')
print(f'Missing keys (in model but NOT in checkpoint): {len(missing)}')
for k in sorted(missing):
    print(f'  MISSING: {k}')
print(f'Unexpected keys (in checkpoint but NOT in model): {len(unexpected)}')
for k in sorted(unexpected):
    print(f'  UNEXPECTED: {k}')

# Actually load and check result
result = model.load_state_dict(state_dict, strict=False)
print(f'\nload_state_dict result:')
print(f'  missing_keys: {result.missing_keys}')
print(f'  unexpected_keys: {result.unexpected_keys}')

# Check if any params are still random (not loaded)
model.eval()

# === 2. OUTPUT LAYER ANALYSIS ===
print('\n=== OUTPUT LAYER ===')
print(f'out_layer: Linear(in={model.out_layer.in_features}, out={model.out_layer.out_features})')
print(f'out_layer.weight shape: {model.out_layer.weight.shape}')
print(f'out_layer.bias: {model.out_layer.bias.data}')

# === 3. CONV_TIME (SincConv) ANALYSIS ===
print('\n=== SINC CONV (conv_time) ===')
print(f'out_channels: {model.conv_time.out_channels}')
print(f'kernel_size: {model.conv_time.kernel_size}')
print(f'sample_rate: {model.conv_time.sample_rate}')
print(f'band_pass is nn.Parameter: {isinstance(model.conv_time.band_pass, torch.nn.Parameter)}')
print(f'band_pass shape: {model.conv_time.band_pass.shape}')
print(f'band_pass requires_grad: {model.conv_time.band_pass.requires_grad if isinstance(model.conv_time.band_pass, torch.nn.Parameter) else "N/A (buffer)"}')

# === 4. DROPOUT STATE IN EVAL MODE ===
print('\n=== DROPOUT IN EVAL MODE ===')
print(f'model.training: {model.training}')
print(f'drop.training: {model.drop.training}')
print(f'drop_way.training: {model.drop_way.training}')
