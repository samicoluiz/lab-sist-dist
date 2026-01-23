#!/usr/bin/env python3
import json
from client import enviar_query

with open('config.local.json') as f:
    nos = json.load(f)['nodes']

# Testar cada nó
for i, no in enumerate(nos):
    print(f"\n=== Testando Nó {i} ({no['ip']}:{no['port']}) ===")
    resultado = enviar_query(no, "SELECT * FROM users")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
