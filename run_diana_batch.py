# Model filename convention and parameter bounds
#
# Each DIANA project file shall be named d%rho%fc%cr%ca.dpf. The stem
# contains exactly five decimal numbers in the order listed below.
# Use a period as the decimal separator and a percent sign as the
# field delimiter. Omit unit symbols and spaces from the filename.
#
# Symbol  Quantity                      Input bounds or output unit
# d       Effective depth               [0, 300] mm
# rho     Reinforcement ratio           [0.2, 3] %
# fc      Concrete compressive strength [20, 100] MPa
# cr      Corrosion level               [0, 1] (dimensionless)
# ca      Corroded area fraction        [0, 1] (dimensionless)
# Pu      Ultimate load capacity        kN (calculated output)
#
# All intervals are closed and serve as filename validation bounds
# for this batch. Encode rho in percent (0.5 denotes 0.5%) and cr
# and ca as fractions (0.5 denotes 50%).
#
# Example: 47%0.5%20%0%1.dpf encodes d = 47 mm, rho = 0.5%,
# fc = 20 MPa, cr = 0, and ca = 1 (100%).
# A malformed or out-of-range filename is recorded in the summary
# CSV with a capacity value of null, and the model is skipped.
#
# The output CSV has a header row. Data columns follow the order
# shown above: d, rho, fc, cr, ca, Pu. Column 6 reports Pu in kN
# to two decimal places.

"""Run existing DIANA 10.3 projects and export each project's peak FBZ to CSV."""

import csv
import math
import os
import re
import tempfile
import time
from decimal import Decimal
from inspect import currentframe
from pathlib import Path


script_name = globals().get("__file__") or currentframe().f_code.co_filename
script_path = Path(script_name).resolve()
if not script_path.is_file():
    raise RuntimeError("Cannot locate the script. Run this saved .py file from DIANA.")
MODEL_DIR = script_path.parent
OUTPUT_CSV = MODEL_DIR / "diana_reaction_forces.csv"
DIAGNOSTICS = MODEL_DIR / "diana_reaction_forces_errors.log"
ANALYSIS_NAME = "Analysis1"
NAME_LIMITS = (
    ("effective thickness (mm)", 0, 300),
    ("reinforcement ratio (%)", 0.2, 3),
    ("concrete compressive strength (MPa)", 20, 100),
    ("corrosion rate", 0, 1),
    ("corroded area ratio", 0, 1),
)
DECIMAL_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)")


def validate_project_name(project_path):
    fields = project_path.stem.split("%")
    if len(fields) != len(NAME_LIMITS):
        raise ValueError("expected five numbers separated by %")

    for field, (label, lower, upper) in zip(fields, NAME_LIMITS):
        if not DECIMAL_NUMBER.fullmatch(field):
            raise ValueError("{} must be a decimal number".format(label))
        if not Decimal(str(lower)) <= Decimal(field) <= Decimal(str(upper)):
            raise ValueError("{}={} outside [{}, {}]".format(label, field, lower, upper))


def get_reaction_force(csv_path):
    errors = []
    for block in outputBlocks(ANALYSIS_NAME):
        try:
            return export_block_peak(csv_path, block)
        except Exception as exc:
            errors.append("{}: {}: {}".format(block, type(exc).__name__, exc))
    raise ValueError("; ".join(errors) or "No output blocks found for " + ANALYSIS_NAME)


def export_block_peak(csv_path, block):
    if csv_path.exists():
        csv_path.unlink()
    exportResults(str(csv_path), {
        "analysis": ANALYSIS_NAME,
        "result": "Reaction Forces",
        "components": ["FBZ"],
        "block": block,
    })

    step_data = {}
    columns = None
    with csv_path.open(encoding="utf-8-sig", errors="ignore", newline="") as stream:
        sample = stream.read(8192)
        stream.seek(0)
        header = next((line for line in sample.splitlines() if "fbz" in line.lower()), "")
        delimiter = max((",", ";", "	"), key=header.count)
        for row in csv.reader(stream, delimiter=delimiter):
            if columns is None:
                names = [cell.strip().lower() for cell in row]
                step_name = "case-id" if "case-id" in names else "step"
                force_index = next((i for i, name in enumerate(names) if "fbz" in name), None)
                if "node" in names and step_name in names and force_index is not None:
                    columns = names.index("node"), names.index(step_name), force_index
                continue

            node_index, step_index, force_index = columns
            if len(row) <= max(columns):
                continue
            try:
                value = row[force_index].strip().replace("D", "E").replace("d", "e")
                force = float(value.replace(",", ".") if delimiter != "," else value)
            except ValueError:
                continue
            if math.isfinite(force) and force < -100.0:
                step = row[step_index].strip()
                node = row[node_index].strip()
                step_data.setdefault(step, {})[node] = force

    if columns is None:
        raise ValueError("Missing node, case-id/step, or FBZ column in DIANA output")
    if not step_data:
        raise ValueError("No FBZ values below -100.0 in DIANA output")
    return round(max((sum(nodes.values()) for nodes in step_data.values()), key=abs), 2)


