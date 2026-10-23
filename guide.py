"""Fetches MiniMax's H3 prompt-writing guide into the Studio's data folder, pinned to a commit and
checked by hash: python3 guide.py [data folder, default $DATA or ./data]. Not kept in this repo:
MiniMax's repo has no license file. Without it the Studio still writes the H3 format, from a short
summary. Exits 0 when the guide is in place, 1 when it couldn't be fetched."""
import hashlib
import os
import socket
import sys
import urllib.request

URL = ("https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/d21241f0a4b3acbb34c97dae47fa417b7065e438"
       "/skills/h3-prompt-writing/references/base-en.txt")
SHA256 = "2cfebc096a6e08370f288d468d90b60f7f9bcb938f94bf090816e910e48e75fc"
NAME = "h3-prompt-guide.txt"


def ipv4_only():
    """GitHub's and Hugging Face's CDNs hang over IPv6 on some networks: resolve to IPv4 only."""
    resolve = socket.getaddrinfo
    socket.getaddrinfo = lambda host, port, family=0, *a, **kw: resolve(host, port, socket.AF_INET, *a, **kw)


def fetch(folder):
    path = os.path.join(folder, NAME)
    try:
        with open(path, "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() == SHA256:
                return True
    except OSError:
        pass
    ipv4_only()
    for _ in range(3):
        try:
            with urllib.request.urlopen(URL, timeout=30) as r:
                data = r.read()
            break
        except OSError as e:
            error = e
    else:
        print(f"Couldn't fetch MiniMax's H3 prompt guide ({error}); the Studio writes motion prompts without it.",
              file=sys.stderr)
        return False
    if hashlib.sha256(data).hexdigest() != SHA256:
        print("MiniMax's H3 prompt guide doesn't match its pinned hash; not using it.", file=sys.stderr)
        return False
    os.makedirs(folder, exist_ok=True)
    with open(path + ".part", "wb") as f:
        f.write(data)
    os.replace(path + ".part", path)
    print(f"Saved {path}")
    return True


if __name__ == "__main__":
    sys.exit(0 if fetch(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATA", "data")) else 1)
