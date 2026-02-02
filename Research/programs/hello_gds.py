
import gdsfactory as gf

# ACTIVATE THE GENERIC PDK (Process Design Kit)
# This provides the standard layer definitions and component settings
# for a "generic" photonic process.
gf.gpdk.PDK.activate()

def create_simple_chip():
    """
    Creates a simple GDSII file with a few basic optical components:
    1. A straight waveguide
    2. A ring resonator (like in your simulations)
    3. A Y-splitter
    """
    # 1. Create a Component (the empty canvas)
    c = gf.Component("My_First_Chip")

    # 2. Add a Straight Waveguide
    # This creates a straight waveguide of length 10um
    wg = c << gf.components.straight(length=10, width=0.5)
    wg.dmovey(0) # Position it at y=0

    # 3. Add a Ring Resonator
    # This uses your simulation parameters (radius approx 4.4um for Polymer)
    # The 'width' is passed via the cross_section argument in newer GDSFactory versions
    # We define a simple cross section with the desired width and minimum bend radius
    # The default generic PDK has a minimum bend radius of 5um, so we need to relax that for our small ring
    xs = gf.cross_section.strip(width=0.5, radius=4.4, radius_min=4.0)
    ring = c << gf.components.ring_single(radius=4.4, gap=0.2, cross_section=xs)
    ring.dmovey(20) # Move it up so it doesn't overlap

    # 4. Add a Y-Splitter (1x2 MMI)
    splitter = c << gf.components.mmi1x2(width_mmi=3, length_mmi=10, gap_mmi=0.5)
    splitter.dmovey(40) # Move it up further

    # 5. Connect them (Optional but cool)
    # Let's add a bend to connect the output of the splitter to a new waveguide
    # This shows how "routing" works
    
    # 6. Show the component
    # This will pop up the KLayout viewer if you run it locally.
    # For now, we just verify it builds.
    print(f"Component '{c.name}' created with:")
    # In newer GDSFactory (v7+), references are accessed via .insts or simplified
    print(f" - {len(c.insts)} sub-components")
    # c.ports is now a dictionary-like object, but we can iterate over it directly or cast to list
    print(f" - Ports: {list(c.ports)}")

    # 7. Write to GDS file
    gds_path = c.write("my_first_chip.gds")
    print(f"GDS file written to: {gds_path}")

    # 8. Show matplotlib plot
    c.plot()
    import matplotlib.pyplot as plt
    plt.show()

    return c

if __name__ == "__main__":
    create_simple_chip()
