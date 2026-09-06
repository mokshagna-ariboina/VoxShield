import sys
from app.services.aasist_detector import AASISTDetector
from app.utils.audio import load_audio

print('Loading model...')
detector = AASISTDetector('aasist/config/AASIST.conf', 'weights/AASIST.pth', 'cpu')

def test_file(path, label):
    print(f'\n{"="*60}')
    print(f'FILE: {path}')
    print(f'LABEL: {label}')
    
    try:
        x, sr = load_audio(path, normalize=False)
        duration = len(x) / sr
        print(f'  Sample rate: {sr} Hz')
        print(f'  Duration: {duration:.3f} s')
    except Exception as e:
        print(f'  Could not read audio: {e}')

    res = detector.detect_file(path)
    print(f'  Raw scores: {res["raw_scores"]}')
    print(f'  Spoof prob: {res["raw_scores"]["spoof"]:.6f}')
    print(f'  Bona fide prob: {res["raw_scores"]["bonafide"]:.6f}')
    print(f'  Final clone_probability: {res["clone_probability"]:.6f}')
    print(f'  Predicted class: {"SPOOF (Clone)" if res["is_clone"] else "BONA FIDE (Human)"}')

# 1. Genuine Human
test_file('uploads/human.m4a.m4a', 'HUMAN (original test call)')

# 2. Synthetic (ElevenLabs)
test_file('uploads/neural.mp3', 'SYNTHETIC (ElevenLabs)')