def run_model(project_path, reaction_csv):
    stems = (project_path.stem, project_path.name.split(".", 1)[0])
    candidates = [project_path.parent / (stem + "_" + ANALYSIS_NAME + ".dnb")
                  for stem in dict.fromkeys(stems)]
    before = {path: result_signature(path) for path in candidates}
    openProject(str(project_path))
    try:
        analysis_names = analyses()
        if ANALYSIS_NAME not in analysis_names:
            raise RuntimeError("{} missing; available analyses: {}".format(
                ANALYSIS_NAME, analysis_names
            ))
        solver_status = None
        try:
            solver_status = runSolver(analysis_names)
        except Exception as exc:
            solver_status = "{}: {}".format(type(exc).__name__, exc)

        try:
            return get_reaction_force(reaction_csv)
        except Exception as export_error:
            details = ["runSolver={!r}".format(solver_status), "initial export: {}".format(export_error)]
            for result_file in candidates:
                signature = result_signature(result_file)
                if signature is None or signature == before[result_file]:
                    details.append("{}: no fresh result file".format(result_file.name))
                    continue
                try:
                    loaded = loadResults(ANALYSIS_NAME, str(result_file))
                    if not loaded:
                        details.append("{}: loadResults returned {!r}".format(result_file.name, loaded))
                        continue
                    return get_reaction_force(reaction_csv)
                except Exception as exc:
                    details.append("{}: {}: {}".format(result_file.name, type(exc).__name__, exc))
            raise RuntimeError("; ".join(details)) from export_error
    finally:
        closeProject()


def result_signature(path):
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return stat.st_size, stat.st_mtime_ns


def write_result(writer, stream, row):
    writer.writerow(row)
    stream.flush()
    os.fsync(stream.fileno())


def main():
    start = time.time()
    projects = sorted(
        (path for path in MODEL_DIR.glob("*.dpf") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )
    if not projects:
        raise ValueError("No .dpf files found in " + str(MODEL_DIR))

    succeeded = invalid = failed = 0
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as stream, \
            DIAGNOSTICS.open("w", encoding="utf-8") as diagnostics:
        writer = csv.writer(stream)
        write_result(writer, stream, [
            "effective depth", "reinforcement ratio",
            "concrete compressive strength", "corrosion level",
            "corrosion area rate", "peak_reaction_force",
        ])
        for project_path in projects:
            fields = project_path.stem.split("%")
            parameters = fields if len(fields) == len(NAME_LIMITS) else [""] * len(NAME_LIMITS)
            try:
                validate_project_name(project_path)
            except ValueError as exc:
                write_result(writer, stream, parameters + ["null"])
                invalid += 1
                print("Invalid name {}: {}".format(project_path.name, exc))
                continue

            print("Running {}".format(project_path.name))
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    force = run_model(project_path, Path(temp_dir) / "temp_8points_sum.csv")
            except Exception as exc:
                failed += 1
                message = "Failed {}: {}: {}".format(project_path.name, type(exc).__name__, exc)
                print(message)
                diagnostics.write(message + "\n")
                diagnostics.flush()
                result = "null"
            else:
                result = "{:.2f}".format(force / -1000.0)
                succeeded += 1
                print("{}: capacity = {} kN".format(project_path.name, result))

            write_result(writer, stream, parameters + [result])

    print("Exported: {}, invalid names: {}, failed: {}, elapsed: {:.1f} s".format(
        succeeded, invalid, failed, time.time() - start
    ))
    print("CSV: " + str(OUTPUT_CSV))


if __name__ == "__main__":
    main()
