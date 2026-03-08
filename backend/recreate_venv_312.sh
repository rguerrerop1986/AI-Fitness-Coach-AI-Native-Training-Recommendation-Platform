#!/usr/bin/env bash
# Recreate backend venv with Python 3.12 (3.12.13 preferred).
# Install Python 3.12.13 first, e.g.:
#   pyenv:  pyenv install 3.12.13 && pyenv local 3.12.13
#   brew:   brew install python@3.12
# Then set PYTHON_312 to your 3.12 binary if not in PATH as python3.12:
#   export PYTHON_312=/path/to/python3.12

set -e
cd "$(dirname "$0")"

PYTHON_312="${PYTHON_312:-python3.12}"
if ! command -v "$PYTHON_312" &>/dev/null; then
  echo "Python 3.12 not found. Install it first, e.g.:"
  echo "  pyenv install 3.12.13 && pyenv local 3.12.13"
  echo "  # or: brew install python@3.12"
  echo "Then run this script again, or set PYTHON_312=/path/to/python3.12"
  exit 1
fi

echo "Using: $($PYTHON_312 --version)"
echo "Removing old venv..."
rm -rf venv
echo "Creating new venv with Python 3.12..."
"$PYTHON_312" -m venv venv
source venv/bin/activate
echo "Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Done. Activate with: source venv/bin/activate"
