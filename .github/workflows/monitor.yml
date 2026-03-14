name: Token Monitor

on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install requests

      - name: Run monitor
        env:
          A: ${{ secrets.A }}
          B: ${{ secrets.B }}
          C: ${{ secrets.C }}
        run: python monitor.py
