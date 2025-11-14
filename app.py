"""
Interactive Föhn Effect Analysis Dashboard

A Streamlit web application for exploring atmospheric thermodynamics
and the Föhn effect using real-time parameter adjustments.

Author: João Manero
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from metpy.plots import SkewT
from metpy.units import units
import metpy.calc as mpcalc
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.skewt_plot import FoehnEffectAnalyzer

# Page configuration
st.set_page_config(
    page_title="Föhn Effect Analyzer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">Föhn Effect: Interactive Weather Analysis</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Quantitative prediction of temperature anomalies from orographic processes</p>', unsafe_allow_html=True)

# Introduction
with st.expander("What is the Föhn Effect?", expanded=False):
    st.markdown("""
    The **Föhn effect** is a meteorological phenomenon where air warms dramatically 
    and dries as it descends the leeward side of a mountain range.
    
    **Real-world impacts:**
    * **Agriculture**: Crop stress, irrigation planning, frost protection
    * **Energy**: Cooling demand spikes, grid management
    * **Aviation**: Turbulence, visibility changes, wind shear
    * **Wildfire**: Increased ignition risk from hot, dry conditions
    * **Insurance**: Climate risk assessment, premium pricing
    
    **Physical process:**
    1. Moist air rises on windward side, cooling and forming clouds
    2. Precipitation removes moisture at summit
    3. Dry air descends leeward side, warming rapidly
    4. Result: Hot, dry conditions (temperature increases of 10-20°C possible)
    """)

# Sidebar - Input Parameters
st.sidebar.header("Configuration")

st.sidebar.subheader("Location Profile")
location_preset = st.sidebar.selectbox(
    "Preset Locations",
    ["Madeira Island (Default)", "Custom Parameters"],
    help="Select a pre-configured location or enter custom values"
)

# Preset data
if location_preset == "Madeira Island (Default)":
    default_values = {
        'north_p': 1000, 'north_t': 20.0, 'north_td': 10.5,
        'north_mr': 8.0, 'summit_p': 400, 'south_p': 1000
    }
else:
    default_values = {
        'north_p': 1013, 'north_t': 18.0, 'north_td': 12.0,
        'north_mr': 9.0, 'summit_p': 500, 'south_p': 1013
    }

st.sidebar.subheader("Windward Side (Initial)")
north_pressure = st.sidebar.number_input(
    "Pressure (hPa)", 
    min_value=900, max_value=1050, 
    value=default_values['north_p'],
    help="Surface pressure on windward side"
)

north_temp = st.sidebar.slider(
    "Temperature (°C)", 
    min_value=-10.0, max_value=40.0, 
    value=default_values['north_t'], step=0.5,
    help="Air temperature at surface"
)

north_dewpoint = st.sidebar.slider(
    "Dewpoint (°C)", 
    min_value=-20.0, max_value=30.0, 
    value=default_values['north_td'], step=0.5,
    help="Dewpoint temperature (moisture indicator)"
)

north_mixing_ratio = st.sidebar.slider(
    "Mixing Ratio (g/kg)", 
    min_value=0.0, max_value=20.0, 
    value=default_values['north_mr'], step=0.5,
    help="Water vapor content"
)

st.sidebar.subheader("Mountain Profile")
summit_pressure = st.sidebar.number_input(
    "Summit Pressure (hPa)", 
    min_value=300, max_value=800, 
    value=default_values['summit_p'],
    help="Pressure at mountain peak"
)

st.sidebar.subheader("Leeward Side")
south_pressure = st.sidebar.number_input(
    "Surface Pressure (hPa)", 
    min_value=900, max_value=1050, 
    value=default_values['south_p'],
    help="Surface pressure on leeward side"
)

# Calculate button
analyze_button = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

# Validation
if north_dewpoint > north_temp:
    st.sidebar.error("WARNING: Dewpoint cannot exceed temperature")
    st.stop()

if summit_pressure >= north_pressure:
    st.sidebar.error("WARNING: Summit pressure must be less than surface pressure")
    st.stop()

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Skew-T Log-P Diagram")
    
    # Create analyzer
    analyzer = FoehnEffectAnalyzer(fig_size=(10, 8))
    analyzer.configure_diagram(
        p_min=summit_pressure - 50,
        p_max=north_pressure + 20,
        t_min=-40,
        t_max=45
    )
    
    # Set conditions
    analyzer.set_initial_conditions(
        north_pressure, north_temp, north_dewpoint, north_mixing_ratio
    )
    
    # Calculate LCL (Lifting Condensation Level)
    lcl_pressure, lcl_temp = mpcalc.lcl(
        north_pressure * units.hPa,
        north_temp * units.degC,
        north_dewpoint * units.degC
    )
    
    # Calculate summit temperature (moist adiabatic from LCL)
    pressures_ascent = np.linspace(lcl_pressure.m, summit_pressure, 50) * units.hPa
    summit_temp_calc = mpcalc.moist_lapse(
        pressures_ascent, lcl_temp, lcl_pressure
    )[-1]
    
    # Calculate new mixing ratio at summit (assume 50% moisture loss)
    summit_mixing_ratio = north_mixing_ratio * 0.5
    
    # Calculate leeward LCL (where parcel becomes unsaturated on descent)
    # Approximate as midpoint between summit and surface
    lcl_descent_pressure = (summit_pressure + south_pressure) / 2
    pressures_descent_moist = np.linspace(summit_pressure, lcl_descent_pressure, 50) * units.hPa
    lcl_descent_temp = mpcalc.moist_lapse(
        pressures_descent_moist, summit_temp_calc, summit_pressure * units.hPa
    )[-1]
    
    # Calculate final temperature (dry adiabatic from leeward LCL)
    pressures_descent_dry = np.linspace(lcl_descent_pressure, south_pressure, 50) * units.hPa
    south_temp_calc = mpcalc.dry_lapse(
        pressures_descent_dry, lcl_descent_temp
    )[-1]
    
    # Calculate final dewpoint from mixing ratio
    south_dewpoint_calc = mpcalc.dewpoint_from_specific_humidity(
        south_pressure * units.hPa,
        south_temp_calc,
        mpcalc.specific_humidity_from_mixing_ratio(summit_mixing_ratio * units('g/kg'))
    )
    
    # Plot points
    analyzer.plot_observation_point(
        north_pressure * units.hPa,
        north_temp * units.degC,
        'orange',
        'Windward Surface'
    )
    
    analyzer.plot_observation_point(
        lcl_pressure,
        lcl_temp,
        'cyan',
        'LCL (Cloud Base)'
    )
    
    analyzer.plot_observation_point(
        summit_pressure * units.hPa,
        summit_temp_calc,
        'red',
        'Summit'
    )
    
    analyzer.plot_observation_point(
        south_pressure * units.hPa,
        south_temp_calc,
        'orange',
        'Leeward Surface (Föhn)'
    )
    
    # Plot processes
    analyzer.plot_adiabatic_process(
        north_pressure, lcl_pressure.m,
        north_temp * units.degC,
        process_type='dry',
        color='blue',
        label='Dry Ascent'
    )
    
    analyzer.plot_adiabatic_process(
        lcl_pressure.m, summit_pressure,
        lcl_temp,
        process_type='moist',
        color='green',
        label='Moist Ascent (Precipitation)'
    )
    
    analyzer.plot_adiabatic_process(
        summit_pressure, lcl_descent_pressure,
        summit_temp_calc,
        process_type='moist',
        color='green',
        linestyle='--',
        label='Moist Descent'
    )
    
    analyzer.plot_adiabatic_process(
        lcl_descent_pressure, south_pressure,
        lcl_descent_temp,
        process_type='dry',
        color='red',
        linestyle='-',
        label='Dry Descent (Föhn)'
    )
    
    # Finalize
    analyzer.finalize_plot(
        'Föhn Effect Analysis',
        legend_loc='upper left'
    )
    
    # Display plot in Streamlit
    st.pyplot(analyzer.fig)

with col2:
    st.subheader("Analysis Results")
    
    # Calculate metrics
    temp_increase = south_temp_calc.to('degC').m - north_temp
    final_rh = mpcalc.relative_humidity_from_dewpoint(
        south_temp_calc,
        south_dewpoint_calc
    ).to('percent').m
    
    moisture_loss = north_mixing_ratio - summit_mixing_ratio
    
    # Display metrics
    st.metric(
        "Temperature Change",
        f"+{temp_increase:.1f}°C",
        delta=f"{temp_increase:.1f}°C increase",
        delta_color="inverse"
    )
    
    st.metric(
        "Final Temperature",
        f"{south_temp_calc.to('degC').m:.1f}°C",
        delta=f"vs {north_temp:.1f}°C initial"
    )
    
    st.metric(
        "Relative Humidity",
        f"{final_rh:.1f}%",
        delta=f"-{100-final_rh:.0f}% decrease",
        delta_color="off"
    )
    
    st.metric(
        "Moisture Loss",
        f"{moisture_loss:.1f} g/kg",
        delta=f"{(moisture_loss/north_mixing_ratio)*100:.0f}% lost",
        delta_color="off"
    )
    
    # Detailed results table
    st.subheader("Detailed Analysis")
    
    results_data = {
        "Location": ["Windward", "LCL", "Summit", "Leeward"],
        "Pressure (hPa)": [
            north_pressure,
            int(lcl_pressure.m),
            summit_pressure,
            south_pressure
        ],
        "Temperature (°C)": [
            f"{north_temp:.1f}",
            f"{lcl_temp.to('degC').m:.1f}",
            f"{summit_temp_calc.to('degC').m:.1f}",
            f"{south_temp_calc.to('degC').m:.1f}"
        ],
        "Conditions": [
            "Initial",
            "Cloud base",
            "Precipitation",
            "Föhn (Hot & Dry)"
        ]
    }
    
    st.table(results_data)
    
    # Risk assessment
    st.subheader("Risk Assessment")
    
    if temp_increase > 15:
        st.error("EXTREME RISK: Very high wildfire danger")
    elif temp_increase > 10:
        st.warning("HIGH RISK: Elevated wildfire and heat stress potential")
    elif temp_increase > 5:
        st.info("MODERATE: Notable temperature anomaly")
    else:
        st.success("LOW RISK: Normal conditions")
    
    if final_rh < 20:
        st.error("EXTREME DRYNESS: Critical fire weather conditions")
    elif final_rh < 30:
        st.warning("VERY DRY: High evapotranspiration rate")
    else:
        st.info("Normal humidity levels")

# Download section
st.divider()
st.subheader("Export Results")

col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    if st.button("Download Plot (PNG)", use_container_width=True):
        analyzer.save_figure('/tmp/foehn_analysis.png', dpi=300)
        with open('/tmp/foehn_analysis.png', 'rb') as f:
            st.download_button(
                "Save Image",
                f,
                "foehn_analysis.png",
                "image/png",
                use_container_width=True
            )

with col_dl2:
    # Generate report
    report = f"""
