#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIKI_SRC_DIR="${ROOT_DIR}/docs/wiki-seed"
TMP_DIR="${TMPDIR:-/tmp}/labtelemetry-wiki-publish"
WIKI_REPO_URL="https://github.com/Roberton003/labtelemetry.wiki.git"

rm -rf "${TMP_DIR}"

if ! git ls-remote "${WIKI_REPO_URL}" >/dev/null 2>&1; then
  echo "Wiki repository not available yet."
  echo "Open https://github.com/Roberton003/labtelemetry/wiki and create the first page in the GitHub UI."
  echo "After that, rerun this script."
  exit 1
fi

git clone "${WIKI_REPO_URL}" "${TMP_DIR}"
find "${TMP_DIR}" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp "${WIKI_SRC_DIR}"/*.md "${TMP_DIR}/"
mkdir -p "${TMP_DIR}/assets"
cp "${ROOT_DIR}/docs/assets/"* "${TMP_DIR}/assets/"
find "${TMP_DIR}/assets" -type f -exec chmod 644 {} +

cd "${TMP_DIR}"
git add .

if git diff --cached --quiet; then
  echo "No wiki changes to publish."
  exit 0
fi

git commit -m "docs: publish initial wiki pages"
git push origin HEAD

echo "Wiki published to https://github.com/Roberton003/labtelemetry/wiki"
