#!/usr/bin/env python3
"""Check for performance regression against Memory System baseline.

This script compares current test metrics against established baselines:
- Memory Management System: 72 tests minimum
- Semantic Bridge System: 97 tests, 100% inference accuracy, 0.12ms/event
- Memory Store System: 36 tests minimum
- Total: 205 tests
"""

import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict[str, Any]:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def check_regression(
    current: dict[str, Any],
    baselines: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Check for performance regression against baselines.

    Returns:
        (has_regression, warning_messages)
    """
    memory_system_baseline = baselines['memory_system']['thresholds']
    warnings = []
    has_regression = False

    # Check total tests
    current_total = current.get('tests_total', 0)
    min_total = memory_system_baseline['total_tests']['min']
    warning_threshold = memory_system_baseline['total_tests']['warning_threshold']

    threshold_value = int(min_total * warning_threshold)

    if current_total < threshold_value:
        msg = (
            f"REGRESSION: Total Tests\n"
            f"  Current:   {current_total} tests\n"
            f"  Threshold: {threshold_value} tests ({warning_threshold*100}% of {min_total})\n"
            f"  Baseline:  {min_total} tests"
        )
        warnings.append(msg)
        has_regression = True

    # Check test pass rate
    if current_total > 0:
        current_pass_rate = current.get('tests_passed', 0) / current_total
    else:
        current_pass_rate = 0.0

    min_pass_rate = memory_system_baseline['test_pass_rate']['min']

    if current_pass_rate < min_pass_rate:
        msg = (
            f"REGRESSION: Test Pass Rate\n"
            f"  Current:   {current_pass_rate*100:.1f}%\n"
            f"  Threshold: {min_pass_rate*100:.1f}%\n"
            f"  Baseline:  100%"
        )
        warnings.append(msg)
        has_regression = True

    # Check Memory Management tests
    current_mm = current.get('memory_management_tests', 0)
    min_mm = memory_system_baseline['memory_management_tests']['min']
    warning_threshold = memory_system_baseline['memory_management_tests']['warning_threshold']
    threshold_value = int(min_mm * warning_threshold)

    if current_mm < threshold_value:
        msg = (
            f"REGRESSION: Memory Management Tests\n"
            f"  Current:   {current_mm} tests\n"
            f"  Threshold: {threshold_value} tests ({warning_threshold*100}% of {min_mm})\n"
            f"  Baseline:  {min_mm} tests"
        )
        warnings.append(msg)
        has_regression = True

    # Check Semantic Bridge tests
    current_sb = current.get('semantic_bridge_tests', 0)
    min_sb = memory_system_baseline['semantic_bridge_tests']['min']
    warning_threshold = memory_system_baseline['semantic_bridge_tests']['warning_threshold']
    threshold_value = int(min_sb * warning_threshold)

    if current_sb < threshold_value:
        msg = (
            f"REGRESSION: Semantic Bridge Tests\n"
            f"  Current:   {current_sb} tests\n"
            f"  Threshold: {threshold_value} tests ({warning_threshold*100}% of {min_sb})\n"
            f"  Baseline:  {min_sb} tests"
        )
        warnings.append(msg)
        has_regression = True

    # Check Memory Store tests
    current_ms = current.get('memory_store_tests', 0)
    min_ms = memory_system_baseline['memory_store_tests']['min']
    warning_threshold = memory_system_baseline['memory_store_tests']['warning_threshold']
    threshold_value = int(min_ms * warning_threshold)

    if current_ms < threshold_value:
        msg = (
            f"REGRESSION: Memory Store Tests\n"
            f"  Current:   {current_ms} tests\n"
            f"  Threshold: {threshold_value} tests ({warning_threshold*100}% of {min_ms})\n"
            f"  Baseline:  {min_ms} tests"
        )
        warnings.append(msg)
        has_regression = True

    # Check inference accuracy
    current_accuracy = current.get('inference_accuracy', 0)
    min_accuracy = memory_system_baseline['inference_accuracy']['min']
    warning_threshold = memory_system_baseline['inference_accuracy']['warning_threshold']
    threshold_value = min_accuracy * warning_threshold

    if current_accuracy < threshold_value:
        msg = (
            f"REGRESSION: Inference Accuracy\n"
            f"  Current:   {current_accuracy:.1f}%\n"
            f"  Threshold: {threshold_value:.1f}% ({warning_threshold*100}% of {min_accuracy}%)\n"
            f"  Baseline:  100%"
        )
        warnings.append(msg)
        has_regression = True

    # Check processing performance (latency)
    current_perf = current.get('processing_performance_ms', 0)
    max_perf = memory_system_baseline['processing_performance_ms']['max']
    warning_threshold = memory_system_baseline['processing_performance_ms']['warning_threshold']
    threshold_value = max_perf * warning_threshold

    if current_perf > threshold_value and current_perf > 0:
        msg = (
            f"REGRESSION: Processing Performance\n"
            f"  Current:   {current_perf:.2f} ms/event\n"
            f"  Threshold: {threshold_value:.2f} ms ({warning_threshold*100}% of {max_perf}ms)\n"
            f"  Baseline:  0.12 ms/event"
        )
        warnings.append(msg)
        has_regression = True

    return has_regression, warnings


def main():
    metrics_path = "performance-metrics.json"
    baselines_path = "config/performance_baselines.json"

    if not Path(metrics_path).exists():
        print(f"Error: {metrics_path} not found")
        sys.exit(1)

    if not Path(baselines_path).exists():
        print(f"Error: {baselines_path} not found")
        sys.exit(1)

    try:
        current = load_json(metrics_path)
        baselines = load_json(baselines_path)

        has_regression, warnings = check_regression(current, baselines)

        if has_regression:
            print("\n" + "="*60)
            print("PERFORMANCE REGRESSION DETECTED")
            print("="*60)
            for warning in warnings:
                print(f"\n{warning}")
            print("\n" + "="*60)
            sys.exit(1)
        else:
            print("No performance regression detected")
            print(f"  Total Tests: {current['tests_total']}")
            print(f"  Passed: {current['tests_passed']}/{current['tests_total']}")
            print(f"  Memory Management: {current.get('memory_management_tests', 'N/A')} tests")
            print(f"  Semantic Bridge: {current.get('semantic_bridge_tests', 'N/A')} tests")
            print(f"  Memory Store: {current.get('memory_store_tests', 'N/A')} tests")
            print(f"  Inference Accuracy: {current.get('inference_accuracy', 'N/A')}%")
            print(f"  Processing Performance: {current.get('processing_performance_ms', 'N/A')} ms/event")
            sys.exit(0)

    except Exception as e:
        print(f"Error checking regression: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
