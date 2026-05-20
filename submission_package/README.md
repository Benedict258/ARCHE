# ARCHE Submission Package

This folder contains final submission artifacts for the current agentic ARCHE state.

## Included

- `arche_solution_paper.md` - final solution paper with evaluation metrics filled in
- `evaluation_metrics.json` - reproducible benchmark results used in the paper
- `validation_summary.md` - latest API and integration verification run

## Reproduction

Run the evaluator against the benchmark files in `data/evaluation/`:

- Task A: `python data/evaluation/run_evaluation.py A data/evaluation/task_a_benchmark_results.json`
- Task B: `python data/evaluation/run_evaluation.py B data/evaluation/task_b_benchmark_results.json --k 10`

Run API validation tests:

- `python -m pytest tests/test_integration.py -q`
- `python -m pytest tests/test_simulate.py -q`
- `python -m pytest tests/test_task_a.py -q`
- `python -m pytest tests/test_performance.py::TestExplainPerformance::test_explain_latency -q`

## Notes

- The benchmark files were generated from live API endpoints in this repository.
- The API now routes through the LangGraph-style multi-agent orchestrator (`orchestrator/langgraph_pipeline.py`) and real dataset loader (`data/dataset_loader.py`) when data is present.
- The paper metrics are rounded to 4 decimal places for presentation.
