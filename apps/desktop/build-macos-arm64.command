#!/bin/bash
set -e
cd "$(dirname "$0")"
npm install
npm run dist:mac-arm64
echo "Built YoungAgent macOS arm64 ZIP in dist/"
