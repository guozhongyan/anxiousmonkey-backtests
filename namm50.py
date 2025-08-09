
import pandas as pd, numpy as np

def zscore(s: pd.Series):
    s = pd.Series(s).astype(float)
    m = s.mean()
    sd = s.std(ddof=0) or 1.0
    return (s - m)/sd

def combine(naaim: pd.Series=None, breadth: pd.Series=None, china: pd.Series=None, fred_level: pd.Series=None):
    parts = []
    if naaim is not None and len(naaim)>30: parts.append(zscore(naaim).rename("NAAIM"))
    if breadth is not None and len(breadth)>30: parts.append(zscore(breadth).rename("BREADTH"))
    if china is not None and len(china)>30: parts.append(zscore(china.pct_change(20)).rename("CHINA_MOMO"))
    if fred_level is not None and len(fred_level)>30: parts.append(zscore(fred_level.diff().fillna(0)).rename("FRED_DELTA"))
    if not parts:
        return pd.Series(dtype=float)
    X = pd.concat(parts, axis=1).dropna()
    score = X.mean(axis=1)
    return score

def regime_from(score: pd.Series, on=0.5, off=-0.5):
    if score.empty: return pd.Series(dtype=object)
    r = pd.Series(index=score.index, dtype=object)
    r[score >= on] = "Risk-On"
    r[score <= off] = "Risk-Off"
    r[(score < on) & (score > off)] = "Neutral"
    return r
