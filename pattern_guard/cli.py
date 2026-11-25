"""pattern-guard command line.

  pattern-guard check quiz.json            check every MCQ and sort task
  pattern-guard check --key BDACABDC       check a bare answer key
  pattern-guard fix quiz.json -o fixed.json --seed 7
  pattern-guard plan 12 --options 4        print a fresh pattern-free key
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import LETTERS, Report, analyse, plan_key
from .quiz import check_mcq, check_sort, fix_file, load

RED, AMBER, GREEN, DIM, RESET = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def _colour(on: bool):
    return (lambda c, s: f"{c}{s}{RESET}") if on else (lambda c, s: s)


def print_report(label: str, rep: Report, paint) -> None:
    status = paint(GREEN, "clean") if rep.clean else (paint(AMBER, "warnings") if rep.ok else paint(RED, "PATTERN"))
    print(f"{label}  {paint(DIM, rep.key_letters())}  {status}")
    for f in rep.findings:
        mark = paint(RED, "✗") if f.severity == "fail" else paint(AMBER, "!")
        print(f"  {mark} {f.rule:<11} {f.where(rep.unit):<13} {f.detail}")


def cmd_check(a) -> int:
    paint = _colour(sys.stdout.isatty() and not a.no_colour)
    failed = False
    if a.key:
        key = [LETTERS.index(c) for c in a.key.upper() if c in LETTERS]
        rep = analyse(key, a.options or max(key) + 1, strict=not a.lenient)
        print_report("key", rep, paint)
        return 0 if rep.ok else 1
    for path in a.files:
        _, qs = load(path)
        rep = check_mcq(qs, strict=not a.lenient)
        if rep:
            print_report(f"{path} · MCQ", rep, paint)
            failed |= not rep.ok
        for i, q in enumerate(qs):
            if q.get("type") == "sort":
                srep = check_sort(q)
                print_report(f"{path} · sort #{i + 1}", srep, paint)
                failed |= not srep.ok
    return 1 if failed else 0


def cmd_fix(a) -> int:
    data, _ = load(a.file)
    fixed = fix_file(data, seed=a.seed, strict=not a.lenient)
    text = json.dumps(fixed, ensure_ascii=False, indent=2) + "\n"
    if a.output:
        Path(a.output).write_text(text, encoding="utf-8")
        print(f"wrote {a.output}")
    else:
        sys.stdout.write(text)
    return 0


def cmd_plan(a) -> int:
    key = plan_key(a.length, a.options, seed=a.seed, strict=not a.lenient)
    print("".join(LETTERS[k] for k in key))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pattern-guard", description="Catch guessable answer patterns in quizzes.")
    p.add_argument("--version", action="version", version=f"pattern-guard {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="check quiz files or a bare key")
    c.add_argument("files", nargs="*")
    c.add_argument("--key", help="answer key as letters, e.g. BDACAB")
    c.add_argument("--options", type=int, help="options per question (with --key)")
    c.add_argument("--lenient", action="store_true", help="allow single back-to-back repeats")
    c.add_argument("--no-colour", action="store_true")
    c.set_defaults(fn=cmd_check)

    f = sub.add_parser("fix", help="reorder options so the key has no pattern")
    f.add_argument("file")
    f.add_argument("-o", "--output")
    f.add_argument("--seed", type=int)
    f.add_argument("--lenient", action="store_true")
    f.set_defaults(fn=cmd_fix)

    pl = sub.add_parser("plan", help="print a pattern-free key")
    pl.add_argument("length", type=int)
    pl.add_argument("--options", type=int, default=4)
    pl.add_argument("--seed", type=int)
    pl.add_argument("--lenient", action="store_true")
    pl.set_defaults(fn=cmd_plan)

    a = p.parse_args(argv)
    if a.cmd == "check" and not a.files and not a.key:
        p.error("give a quiz file or --key")
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
