"""CLI: re-tagueia uma imagem GHCR de um ambiente pra outro, SEM rebuild.

Conceito central do CD imutável: a imagem que passou em `dev` é exatamente
a mesma byte-a-byte que vai pra `staging` e `prod`. Promoção é apenas
"adicionar uma nova tag" — nunca recompilação.

Uso:
    python -m tools.promote_release \\
        --from dev-<sha> \\
        --to staging-<sha> \\
        [--image ghcr.io/josercf/px4-sitl] \\
        [--registry ghcr.io] \\
        [--user $GITHUB_ACTOR] \\
        [--token $GITHUB_TOKEN]

Requer `docker` no PATH. Em CI, login no registry deve ter sido feito antes
via docker/login-action.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from typing import NoReturn

LOG = logging.getLogger("promote_release")


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    LOG.info("$ %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def promote(image: str, src_tag: str, dst_tag: str) -> int:
    """Re-tag de src_tag → dst_tag na imagem indicada.

    Returns:
        exit code: 0 sucesso, 1 falha.
    """
    src = f"{image}:{src_tag}"
    dst = f"{image}:{dst_tag}"

    # 1. Pull da imagem origem (valida que existe)
    LOG.info("validando imagem origem %s", src)
    pull = _run(["docker", "pull", src], check=False)
    if pull.returncode != 0:
        LOG.error("falha pulling %s: %s", src, pull.stderr)
        return 1

    # 2. Re-tag local
    LOG.info("retag %s → %s", src, dst)
    tag = _run(["docker", "tag", src, dst], check=False)
    if tag.returncode != 0:
        LOG.error("falha retagueando: %s", tag.stderr)
        return 1

    # 3. Push da nova tag
    LOG.info("push %s", dst)
    push = _run(["docker", "push", dst], check=False)
    if push.returncode != 0:
        LOG.error("falha pushing %s: %s", dst, push.stderr)
        return 1

    LOG.info("promoção concluída: %s agora referencia o mesmo sha de %s", dst, src)
    return 0


def main() -> NoReturn:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--from", dest="src", required=True, help="tag de origem (ex.: dev-abc123)")
    p.add_argument("--to", dest="dst", required=True, help="tag de destino (ex.: staging-abc123)")
    p.add_argument(
        "--image",
        default="ghcr.io/josercf/px4-sitl",
        help="imagem (default: ghcr.io/josercf/px4-sitl)",
    )
    args = p.parse_args()

    code = promote(args.image, args.src, args.dst)
    sys.exit(code)


if __name__ == "__main__":
    main()
