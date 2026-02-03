# Copyright (c) 2026 Christopher Riner
# Licensed under the MIT License. See LICENSE file for details.
#
# Wavelength-Division Ternary Optical Computer
# https://github.com/jackwayne234/-wavelength-ternary-optical-computer
#
# This file is part of an open source research project to develop a
# ternary optical computer using wavelength-division multiplexing.
# The research is documented in the paper published on Zenodo:
# DOI: 10.5281/zenodo.18437600

import os
import sys
import pytest
import glob

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts import sfg_mixer
from scripts import optical_selector
from scripts import y_junction
from scripts import photodetector

def get_data_path(filename):
    """
    Helper to get the absolute path to a file in the data directory.
    Assumes we are running from project root or inside scripts.
    """
    # Base dir is the parent of the 'scripts' directory containing this test file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", filename)

def test_sfg_mixer_execution():
    """
    Verifies that the SFG Mixer simulation runs and generates the spectrum plot.
    """
    # Run the simulation function
    sfg_mixer.run_sfg_simulation()
    
    # Check if output file exists
    output_plot = get_data_path("sfg_spectrum.png")
    assert os.path.exists(output_plot), f"SFG Spectrum plot was not created at {output_plot}"

def test_optical_selector_execution():
    """
    Verifies the Optical Selector runs for both ON and OFF states.
    """
    # Test OFF state
    optical_selector.run_selector_simulation(voltage_on=False)
    assert os.path.exists(get_data_path("selector_spectrum_OFF.png"))
    
    # Test ON state
    optical_selector.run_selector_simulation(voltage_on=True)
    assert os.path.exists(get_data_path("selector_spectrum_ON.png"))

def test_y_junction_execution():
    """
    Verifies the Y-Junction Combiner simulation.
    """
    y_junction.run_y_junction_simulation()
    assert os.path.exists(get_data_path("y_junction_spectrum.png"))
    assert os.path.exists(get_data_path("y_junction_geometry.png"))


def test_photodetector_execution():
    """
    Verifies the Photodetector simulation.
    """
    # Capture stdout to check for detection message if needed,
    # but for now just check it runs without error.
    photodetector.run_photodetector_simulation()

    # Verify data files if any (we print to stdout, but we could check for log files)
    # Ideally, we'd check the return value of the function, but our scripts print to stdout.
    # We assume success if no exception is raised.


# =============================================================================
# NEW TESTS: Log/Exp Converters, Optimization, ALU Selectors, Timing, Masks
# =============================================================================

def test_alu_with_wavelength_selectors():
    """
    Verifies the ALU with wavelength selectors component generates correctly.
    """
    from programs.ternary_chip_generator import alu_with_wavelength_selectors

    # Generate ALU with selectors
    alu = alu_with_wavelength_selectors(
        name="test_alu_selectors",
        include_wavelength_selectors=True,
        selector_type='mzi'
    )

    # Verify component was created
    assert alu is not None

    # Check for expected ports
    expected_ports = ['input_a', 'input_b', 'ctrl_linear', 'ctrl_log',
                      'ctrl_sfg', 'ctrl_dfg', 'out_neg2', 'out_neg1',
                      'out_zero', 'out_pos1', 'out_pos2']
    for port_name in expected_ports:
        assert port_name in alu.ports, f"Missing port: {port_name}"

    # Check for selector control ports (only when selectors included)
    selector_ports = ['ctrl_sel_a_r', 'ctrl_sel_a_g', 'ctrl_sel_a_b',
                      'ctrl_sel_b_r', 'ctrl_sel_b_g', 'ctrl_sel_b_b']
    for port_name in selector_ports:
        assert port_name in alu.ports, f"Missing selector port: {port_name}"


def test_alu_without_wavelength_selectors():
    """
    Verifies the ALU without wavelength selectors (direct path).
    """
    from programs.ternary_chip_generator import alu_with_wavelength_selectors

    # Generate ALU without selectors
    alu = alu_with_wavelength_selectors(
        name="test_alu_no_selectors",
        include_wavelength_selectors=False
    )

    assert alu is not None

    # Main ports should still exist
    assert 'input_a' in alu.ports
    assert 'input_b' in alu.ports
    assert 'out_zero' in alu.ports


