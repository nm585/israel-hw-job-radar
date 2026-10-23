from pathlib import Path
import yaml


def test_source_names_are_unique_enough():
    cfg = yaml.safe_load(Path("config/sources.yaml").read_text())
    enabled = [s for s in cfg["sources"] if s.get("enabled", True)]
    names = [s["name"] for s in enabled]
    assert len(names) == len(set(names))
    watch = yaml.safe_load(Path("config/watchlist.yaml").read_text())["watchlist"]
    assert len(names) + len(watch) >= 60
    for src in enabled:
        assert src.get("verification") in {"live_adapter_returned_jobs", "live_structured_feed_empty"}


def test_no_accidental_lm_studio_element_labs_source():
    text = Path("config/sources.yaml").read_text().lower()
    assert "elementlabs.ai" in text  # explanatory warning is present
    enabled_urls = []
    cfg = yaml.safe_load(Path("config/sources.yaml").read_text())
    for src in cfg["sources"]:
        if src.get("enabled", True):
            enabled_urls.append(str(src.get("url", "")))
    assert all("elementlabs.ai" not in u.lower() for u in enabled_urls)


def test_requested_names_preserved():
    cfg = yaml.safe_load(Path("config/sources.yaml").read_text())
    watch = yaml.safe_load(Path("config/watchlist.yaml").read_text())["watchlist"]
    entries = cfg["sources"] + watch
    names = " ".join(s["name"] + " " + " ".join(s.get("aliases", [])) for s in entries).lower()
    for name in ["Chain Reaction", "NeuroBlade", "Majestic Labs AI", "Exaware", "ColorChip", "Newsight Imaging", "Weebit Nano", "RAAM Memory Technologies", "HiveWare", "VisIC Technologies", "Articron", "Quantum Transistors", "Qarakal", "Q-Factor", "Microchip", "Hailo", "Qualcomm", "Autotalks", "MDA Space", "SatixFy", "Credo", "DustPhotonics", "Molex", "Teramount"]:
        assert name.lower() in names
    assert next(w for w in watch if w["name"] == "Articron")["israel_presence"] == "unverified"
