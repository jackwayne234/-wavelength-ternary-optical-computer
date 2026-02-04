#!/usr/bin/env python3
"""
Minimal diagnostic: Does the source produce ANY signal?
Tests source in vacuum without any geometry.
"""

import meep as mp
import numpy as np

print("=" * 60)
print("SOURCE DIAGNOSTIC TEST")
print("=" * 60)

wavelength = 1.55  # μm
freq = 1.0 / wavelength

# Simple cell - just vacuum
cell_size = mp.Vector3(100, 100, 0)

# Source at center
sources = [
    mp.Source(
        mp.GaussianSource(freq, fwidth=0.2 * freq),
        component=mp.Ez,
        center=mp.Vector3(0, 0, 0),
        size=mp.Vector3(2, 2, 0)
    )
]

print(f"\nSource config:")
print(f"  Frequency: {freq:.4f} (wavelength: {wavelength} μm)")
print(f"  Bandwidth: {0.2 * freq:.4f}")
print(f"  Location: center (0, 0)")

sim = mp.Simulation(
    cell_size=cell_size,
    boundary_layers=[mp.PML(2.0)],
    geometry=[],  # NO geometry - just vacuum
    sources=sources,
    resolution=20
)

# Record field at source location
times = []
fields = []

def record(sim):
    t = sim.meep_time()
    ez = abs(sim.get_field_point(mp.Ez, mp.Vector3(0, 0)))**2
    times.append(t)
    fields.append(ez)
    if len(times) <= 10 or len(times) % 50 == 0:
        print(f"  t={t:6.2f}: Ez²={ez:.6f}")

print("\nRunning simulation...")
sim.run(mp.at_every(0.5, record), until=50)

max_field = max(fields)
max_time = times[fields.index(max_field)]

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Max field intensity: {max_field:.6f}")
print(f"Peak time: {max_time:.2f}")

if max_field > 0.001:
    print("\n✓ Source is working! Field detected.")
else:
    print("\n✗ Source appears dead - no field detected.")
    print("  This is a source configuration problem.")
