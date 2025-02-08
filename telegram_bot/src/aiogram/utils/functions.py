import re

def is_sha256(text):
    return bool(re.fullmatch(r'[a-fA-F0-9]{64}', text))
