#!/usr/bin/env python3
"""
Optical Computer Benchmark Suite
================================

Comprehensive stress testing for the Wavelength-Division Ternary Optical Computer.
Tests all three system tiers with multiple benchmarks.

Benchmarks:
  A) Full Suite:
     - GEMM (Matrix Multiply) - Gold standard for systolic arrays
     - Mandelbrot Set - Embarrassingly parallel, multiply-heavy
     - Monte Carlo Pi - Random sampling stress test
     - Prime Counting (Miller-Rabin) - Modular exponentiation

  C) AI Workload:
     - Transformer Layer - Attention + MLP (real LLM workload)

System Tiers:
  1. Standard Computer: 81-trit ALU (~3.2 TFLOPS)
  2. Home AI: 243x243 x 8 WDM (~291 TFLOPS)
  3. Supercomputer: 8 chips x 243x243 x 8 WDM (~2,332 TFLOPS)

Author: Wavelength-Division Ternary Optical Computer Project
"""

import numpy as np
import time
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple
import sys

# =============================================================================
# SYSTEM TIER DEFINITIONS
# =============================================================================

@dataclass
class SystemTier:
    """Defines a system configuration tier."""
    name: str
    array_size: int          # PEs per dimension (e.g., 81 means 81x81)
    n_chips: int             # Number of chips
    n_wdm: int               # WDM channels
    clock_mhz: float         # Clock frequency
    description: str

    @property
    def total_pes(self) -> int:
        return self.n_chips * self.array_size * self.array_size

    @property
    def total_compute_units(self) -> int:
        return self.total_pes * self.n_wdm

    @property
    def peak_tflops(self) -> float:
        # Each compute unit does 1 MAC per cycle
        return self.total_compute_units * self.clock_mhz / 1e6

    @property
    def peak_pflops(self) -> float:
        return self.peak_tflops / 1000


# Define the three tiers
TIERS = {
    "standard": SystemTier(
        name="TIER 1: STANDARD COMPUTER",
        array_size=81,
        n_chips=1,
        n_wdm=1,
        clock_mhz=617,
        description="81-trit ALU + IOC + Backplane"
    ),
    "home_ai": SystemTier(
        name="TIER 2: HOME AI",
        array_size=243,
        n_chips=1,
        n_wdm=8,
        clock_mhz=617,
        description="243x243 Systolic + 8 WDM + Super IOC"
    ),
    "supercomputer": SystemTier(
        name="TIER 3: SUPERCOMPUTER",
        array_size=243,
        n_chips=8,
        n_wdm=8,
        clock_mhz=617,
        description="8-Chip Circular Backplane + 8 WDM"
    )
}

# Reference systems for comparison
REFERENCE_SYSTEMS = {
    "RTX_4090": {"name": "NVIDIA RTX 4090", "tflops": 83},
    "H100": {"name": "NVIDIA H100", "tflops": 2000},
    "B200": {"name": "NVIDIA B200", "tflops": 4500},
    "TPU_v5p": {"name": "Google TPU v5p", "tflops": 459},
}


# =============================================================================
# BENCHMARK DEFINITIONS
# =============================================================================

@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    benchmark_name: str
    tier_name: str
    total_operations: int
    theoretical_time_ms: float
    operations_per_second: float
    utilization: float  # 0-1, how well the array is used
    notes: str = ""


