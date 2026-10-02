import io

import cli


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    code = cli.run(argv, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_summary_line(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world\nbye\n", encoding="utf-8")
    code, out, err = run_cli([str(sample)])
    assert code == 0
    assert out == "sample.txt: 2 lines, 3 words, 16 chars\n"
    assert err == ""


def test_top_flag_lists_frequent_words(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("red red blue\n", encoding="utf-8")
    code, out, _ = run_cli([str(sample), "--top", "1"])
    assert code == 0
    assert out.splitlines()[1] == "  red 2"


def test_missing_file_reports_error_and_continues(tmp_path):
    present = tmp_path / "present.txt"
    present.write_text("ok\n", encoding="utf-8")
    code, out, err = run_cli([str(tmp_path / "absent.txt"), str(present)])
    assert code == 1
    assert "absent.txt" in err
    assert "present.txt: 1 lines, 1 words, 3 chars" in out
