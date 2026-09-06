import sys
import soundfile as sf
from app.services.aasist_detector import AASISTDetector

print('Loading model...')
detector = AASISTDetector('aasist/config/AASIST.conf', 'weights/AASIST.pth', 'cpu')

def test_file(path, label):
    print(f'\n{"="*60}')
    print(f'FILE: {path}')
    print(f'LABEL: {label}')
    
    try:
        x_sf, sr = sf.read(path)
        duration = len(x_sf) / sr
        print(f'  Sample rate: {sr} Hz')
        print(f'  Duration: {duration:.3f} s')
    except Exception as e:
        print(f'  Could not read with soundfile: {e}')

    res = detector.detect_file(path)
    print(f'  Raw scores: {res["raw_scores"]}')
    print(f'  Spoof prob: {res["raw_scores"]["spoof"]:.6f}')
    print(f'  Bona fide prob: {res["raw_scores"]["bonafide"]:.6f}')
    print(f'  Final clone_probability: {res["clone_probability"]:.6f}')
    print(f'  Predicted class: {"SPOOF (Clone)" if res["is_clone"] else "BONA FIDE (Human)"}')

# 1. Genuine Human
test_file('uploads/0c2145c4-c502-4b0c-a3d8-cbfe6cf415de.wav', 'HUMAN (original test call)')

# 2. Synthetic (TTS)
test_file('test2.wav', 'SYNTHETIC (gTTS)')

# 3. Another Synthetic
test_file('test1.wav', 'SYNTHETIC 2 (gTTS)')

