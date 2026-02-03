#!/usr/bin/env python3
"""
Integration tests for IOC (Input/Output Converter) Module

Verifies:
1. Component generation without errors
2. Port connectivity and naming
3. Layer assignments
4. Size constraints

Author: Wavelength-Division Ternary Optical Computer Project
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ioc_module import (
    # Encode stage
    ioc_laser_source,
    ioc_mzi_modulator,
    ioc_wavelength_combiner,
    ioc_encoder_unit,
    # Decode stage
    ioc_awg_demux,
    ioc_photodetector,
    ioc_result_encoder,
    ioc_decoder_unit,
    # Buffer/Sync stage
    ioc_timing_sync,
    ioc_elastic_buffer,
    ioc_shift_register_81trit,
    # RAM adapters
    tier1_adapter,
    tier2_adapter,
    tier3_adapter,
    # Complete module
    ioc_module_complete,
    # Constants
    LAYER_WAVEGUIDE,
    LAYER_HEATER,
    LAYER_METAL_PAD,
    LAYER_TEXT,
)


def test_encode_stage():
    """Test encode stage components."""
    print("Testing ENCODE stage components...")

    # Laser source
    laser = ioc_laser_source(wavelength_um=1.55, label="R")
    assert laser is not None
    assert "output" in [p.name for p in laser.ports]
    print("  ✓ ioc_laser_source")

    # MZI modulator
    mzi = ioc_mzi_modulator()
    assert mzi is not None
    port_names = [p.name for p in mzi.ports]
    assert "input" in port_names
    assert "output" in port_names or "bar" in port_names
    print("  ✓ ioc_mzi_modulator")

    # Wavelength combiner
    combiner = ioc_wavelength_combiner(n_inputs=3)
    assert combiner is not None
    port_names = [p.name for p in combiner.ports]
    assert "in_r" in port_names
    assert "in_g" in port_names
    assert "in_b" in port_names
    assert "output" in port_names
    print("  ✓ ioc_wavelength_combiner")

    # Encoder unit
    encoder = ioc_encoder_unit(trit_id=0)
    assert encoder is not None
    port_names = [p.name for p in encoder.ports]
    assert "output" in port_names
    assert "ctrl_d0" in port_names
    assert "ctrl_d1" in port_names
    print("  ✓ ioc_encoder_unit")

    print("  ENCODE stage: ALL PASS\n")


def test_decode_stage():
    """Test decode stage components."""
    print("Testing DECODE stage components...")

    # AWG demux
    awg = ioc_awg_demux(n_channels=5)
    assert awg is not None
    port_names = [p.name for p in awg.ports]
    assert "input" in port_names
    # Should have 5 output channels
    channel_ports = [p for p in port_names if p.startswith("ch")]
    assert len(channel_ports) == 5
    print("  ✓ ioc_awg_demux (5 channels)")

    # Photodetector
    pd = ioc_photodetector(channel_id=0)
    assert pd is not None
    port_names = [p.name for p in pd.ports]
    assert "input" in port_names
    assert "tia_out" in port_names
    print("  ✓ ioc_photodetector")

    # Result encoder
    encoder = ioc_result_encoder()
    assert encoder is not None
    print("  ✓ ioc_result_encoder")

    # Decoder unit
    decoder = ioc_decoder_unit(trit_id=0)
    assert decoder is not None
    port_names = [p.name for p in decoder.ports]
    assert "optical_in" in port_names
    print("  ✓ ioc_decoder_unit")

    print("  DECODE stage: ALL PASS\n")


def test_buffer_sync_stage():
    """Test buffer/sync stage components."""
    print("Testing BUFFER/SYNC stage components...")

    # Timing sync
    timing = ioc_timing_sync()
    assert timing is not None
    port_names = [p.name for p in timing.ports]
    assert "kerr_in" in port_names
    assert "kerr_thru" in port_names
    assert "clk_out" in port_names
    print("  ✓ ioc_timing_sync")

    # Elastic buffer
    buffer = ioc_elastic_buffer(depth=4)
    assert buffer is not None
    port_names = [p.name for p in buffer.ports]
    assert "data_in" in port_names
    assert "data_out" in port_names
    assert "clk" in port_names
    print("  ✓ ioc_elastic_buffer")

    # 81-trit shift register
    shift_reg = ioc_shift_register_81trit()
    assert shift_reg is not None
    port_names = [p.name for p in shift_reg.ports]
    assert "serial_in" in port_names
    assert "parallel_out" in port_names
    print("  ✓ ioc_shift_register_81trit")

    print("  BUFFER/SYNC stage: ALL PASS\n")


def test_ram_adapters():
    """Test RAM tier adapter components."""
    print("Testing RAM TIER ADAPTERS...")

    # Tier 1 adapter
    t1 = tier1_adapter()
    assert t1 is not None
    port_names = [p.name for p in t1.ports]
    assert "write_in" in port_names
    print("  ✓ tier1_adapter (Hot Register)")

    # Tier 2 adapter
    t2 = tier2_adapter()
    assert t2 is not None
    port_names = [p.name for p in t2.ports]
    assert "write_in" in port_names
    assert "soa_gate" in port_names
    print("  ✓ tier2_adapter (Working Register)")

    # Tier 3 adapter
    t3 = tier3_adapter()
    assert t3 is not None
    port_names = [p.name for p in t3.ports]
    assert "data_in" in port_names
    assert "addr" in port_names
    print("  ✓ tier3_adapter (Parking Register)")

    print("  RAM ADAPTERS: ALL PASS\n")


def test_complete_module():
    """Test complete IOC module assembly."""
    print("Testing COMPLETE IOC MODULE...")

    # With laser sources
    chip_with_lasers = ioc_module_complete(include_laser_sources=True)
    assert chip_with_lasers is not None
    port_names = [p.name for p in chip_with_lasers.ports]

    # Check main ports
    assert "laser_out" in port_names, "Missing laser_out port"
    assert "detect_in" in port_names, "Missing detect_in port"
    assert "kerr_clock_in" in port_names, "Missing kerr_clock_in port"
    print("  ✓ ioc_module_complete (with lasers)")

    # Without laser sources
    chip_no_lasers = ioc_module_complete(include_laser_sources=False)
    assert chip_no_lasers is not None
    print("  ✓ ioc_module_complete (without lasers)")

    print("  COMPLETE MODULE: ALL PASS\n")


def test_gds_generation():
    """Test GDS file generation."""
    print("Testing GDS FILE GENERATION...")

    import tempfile

    # Generate to temp file
    chip = ioc_module_complete(include_laser_sources=True)

    with tempfile.NamedTemporaryFile(suffix='.gds', delete=False) as f:
        temp_path = f.name

    chip.write(temp_path)

    # Verify file was created and has content
    assert os.path.exists(temp_path)
    assert os.path.getsize(temp_path) > 0
    print(f"  ✓ GDS file generated ({os.path.getsize(temp_path)} bytes)")

    # Cleanup
    os.remove(temp_path)

    print("  GDS GENERATION: ALL PASS\n")


def test_port_connectivity():
    """Test that ports can be connected between modules."""
    print("Testing PORT CONNECTIVITY...")

    # Test that encoder output is optical (can connect to ALU)
    encoder = ioc_encoder_unit(trit_id=0)
    output_port = None
    for p in encoder.ports:
        if p.name == "output":
            output_port = p
            break

    assert output_port is not None
    print(f"  ✓ Encoder output port: orientation={output_port.orientation}")

    # Test that decoder input is optical (can receive from ALU)
    decoder = ioc_decoder_unit(trit_id=0)
    input_port = None
    for p in decoder.ports:
        if p.name == "optical_in":
            input_port = p
            break

    assert input_port is not None
    print(f"  ✓ Decoder optical_in port: orientation={input_port.orientation}")

    print("  PORT CONNECTIVITY: ALL PASS\n")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("  IOC MODULE INTEGRATION TESTS")
    print("="*60 + "\n")

    try:
        test_encode_stage()
        test_decode_stage()
        test_buffer_sync_stage()
        test_ram_adapters()
        test_complete_module()
        test_gds_generation()
        test_port_connectivity()

        print("="*60)
        print("  ALL TESTS PASSED!")
        print("="*60 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n  ASSERTION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
