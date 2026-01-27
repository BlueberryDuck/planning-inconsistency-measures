#!/usr/bin/env python3
"""
PDDL to ASP Translator for Thesis Planning Measures

Converts PDDL domain/problem files to the thesis ASP format:
  init(prop).
  goal(prop).
  precond(operator, prop).
  add(operator, prop).
  delete(operator, prop).

Usage:
  python pddl_to_asp.py domain.pddl problem.pddl [-o output.lp]
"""

import argparse
import sys
from itertools import product
from pathlib import Path
from typing import Iterator

from pddl import parse_domain, parse_problem
from pddl.core import Domain, Problem
from pddl.logic import Predicate
from pddl.logic.base import And, Not
from pddl.logic.predicates import EqualTo
from pddl.logic.terms import Constant, Variable


def sanitize_name(name: str) -> str:
    """Convert PDDL name to valid ASP atom (lowercase, underscores)."""
    return name.lower().replace("-", "_").replace(" ", "_")


def ground_predicate(pred: Predicate, substitution: dict[Variable, Constant]) -> str:
    """Ground a predicate and convert to ASP atom name."""
    pred_name = sanitize_name(pred.name)
    if not pred.terms:
        return pred_name

    args = []
    for term in pred.terms:
        if isinstance(term, Variable):
            args.append(sanitize_name(substitution[term].name))
        elif isinstance(term, Constant):
            args.append(sanitize_name(term.name))
        else:
            args.append(sanitize_name(str(term)))

    return f"{pred_name}_{'_'.join(args)}"


def ground_atom(atom, substitution: dict[Variable, Constant]) -> str | None:
    """Ground an atom (predicate or equality) and convert to ASP atom name."""
    if isinstance(atom, Predicate):
        return ground_predicate(atom, substitution)
    elif isinstance(atom, EqualTo):
        # Equality constraints are evaluated, not converted to atoms
        return None
    elif isinstance(atom, Not):
        # Handle negated atoms (negative preconditions)
        inner = atom.argument
        if isinstance(inner, Predicate):
            return ground_predicate(inner, substitution)
        return None
    return None


def extract_predicates_from_formula(formula, substitution: dict) -> Iterator[tuple[str, bool]]:
    """
    Extract predicates from a formula, yielding (atom_name, is_positive) tuples.
    """
    if formula is None:
        return

    if isinstance(formula, Predicate):
        atom = ground_predicate(formula, substitution)
        yield (atom, True)
    elif isinstance(formula, Not):
        inner = formula.argument
        if isinstance(inner, Predicate):
            atom = ground_predicate(inner, substitution)
            yield (atom, False)
    elif isinstance(formula, And):
        for operand in formula.operands:
            yield from extract_predicates_from_formula(operand, substitution)
    elif isinstance(formula, EqualTo):
        # Skip equality constraints (handled during grounding)
        pass


def check_equality_constraint(formula, substitution: dict) -> bool:
    """Check if equality constraints in formula are satisfied by substitution."""
    if formula is None:
        return True

    if isinstance(formula, EqualTo):
        left = formula.left
        right = formula.right
        left_val = substitution.get(left, left) if isinstance(left, Variable) else left
        right_val = substitution.get(right, right) if isinstance(right, Variable) else right
        return left_val == right_val
    elif isinstance(formula, Not):
        if isinstance(formula.argument, EqualTo):
            return not check_equality_constraint(formula.argument, substitution)
        return True
    elif isinstance(formula, And):
        return all(check_equality_constraint(op, substitution) for op in formula.operands)
    return True


def get_typed_objects(problem: Problem, domain: Domain) -> dict[str, list[Constant]]:
    """Get all objects grouped by type, including type hierarchy."""
    objects_by_type: dict[str, list[Constant]] = {}

    # Collect all objects from problem
    all_objects = list(problem.objects)

    # Also include constants from domain if any
    if hasattr(domain, "constants") and domain.constants:
        all_objects.extend(domain.constants)

    for obj in all_objects:
        type_tags = obj.type_tags if hasattr(obj, "type_tags") else set()
        if not type_tags:
            type_tags = {"object"}

        for type_tag in type_tags:
            type_name = str(type_tag)
            if type_name not in objects_by_type:
                objects_by_type[type_name] = []
            if obj not in objects_by_type[type_name]:
                objects_by_type[type_name].append(obj)

    # Handle type hierarchy - objects of subtype are also of supertype
    if hasattr(domain, "types") and domain.types:
        for type_def in domain.types:
            type_name = str(type_def.name) if hasattr(type_def, "name") else str(type_def)
            type_tags = type_def.type_tags if hasattr(type_def, "type_tags") else set()
            for parent_tag in type_tags:
                parent_name = str(parent_tag)
                if parent_name not in objects_by_type:
                    objects_by_type[parent_name] = []
                for obj in objects_by_type.get(type_name, []):
                    if obj not in objects_by_type[parent_name]:
                        objects_by_type[parent_name].append(obj)

    # Ensure 'object' type contains all objects
    if "object" not in objects_by_type:
        objects_by_type["object"] = []
    for objs in list(objects_by_type.values()):
        for obj in objs:
            if obj not in objects_by_type["object"]:
                objects_by_type["object"].append(obj)

    return objects_by_type


