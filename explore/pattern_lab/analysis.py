import pickle, numpy as np, pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA

def load(S):
    df = pickle.load(open(f"{S}/tokens.pkl", "rb"))
    df["dur"] = df.dur_ms
    df["d0"] = df.f2.apply(lambda a: a[0]) - df.f2mid
    df["d10"] = df.f2.apply(lambda a: a[1]) - df.f2mid
    df["d30"] = df.f2.apply(lambda a: a[3]) - df.f2mid
    df["f2_10"] = df.f2.apply(lambda a: a[1])
    sh = np.stack(df["shape"].values)
    df["shape_t"] = list(sh - sh.mean(axis=1, keepdims=True))   # remove each token's own level
    return df

SCALARS = ["cog", "fm", "sd", "skew", "kurt", "e0_2", "e2_4", "e4_6", "e6_8", "relamp", "dur"]
F2FEATS = ["d0", "d10", "d30", "f2_10", "f2mid"]

def normalise(df, cols):
    """z-score every feature inside each speaker (over all fricative classes); subtract speaker mean shape."""
    out = df.copy()
    for c in cols:
        g = out.groupby("spk")[c]
        out[c] = (out[c] - g.transform("mean")) / g.transform("std")
    shapes = np.stack(out["shape"].values)
    for s in out.spk.unique():
        m = (out.spk == s).values
        shapes[m] = shapes[m] - shapes[m].mean(axis=0)
    out["shape_n"] = list(shapes)
    return out

def bal_acc(y, p):
    return float(np.mean([(p[y == c] == c).mean() for c in np.unique(y)]))

def best_thresh(x, y):
    best = (0.0, None, 1)
    for t in np.unique(np.quantile(x, np.linspace(0.01, 0.99, 99))):
        for o in (1, -1):
            a = bal_acc(y, (o * (x - t) > 0).astype(int))
            if a > best[0]: best = (a, t, o)
    return best

def split(df, pair):
    d = df[df.phone.isin(pair)].copy(); d["y"] = (d.phone == pair[1]).astype(int); return d

def cross(d, fn):
    """Train on one speaker, test on the other, both directions; mean balanced accuracy."""
    accs = []
    for tr, te in (("bdl", "slt"), ("slt", "bdl")):
        a, b = d[d.spk == tr], d[d.spk == te]
        a, b = a.dropna(subset=fn.need), b.dropna(subset=fn.need)
        accs.append(bal_acc(b.y.values, fn(a, b)))
    return float(np.mean(accs)), accs

def thresh_fn(col):
    def f(a, b):
        _, t, o = best_thresh(a[col].values, a.y.values)
        return (o * (b[col].values - t) > 0).astype(int)
    f.need = [col]; return f

def same_rows(fn, extra):
    """Same classifier, but evaluated only on rows that also have `extra` columns (fair comparison)."""
    def f(a, b): return fn(a.dropna(subset=extra), b.dropna(subset=extra)) if False else fn(a, b)
    f.need = list(fn.need) + list(extra); return f

def lda_fn(cols=None, shape=None):
    def feats(d):
        parts = []
        if shape: parts.append(np.stack(d[shape].values))
        if cols: parts.append(d[cols].values)
        return np.hstack(parts)
    def f(a, b):
        m = LDA(solver="lsqr", shrinkage="auto", priors=[0.5, 0.5]).fit(feats(a), a.y.values)
        return m.predict(feats(b))
    f.need = (cols or []) + ([shape] if shape else []); return f

def template_fn(shape):
    def f(a, b):
        A = np.stack(a[shape].values); B = np.stack(b[shape].values)
        m0, m1 = A[a.y.values == 0].mean(0), A[a.y.values == 1].mean(0)
        return (np.linalg.norm(B - m1, axis=1) < np.linalg.norm(B - m0, axis=1)).astype(int)
    f.need = [shape]; return f

def table(df, pair, feats, extra):
    """rows: method -> (cross-speaker bal acc raw, normalised)"""
    d_raw = split(df, pair); d_n = split(normalise(df, SCALARS + F2FEATS), pair)
    rows = []
    for c in feats:
        rows.append((c, cross(d_raw, thresh_fn(c))[0], cross(d_n, thresh_fn(c))[0]))
    for name, mk in extra.items():
        rows.append((name,) + tuple(cross(d, fn)[0] for d, fn in ((d_raw, mk[0]), (d_n, mk[1]))))
    return pd.DataFrame(rows, columns=["method", "raw", "normalised"])

if __name__ == "__main__":
    import sys
    df = load(sys.argv[1])
    ext = {
        "template (token shape)": (template_fn("shape_t"), template_fn("shape_t")),
        "template (speaker-normalised shape)": (template_fn("shape"), template_fn("shape_n")),
        "LDA shape": (lda_fn(shape="shape_t"), lda_fn(shape="shape_n")),
        "LDA all scalars": (lda_fn(cols=SCALARS), lda_fn(cols=SCALARS)),
        "LDA shape+scalars": (lda_fn(cols=SCALARS, shape="shape_t"), lda_fn(cols=SCALARS, shape="shape_n")),
    }
    pd.set_option("display.width", 200)
    print("== S vs SH  (n:", df[df.phone.isin(['S','SH'])].groupby(['spk','phone']).size().to_dict(), ")")
    print(table(df, ("S", "SH"), SCALARS, ext).round(3).to_string(index=False))
    exts = dict(ext)
    exts["LDA scalars (rows with F2)"] = (same_rows(lda_fn(cols=SCALARS), ["d0", "d10", "d30", "f2mid"]), same_rows(lda_fn(cols=SCALARS), ["d0", "d10", "d30", "f2mid"]))
    exts["LDA scalars + F2"] = (lda_fn(cols=SCALARS + ["d0", "d10", "d30", "f2mid"]), lda_fn(cols=SCALARS + ["d0", "d10", "d30", "f2mid"]))
    print("\n== S vs SH incl. F2 (rows with F2:", int(df[df.phone.isin(['S','SH'])].d0.notna().sum()), ")")
    print(table(df, ("S", "SH"), SCALARS + F2FEATS, exts).round(3).loc[lambda x: x.method.isin(F2FEATS + ["cog", "e2_4", "LDA all scalars", "LDA scalars (rows with F2)", "LDA scalars + F2"])].to_string(index=False))
    extf = dict(ext); extf["LDA shape+F2"] = (lda_fn(cols=["d10", "d30", "f2mid"], shape="shape_t"), lda_fn(cols=["d10", "d30", "f2mid"], shape="shape_n"))
    extf["LDA all scalars (same rows as F2)"] = (same_rows(lda_fn(cols=SCALARS), ["d10", "d30", "f2mid"]), same_rows(lda_fn(cols=SCALARS), ["d10", "d30", "f2mid"]))
    extf["LDA scalars+F2"] = (lda_fn(cols=SCALARS + ["d10", "d30", "f2mid"]), lda_fn(cols=SCALARS + ["d10", "d30", "f2mid"]))
    print("\n== TH vs F  (n:", df[df.phone.isin(['F','TH'])].groupby(['spk','phone']).size().to_dict(), "; with F2:", int(df[df.phone.isin(['F','TH'])].d10.notna().sum()), ")")
    print(table(df, ("F", "TH"), SCALARS + F2FEATS, extf).round(3).to_string(index=False))
