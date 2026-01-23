#!/bin/bash
IPS=()
while IFS= read -r line; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IPS+=("$line")
done < ips.txt

echo "Total IPs: ${#IPS[@]}"
echo "IPs: ${IPS[@]}"
for i in "${!IPS[@]}"; do
    echo "  [$i] = ${IPS[$i]}"
done
