from analytical_model import calculate
from geometry import direct_path_visibility
from plot_geometry import make_plot

def main():
    values = calculate()
    visible, outside = direct_path_visibility()

    print("=== NLOS MICROWAVE PROJECT: BASELINE ===")
    print(f"Frequency: {values['frequency_hz']/1e9:.3f} GHz")
    print(f"Wavelength: {values['wavelength_m']*1000:.3f} mm")
    print(f"Grid spacing (lambda/20): {values['dx_m']*1000:.3f} mm")
    print(f"Maximum CFL time step: {values['dt_max_s']*1e12:.3f} ps")
    print(f"Chosen time step (0.99 CFL): {values['dt_used_s']*1e12:.3f} ps")
    print(f"Tx-to-reflector distance: {values['d_tx_reflector_m']:.3f} m")
    print(f"Reflector-to-Rx distance: {values['d_reflector_rx_m']:.3f} m")
    print(f"Total specular path: {values['reflected_path_length_m']:.3f} m")
    print(f"First Fresnel radius at reflector: {values['first_fresnel_radius_m']*100:.2f} cm")
    print(f"Plate length: {values['plate_length_over_lambda']:.1f} wavelengths")
    print(f"Theoretical plate angle: {values['plate_angle_deg']:.1f} deg")
    print(f"Reflected direction: {values['reflected_direction']}")
    print(f"Direct path entirely inside corridor: {visible}")
    print(f"Unobstructed LOS FSPL reference: {values['unobstructed_direct_fspl_db']:.2f} dB")
    print("NOTE: Friis FSPL is an unobstructed LOS reference, not reflected-link received power.")

    make_plot()

if __name__ == "__main__":
    main()
