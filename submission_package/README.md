# ARCHE Submission Package

This folder contains the final submission artifacts prepared from the current MVP state.

## Included

- `arche_solution_paper.md` - final solution paper with evaluation metrics filled in
- `evaluation_metrics.json` - reproducible benchmark results used in the paper

## Reproduction

Run the evaluator against the benchmark files in `data/evaluation/`:

- Task A: `python data/evaluation/run_evaluation.py A data/evaluation/task_a_benchmark_results.json`
- Task B: `python data/evaluation/run_evaluation.py B data/evaluation/task_b_benchmark_results.json --k 10`

## Notes

- The benchmark files were generated from the live API endpoints in the current repo state.
- The paper metrics are rounded to 4 decimal places for presentation.
