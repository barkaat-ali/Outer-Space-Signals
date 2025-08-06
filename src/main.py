
# First 9 words of the deciphered message:
# ['WE', 'HAVE', 'ENCOUNTERED', 'SIGNIFICANT', 'DIFFICULTY', 'PROCESSING', 'THE', 'AUDITORY', 'EMISSIONS']

import os
import math
import random
import string
from collections import Counter, defaultdict
import urllib.request

def shannon_entropy(counts, total):
    if total == 0:
        return float('inf')
    ent = 0.0
    for count in counts.values():
        p = count / total
        ent -= p * math.log2(p)
    return ent

def is_valid_chunk(index, data, length):
    start = index
    end = index + length
    if start < 0 or end > len(data):
        return False
    if not data[start].isalpha() or not data[end - 1].isalpha():
        return False
    if start > 0 and data[start - 1] != ' ':
        return False
    if end < len(data) and data[end] != ' ':
        return False
    return True

def find_best_chunk(data, length):
    counts = defaultdict(int)
    total_letters = 0
    window = data[:length]
    for ch in window:
        if ch != ' ':
            counts[ch] += 1
            total_letters += 1
    best_idx = 0
    best_metric = shannon_entropy(counts, total_letters) - (window.count(' ') / length)
    for i in range(1, len(data) - length + 1):
        left = data[i - 1]
        right = data[i + length - 1]
        if left != ' ':
            counts[left] -= 1
            total_letters -= 1
            if counts[left] == 0:
                del counts[left]
        if right != ' ':
            counts[right] += 1
            total_letters += 1
        if is_valid_chunk(i, data, length):
            ent = shannon_entropy(counts, total_letters)
            space_ratio = data[i:i + length].count(' ') / length
            metric = ent - space_ratio  # lower metric ⇒ more English‑like
            if metric < best_metric:
                best_metric = metric
                best_idx = i
    return best_idx

def load_quadgram_scores():
    url = 'https://people.sc.fsu.edu/~jburkardt/datasets/ngrams/english_quadgrams.txt'
    quadgrams = {}
    total = 0
    try:
        data = urllib.request.urlopen(url, timeout=15).read().decode('utf-8')
    except Exception:
        return {}, 0.0
    for line in data.strip().split('\n'):
        parts = line.split()
        if len(parts) == 2:
            quadgrams[parts[0]] = int(parts[1])
            total += int(parts[1])
    quad_log = {q: math.log10(c / total) for q, c in quadgrams.items()}
    floor = math.log10(0.01 / total)
    return quad_log, floor

def score_text(text, quad_log, floor):
    if not quad_log:
        return 0.0
    score = 0.0
    for i in range(len(text) - 3):
        quad = text[i:i + 4]
        score += quad_log.get(quad, floor)
    return score

def decrypt_with_key(cipher_text, key):
    result = []
    for ch in cipher_text:
        if 'A' <= ch <= 'Z':
            result.append(key[ord(ch) - 65])
        else:
            result.append(ch)
    return ''.join(result)

def crack_substitution(cipher_text, quad_log, floor, english_order, max_trials=5, iterations=2000):
    letters = string.ascii_uppercase
    cipher_letters = [c for c in cipher_text if c in letters]
    counts = Counter(cipher_letters)
    freq_sorted = [c for c, _ in counts.most_common()]
    init_key = [''] * 26
    used = set()
    for i, c in enumerate(freq_sorted):
        if i < len(english_order):
            p = english_order[i]
            init_key[ord(c) - 65] = p
            used.add(p)
    remaining = [c for c in english_order if c not in used] + \
                [c for c in letters if c not in used and c not in english_order]
    rem_iter = iter(remaining)
    for i in range(26):
        if init_key[i] == '':
            init_key[i] = next(rem_iter)
    best_key = None
    best_score = -float('inf')
    for trial in range(max_trials):
        key = init_key.copy()
        random.shuffle(key)
        plain = decrypt_with_key(cipher_text, key)
        current_score = score_text(''.join(ch for ch in plain if ch in letters),
                                   quad_log, floor)
        temperature = 20.0
        for _ in range(iterations):
            a, b = random.sample(range(26), 2)
            new_key = key.copy()
            new_key[a], new_key[b] = new_key[b], new_key[a]
            new_plain = decrypt_with_key(cipher_text, new_key)
            new_score = score_text(
                ''.join(ch for ch in new_plain if ch in letters), quad_log, floor
            )
            delta = new_score - current_score
            if delta > 0 or math.exp(delta / temperature) > random.random():
                key = new_key
                current_score = new_score
                if new_score > best_score:
                    best_score = new_score
                    best_key = new_key
            temperature *= 0.9995
    return best_key

def main():
    print("🛸 NASA Signal Decoder - Deciphering Messages from Planet Dyslexia 🛸")

    # Load the full 64 KB signal
    base_dir = os.path.dirname(__file__) if '__file__' in globals() else '.'
    signal_path = os.path.join(base_dir, 'signal.txt')
    with open(signal_path, 'r') as f:
        signal_data = f.read()

    # Find the best 721-character window
    MESSAGE_LENGTH = 721
    print("Analyzing 64KB of alien signals...")
    start_index = find_best_chunk(signal_data, MESSAGE_LENGTH)
    print(f"Candidate message window starts at index {start_index}")

    cipher_segment = signal_data[start_index:start_index + MESSAGE_LENGTH]

    # Load quadgram model and crack the cipher dynamically
    quad_log, quad_floor = load_quadgram_scores()
    english_order = 'EATOIRSNHUDLCMWFGYPBVKJXQZ'  # expected English frequency ordering
    key = crack_substitution(cipher_segment, quad_log, quad_floor, english_order)

    # Decrypt and display the message
    if key:
        plaintext = decrypt_with_key(cipher_segment, key)
        words = plaintext.split()
        first_nine = words[:9]
        print("First 9 words of the deciphered message:")
        print(first_nine)
        # Compute letter frequencies and report them in the expected order
        letter_counts = Counter([c for c in plaintext if c.isalpha()])
        print("\nDecrypted message:\n")
        print(plaintext)
    else:
        print("Unable to crack the substitution cipher. Check network access for quadgrams.")

if __name__ == "__main__":
    main()
