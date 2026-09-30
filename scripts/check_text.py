"""Mechanical preflight only; semantic approval requires reference 16 Gate."""
import argparse
import hashlib
import json
from pathlib import Path

BANNED = ('小老板', '朋友圈', '钱', '本质上', '抠', '抠门', '黑心', '坑人', '垃圾公司', '吸血', '恶心', '缺德', '压榨')
PREFIX = '小老板-标题：'

def normalize(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')

def inspect(text, original=None, limit=1000, mode='write'):
    final = normalize(text)
    exempt = 3 if final.startswith(PREFIX) else 0
    hits = []
    for word in BANNED:
        start = 0
        while True:
            index = final.find(word, start)
            if index < 0:
                break
            start = index + 1
            if word == '小老板' and index == 0 and exempt:
                continue
            line = final.count('\n', 0, index) + 1
            col = index - final.rfind('\n', 0, index)
            hits.append({'word': word, 'codepoint_offset': index, 'line': line, 'column': col})
    result = {
        'mode': mode, 'count': len(final), 'limit': limit,
        'within_limit': len(final) <= limit,
        'banned_hits': sorted(hits, key=lambda h: (h['codepoint_offset'], h['word'])),
        'sha256_lf_utf8': hashlib.sha256(final.encode('utf-8')).hexdigest(),
        'mechanical_pass': len(final) <= limit and not hits,
        'semantic_gate': 'NOT_EVALUATED: reference 16 required; mechanical pass is not delivery approval',
    }
    if original is not None:
        before = len(normalize(original))
        result.update(original_count=before, delta=len(final)-before,
                      growth_review_required=len(final)>before)
    elif mode == 'edit':
        result['growth_status'] = 'UNVERIFIED: original missing'
    return result

def read(path):
    # Preserve whitespace and BOM if present: they count in the final text.
    with Path(path).open('r', encoding='utf-8', newline='') as f:
        return f.read()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file')
    parser.add_argument('--original')
    parser.add_argument('--limit', type=int, default=1000)
    parser.add_argument('--mode', choices=('write','edit','review'), default='write')
    args = parser.parse_args()
    if not 0 < args.limit <= 1000:
        parser.error('limit must be between 1 and 1000')
    result = inspect(read(args.file), read(args.original) if args.original else None, args.limit, args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['mechanical_pass'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