def test_log_exp_simulation_module():
    """
    Verifies that the log/exp simulation module can be imported and
    its key functions are callable.
    """
    from programs import log_exp_simulation

    # Check functions exist
    assert hasattr(log_exp_simulation, 'run_log_converter_simulation')
    assert hasattr(log_exp_simulation, 'run_exp_converter_simulation')
    assert hasattr(log_exp_simulation, 'plot_transfer_functions')

    # Note: Full simulation run is too slow for unit tests
    # Integration tests should run the full simulation


def test_optimize_log_converter_module():
    """
    Verifies that the optimization module can be imported and
    its analytical model functions work correctly.
    """
    from programs import optimize_log_converter
    import numpy as np

    # Check functions exist
    assert hasattr(optimize_log_converter, 'saturable_absorber_model')
    assert hasattr(optimize_log_converter, 'fit_to_log_curve')
    assert hasattr(optimize_log_converter, 'calculate_dynamic_range')

    # Test analytical model with known values
    input_powers = np.logspace(-1, 2, 20)
    output_powers = optimize_log_converter.saturable_absorber_model(
        input_powers, i_sat=1.0, length_um=50.0, alpha_0=2.0
    )

    # Output should be less than input (absorption)
    assert np.all(output_powers <= input_powers)

    # Output should be positive
    assert np.all(output_powers > 0)

    # Test R-squared fitting
    r_squared = optimize_log_converter.fit_to_log_curve(input_powers, output_powers)
    assert 0 <= r_squared <= 1


def test_carry_chain_timing_module():
    """
    Verifies that the carry chain timing module can be imported and
    its utility functions work correctly.
    """
    from programs import carry_chain_timing_sim

    # Check functions exist
    assert hasattr(carry_chain_timing_sim, 'calculate_delay_line_length')
    assert hasattr(carry_chain_timing_sim, 'simulate_carry_chain_timing')

    # Test delay line calculation
    length_um = carry_chain_timing_sim.calculate_delay_line_length(
        delay_ps=20.0, n_eff=2.2
    )

    # Should be approximately 2725 um for 20 ps at n=2.2
    # L = t * c / n = 20e-12 * 3e8 / 2.2 = 2.73e-3 m = 2725 um
    assert 2700 < length_um < 2800, f"Expected ~2725 um, got {length_um}"


def test_carry_chain_analytical_simulation():
    """
    Tests the analytical carry chain simulation (fast, no FDTD).
    """
    from programs import carry_chain_timing_sim

    # Run analytical simulation
    result = carry_chain_timing_sim.simulate_carry_chain_timing(
        n_trits=81,
        inter_trit_delay_ps=20.0,
        soa_interval=3,
        soa_gain_db=30.0
    )

    # Verify results
    assert result['n_trits'] == 81
    assert result['total_delay_ps'] == 1620  # 81 * 20 ps
    assert result['n_soas'] == 27  # 81 / 3
    assert len(result['trit_numbers']) == 81
    assert len(result['signal_levels_db']) == 81


def test_mask_layer_generator_module():
    """
    Verifies that the mask layer generator can be imported and
    generates test components correctly.
    """
    from programs import mask_layer_generator

    # Check functions exist
    assert hasattr(mask_layer_generator, 'generate_test_chip')
    assert hasattr(mask_layer_generator, 'add_alignment_marks')
    assert hasattr(mask_layer_generator, 'extract_mask_layers')

    # Generate test chip
    test_chip = mask_layer_generator.generate_test_chip()
    assert test_chip is not None

    # Verify it has polygons on expected layers
    polygons = test_chip.get_polygons(by_spec=True)
    expected_layers = [(1, 0), (10, 0), (12, 0), (2, 0), (4, 0), (13, 0), (14, 0)]

    for layer in expected_layers:
        assert layer in polygons, f"Missing layer {layer} in test chip"


def test_layer_mapping_completeness():
    """
    Verifies that all required mask layers are defined in the mapping.
    """
    from programs.mask_layer_generator import LAYER_MAPPING

    required_masks = [
        'WAVEGUIDE', 'METAL1_HEATER', 'METAL2_PAD',
        'CHI2_POLING', 'DOPING_SA', 'DOPING_GAIN'
    ]

    for mask in required_masks:
        assert mask in LAYER_MAPPING, f"Missing mask definition: {mask}"
        assert 'source_layers' in LAYER_MAPPING[mask]
        assert 'process' in LAYER_MAPPING[mask]
        assert 'description' in LAYER_MAPPING[mask]
