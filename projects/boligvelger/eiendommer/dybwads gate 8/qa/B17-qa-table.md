# B17 QA-tabell — batch-regenerering 2026-06-08

Alle 16 enheter regenerert fra specs, build_pages.py + export_pdf.py kjørt.
qa_score.py kjørt med --search (bruker crop_offset fra units.json der tilgjengelig).

| Enhet  | best-precision | best-offset   | Status |
|--------|---------------|---------------|--------|
| H0101  | 0.889         | [8, -32]      | OK     |
| H0102  | 0.824         | [-28, -36]    | OK     |
| H0103  | 0.818         | [32, -36]     | OK     |
| H0104  | 0.827         | [-32, 8]      | OK     |
| H0105  | 0.806         | [42, 52]      | OK     |
| H0201  | 0.908         | [77, 67]      | OK     |
| H0202  | 0.831         | [-36, -36]    | OK     |
| H0203  | 0.824         | [36, -36]     | OK     |
| H0204  | 0.818         | [26, -100]    | OK     |
| H0205  | 0.812         | [32, 32]      | OK     |
| H0301  | 0.899         | [-24, -36]    | OK     |
| H0302  | 0.816         | [36, 28]      | OK     |
| H0303  | 0.829         | [58, 80]      | OK     |
| H0304  | 0.839         | [28, 32]      | OK     |
| H0305  | 0.836         | [-32, -32]    | OK     |
| H0306  | 0.888         | [12, 12]      | OK     |

Gate: >= 0.80. Alle 16 enheter passerer. Lavest: H0105 = 0.806. Høyest: H0201 = 0.908.
