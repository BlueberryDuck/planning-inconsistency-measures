"""Tests for Benchmark layout discovery.

`discover` walks a Benchmark directory and returns
`(domain_name, domain_path, problem_path)` triples — one per
(Domain, Problem) pair found under one of the supported IPC layouts.
"""

from pathlib import Path

from planning_measures.benchmark_layout import discover


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


class TestDiscover:
    def test_single_domain_layout_pairs_domain_with_each_problem(self, tmp_path: Path):
        _touch(tmp_path / "domain.pddl")
        _touch(tmp_path / "prob01.pddl")
        _touch(tmp_path / "prob02.pddl")

        pairs = discover(tmp_path)

        assert sorted((name, dom.name, prob.name) for name, dom, prob in pairs) == [
            (tmp_path.name, "domain.pddl", "prob01.pddl"),
            (tmp_path.name, "domain.pddl", "prob02.pddl"),
        ]

    def test_numbered_pairs_match_dom_with_prob(self, tmp_path: Path):
        _touch(tmp_path / "dom01.pddl")
        _touch(tmp_path / "prob01.pddl")
        _touch(tmp_path / "dom02.pddl")
        _touch(tmp_path / "prob02.pddl")

        pairs = discover(tmp_path)

        assert sorted((dom.name, prob.name) for _, dom, prob in pairs) == [
            ("dom01.pddl", "prob01.pddl"),
            ("dom02.pddl", "prob02.pddl"),
        ]

    def test_numbered_pairs_include_satprob_alongside_prob(self, tmp_path: Path):
        _touch(tmp_path / "dom01.pddl")
        _touch(tmp_path / "prob01.pddl")
        _touch(tmp_path / "satprob01.pddl")

        pairs = discover(tmp_path)

        assert sorted((dom.name, prob.name) for _, dom, prob in pairs) == [
            ("dom01.pddl", "prob01.pddl"),
            ("dom01.pddl", "satprob01.pddl"),
        ]

    def test_eriksson_layout_pairs_domain_prefix_with_suffix_problem(
        self, tmp_path: Path
    ):
        _touch(tmp_path / "domain_blocks.pddl")
        _touch(tmp_path / "blocks.pddl")
        _touch(tmp_path / "domain_logistics.pddl")
        _touch(tmp_path / "logistics.pddl")

        pairs = discover(tmp_path)

        assert sorted((dom.name, prob.name) for _, dom, prob in pairs) == [
            ("domain_blocks.pddl", "blocks.pddl"),
            ("domain_logistics.pddl", "logistics.pddl"),
        ]

    def test_parent_of_subdirs_recurses_into_each_domain_subdir(self, tmp_path: Path):
        _touch(tmp_path / "blocks" / "domain.pddl")
        _touch(tmp_path / "blocks" / "prob01.pddl")
        _touch(tmp_path / "logistics" / "dom01.pddl")
        _touch(tmp_path / "logistics" / "prob01.pddl")

        pairs = discover(tmp_path)

        assert sorted((name, dom.name, prob.name) for name, dom, prob in pairs) == [
            ("blocks", "domain.pddl", "prob01.pddl"),
            ("logistics", "dom01.pddl", "prob01.pddl"),
        ]

    def test_skip_domains_excludes_named_subdirs(self, tmp_path: Path):
        _touch(tmp_path / "blocks" / "domain.pddl")
        _touch(tmp_path / "blocks" / "prob01.pddl")
        _touch(tmp_path / "tetris" / "domain.pddl")
        _touch(tmp_path / "tetris" / "prob01.pddl")

        pairs = discover(tmp_path, skip_domains={"tetris"})

        assert [name for name, _, _ in pairs] == ["blocks"]
