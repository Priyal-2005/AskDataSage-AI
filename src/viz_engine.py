"""
AskDataSage AI — Visualization Engine
Rule-based chart selection and generation using Plotly.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.logger import get_logger

logger = get_logger("viz_engine")

# ---------------------------------------------------------------------------
# Color palette (harmonious, modern)
# ---------------------------------------------------------------------------
COLORS = [
    "#6C63FF", "#FF6584", "#43E97B", "#FFB347", "#38B6FF",
    "#FF6B6B", "#A78BFA", "#34D399", "#F472B6", "#60A5FA",
]


class VizEngine:
    """Generates Plotly charts based on DataFrame structure and question context."""

    def _detect_column_types(self, df: pd.DataFrame) -> dict:
        """Classify each column as datetime, numeric, or categorical."""
        types = {"datetime": [], "numeric": [], "categorical": []}

        for col in df.columns:
            # Check datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                types["datetime"].append(col)
                continue

            # Try parsing as datetime
            if df[col].dtype == object:
                try:
                    parsed = pd.to_datetime(df[col], format="mixed", dayfirst=False)
                    if parsed.notna().sum() > len(df) * 0.5:
                        types["datetime"].append(col)
                        continue
                except (ValueError, TypeError):
                    pass

            # Check numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                # If few unique values, treat as categorical
                if df[col].nunique() <= 10 and df[col].nunique() < len(df) * 0.3:
                    types["categorical"].append(col)
                else:
                    types["numeric"].append(col)
                continue

            # Default: categorical (if reasonable cardinality)
            if df[col].nunique() <= 50:
                types["categorical"].append(col)

        return types

    def generate_chart(
        self, df: pd.DataFrame, question: str = ""
    ) -> go.Figure | None:
        """Generate an appropriate chart based on the data structure."""
        if df is None or df.empty:
            logger.info("No data to visualize")
            return None

        # Single-value results (KPI) — no chart needed
        if len(df) == 1 and len(df.columns) == 1:
            logger.info("Single-value result — skipping chart")
            return None

        types = self._detect_column_types(df)
        logger.info(f"Column types: {types}")

        fig = None

        try:
            # ---- Single numeric column → Histogram ----
            if len(types["numeric"]) == 1 and not types["categorical"] and not types["datetime"]:
                col = types["numeric"][0]
                fig = px.histogram(
                    df, x=col,
                    title=f"Distribution of {col}",
                    color_discrete_sequence=COLORS,
                    nbins=min(30, df[col].nunique()),
                )

            # ---- 1 datetime + 1 numeric → Line chart ----
            elif types["datetime"] and types["numeric"]:
                date_col = types["datetime"][0]
                num_col = types["numeric"][0]
                df_sorted = df.copy()
                df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
                df_sorted = df_sorted.sort_values(date_col)

                if types["categorical"]:
                    cat_col = types["categorical"][0]
                    fig = px.line(
                        df_sorted, x=date_col, y=num_col, color=cat_col,
                        title=f"{num_col} over {date_col} by {cat_col}",
                        color_discrete_sequence=COLORS,
                        markers=True,
                    )
                else:
                    fig = px.line(
                        df_sorted, x=date_col, y=num_col,
                        title=f"{num_col} over {date_col}",
                        color_discrete_sequence=COLORS,
                        markers=True,
                    )

            # ---- 1 categorical + 1 numeric → Bar chart ----
            elif len(types["categorical"]) >= 1 and len(types["numeric"]) >= 1:
                cat_col = types["categorical"][0]
                num_col = types["numeric"][0]

                if len(types["categorical"]) >= 2 and len(df[types["categorical"][1]].unique()) <= 8:
                    group_col = types["categorical"][1]
                    fig = px.bar(
                        df, x=cat_col, y=num_col, color=group_col,
                        title=f"{num_col} by {cat_col} (grouped by {group_col})",
                        color_discrete_sequence=COLORS,
                        barmode="group",
                    )
                else:
                    # Horizontal bar for better readability
                    if len(df) > 5:
                        fig = px.bar(
                            df, y=cat_col, x=num_col, orientation="h",
                            title=f"{num_col} by {cat_col}",
                            color=num_col,
                            color_continuous_scale=["#6C63FF", "#FF6584"],
                        )
                    else:
                        fig = px.bar(
                            df, x=cat_col, y=num_col,
                            title=f"{num_col} by {cat_col}",
                            color=cat_col,
                            color_discrete_sequence=COLORS,
                        )

            # ---- Multiple numeric → first two as scatter ----
            elif len(types["numeric"]) >= 2:
                x_col = types["numeric"][0]
                y_col = types["numeric"][1]
                color_col = types["categorical"][0] if types["categorical"] else None
                fig = px.scatter(
                    df, x=x_col, y=y_col, color=color_col,
                    title=f"{y_col} vs {x_col}",
                    color_discrete_sequence=COLORS,
                )

            # ---- Single categorical → pie if few values ----
            elif len(types["categorical"]) == 1 and len(types["numeric"]) == 0:
                cat_col = types["categorical"][0]
                counts = df[cat_col].value_counts().reset_index()
                counts.columns = [cat_col, "count"]
                if len(counts) <= 10:
                    fig = px.pie(
                        counts, names=cat_col, values="count",
                        title=f"Distribution of {cat_col}",
                        color_discrete_sequence=COLORS,
                    )

            # Apply common styling
            if fig:
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif", size=13),
                    title_font=dict(size=16, color="#FAFAFA"),
                    margin=dict(l=20, r=20, t=50, b=20),
                    legend=dict(
                        bgcolor="rgba(0,0,0,0)",
                        font=dict(size=11),
                    ),
                    hoverlabel=dict(
                        bgcolor="#1A1F2E",
                        font_size=12,
                        font_family="Inter, sans-serif",
                    ),
                )
                logger.info(f"Chart generated: {fig.layout.title.text}")

        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return None

        return fig