class Benchmark:
    """Base class for benchmarks."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def calculate_operations(self, **kwargs) -> int:
        """Calculate total operations for this benchmark."""
        raise NotImplementedError

    def estimate_utilization(self, tier: SystemTier, **kwargs) -> float:
        """Estimate how well this benchmark uses the systolic array."""
        raise NotImplementedError

    def run(self, tier: SystemTier, **kwargs) -> BenchmarkResult:
        """Run the benchmark on a given tier."""
        ops = self.calculate_operations(**kwargs)
        util = self.estimate_utilization(tier, **kwargs)

        # Effective FLOPS considering utilization
        effective_tflops = tier.peak_tflops * util

        # Time to complete (in milliseconds)
        time_ms = (ops / (effective_tflops * 1e12)) * 1000

        # Operations per second
        ops_per_sec = ops / (time_ms / 1000) if time_ms > 0 else 0

        return BenchmarkResult(
            benchmark_name=self.name,
            tier_name=tier.name,
            total_operations=ops,
            theoretical_time_ms=time_ms,
            operations_per_second=ops_per_sec,
            utilization=util
        )


# =============================================================================
# BENCHMARK IMPLEMENTATIONS
# =============================================================================

class GEMMBenchmark(Benchmark):
    """
    General Matrix-Matrix Multiplication (GEMM)
    C = A × B where A is MxK, B is KxN, C is MxN

    This is the gold standard for systolic arrays.
    Operations: 2*M*N*K (multiply + accumulate for each element)
    """

    def __init__(self):
        super().__init__(
            "GEMM (Matrix Multiply)",
            "C[MxN] = A[MxK] × B[KxN]"
        )

    def calculate_operations(self, M=1024, N=1024, K=1024, **kwargs) -> int:
        # Each output element requires K multiply-adds
        return 2 * M * N * K

    def estimate_utilization(self, tier: SystemTier, M=1024, N=1024, K=1024, **kwargs) -> float:
        # Systolic arrays are designed for GEMM - very high utilization
        # But utilization drops if matrix doesn't fit well
        array_dim = tier.array_size

        # Best case: matrix dimensions are multiples of array size
        m_fit = min(1.0, M / array_dim)
        n_fit = min(1.0, N / array_dim)

        # Base utilization for well-matched matrices
        base_util = 0.95

        # Penalty for small matrices that don't fill the array
        size_factor = min(m_fit, n_fit)

        return base_util * max(0.3, size_factor)


class MandelbrotBenchmark(Benchmark):
    """
    Mandelbrot Set Calculation

    For each pixel (x, y), iterate z = z² + c until |z| > 2 or max_iter reached.
    Embarrassingly parallel - each pixel is independent.

    Operations per pixel: ~15 FLOPS per iteration (complex multiply + add + magnitude)
    """

    def __init__(self):
        super().__init__(
            "Mandelbrot Set",
            "Fractal computation - embarrassingly parallel"
        )

    def calculate_operations(self, width=4096, height=4096, max_iter=1000, avg_iter=500, **kwargs) -> int:
        # Operations per iteration: z² requires 4 muls + 2 adds, plus comparison
        ops_per_iter = 15
        total_pixels = width * height
        return total_pixels * avg_iter * ops_per_iter

    def estimate_utilization(self, tier: SystemTier, width=4096, height=4096, **kwargs) -> float:
        # Each pixel is independent - maps well to parallel compute
        # But systolic arrays prefer matrix ops, so some inefficiency
        total_pixels = width * height
        total_pes = tier.total_compute_units

        # Good utilization if we have enough pixels to keep all PEs busy
        if total_pixels >= total_pes * 10:
            return 0.80  # Good parallelism
        elif total_pixels >= total_pes:
            return 0.60
        else:
            return 0.40  # Underutilized


class MonteCarloPiBenchmark(Benchmark):
    """
    Monte Carlo Pi Estimation

    Generate random (x, y) points in unit square.
    Count how many fall inside unit circle.
    Pi ≈ 4 * (inside / total)

    Operations per sample: 2 muls (x², y²) + 1 add + 1 compare
    """

    def __init__(self):
        super().__init__(
            "Monte Carlo Pi",
            "Random sampling to estimate π"
        )

    def calculate_operations(self, n_samples=1_000_000_000, **kwargs) -> int:
        # Per sample: x², y², x²+y², compare to 1
        ops_per_sample = 5
        return n_samples * ops_per_sample

    def estimate_utilization(self, tier: SystemTier, **kwargs) -> float:
        # Random number generation and independent samples
        # Not ideal for systolic arrays but highly parallel
        return 0.65


class PrimeCountingBenchmark(Benchmark):
    """
    Prime Counting using Miller-Rabin Primality Test

    For each number n in range, run Miller-Rabin with k witnesses.
    Each test involves modular exponentiation (lots of multiplies).

    This is adapted for LOG domain - modular exponentiation becomes
    repeated addition in log space, which is perfect for our architecture!

    Operations: O(k * log²(n)) per number tested
    """

    def __init__(self):
        super().__init__(
            "Prime Counting (Miller-Rabin)",
            "Count primes using modular exponentiation"
        )

    def calculate_operations(self, max_n=10_000_000, witnesses=10, **kwargs) -> int:
        # For each odd number from 3 to max_n
        numbers_to_test = max_n // 2

        # Miller-Rabin per number: k witnesses, log²(n) ops each
        avg_bits = math.log2(max_n / 2)  # Average bit length
        ops_per_witness = avg_bits * avg_bits * 3  # Square, multiply, mod
        ops_per_number = witnesses * ops_per_witness

        return int(numbers_to_test * ops_per_number)

    def estimate_utilization(self, tier: SystemTier, **kwargs) -> float:
        # LOG domain makes this efficient for our architecture!
        # Modular exponentiation = repeated addition in log space
        # But it's not perfectly systolic
        return 0.55


class TransformerLayerBenchmark(Benchmark):
    """
    Transformer Layer (Attention + MLP)

    This is the core of modern LLMs (GPT, Llama, etc.)

    Components:
    1. Multi-Head Attention:
       - Q, K, V projections: 3 × (batch × seq × d_model × d_model)
       - Attention scores: batch × heads × seq × seq
       - Softmax: batch × heads × seq × seq (uses LOG domain!)
       - Output projection: batch × seq × d_model × d_model

    2. MLP (Feed-Forward):
       - Up projection: batch × seq × d_model × (4*d_model)
       - Activation (GELU): batch × seq × (4*d_model)
       - Down projection: batch × seq × (4*d_model) × d_model

    This is where our LOG and LOG-LOG domains really shine!
    """

    def __init__(self):
        super().__init__(
            "Transformer Layer",
            "Attention + MLP (LLM core workload)"
        )

    def calculate_operations(self, batch=1, seq_len=2048, d_model=4096, n_heads=32, **kwargs) -> int:
        d_head = d_model // n_heads

        # === Attention ===
        # QKV projections: 3 linear layers
        qkv_ops = 3 * (2 * batch * seq_len * d_model * d_model)

        # Attention scores: Q @ K^T
        attn_scores_ops = 2 * batch * n_heads * seq_len * seq_len * d_head

        # Softmax: ~5 ops per element (exp, sum, div)
        softmax_ops = 5 * batch * n_heads * seq_len * seq_len

        # Attention output: scores @ V
        attn_out_ops = 2 * batch * n_heads * seq_len * d_head * seq_len

        # Output projection
        out_proj_ops = 2 * batch * seq_len * d_model * d_model

        attention_total = qkv_ops + attn_scores_ops + softmax_ops + attn_out_ops + out_proj_ops

        # === MLP ===
        # Up projection (d_model -> 4*d_model)
        up_ops = 2 * batch * seq_len * d_model * (4 * d_model)

        # GELU activation: ~10 ops per element
        gelu_ops = 10 * batch * seq_len * (4 * d_model)

        # Down projection (4*d_model -> d_model)
        down_ops = 2 * batch * seq_len * (4 * d_model) * d_model

        mlp_total = up_ops + gelu_ops + down_ops

        return attention_total + mlp_total

    def estimate_utilization(self, tier: SystemTier, seq_len=2048, d_model=4096, **kwargs) -> float:
        # Transformers are heavy on matrix multiplies - great for systolic arrays!
        array_dim = tier.array_size

        # Check how well dimensions map to array
        d_fit = min(1.0, d_model / array_dim)
        seq_fit = min(1.0, seq_len / array_dim)

        # Transformers are well-suited to systolic arrays
        base_util = 0.85

        # Bonus: Our LOG domain makes softmax super efficient!
        log_bonus = 1.05

        return min(0.95, base_util * max(0.5, (d_fit + seq_fit) / 2) * log_bonus)


# =============================================================================
# BENCHMARK RUNNER
# =============================================================================

def print_header(text: str, char: str = "=", width: int = 80):
    """Print a formatted header."""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)


def format_number(n: float) -> str:
    """Format large numbers with K/M/G/T suffixes."""
    if n >= 1e12:
        return f"{n/1e12:.2f}T"
    elif n >= 1e9:
        return f"{n/1e9:.2f}G"
    elif n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif n >= 1e3:
        return f"{n/1e3:.2f}K"
    else:
        return f"{n:.2f}"


def format_time(ms: float) -> str:
    """Format time with appropriate units."""
    if ms >= 1000:
        return f"{ms/1000:.3f} s"
    elif ms >= 1:
        return f"{ms:.3f} ms"
    else:
        return f"{ms*1000:.3f} μs"


def run_benchmark_suite(tier: SystemTier, benchmarks: List[Benchmark], params: Dict) -> List[BenchmarkResult]:
    """Run all benchmarks on a given tier."""
    results = []

    print_header(f"{tier.name}", "=")
    print(f"  {tier.description}")
    print(f"  Array: {tier.array_size}x{tier.array_size} | Chips: {tier.n_chips} | WDM: {tier.n_wdm}")
    print(f"  Total PEs: {tier.total_pes:,} | Compute Units: {tier.total_compute_units:,}")
    print(f"  Peak: {tier.peak_tflops:,.1f} TFLOPS ({tier.peak_pflops:.3f} PFLOPS)")
    print("-" * 80)

    for benchmark in benchmarks:
        bench_params = params.get(benchmark.name, {})
        result = benchmark.run(tier, **bench_params)
        results.append(result)

        print(f"\n  [{benchmark.name}]")
        print(f"    {benchmark.description}")
        print(f"    Operations:    {format_number(result.total_operations)} OPs")
        print(f"    Time:          {format_time(result.theoretical_time_ms)}")
        print(f"    Throughput:    {format_number(result.operations_per_second)} OPs/s")
        print(f"    Utilization:   {result.utilization*100:.1f}%")

    return results


def compare_to_reference(results: List[BenchmarkResult], tier: SystemTier):
    """Compare benchmark results to reference systems."""
    print_header("COMPARISON TO REFERENCE SYSTEMS", "-")

    # Calculate effective TFLOPS from transformer benchmark (most representative)
    transformer_result = next((r for r in results if "Transformer" in r.benchmark_name), None)

    if transformer_result:
        effective_tflops = transformer_result.operations_per_second / 1e12

        print(f"\n  {tier.name}")
        print(f"  Effective TFLOPS (Transformer): {effective_tflops:.1f}")
        print()

        for ref_name, ref_data in REFERENCE_SYSTEMS.items():
            ratio = effective_tflops / ref_data["tflops"]
            if ratio >= 1:
                print(f"    vs {ref_data['name']:20s}: {ratio:.2f}x FASTER")
            else:
                print(f"    vs {ref_data['name']:20s}: {1/ratio:.2f}x slower")


def run_all_tiers(selected_tiers: List[str] = None):
    """Run benchmarks on selected tiers."""

    if selected_tiers is None:
        selected_tiers = ["standard", "home_ai", "supercomputer"]

    # Define benchmarks
    benchmarks = [
        GEMMBenchmark(),
        MandelbrotBenchmark(),
        MonteCarloPiBenchmark(),
        PrimeCountingBenchmark(),
        TransformerLayerBenchmark(),
    ]

    # Benchmark parameters
    params = {
        "GEMM (Matrix Multiply)": {"M": 4096, "N": 4096, "K": 4096},
        "Mandelbrot Set": {"width": 8192, "height": 8192, "max_iter": 1000, "avg_iter": 500},
        "Monte Carlo Pi": {"n_samples": 10_000_000_000},  # 10 billion samples
        "Prime Counting (Miller-Rabin)": {"max_n": 100_000_000, "witnesses": 10},  # 100 million
        "Transformer Layer": {"batch": 1, "seq_len": 2048, "d_model": 4096, "n_heads": 32},
    }

    print_header("OPTICAL COMPUTER BENCHMARK SUITE", "=")
    print("  Wavelength-Division Ternary Optical Computer")
    print("  Testing all system tiers with comprehensive benchmarks")

    print("\n  BENCHMARKS:")
    print("    A) Full Suite: GEMM, Mandelbrot, Monte Carlo Pi, Prime Counting")
    print("    C) AI Workload: Transformer Layer (Attention + MLP)")

    print("\n  PARAMETERS:")
    for name, p in params.items():
        print(f"    {name}: {p}")

    all_results = {}

    for tier_key in selected_tiers:
        if tier_key not in TIERS:
            print(f"Unknown tier: {tier_key}")
            continue

        tier = TIERS[tier_key]
        results = run_benchmark_suite(tier, benchmarks, params)
        all_results[tier_key] = results

        compare_to_reference(results, tier)

    # Summary comparison across tiers
    print_header("SUMMARY: ALL TIERS COMPARISON", "=")

    print(f"\n{'Benchmark':<30} | {'Standard':>12} | {'Home AI':>12} | {'Supercomputer':>15}")
    print("-" * 80)

    benchmark_names = [b.name for b in benchmarks]

    for bench_name in benchmark_names:
        row = f"{bench_name:<30} |"
        for tier_key in selected_tiers:
            if tier_key in all_results:
                result = next((r for r in all_results[tier_key] if r.benchmark_name == bench_name), None)
                if result:
                    row += f" {format_time(result.theoretical_time_ms):>12} |"
                else:
                    row += f" {'N/A':>12} |"
        print(row)

    # Peak performance summary
    print_header("PEAK PERFORMANCE SUMMARY", "-")

    print(f"\n{'Tier':<25} | {'Peak TFLOPS':>15} | {'vs RTX 4090':>12} | {'vs H100':>12}")
    print("-" * 75)

    for tier_key in selected_tiers:
        tier = TIERS[tier_key]
        rtx_ratio = tier.peak_tflops / REFERENCE_SYSTEMS["RTX_4090"]["tflops"]
        h100_ratio = tier.peak_tflops / REFERENCE_SYSTEMS["H100"]["tflops"]

        print(f"{tier.name:<25} | {tier.peak_tflops:>12,.1f}   | {rtx_ratio:>10.2f}x  | {h100_ratio:>10.2f}x")

    print("\n" + "=" * 80)
    print("  Benchmark suite complete!")
    print("=" * 80)

    return all_results


# =============================================================================
# INTERACTIVE MODE
# =============================================================================

def interactive_mode():
    """Interactive benchmark selection."""

    print("\n" + "=" * 70)
    print("  OPTICAL COMPUTER BENCHMARK SUITE")
    print("  Stress Testing for Ternary Optical Architecture")
    print("=" * 70)

    print("\n  SELECT SYSTEM TIER(S) TO TEST:")
    print("  [1] Standard Computer (~3.2 TFLOPS)")
    print("  [2] Home AI (~291 TFLOPS)")
    print("  [3] Supercomputer (~2,332 TFLOPS)")
    print("  [4] ALL TIERS (compare all)")

    choice = input("\n  Select (1-4) [4]: ").strip() or "4"

    if choice == "1":
        selected = ["standard"]
    elif choice == "2":
        selected = ["home_ai"]
    elif choice == "3":
        selected = ["supercomputer"]
    else:
        selected = ["standard", "home_ai", "supercomputer"]

    print("\n  SELECT BENCHMARK SUITE:")
    print("  [A] Full Suite (GEMM + Mandelbrot + Monte Carlo + Primes)")
    print("  [C] AI Workload (Transformer Layer)")
    print("  [B] BOTH (A + C)")

    bench_choice = input("\n  Select (A/C/B) [B]: ").strip().upper() or "B"

    # Run the benchmarks
    run_all_tiers(selected)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "--all":
            run_all_tiers()
        elif sys.argv[1] == "--standard":
            run_all_tiers(["standard"])
        elif sys.argv[1] == "--home":
            run_all_tiers(["home_ai"])
        elif sys.argv[1] == "--super":
            run_all_tiers(["supercomputer"])
        else:
            print("Usage: python optical_benchmark_suite.py [--all|--standard|--home|--super]")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
