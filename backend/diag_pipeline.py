import torch
import numpy as np
import json
import librosa
import soundfile as sf
from aasist.models.AASIST import Model

device = torch.device('cpu')
with open('aasist/config/AASIST.conf', 'r') as f:
    config = json.load(f)
model = Model(config.get('model_config', {})).to(device)
model.load_state_dict(torch.load('weights/AASIST.pth', map_location=device))
model.eval()

target_length = 64600

def official_pad(x, max_len=64600):
    """EXACT pad function from official data_utils.py (eval mode)"""
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    num_repeats = int(max_len / x_len) + 1
    padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
    return padded_x

def our_pad(x, max_len=64600):
    """What aasist_detector.py currently does"""
    if len(x) > max_len:
        x = x[:max_len]
    else:
        x = np.pad(x, (0, max_len - len(x)), 'constant')
    return x

def test_file(path, label):
    print(f'\n{"="*60}')
    print(f'FILE: {path}')
    print(f'LABEL: {label}')

    # === A. Load with soundfile (official method) ===
    try:
        x_sf, sr_sf = sf.read(path)
        print(f'  soundfile: sr={sr_sf}, shape={x_sf.shape}, dtype={x_sf.dtype}')
        print(f'  soundfile: duration={len(x_sf)/sr_sf:.3f}s, min={x_sf.min():.6f}, max={x_sf.max():.6f}')
    except Exception as e:
        print(f'  soundfile FAILED: {e}')
        x_sf = None

    # === B. Load with librosa (our method) ===
    y_lr, sr_lr = librosa.load(path, sr=16000, mono=True)
    print(f'  librosa: sr={sr_lr}, shape={y_lr.shape}, dtype={y_lr.dtype}')
    print(f'  librosa: duration={len(y_lr)/sr_lr:.3f}s, min={y_lr.min():.6f}, max={y_lr.max():.6f}')

    # Our normalization
    y_norm = y_lr.copy()
    if np.max(np.abs(y_norm)) > 0:
        y_norm = y_norm / np.max(np.abs(y_norm))
    print(f'  after our normalize: min={y_norm.min():.6f}, max={y_norm.max():.6f}')

    # === C. Compare padding strategies ===
    our_padded = our_pad(y_norm)
    print(f'  our_pad result: shape={our_padded.shape}')

    # Official uses soundfile raw at native sr
    if x_sf is not None and sr_sf == 16000:
        official_input = official_pad(x_sf)
        print(f'  official_pad(soundfile@16k): shape={official_input.shape}')
    elif x_sf is not None:
        print(f'  WARNING: soundfile sr={sr_sf}, NOT 16000 (official expects 16kHz FLAC)')

    # === D. Run model with OUR preprocessing ===
    tensor_ours = torch.FloatTensor(our_padded).unsqueeze(0).to(device)
    print(f'  tensor (our preprocess): shape={tensor_ours.shape}, dtype={tensor_ours.dtype}')
    with torch.no_grad():
        _, logits_ours = model(tensor_ours)
        probs_ours = torch.nn.functional.softmax(logits_ours, dim=1).cpu().numpy()[0]
    print(f'  OUR PREPROCESS -> logits={logits_ours.cpu().numpy()[0]}, probs={probs_ours}')

    # === E. Run model with OFFICIAL preprocessing (soundfile, no normalize, tile-pad) ===
    if x_sf is not None and sr_sf == 16000:
        official_input = official_pad(x_sf)
        tensor_official = torch.FloatTensor(official_input).unsqueeze(0).to(device)
        print(f'  tensor (official preprocess): shape={tensor_official.shape}, dtype={tensor_official.dtype}')
        with torch.no_grad():
            _, logits_off = model(tensor_official)
            probs_off = torch.nn.functional.softmax(logits_off, dim=1).cpu().numpy()[0]
        print(f'  OFFICIAL PREPROCESS -> logits={logits_off.cpu().numpy()[0]}, probs={probs_off}')

    # === F. Run with librosa but NO normalization, tile-pad ===
    if x_sf is not None and sr_sf == 16000:
        pass  # already covered by official
    else:
        # librosa at 16k, no normalize, tile-pad
        y_raw = y_lr.copy()  # librosa already resampled
        if len(y_raw) >= target_length:
            y_tiled = y_raw[:target_length]
        else:
            num_repeats = int(target_length / len(y_raw)) + 1
            y_tiled = np.tile(y_raw, num_repeats)[:target_length]
        tensor_raw = torch.FloatTensor(y_tiled).unsqueeze(0).to(device)
        with torch.no_grad():
            _, logits_raw = model(tensor_raw)
            probs_raw = torch.nn.functional.softmax(logits_raw, dim=1).cpu().numpy()[0]
        print(f'  LIBROSA NO-NORM TILE-PAD -> logits={logits_raw.cpu().numpy()[0]}, probs={probs_raw}')

# Test files
test_file('uploads/0c2145c4-c502-4b0c-a3d8-cbfe6cf415de.wav', 'HUMAN (original test call)')
test_file('test2.wav', 'SYNTHETIC (gTTS)')

# Also test the two most recently uploaded files if they exist
import os
uploads = sorted(
    [(f, os.path.getmtime(os.path.join('uploads', f))) for f in os.listdir('uploads') if f.endswith('.wav')],
    key=lambda x: x[1], reverse=True
)
if len(uploads) >= 2:
    test_file(os.path.join('uploads', uploads[0][0]), 'MOST RECENT UPLOAD')
    test_file(os.path.join('uploads', uploads[1][0]), 'SECOND MOST RECENT UPLOAD')
