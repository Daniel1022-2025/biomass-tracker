# utils.py

def compute_alert_level(value):
    """
    Returns a color code based on biomass value.
    - Green for healthy (≥ 80)
    - Orange for moderate (40–79)
    - Red for low (< 40)
    """
    if value >= 80:
        return "#4caf50"  # green
    elif value >= 40:
        return "#ff9800"  # orange
    else:
        return "#f44336"  # red


def compute_alert_label(value):
    """
    Returns a human-readable label for the biomass level.
    """
    if value >= 80:
        return "Healthy"
    elif value >= 40:
        return "Moderate"
    else:
        return "Critical"


def format_biomass(value):
    """
    Formats biomass value to 2 decimal places with units.
    """
    return f"{value:.2f} g/m²"