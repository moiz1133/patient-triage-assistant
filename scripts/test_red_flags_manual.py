from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.layers.red_flag_matcher import (
    RedFlagMatch,
    evaluate_all_rules,
    get_minimum_esi_floor,
)
from src.models import PatientCase, Symptom, Vitals

console = Console()


# ---------------------------------------------------------------------------
# Expected-outcome spec
# ---------------------------------------------------------------------------

@dataclass
class Expectation:
    label: str
    must_include: set[str]       # rule_ids that MUST be in matches
    must_exclude: set[str]       # rule_ids that MUST NOT be in matches
    expected_floor: Optional[int]


EXPECTATIONS: list[Expectation] = [
    Expectation("chest_pain_elderly",       {"RF001", "RF009"}, set(),        1),
    Expectation("chest_pain_young",         {"RF009"},          {"RF001"},     2),
    Expectation("stroke_symptoms",          {"RF002"},          set(),        1),
    Expectation("low_oxygen_no_keyword",    {"RF003"},          set(),        1),
    Expectation("hypotension",              {"RF010"},          set(),        1),
    Expectation("suicidal_ideation",        {"RF013"},          set(),        2),
    Expectation("clean_case_no_flags",      set(),              set(),        None),
    Expectation("missing_age_chest_pain",   {"RF001", "RF009"}, set(),        1),
    Expectation("multiple_flags_same_case", {"RF001", "RF009", "RF003"}, set(), 1),
    Expectation("pediatric_fever",          {"RF007"},          set(),        2),
]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def _case(**kwargs) -> PatientCase:
    """Minimal PatientCase factory; fills required fields with safe defaults."""
    defaults = {
        "chief_complaint": "unspecified complaint",
        "raw_input_text": "(test)",
        "extraction_confidence": 1.0,
    }
    return PatientCase(**{**defaults, **kwargs})


TEST_CASES: list[tuple[str, PatientCase]] = [
    (
        "chest_pain_elderly",
        _case(age=60, chief_complaint="chest pain",
              symptoms=[Symptom(name="chest pain")]),
    ),
    (
        "chest_pain_young",
        _case(age=25, chief_complaint="mild chest pain after exercise",
              symptoms=[Symptom(name="chest pain")]),
    ),
    (
        "stroke_symptoms",
        _case(chief_complaint="sudden facial droop and arm weakness",
              symptoms=[Symptom(name="facial droop"), Symptom(name="arm weakness")]),
    ),
    (
        "low_oxygen_no_keyword",
        _case(chief_complaint="feeling unwell",
              vitals=Vitals(oxygen_saturation=88)),
    ),
    (
        "hypotension",
        _case(chief_complaint="dizziness",
              vitals=Vitals(systolic_bp=85)),
    ),
    (
        "suicidal_ideation",
        _case(chief_complaint="patient reports wanting to end my life"),
    ),
    (
        "clean_case_no_flags",
        _case(age=30, chief_complaint="mild cold symptoms",
              symptoms=[Symptom(name="runny nose")]),
    ),
    (
        "missing_age_chest_pain",
        _case(age=None, chief_complaint="chest pain"),
    ),
    (
        "multiple_flags_same_case",
        _case(age=70, chief_complaint="chest pain and difficulty breathing",
              symptoms=[Symptom(name="chest pain"), Symptom(name="difficulty breathing")],
              vitals=Vitals(oxygen_saturation=89)),
    ),
    (
        # age=0 represents an infant (~5 weeks old).
        # PatientCase.age is Optional[int]; 0.1 years would fail validation.
        # RF007 max_age=0: check is age > 0, so age=0 passes the constraint.
        "pediatric_fever",
        _case(age=0, chief_complaint="elevated temperature noted",
              vitals=Vitals(temperature_celsius=38.5)),
    ),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _check(
    label: str,
    matches: list[RedFlagMatch],
    floor: Optional[int],
    expectation: Expectation,
) -> tuple[bool, str]:
    triggered_ids = {m.rule_id for m in matches}
    failures: list[str] = []

    missing = expectation.must_include - triggered_ids
    if missing:
        failures.append(f"expected rule(s) {missing} to trigger but did not")

    unexpected = expectation.must_exclude & triggered_ids
    if unexpected:
        failures.append(f"rule(s) {unexpected} triggered but should not have")

    if floor != expectation.expected_floor:
        failures.append(f"expected floor={expectation.expected_floor}, got floor={floor}")

    if failures:
        return False, "; ".join(failures)
    return True, "all expectations met"


def run() -> None:
    results: list[tuple[str, list[RedFlagMatch], Optional[int], bool, str]] = []

    for label, case in TEST_CASES:
        console.rule(f"[bold cyan]{label}[/bold cyan]")

        matches = evaluate_all_rules(case)
        floor = get_minimum_esi_floor(matches)

        expectation = next(e for e in EXPECTATIONS if e.label == label)
        passed, reason = _check(label, matches, floor, expectation)
        results.append((label, matches, floor, passed, reason))

        if matches:
            match_table = Table(show_header=True, box=None, padding=(0, 1))
            match_table.add_column("Rule ID", style="bold yellow")
            match_table.add_column("Name")
            match_table.add_column("ESI Floor", justify="center")
            match_table.add_column("Trigger Reason")
            for m in matches:
                match_table.add_row(m.rule_id, m.rule_name, str(m.minimum_esi_floor), m.trigger_reason)
            console.print(match_table)
        else:
            console.print("[dim]No red flags triggered.[/dim]")

        console.print(f"ESI floor: [bold]{floor}[/bold]\n")

    # --- summary ---
    console.rule("[bold]Summary[/bold]")
    summary = Table(title="Red Flag Matching Results", show_lines=True)
    summary.add_column("Label", style="bold cyan", no_wrap=True)
    summary.add_column("Triggered Rules")
    summary.add_column("Floor", justify="center")
    summary.add_column("Result", justify="center")

    all_passed = True
    for label, matches, floor, passed, reason in results:
        triggered_str = ", ".join(m.rule_id for m in matches) or "—"
        floor_str = str(floor) if floor is not None else "—"

        if passed:
            result_cell = Text("PASS", style="bold green")
        else:
            result_cell = Text("FAIL", style="bold red")
            all_passed = False

        summary.add_row(label, triggered_str, floor_str, result_cell)

    console.print(summary)

    # --- detailed failures ---
    failures = [(label, reason) for label, _, _, passed, reason in results if not passed]
    if failures:
        console.print()
        for label, reason in failures:
            console.print(
                Panel(
                    f"[bold]{label}[/bold]\n[red]{reason}[/red]",
                    title="[bold red]FAIL — Expectation Not Met[/bold red]",
                    border_style="red",
                )
            )
    else:
        console.print(
            Panel("[green]All 10 cases passed.[/green]",
                  title="[green]All Tests Passed[/green]",
                  border_style="green")
        )


if __name__ == "__main__":
    run()
