"""
AskDataSage AI — Data Loader
Handles CSV file upload → SQLite database conversion.
Includes validation, column cleaning, schema extraction, and smart query suggestions.
"""

import os
import re
import sqlite3

import pandas as pd

from src.logger import get_logger

logger = get_logger("data_loader")

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
USER_DB_PATH = os.path.join(DATA_DIR, "user_data.db")
USER_TABLE_NAME = "user_data"

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class DataLoadError(Exception):
    """Raised when CSV loading fails validation."""
    pass


class DataLoader:
    """Converts uploaded CSV files into a queryable SQLite database."""

    def _clean_column_name(self, name: str) -> str:
        """Clean a column name: lowercase, underscores, no special chars."""
        name = str(name).strip().lower()
        name = re.sub(r"[^a-z0-9_]", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")
        if not name or name[0].isdigit():
            name = f"col_{name}"
        return name

    def load_csv(self, uploaded_file) -> dict:
        """
        Load a CSV file into SQLite and return dataset info.

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            dict with keys: db_path, table_name, schema_str, row_count,
                            columns, sample_df, suggestions

        Raises:
            DataLoadError: If validation fails
        """
        # ── Validate file size ──
        uploaded_file.seek(0, 2)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)

        if file_size > MAX_FILE_SIZE_BYTES:
            raise DataLoadError(
                f"File too large ({file_size / 1024 / 1024:.1f}MB). "
                f"Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
            )

        if file_size == 0:
            raise DataLoadError("The uploaded file is empty.")

        # ── Read CSV with encoding detection ──
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, encoding="latin-1")
                logger.info("Fell back to latin-1 encoding")
            except Exception as e:
                raise DataLoadError(f"Could not read file — encoding error: {e}")
        except pd.errors.EmptyDataError:
            raise DataLoadError("The CSV file contains no data.")
        except Exception as e:
            raise DataLoadError(f"Failed to read CSV: {e}")

        # ── Validate structure ──
        if df.empty:
            raise DataLoadError("The dataset is empty (0 rows).")

        if len(df.columns) < 2:
            raise DataLoadError(
                f"Dataset has only {len(df.columns)} column. "
                "Please upload a CSV with at least 2 columns."
            )

        # ── Clean column names ──
        original_cols = df.columns.tolist()
        clean_cols = [self._clean_column_name(c) for c in original_cols]

        # Handle duplicates
        seen = {}
        for i, col in enumerate(clean_cols):
            if col in seen:
                seen[col] += 1
                clean_cols[i] = f"{col}_{seen[col]}"
            else:
                seen[col] = 0

        df.columns = clean_cols
        logger.info(f"Cleaned columns: {clean_cols}")

        # ── Create SQLite database ──
        os.makedirs(DATA_DIR, exist_ok=True)

        # Remove old user DB if exists
        if os.path.exists(USER_DB_PATH):
            os.remove(USER_DB_PATH)

        try:
            conn = sqlite3.connect(USER_DB_PATH)
            df.to_sql(USER_TABLE_NAME, conn, index=False, if_exists="replace")
            conn.close()
            logger.info(
                f"Created {USER_DB_PATH}: {len(df)} rows, {len(df.columns)} cols"
            )
        except Exception as e:
            raise DataLoadError(f"Failed to create database: {e}")

        # ── Build schema string for LLM ──
        col_types = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            if "int" in dtype:
                col_types.append(f"{col} (INTEGER)")
            elif "float" in dtype:
                col_types.append(f"{col} (REAL)")
            else:
                col_types.append(f"{col} (TEXT)")

        schema_str = (
            f"TABLE: {USER_TABLE_NAME} ({len(df):,} rows)\n"
            f"  COLUMNS: {', '.join(col_types)}\n"
            f"  SAMPLE DATA:\n{df.head(3).to_string(index=False)}"
        )

        # ── Generate smart query suggestions ──
        suggestions = self._generate_suggestions(df)

        # ── Build column info ──
        columns_info = []
        for col in df.columns:
            columns_info.append({
                "name": col,
                "type": str(df[col].dtype),
                "nunique": int(df[col].nunique()),
                "null_pct": round(df[col].isna().mean() * 100, 1),
            })

        return {
            "db_path": USER_DB_PATH,
            "table_name": USER_TABLE_NAME,
            "schema_str": schema_str,
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": columns_info,
            "sample_df": df.head(5),
            "suggestions": suggestions,
        }

    def _generate_suggestions(self, df: pd.DataFrame) -> list[tuple[str, str]]:
        """
        Generate smart query suggestions based on column types.

        Returns:
            List of (label, question) tuples for the UI.
        """
        suggestions = []
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        text_cols = df.select_dtypes(include=["object"]).columns.tolist()
        date_cols = []

        # Detect date-like columns
        for col in text_cols[:]:
            try:
                parsed = pd.to_datetime(df[col], format="mixed", dayfirst=False)
                if parsed.notna().sum() > len(df) * 0.5:
                    date_cols.append(col)
                    text_cols.remove(col)
            except (ValueError, TypeError):
                pass

        # Always add row count
        suggestions.append(
            ("📊 Overview", f"How many rows are in {USER_TABLE_NAME}?")
        )

        # Numeric suggestions
        if numeric_cols:
            col = numeric_cols[0]
            suggestions.append(
                ("📈 Summary", f"What is the average, min, and max of {col}?")
            )

        # Categorical breakdown
        if text_cols and numeric_cols:
            cat = text_cols[0]
            num = numeric_cols[0]
            suggestions.append(
                ("📊 Breakdown", f"Show total {num} by {cat}")
            )

            suggestions.append(
                ("🏆 Top Values", f"What are the top 10 {cat} by {num}?")
            )

        # Time-based
        if date_cols and numeric_cols:
            suggestions.append(
                ("📅 Trend", f"Show {numeric_cols[0]} over {date_cols[0]}")
            )

        # Distribution
        if text_cols:
            suggestions.append(
                ("🎯 Distribution", f"Show distribution of {text_cols[0]}")
            )

        return suggestions[:6]  # Max 6 suggestions
