import hashlib


def calculate_hash(file_path: str) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify_integrity(file_path: str, stored_hash: str) -> bool:
    return calculate_hash(file_path) == stored_hash
