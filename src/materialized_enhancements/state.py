from __future__ import annotations

import reflex as rx

from materialized_enhancements.gene_data import UNIQUE_CATEGORIES


CATEGORY_COLORS: dict[str, str] = {
    "Radiation Resistance": "orange",
    "Longevity & Cancer Resistance": "green",
    "DNA Repair & Stress Resistance": "green",
    "Genome Stability": "green",
    "Oxidative Stress Resistance": "green",
    "Longevity & Metabolic Regulation": "green",
    "Longevity & Cognitive Protection": "green",
    "Cancer Resistance": "green",
    "Longevity & Cellular Rejuvenation": "green",
    "Extreme Longevity": "green",
    "Oncogenic Redundancy": "green",
    "Environmental Adaptation": "teal",
    "Hypoxia Tolerance": "teal",
    "Desiccation Tolerance": "orange",
    "Post-Damage Genome Repair": "orange",
    "Radiosynthesis": "orange",
    "Biological Immortality": "teal",
    "Distributed Stem Cell Regeneration": "teal",
    "Regeneration": "teal",
    "Viral Tolerance & Immune Balance": "blue",
    "Extreme Breath-Holding": "blue",
    "Extreme Cold Tolerance": "blue",
    "Unihemispheric Sleep": "violet",
    "Echolocation / Ultrasonic Hearing": "pink",
    "Infrared Sensing": "pink",
    "Hyper-Spectral Vision": "pink",
    "Magnetoreception": "pink",
    "Night Vision Enhancement": "pink",
    "Adaptive Camouflage": "pink",
    "Bioluminescence / Fluorescence": "pink",
    "True Bioluminescence": "pink",
    "Bioelectrogenesis": "orange",
    "Photosynthesis / Kleptoplasty": "teal",
    "Surface Adhesion": "teal",
}

CATEGORIES: list[str] = ["All"] + UNIQUE_CATEGORIES


class AppState(rx.State):
    """Root application state."""

    active_tab: str = "library"
    active_category: str = "All"

    def set_tab(self, tab: str) -> None:
        self.active_tab = tab

    def set_category(self, category: str) -> None:
        self.active_category = category
