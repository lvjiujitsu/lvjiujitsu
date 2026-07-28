from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOTS = (
    ROOT / ".agents" / "skills",
    ROOT / ".claude" / "skills",
    ROOT / ".cursor" / "skills",
)


def load_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"Frontmatter ausente: {path.relative_to(ROOT)}")

    try:
        _, frontmatter, _ = content.split("---", 2)
    except ValueError as exc:
        raise ValueError(
            f"Frontmatter incompleto: {path.relative_to(ROOT)}"
        ) from exc

    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        raise ValueError(f"Frontmatter invalido: {path.relative_to(ROOT)}")
    for required_key in ("name", "description"):
        if not str(metadata.get(required_key, "")).strip():
            raise ValueError(
                f"Campo {required_key} ausente: {path.relative_to(ROOT)}"
            )
    return metadata


def validate_platform_coverage() -> set[str]:
    by_platform = {
        skill_root: {path.parent.name for path in skill_root.glob("*/SKILL.md")}
        for skill_root in SKILL_ROOTS
        if skill_root.exists()
    }
    missing_roots = [root for root in SKILL_ROOTS if root not in by_platform]
    if missing_roots:
        raise ValueError(
            "Diretorio de skills ausente: "
            + ", ".join(str(root.relative_to(ROOT)) for root in missing_roots)
        )

    expected = set().union(*by_platform.values())
    for skill_root, names in by_platform.items():
        missing = sorted(expected - names)
        if missing:
            raise ValueError(
                f"Skill(s) ausente(s) em {skill_root.relative_to(ROOT)}: "
                + ", ".join(missing)
            )

    canonical_root = ROOT / ".claude" / "skills"
    for name in sorted(expected):
        canonical = (canonical_root / name / "SKILL.md").read_bytes()
        for skill_root in SKILL_ROOTS:
            if skill_root == canonical_root:
                continue
            mirror = skill_root / name / "SKILL.md"
            if mirror.read_bytes() != canonical:
                raise ValueError(
                    f"Conteudo divergente da fonte: {mirror.relative_to(ROOT)}"
                )

    return expected


def validate_codex_metadata(names: set[str]) -> None:
    codex_root = ROOT / ".agents" / "skills"
    required_keys = {"display_name", "short_description", "default_prompt"}

    for name in sorted(names):
        path = codex_root / name / "agents" / "openai.yaml"
        if not path.is_file():
            raise ValueError(f"Metadado Codex ausente: {path.relative_to(ROOT)}")

        raw = path.read_bytes()
        if b"\xef\xbf\xbd" in raw:
            raise ValueError(
                f"Replacement character (encoding corrompido): {path.relative_to(ROOT)}"
            )
        if b"\r\n" in raw:
            raise ValueError(
                f"Fim de linha CRLF, esperado LF: {path.relative_to(ROOT)}"
            )

        payload = yaml.safe_load(raw.decode("utf-8"))
        interface = (payload or {}).get("interface")
        if not isinstance(interface, dict):
            raise ValueError(f"Bloco 'interface' ausente: {path.relative_to(ROOT)}")
        missing = sorted(required_keys - set(interface))
        if missing:
            raise ValueError(
                f"Chave(s) ausente(s) em {path.relative_to(ROOT)}: {', '.join(missing)}"
            )


def validate_agents() -> int:
    agent_root = ROOT / ".claude" / "agents"
    if not agent_root.is_dir():
        raise ValueError("Diretorio de agentes ausente: .claude/agents")

    agent_files = sorted(agent_root.glob("*.md"))
    if not agent_files:
        raise ValueError("Nenhum agente encontrado em .claude/agents")

    for path in agent_files:
        metadata = load_frontmatter(path)
        for required_key in ("tools", "model"):
            if not str(metadata.get(required_key, "")).strip():
                raise ValueError(
                    f"Campo {required_key} ausente: {path.relative_to(ROOT)}"
                )
        if metadata["name"] != path.stem:
            raise ValueError(
                f"Campo name diverge do arquivo: {path.relative_to(ROOT)}"
            )
        if metadata["model"] not in {"opus", "sonnet", "haiku", "inherit"}:
            raise ValueError(
                f"Modelo desconhecido em {path.relative_to(ROOT)}: {metadata['model']}"
            )

    return len(agent_files)


def main() -> int:
    skill_files = sorted(
        path
        for skill_root in SKILL_ROOTS
        if skill_root.exists()
        for path in skill_root.glob("*/SKILL.md")
    )
    if not skill_files:
        raise ValueError("Nenhuma skill encontrada.")

    for skill_file in skill_files:
        load_frontmatter(skill_file)
        print(f"[OK] {skill_file.relative_to(ROOT)}")

    names = validate_platform_coverage()
    print(f"[OK] {len(names)} skill(s) nas {len(SKILL_ROOTS)} plataformas: " + ", ".join(sorted(names)))

    validate_codex_metadata(names)
    print(f"[OK] {len(names)} metadado(s) Codex integro(s) em UTF-8 com LF.")

    agents = validate_agents()
    print(f"[OK] {agents} agente(s) em .claude/agents com frontmatter valido.")

    print(f"{len(skill_files)} arquivo(s) de skill validado(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