FÖHN EFFECT ANALYSIS REPORT
Generated: {st.session_state.get('timestamp', 'N/A')}

INPUT PARAMETERS
================
Windward Side:
- Pressure: {north_pressure} hPa
- Temperature: {north_temp}°C
- Dewpoint: {north_dewpoint}°C
- Mixing Ratio: {north_mixing_ratio} g/kg

Mountain Profile:
- Summit Pressure: {summit_pressure} hPa

RESULTS
=======
Leeward Side (Föhn):
- Temperature: {south_temp_calc.to('degC').m:.1f}°C
- Dewpoint: {south_dewpoint_calc.to('degC').m:.1f}°C
- Relative Humidity: {final_rh:.1f}%

FÖHN EFFECT METRICS
===================
- Temperature Increase: +{temp_increase:.1f}°C
- Moisture Loss: {moisture_loss:.1f} g/kg ({(moisture_loss/north_mixing_ratio)*100:.0f}%)

INTERPRETATION
==============
This analysis demonstrates {"an extreme" if temp_increase > 10 else "a moderate"} Föhn effect
with significant warming and drying on the leeward side.
"""
    
    st.download_button(
        "Download Report (TXT)",
        report,
        "foehn_report.txt",
        "text/plain",
        use_container_width=True
    )

with col_dl3:
    if st.button("Export Data (CSV)", use_container_width=True):
        import pandas as pd
        df = pd.DataFrame(results_data)
        csv = df.to_csv(index=False)
        st.download_button(
            "Save CSV",
            csv,
            "foehn_data.csv",
            "text/csv",
            use_container_width=True
        )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><strong>Föhn Effect Analyzer</strong> | Built with Python, MetPy & Streamlit</p>
    <p>Developed by <strong>João Manero</strong> | 
    <a href="https://github.com/Miauneiro" target="_blank">GitHub</a> | 
    <a href="https://linkedin.com/in/joão-manero" target="_blank">LinkedIn</a></p>
    <p style='font-size: 0.8rem; margin-top: 1rem;'>
    For agricultural planning, energy forecasting, aviation safety, and climate risk assessment
    </p>
</div>
""", unsafe_allow_html=True)
