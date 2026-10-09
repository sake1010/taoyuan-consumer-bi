"""
ETL：桃園市政府消費諮詢商品類型分析表（109-114年）
執行方式（在專案根目錄執行）：
    python etl/etl.py

輸入：data/raw/taoyuan_consumer_consultation_raw.csv
輸出：
    data/processed/taoyuan_consumer_consultation_clean.csv
    data/processed/validation_report.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "taoyuan_consumer_consultation_raw.csv"
OUT_DIR = ROOT / "data" / "processed"
CLEAN_PATH = OUT_DIR / "taoyuan_consumer_consultation_clean.csv"
REPORT_PATH = OUT_DIR / "validation_report.csv"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    if "年度" not in df.columns or "合計" not in df.columns:
        raise ValueError("原始資料缺少「年度」或「合計」欄位。")

    df["年度"] = pd.to_numeric(df["年度"], errors="raise").astype(int)
    df["合計"] = pd.to_numeric(df["合計"], errors="raise")
    category_cols = [c for c in df.columns if c not in ["年度", "合計"]]
    for col in category_cols:
        df[col] = pd.to_numeric(df[col], errors="raise")

    if df["年度"].duplicated().any():
        raise ValueError("發現重複年度，請先檢查原始資料。")
    if df[category_cols + ["合計"]].isna().any().any():
        raise ValueError("數值欄位存在缺失值，請檢查原始資料。")
    if (df[category_cols + ["合計"]] < 0).any().any():
        raise ValueError("數值欄位出現負數，請檢查原始資料。")

    report = []
    records = []
    for _, row in df.iterrows():
        category_sum = int(row[category_cols].sum())
        total = int(row["合計"])
        report.append({
            "民國年": int(row["年度"]),
            "西元年": int(row["年度"]) + 1911,
            "原始合計": total,
            "各商品類型加總": category_sum,
            "是否一致": category_sum == total,
        })
        for category in category_cols:
            count = int(row[category])
            records.append({
                "民國年": int(row["年度"]),
                "西元年": int(row["年度"]) + 1911,
                "商品類型": category,
                "諮詢件數": count,
                "年度總件數": total,
                "年度占比": round(count / total * 100, 4) if total else 0,
            })

    report_df = pd.DataFrame(report).sort_values("西元年")
    if not report_df["是否一致"].all():
        raise ValueError("資料驗證失敗：商品類型加總與原始合計不一致。")

    clean_df = pd.DataFrame(records).sort_values(
        ["西元年", "諮詢件數"], ascending=[True, False]
    )
    clean_df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")
    report_df.to_csv(REPORT_PATH, index=False, encoding="utf-8-sig")
    print(f"原始資料：{len(df)} 個年度")
    print(f"商品類型：{len(category_cols)} 類")
    print(f"整理後資料：{len(clean_df)} 筆")
    print(f"加總驗證：{'全部通過' if report_df['是否一致'].all() else '未通過'}")
    print(f"已輸出：{CLEAN_PATH}")
    print(f"已輸出：{REPORT_PATH}")

if __name__ == "__main__":
    main()
