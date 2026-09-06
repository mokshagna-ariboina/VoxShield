import asyncio
from app.services.aasist_detector import AASISTDetector

def run_diagnostic():
    aasist = AASISTDetector('aasist/config/AASIST.conf', 'weights/AASIST.pth', 'cpu')
    
    res_human = aasist.detect_file("uploads/human.m4a.m4a")
    res_neural = aasist.detect_file("uploads/neural.mp3")
    
    print(f"- human.m4a clone_probability: {res_human['clone_probability']}")
    print(f"- neural.mp3 clone_probability: {res_neural['clone_probability']}")

run_diagnostic()
