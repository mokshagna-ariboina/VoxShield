import sys
import argparse
import json
import torch
import numpy as np
from app.utils.audio import load_audio
from aasist.models.AASIST import Model

def _tile_pad(x: np.ndarray, max_len: int = 64600) -> np.ndarray:
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    num_repeats = int(max_len / x_len) + 1
    padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
    return padded_x

def main():
    if len(sys.argv) < 2:
        print("Usage: python diag_independent.py <audio_path>")
        sys.exit(1)
        
    path = sys.argv[1]
    
    # 1. Load Audio
    try:
        audio, sr = load_audio(path, target_sr=16000, normalize=False)
        duration = len(audio) / sr
    except Exception as e:
        print(f"Failed to read audio: {e}")
        sys.exit(1)

    # 2. Load Model
    config_path = 'aasist/config/AASIST.conf'
    checkpoint_path = 'weights/AASIST.pth'
    device = torch.device('cpu')
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    model = Model(config['model_config']).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    # 3. Inference
    padded_audio = _tile_pad(audio, 64600)
    tensor_audio = torch.FloatTensor(padded_audio).unsqueeze(0).to(device)
    
    with torch.no_grad():
        _, logits = model(tensor_audio)
        probs = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()[0]
        logits = logits.cpu().numpy()[0]
        
    spoof_prob = float(probs[0])
    bonafide_prob = float(probs[1])
    is_clone = spoof_prob > 0.5
    pred_class = 'SPOOF (Clone)' if is_clone else 'BONA FIDE (Human)'
    
    print(f"FILE: {path}")
    print(f"SAMPLE RATE: {sr} Hz")
    print(f"DURATION: {duration:.3f} s")
    print(f"RAW LOGITS: {logits.tolist()}")
    print(f"SPOOF PROB: {spoof_prob:.6f}")
    print(f"BONA FIDE PROB: {bonafide_prob:.6f}")
    print(f"PREDICTED CLASS: {pred_class}")
    print("-" * 40)

if __name__ == '__main__':
    main()
