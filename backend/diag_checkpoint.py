import torch
import sys

ckpt_path = 'weights/AASIST.pth'
state_dict = torch.load(ckpt_path, map_location='cpu')

print('=== CHECKPOINT STRUCTURE ===')
print(f'Type: {type(state_dict)}')
if isinstance(state_dict, dict) and 'state_dict' in state_dict:
    print('Nested state_dict detected, unwrapping...')
    state_dict = state_dict['state_dict']
elif isinstance(state_dict, dict) and 'model' in state_dict:
    print('Nested model key detected, unwrapping...')
    state_dict = state_dict['model']

print(f'Number of keys: {len(state_dict)}')
print()

print('=== ALL KEYS ===')
for k in sorted(state_dict.keys()):
    v = state_dict[k]
    print(f'  {k}: shape={list(v.shape)}, dtype={v.dtype}')

print()
print('=== OUTPUT LAYER (out_layer) ===')
for k, v in state_dict.items():
    if 'out_layer' in k:
        print(f'  {k}: shape={list(v.shape)}, dtype={v.dtype}')
        print(f'    values: {v}')

print()
print(f'Total checkpoint params: {sum(p.numel() for p in state_dict.values())}')
