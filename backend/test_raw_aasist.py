
import torch
import numpy as np
import librosa
from app.services.aasist_detector import AASISTDetector

detector = AASISTDetector('aasist/config/AASIST.conf', 'weights/AASIST.pth', 'cpu')

def test_file(path, label):
    y, sr = librosa.load(path, sr=16000, mono=True)
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
        
    target_length = 64600
    if len(y) > target_length:
        y = y[:target_length]
    else:
        y = np.pad(y, (0, target_length - len(y)), 'constant')
        
    tensor_audio = torch.FloatTensor(y).unsqueeze(0).to(detector.device)
    with torch.no_grad():
        _, logits = detector.model(tensor_audio)
        probs = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()[0]
        
    print(f'\n--- {label} ---')
    print('Raw logits (class 0, class 1):', logits.cpu().numpy()[0])
    print('Softmax probs (class 0, class 1):', probs)
    
    # Test the class function directly
    result = detector.detect(y, sr)
    print('Returned clone_probability:', result['clone_probability'])

test_file('uploads/0c2145c4-c502-4b0c-a3d8-cbfe6cf415de.wav', 'HUMAN CLIP (User Test Call)')
test_file('test2.wav', 'NEURAL CLIP (gTTS Test)')

