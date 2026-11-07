#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${FAN_TOKEN_R_IMAGE:-gianvriz/green_bubbles@sha256:39586b764cbd2260aa0dbeed20cd16dd87b0833e97e6ce5210ae5f101af9c251}"
# An explicit mount of this standalone folder is the only host data exposed.
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e TZ=UTC -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 \
  -v "$TASK_ROOT:/project" -w /project/Code-and-Data \
  --entrypoint Rscript "$IMAGE" "${1:-run_all.R}"
