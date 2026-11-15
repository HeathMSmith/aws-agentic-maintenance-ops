
#!/usr/bin/env bash
set -euo pipefail

# Resolve paths relative to this script.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build/lambda"
ZIP_FILE="$BUILD_DIR/aws-agentic-maintenance-lambda.zip"

# Create a temporary directory and remove it on exit.
STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

mkdir -p "$BUILD_DIR"

echo "Installing Lambda dependencies..."

python -m pip install \
  --requirement "$REPO_ROOT/requirements.txt" \
  --target "$STAGING_DIR" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.13 \
  --abi cp313 \
  --only-binary=:all: \
  --no-compile \
  --quiet

echo "Copying application source..."

cp "$REPO_ROOT/lambda_handler.py" "$STAGING_DIR/"
cp -R "$REPO_ROOT/agent" "$STAGING_DIR/"
cp -R "$REPO_ROOT/simulation" "$STAGING_DIR/"
cp -R "$REPO_ROOT/data" "$STAGING_DIR/"

# Remove development artifacts.
find "$STAGING_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$STAGING_DIR" -type f -name '*.pyc' -delete

# Exclude installed command-line scripts and environment-specific pip records.
# Lambda imports the Python packages directly and does not need these files.
rm -rf "$STAGING_DIR/bin"
find "$STAGING_DIR" -type f -name RECORD -path '*.dist-info/*' -delete

# Normalize file and directory timestamps for reproducible ZIP archives.
find "$STAGING_DIR" -exec touch -t 202001010000 {} +

echo "Creating deployment ZIP..."

rm -f "$ZIP_FILE"

(
  cd "$STAGING_DIR"
  find . -type f | LC_ALL=C sort | zip -q -X "$ZIP_FILE" -@
)

echo "Verifying ZIP integrity..."
unzip -tq "$ZIP_FILE"

echo
echo "Lambda package created:"
ls -lh "$ZIP_FILE"