def ground_action(action, objects_by_type: dict[str, list[Constant]]) -> Iterator[tuple[str, list[str], list[str], list[str]]]:
    """
    Ground an action schema and yield (action_name, preconditions, add_effects, delete_effects).
    """
    params = list(action.parameters)

    if not params:
        # No parameters - single ground action
        action_name = sanitize_name(action.name)

        preconditions = []
        for atom, is_positive in extract_predicates_from_formula(action.precondition, {}):
            if is_positive:
                preconditions.append(atom)

        add_effects = []
        delete_effects = []
        for atom, is_positive in extract_predicates_from_formula(action.effect, {}):
            if is_positive:
                add_effects.append(atom)
            else:
                delete_effects.append(atom)

        yield (action_name, preconditions, add_effects, delete_effects)
        return

    # Get domain for each parameter
    param_domains = []
    for param in params:
        type_tags = param.type_tags if hasattr(param, "type_tags") else set()
        if not type_tags:
            type_tags = {"object"}

        # Collect objects from all type tags
        domain_objects = set()
        for type_tag in type_tags:
            type_name = str(type_tag)
            domain_objects.update(objects_by_type.get(type_name, []))

        if not domain_objects:
            # No objects of this type - action cannot be grounded
            return

        param_domains.append(list(domain_objects))

    # Generate all substitutions
    for values in product(*param_domains):
        substitution = dict(zip(params, values))

        # Check equality constraints in precondition
        if not check_equality_constraint(action.precondition, substitution):
            continue

        # Build grounded action name
        action_name = sanitize_name(action.name)
        arg_names = [sanitize_name(v.name) for v in values]
        if arg_names:
            action_name = f"{action_name}_{'_'.join(arg_names)}"

        # Extract grounded preconditions
        preconditions = []
        for atom, is_positive in extract_predicates_from_formula(action.precondition, substitution):
            if is_positive:
                preconditions.append(atom)

        # Extract grounded effects
        add_effects = []
        delete_effects = []
        for atom, is_positive in extract_predicates_from_formula(action.effect, substitution):
            if is_positive:
                add_effects.append(atom)
            else:
                delete_effects.append(atom)

        yield (action_name, preconditions, add_effects, delete_effects)


def translate(domain: Domain, problem: Problem) -> str:
    """Translate a PDDL domain/problem to thesis ASP format."""
    lines = []

    # Header comment
    lines.append(f"% Translated from PDDL: {problem.name}")
    lines.append(f"% Domain: {domain.name}")
    lines.append("")

    # Initial state
    lines.append("% Initial state")
    for pred in problem.init:
        if isinstance(pred, Predicate):
            atom = ground_predicate(pred, {})
            lines.append(f"init({atom}).")
    lines.append("")

    # Goals
    lines.append("% Goals")
    for atom, is_positive in extract_predicates_from_formula(problem.goal, {}):
        if is_positive:
            lines.append(f"goal({atom}).")
    lines.append("")

    # Get typed objects for grounding
    objects_by_type = get_typed_objects(problem, domain)

    # Ground and translate actions
    lines.append("% Actions")
    for action in domain.actions:
        for action_name, preconditions, add_effects, delete_effects in ground_action(action, objects_by_type):
            # Preconditions
            for prec in preconditions:
                lines.append(f"precond({action_name}, {prec}).")

            # Add effects
            for add in add_effects:
                lines.append(f"add({action_name}, {add}).")

            # Delete effects
            for delete in delete_effects:
                lines.append(f"delete({action_name}, {delete}).")

            if preconditions or add_effects or delete_effects:
                lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Translate PDDL domain/problem to thesis ASP format"
    )
    parser.add_argument("domain", type=Path, help="PDDL domain file")
    parser.add_argument("problem", type=Path, help="PDDL problem file")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print statistics"
    )

    args = parser.parse_args()

    # Parse PDDL files
    try:
        domain = parse_domain(args.domain)
        problem = parse_problem(args.problem)
    except Exception as e:
        print(f"Error parsing PDDL: {e}", file=sys.stderr)
        sys.exit(1)

    # Translate
    output = translate(domain, problem)

    # Write output
    if args.output:
        args.output.write_text(output)
        if args.verbose:
            print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.verbose:
        # Count statistics
        n_init = output.count("init(")
        n_goal = output.count("goal(")
        n_precond = output.count("precond(")
        n_add = output.count("add(")
        n_delete = output.count("delete(")
        print(f"Stats: {n_init} init, {n_goal} goals, {n_precond} precond, {n_add} add, {n_delete} delete", file=sys.stderr)


if __name__ == "__main__":
    main()
