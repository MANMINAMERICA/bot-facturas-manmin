import re

def _parse_monto(text):
    text = text.replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0

def _find_amount_after_keyword(line, keywords):
    line_lower = line.lower()
    for kw in keywords:
        if kw in line_lower:
            idx = line_lower.index(kw) + len(kw)
            rest = line[idx:]
            print(f'  Keyword: {kw}, rest: [{rest}]')
            m = re.search(r'[$:\s]*([\d][\d\.\,]*)', rest)
            if m:
                print(f'  Match: {m.group(1)}')
                return _parse_monto(m.group(1))
    return 0.0

test_lines = [
    'SUBTOTAL: $ 22,400.00',
    'TOTAL: $ 22,400.00',
    'IVA 19%: 0.00',
]

for line in test_lines:
    print(f'Line: [{line}]')
    val = _find_amount_after_keyword(line, ['total', 'subtotal', 'iva'])
    print(f'  Result: {val}')
    print()
