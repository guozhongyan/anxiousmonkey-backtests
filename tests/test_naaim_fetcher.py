import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import fetchers.naaim as naaim


def test_naaim_handles_uppercase_columns(tmp_path, monkeypatch):
    csv_text = "Date,Exposure\n2024-01-01,100\n2024-01-02,110\n"
    monkeypatch.setattr(naaim, "get_text_with_fallbacks", lambda urls, timeout=30: csv_text)
    monkeypatch.setattr(naaim, "load_prev_csv", lambda path: None)
    out_path = tmp_path / "naaim_exposure.csv"
    monkeypatch.setattr(naaim, "OUT_CSV", str(out_path))
    naaim.main()
    df = pd.read_csv(out_path)
    assert list(df.columns) == ["date", "value"]
    assert len(df) == 2
