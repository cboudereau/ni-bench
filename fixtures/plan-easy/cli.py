"""wordstats — line, word, and character statistics for text files."""

import argparse
import sys
from pathlib import Path

import stats


def build_parser():
    parser = argparse.ArgumentParser(
        prog="wordstats",
        description="Print line, word, and character statistics for text files.",
    )
    parser.add_argument("paths", nargs="+", help="text files to analyse")
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="also list the N most frequent words per file",
    )
    return parser


def format_summary(name, summary):
    return (
        f"{name}: {summary['lines']} lines, "
        f"{summary['words']} words, {summary['chars']} chars"
    )


def format_top(pairs):
    return "\n".join(f"  {word} {count}" for word, count in pairs)


def run(argv, out=sys.stdout, err=sys.stderr):
    args = build_parser().parse_args(argv)
    exit_code = 0
    for raw_path in args.paths:
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"wordstats: {raw_path}: {exc.strerror}", file=err)
            exit_code = 1
            continue
        print(format_summary(path.name, stats.summarize(text)), file=out)
        if args.top > 0:
            print(format_top(stats.top_words(text, args.top)), file=out)
    return exit_code


def main():
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
