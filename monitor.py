name: Test Env

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Run test
        env:
          A: ${{ secrets.A }}
          B: ${{ secrets.B }}
          C: ${{ secrets.C }}
        run: python test.py
