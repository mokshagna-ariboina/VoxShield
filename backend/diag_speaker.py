import asyncio
from app.services.speaker_verifier import SpeakerVerifier

def test():
    verifier = SpeakerVerifier()
    audio = "uploads/human.m4a.m4a"
    emb1 = verifier.extract_embedding(audio)
    import pickle
    emb_bytes = pickle.dumps(emb1)
    
    res = verifier.verify(audio, emb_bytes)
    print(res)

test()
