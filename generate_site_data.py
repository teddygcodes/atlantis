#!/usr/bin/env python3
from pathlib import Path

DATA_TS_PATH = Path("lib/data.ts")


def generate_ts() -> str:
    lines = DATA_TS_PATH.read_text(encoding="utf-8").splitlines()

    exports = {
        "DEBATES": any(line.startswith("export const DEBATES") for line in lines),
        "HYPOTHESES": any(line.startswith("export const HYPOTHESES") for line in lines),
        "CLAIMS": any(line.startswith("export const CLAIMS") for line in lines),
        "Debate": any(line.startswith("export interface Debate") or line.startswith("export type Debate") for line in lines),
        "Hypothesis": any(line.startswith("export interface Hypothesis") or line.startswith("export type Hypothesis") for line in lines),
        "Claim": any(line.startswith("export interface Claim") or line.startswith("export type Claim") for line in lines),
    }

    if exports["DEBATES"]:
        if not exports["CLAIMS"]:
            lines.append("export const CLAIMS = DEBATES;")
        if not exports["Claim"] and exports["Debate"]:
            lines.append("export type Claim = Debate;")
        if not exports["HYPOTHESES"]:
            lines.append("export const HYPOTHESES = DEBATES;")
        if not exports["Hypothesis"] and exports["Debate"]:
            lines.append("export type Hypothesis = Debate;")
    elif exports["HYPOTHESES"]:
        if not exports["DEBATES"]:
            lines.append("export const DEBATES = HYPOTHESES;")
        if not exports["Debate"] and exports["Hypothesis"]:
            lines.append("export type Debate = Hypothesis;")
        if not exports["CLAIMS"]:
            lines.append("export const CLAIMS = DEBATES;")
        if not exports["Claim"]:
            lines.append("export type Claim = Debate;")

    return "\n".join(lines) + "\n"


def main() -> None:
    DATA_TS_PATH.write_text(generate_ts(), encoding="utf-8")
    print(f"Generated {DATA_TS_PATH}")


if __name__ == "__main__":
    main()
