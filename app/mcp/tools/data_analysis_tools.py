"""
Data analysis and visualization tools for the MCP server.
"""

import base64
import io
import json
import logging
import os
import re
import tempfile
from typing import Dict, Any, List, Union, Optional, Tuple

# Optional data analysis dependencies
try:
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.figure import Figure
    DATA_ANALYSIS_DEPS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Data analysis dependencies not available: {e}")
    # Create dummy objects to prevent NameError
    np = None
    pd = None
    plt = None
    sns = None
    Figure = None
    DATA_ANALYSIS_DEPS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAnalysisTools:
    """
    Tools for data analysis and visualization.
    """

    def __init__(self):
        """Initialize the data analysis tools."""
        self.logger = logging.getLogger(__name__)

        # Check if data analysis dependencies are available
        if not DATA_ANALYSIS_DEPS_AVAILABLE:
            self.logger.warning("Data analysis dependencies (numpy, pandas, matplotlib, seaborn) are not available. Data analysis features will be disabled.")

        # Load API keys from environment
        from dotenv import load_dotenv
        load_dotenv()

        # Initialize supported chart types (only if dependencies are available)
        if DATA_ANALYSIS_DEPS_AVAILABLE:
            self.chart_types = {
                "line": self._generate_line_chart,
                "bar": self._generate_bar_chart,
                "scatter": self._generate_scatter_plot,
                "histogram": self._generate_histogram,
                "pie": self._generate_pie_chart,
                "heatmap": self._generate_heatmap,
                "box": self._generate_box_plot,
                "correlation": self._generate_correlation_matrix
            }
        else:
            self.chart_types = {}

        # Initialize supported data formats (only if pandas is available)
        if DATA_ANALYSIS_DEPS_AVAILABLE and pd is not None:
            self.data_formats = {
                "csv": pd.read_csv,
                "excel": pd.read_excel,
                "json": pd.read_json,
                "dict": pd.DataFrame.from_dict
            }
        else:
            self.data_formats = {}

        # Set default style for visualizations (if seaborn is available)
        if DATA_ANALYSIS_DEPS_AVAILABLE and sns is not None:
            sns.set_theme(style="darkgrid")

    def analyze_data(self, data: Union[str, Dict[str, Any]],
                    analysis_type: str = "summary",
                    chart_type: str = "bar",
                    title: str = "Data Analysis",
                    x_column: Optional[str] = None,
                    y_column: Optional[str] = None,
                    group_by: Optional[str] = None,
                    filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze data and generate visualizations.

        Args:
            data: Data to analyze (CSV string, JSON string, or dictionary)
            analysis_type: Type of analysis to perform (summary, correlation, distribution, etc.)
            chart_type: Type of chart to generate (bar, line, scatter, etc.)
            title: Title for the analysis and charts
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to group data by
            filters: Filters to apply to the data

        Returns:
            Dictionary containing analysis results and visualizations
        """
        self.logger.info(f"Analyzing data: {title} (analysis_type: {analysis_type}, chart_type: {chart_type})")

        # Check if data analysis dependencies are available
        if not DATA_ANALYSIS_DEPS_AVAILABLE:
            return {
                "title": title,
                "error": "Data analysis dependencies (numpy, pandas, matplotlib, seaborn) are not available. Please install these packages to use data analysis features.",
                "analysis_type": analysis_type,
                "chart_type": chart_type,
                "success": False
            }

        try:
            # Parse the data into a DataFrame
            df = self._parse_data(data)

            # Apply filters if provided
            if filters:
                df = self._apply_filters(df, filters)

            # Perform the analysis
            analysis_results = self._perform_analysis(df, analysis_type, x_column, y_column, group_by)

            # Generate visualizations
            visualizations = self._generate_visualizations(df, chart_type, title, x_column, y_column, group_by)

            return {
                "title": title,
                "analysis": analysis_results,
                "visualizations": visualizations,
                "summary": self._generate_analysis_summary(df, analysis_results, analysis_type)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing data: {str(e)}")
            return {
                "error": str(e),
                "title": title
            }

    def _parse_data(self, data: Union[str, Dict[str, Any]]) -> "pd.DataFrame":
        """
        Parse data into a pandas DataFrame.

        Args:
            data: Data to parse (CSV string, JSON string, or dictionary)

        Returns:
            Pandas DataFrame
        """
        if isinstance(data, dict):
            # Data is already a dictionary
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, str):
            # Try to determine the format of the string
            data = data.strip()
            if data.startswith('{') or data.startswith('['):
                # Looks like JSON
                return pd.read_json(data)
            else:
                # Assume CSV
                return pd.read_csv(io.StringIO(data))
        else:
            raise ValueError("Unsupported data format. Please provide data as a CSV string, JSON string, or dictionary.")

    def _apply_filters(self, df: "pd.DataFrame", filters: Dict[str, Any]) -> "pd.DataFrame":
        """
        Apply filters to a DataFrame.

        Args:
            df: DataFrame to filter
            filters: Dictionary of filters to apply

        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()

        for column, value in filters.items():
            if column in filtered_df.columns:
                if isinstance(value, list):
                    # Filter for values in a list
                    filtered_df = filtered_df[filtered_df[column].isin(value)]
                elif isinstance(value, dict) and ('min' in value or 'max' in value):
                    # Range filter
                    if 'min' in value:
                        filtered_df = filtered_df[filtered_df[column] >= value['min']]
                    if 'max' in value:
                        filtered_df = filtered_df[filtered_df[column] <= value['max']]
                else:
                    # Exact match
                    filtered_df = filtered_df[filtered_df[column] == value]

        return filtered_df

    def _perform_analysis(self, df: "pd.DataFrame", analysis_type: str,
                         x_column: Optional[str], y_column: Optional[str],
                         group_by: Optional[str]) -> Dict[str, Any]:
        """
        Perform analysis on a DataFrame.

        Args:
            df: DataFrame to analyze
            analysis_type: Type of analysis to perform
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to group data by

        Returns:
            Dictionary containing analysis results
        """
        results = {}

        if analysis_type == "summary":
            # Basic summary statistics
            results["summary_stats"] = df.describe().to_dict()
            results["column_types"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
            results["missing_values"] = df.isnull().sum().to_dict()

        elif analysis_type == "correlation":
            # Correlation analysis
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                results["correlation_matrix"] = numeric_df.corr().to_dict()
            else:
                results["error"] = "No numeric columns available for correlation analysis"

        elif analysis_type == "distribution":
            # Distribution analysis
            if x_column and x_column in df.columns:
                if df[x_column].dtype in [np.number]:
                    results["distribution"] = {
                        "mean": df[x_column].mean(),
                        "median": df[x_column].median(),
                        "std": df[x_column].std(),
                        "min": df[x_column].min(),
                        "max": df[x_column].max(),
                        "quantiles": df[x_column].quantile([0.25, 0.5, 0.75]).to_dict()
                    }
                else:
                    # For categorical data
                    results["distribution"] = df[x_column].value_counts().to_dict()
            else:
                results["error"] = f"Column '{x_column}' not found or not specified"

        elif analysis_type == "group_analysis":
            # Group analysis
            if group_by and group_by in df.columns:
                if y_column and y_column in df.columns and df[y_column].dtype in [np.number]:
                    results["group_stats"] = df.groupby(group_by)[y_column].agg(['mean', 'median', 'std', 'min', 'max']).to_dict()
                else:
                    results["group_counts"] = df.groupby(group_by).size().to_dict()
            else:
                results["error"] = f"Column '{group_by}' not found or not specified"

        return results

    def _generate_visualizations(self, df: "pd.DataFrame", chart_type: str,
                               title: str, x_column: Optional[str],
                               y_column: Optional[str], group_by: Optional[str]) -> Dict[str, Any]:
        """
        Generate visualizations for a DataFrame.

        Args:
            df: DataFrame to visualize
            chart_type: Type of chart to generate
            title: Title for the chart
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to group data by

        Returns:
            Dictionary containing visualization data
        """
        # Default to bar chart if type not supported
        if chart_type not in self.chart_types:
            self.logger.warning(f"Chart type '{chart_type}' not supported, defaulting to bar chart")
            chart_type = "bar"

        # Generate the chart
        generator_func = self.chart_types[chart_type]
        chart_image, chart_data = generator_func(df, title, x_column, y_column, group_by)

        return {
            "chart_type": chart_type,
            "image": chart_image,
            "data": chart_data
        }

    def _generate_analysis_summary(self, df: "pd.DataFrame", analysis_results: Dict[str, Any],
                                 analysis_type: str) -> str:
        """
        Generate a summary of the analysis results.

        Args:
            df: DataFrame that was analyzed
            analysis_results: Results of the analysis
            analysis_type: Type of analysis that was performed

        Returns:
            Summary text
        """
        summary = f"## Data Analysis Summary\n\n"
        summary += f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns.\n\n"

        if analysis_type == "summary":
            summary += "### Key Statistics\n\n"
            if "summary_stats" in analysis_results:
                # Add summary of numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if not numeric_cols.empty:
                    summary += "**Numeric Columns:**\n\n"
                    for col in numeric_cols[:5]:  # Limit to first 5 columns
                        stats = analysis_results["summary_stats"].get(col, {})
                        if stats:
                            summary += f"- **{col}**: Mean: {stats.get('mean', 'N/A'):.2f}, "
                            summary += f"Min: {stats.get('min', 'N/A'):.2f}, "
                            summary += f"Max: {stats.get('max', 'N/A'):.2f}\n"

                    if len(numeric_cols) > 5:
                        summary += f"- ... and {len(numeric_cols) - 5} more numeric columns\n"

                # Add summary of categorical columns
                cat_cols = df.select_dtypes(exclude=[np.number]).columns
                if not cat_cols.empty:
                    summary += "\n**Categorical Columns:**\n\n"
                    for col in cat_cols[:5]:  # Limit to first 5 columns
                        unique_vals = df[col].nunique()
                        summary += f"- **{col}**: {unique_vals} unique values\n"

                    if len(cat_cols) > 5:
                        summary += f"- ... and {len(cat_cols) - 5} more categorical columns\n"

            # Add missing values information
            if "missing_values" in analysis_results:
                missing = analysis_results["missing_values"]
                cols_with_missing = [col for col, count in missing.items() if count > 0]
                if cols_with_missing:
                    summary += "\n### Missing Values\n\n"
                    for col in cols_with_missing[:5]:  # Limit to first 5 columns
                        pct_missing = (missing[col] / df.shape[0]) * 100
                        summary += f"- **{col}**: {missing[col]} missing values ({pct_missing:.1f}%)\n"

                    if len(cols_with_missing) > 5:
                        summary += f"- ... and {len(cols_with_missing) - 5} more columns with missing values\n"

        elif analysis_type == "correlation":
            summary += "### Correlation Analysis\n\n"
            if "correlation_matrix" in analysis_results:
                # Find the strongest correlations
                corr_matrix = analysis_results["correlation_matrix"]
                strong_correlations = []

                for col1 in corr_matrix:
                    for col2 in corr_matrix[col1]:
                        if col1 != col2:
                            corr_value = corr_matrix[col1][col2]
                            if abs(corr_value) > 0.5:  # Only show strong correlations
                                strong_correlations.append((col1, col2, corr_value))

                # Sort by absolute correlation value
                strong_correlations.sort(key=lambda x: abs(x[2]), reverse=True)

                if strong_correlations:
                    summary += "**Strong Correlations:**\n\n"
                    for col1, col2, corr in strong_correlations[:5]:  # Limit to top 5
                        summary += f"- **{col1}** and **{col2}**: {corr:.2f}\n"
                else:
                    summary += "No strong correlations found between variables.\n"

        elif analysis_type == "distribution":
            summary += "### Distribution Analysis\n\n"
            if "distribution" in analysis_results:
                dist = analysis_results["distribution"]
                if isinstance(dist, dict) and "mean" in dist:
                    # Numeric distribution
                    summary += f"**Statistics:**\n\n"
                    summary += f"- Mean: {dist.get('mean', 'N/A'):.2f}\n"
                    summary += f"- Median: {dist.get('median', 'N/A'):.2f}\n"
                    summary += f"- Standard Deviation: {dist.get('std', 'N/A'):.2f}\n"
                    summary += f"- Range: {dist.get('min', 'N/A'):.2f} to {dist.get('max', 'N/A'):.2f}\n"
                else:
                    # Categorical distribution
                    summary += f"**Top Categories:**\n\n"
                    sorted_cats = sorted(dist.items(), key=lambda x: x[1], reverse=True)
                    for cat, count in sorted_cats[:5]:  # Limit to top 5
                        pct = (count / df.shape[0]) * 100
                        summary += f"- {cat}: {count} ({pct:.1f}%)\n"

                    if len(sorted_cats) > 5:
                        summary += f"- ... and {len(sorted_cats) - 5} more categories\n"

        elif analysis_type == "group_analysis":
            summary += "### Group Analysis\n\n"
            if "group_stats" in analysis_results:
                stats = analysis_results["group_stats"]
                if "mean" in stats:
                    summary += f"**Mean Values by Group:**\n\n"
                    sorted_groups = sorted(stats["mean"].items(), key=lambda x: x[1], reverse=True)
                    for group, value in sorted_groups[:5]:  # Limit to top 5
                        summary += f"- {group}: {value:.2f}\n"

                    if len(sorted_groups) > 5:
                        summary += f"- ... and {len(sorted_groups) - 5} more groups\n"

            elif "group_counts" in analysis_results:
                counts = analysis_results["group_counts"]
                summary += f"**Group Counts:**\n\n"
                sorted_groups = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                for group, count in sorted_groups[:5]:  # Limit to top 5
                    pct = (count / df.shape[0]) * 100
                    summary += f"- {group}: {count} ({pct:.1f}%)\n"

                if len(sorted_groups) > 5:
                    summary += f"- ... and {len(sorted_groups) - 5} more groups\n"

        return summary

    def _generate_line_chart(self, df: "pd.DataFrame", title: str,
                           x_column: Optional[str], y_column: Optional[str],
                           group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a line chart.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to group data by

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(10, 6))

        # Validate columns
        if not x_column or x_column not in df.columns:
            x_column = df.columns[0] if not df.empty else None

        if not y_column or y_column not in df.columns:
            # Find the first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            y_column = numeric_cols[0] if not numeric_cols.empty else None

        if not x_column or not y_column:
            # Create a simple placeholder chart
            plt.text(0.5, 0.5, "No suitable columns found for line chart",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "No suitable columns found"}
        else:
            # Create the line chart
            if group_by and group_by in df.columns:
                # Group by the specified column
                for group_val, group_df in df.groupby(group_by):
                    plt.plot(group_df[x_column], group_df[y_column], marker='o', label=str(group_val))
                plt.legend(title=group_by)
            else:
                # Simple line chart
                plt.plot(df[x_column], df[y_column], marker='o')

            plt.title(title)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Prepare chart data
            chart_data = {
                "x_column": x_column,
                "y_column": y_column,
                "group_by": group_by,
                "data_points": len(df)
            }

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_bar_chart(self, df: "pd.DataFrame", title: str,
                          x_column: Optional[str], y_column: Optional[str],
                          group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a bar chart.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to group data by

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(10, 6))

        # Validate columns
        if not x_column or x_column not in df.columns:
            # Find the first categorical column
            cat_cols = df.select_dtypes(exclude=[np.number]).columns
            x_column = cat_cols[0] if not cat_cols.empty else df.columns[0]

        if not y_column or y_column not in df.columns:
            # Find the first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            y_column = numeric_cols[0] if not numeric_cols.empty else None

        if not x_column or not y_column:
            # Create a simple placeholder chart
            plt.text(0.5, 0.5, "No suitable columns found for bar chart",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "No suitable columns found"}
        else:
            # Create the bar chart
            if group_by and group_by in df.columns:
                # Group by the specified column
                grouped_df = df.groupby([x_column, group_by])[y_column].mean().unstack()
                grouped_df.plot(kind='bar', ax=plt.gca())
            else:
                # Simple bar chart
                if df[x_column].nunique() > 15:
                    # Too many categories, show top 15
                    top_cats = df.groupby(x_column)[y_column].mean().nlargest(15).index
                    filtered_df = df[df[x_column].isin(top_cats)]
                    sns.barplot(x=x_column, y=y_column, data=filtered_df)
                    plt.text(0.5, -0.15, "Showing top 15 categories",
                            ha='center', va='center', fontsize=10, transform=plt.gca().transAxes)
                else:
                    sns.barplot(x=x_column, y=y_column, data=df)

            plt.title(title)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()

            # Prepare chart data
            chart_data = {
                "x_column": x_column,
                "y_column": y_column,
                "group_by": group_by,
                "categories": df[x_column].nunique()
            }

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_scatter_plot(self, df: "pd.DataFrame", title: str,
                             x_column: Optional[str], y_column: Optional[str],
                             group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a scatter plot.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to group data by

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(10, 6))

        # Validate columns - need numeric columns for scatter plot
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if not x_column or x_column not in numeric_cols:
            x_column = numeric_cols[0] if len(numeric_cols) > 0 else None

        if not y_column or y_column not in numeric_cols:
            y_column = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0] if len(numeric_cols) > 0 else None

        if not x_column or not y_column:
            # Create a simple placeholder chart
            plt.text(0.5, 0.5, "No suitable numeric columns found for scatter plot",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "No suitable numeric columns found"}
        else:
            # Create the scatter plot
            if group_by and group_by in df.columns:
                # Group by the specified column
                for group_val, group_df in df.groupby(group_by):
                    plt.scatter(group_df[x_column], group_df[y_column], label=str(group_val), alpha=0.7)
                plt.legend(title=group_by)
            else:
                # Simple scatter plot
                plt.scatter(df[x_column], df[y_column], alpha=0.7)

            plt.title(title)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Calculate correlation
            correlation = df[[x_column, y_column]].corr().iloc[0, 1]
            plt.text(0.05, 0.95, f"Correlation: {correlation:.2f}",
                    transform=plt.gca().transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

            # Prepare chart data
            chart_data = {
                "x_column": x_column,
                "y_column": y_column,
                "group_by": group_by,
                "correlation": correlation,
                "data_points": len(df)
            }

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_histogram(self, df: "pd.DataFrame", title: str,
                          x_column: Optional[str], y_column: Optional[str],
                          group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a histogram.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis (not used for histograms)
            group_by: Column to group data by

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(10, 6))

        # Validate columns - need numeric column for histogram
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if not x_column or x_column not in numeric_cols:
            x_column = numeric_cols[0] if not numeric_cols.empty else None

        if not x_column:
            # Create a simple placeholder chart
            plt.text(0.5, 0.5, "No suitable numeric column found for histogram",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "No suitable numeric column found"}
        else:
            # Create the histogram
            if group_by and group_by in df.columns:
                # Group by the specified column
                for group_val, group_df in df.groupby(group_by):
                    sns.histplot(group_df[x_column], label=str(group_val), kde=True, alpha=0.6)
                plt.legend(title=group_by)
            else:
                # Simple histogram
                sns.histplot(df[x_column], kde=True)

            plt.title(title)
            plt.xlabel(x_column)
            plt.ylabel("Frequency")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Calculate statistics
            mean = df[x_column].mean()
            median = df[x_column].median()
            std = df[x_column].std()

            # Add statistics to the plot
            stats_text = f"Mean: {mean:.2f}\nMedian: {median:.2f}\nStd Dev: {std:.2f}"
            plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

            # Prepare chart data
            chart_data = {
                "x_column": x_column,
                "mean": mean,
                "median": median,
                "std_dev": std,
                "min": df[x_column].min(),
                "max": df[x_column].max()
            }

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_pie_chart(self, df: "pd.DataFrame", title: str,
                          x_column: Optional[str], y_column: Optional[str],
                          group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a pie chart.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for categories
            y_column: Column to use for values
            group_by: Column to group data by (not used for pie charts)

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(10, 6))

        # Validate columns
        if not x_column or x_column not in df.columns:
            # Find the first categorical column
            cat_cols = df.select_dtypes(exclude=[np.number]).columns
            x_column = cat_cols[0] if not cat_cols.empty else df.columns[0]

        if not y_column or y_column not in df.columns:
            # Find the first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            y_column = numeric_cols[0] if not numeric_cols.empty else None

        if not x_column or not y_column:
            # Create a simple placeholder chart
            plt.text(0.5, 0.5, "No suitable columns found for pie chart",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "No suitable columns found"}
        else:
            # Aggregate data for pie chart
            if df[x_column].nunique() > 10:
                # Too many categories, show top 10 and group others
                top_cats = df.groupby(x_column)[y_column].sum().nlargest(9).index
                pie_data = df.groupby(x_column)[y_column].sum()

                # Create a new series with top categories and "Others"
                top_data = pie_data.loc[top_cats]
                others = pd.Series({"Others": pie_data.loc[~pie_data.index.isin(top_cats)].sum()})
                pie_data = pd.concat([top_data, others])

                plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=90, shadow=False)
                plt.text(0.5, -0.1, "Showing top 9 categories + Others",
                        ha='center', va='center', fontsize=10, transform=plt.gca().transAxes)
            else:
                # Simple pie chart
                pie_data = df.groupby(x_column)[y_column].sum()
                plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=90, shadow=False)

            plt.title(title)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

            # Prepare chart data
            chart_data = {
                "x_column": x_column,
                "y_column": y_column,
                "categories": len(pie_data),
                "values": pie_data.to_dict()
            }

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_heatmap(self, df: "pd.DataFrame", title: str,
                        x_column: Optional[str], y_column: Optional[str],
                        group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a heatmap.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            group_by: Column to use for values

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(12, 8))

        # For heatmaps, we'll use correlation matrix if no specific columns are provided
        if not x_column or not y_column or not group_by:
            # Create correlation heatmap
            numeric_df = df.select_dtypes(include=[np.number])

            if numeric_df.empty or numeric_df.shape[1] < 2:
                # Not enough numeric columns for correlation
                plt.text(0.5, 0.5, "Not enough numeric columns for correlation heatmap",
                        ha='center', va='center', fontsize=12)
                plt.title(title)
                chart_data = {"error": "Not enough numeric columns"}
            else:
                # Generate correlation matrix
                corr_matrix = numeric_df.corr()

                # Create heatmap
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1,
                           linewidths=0.5, fmt=".2f")
                plt.title(f"{title} - Correlation Matrix")

                # Prepare chart data
                chart_data = {
                    "type": "correlation",
                    "columns": corr_matrix.columns.tolist(),
                    "data": corr_matrix.to_dict()
                }
        else:
            # Create pivot table heatmap
            if x_column in df.columns and y_column in df.columns and group_by in df.columns:
                # Check if we have too many unique values
                if df[x_column].nunique() > 20 or df[y_column].nunique() > 20:
                    # Too many categories, show warning
                    plt.text(0.5, 0.5, "Too many unique values for heatmap\nTry using fewer categories",
                            ha='center', va='center', fontsize=12)
                    plt.title(title)
                    chart_data = {"error": "Too many unique values"}
                else:
                    # Create pivot table
                    pivot_table = df.pivot_table(index=y_column, columns=x_column, values=group_by, aggfunc='mean')

                    # Create heatmap
                    sns.heatmap(pivot_table, annot=True, cmap='viridis', fmt=".2f", linewidths=0.5)
                    plt.title(title)

                    # Prepare chart data
                    chart_data = {
                        "type": "pivot",
                        "x_column": x_column,
                        "y_column": y_column,
                        "value_column": group_by,
                        "x_categories": df[x_column].nunique(),
                        "y_categories": df[y_column].nunique()
                    }
            else:
                # Missing columns
                plt.text(0.5, 0.5, "Missing required columns for heatmap",
                        ha='center', va='center', fontsize=12)
                plt.title(title)
                chart_data = {"error": "Missing required columns"}

        plt.tight_layout()

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_box_plot(self, df: "pd.DataFrame", title: str,
                         x_column: Optional[str], y_column: Optional[str],
                         group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a box plot.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Column to use for categories
            y_column: Column to use for values
            group_by: Column to group data by

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(10, 6))

        # Validate columns - need numeric column for y-axis
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if not y_column or y_column not in numeric_cols:
            y_column = numeric_cols[0] if not numeric_cols.empty else None

        if not y_column:
            # Create a simple placeholder chart
            plt.text(0.5, 0.5, "No suitable numeric column found for box plot",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "No suitable numeric column found"}
        else:
            # Create the box plot
            if x_column and x_column in df.columns:
                # Box plot with categories
                if df[x_column].nunique() > 10:
                    # Too many categories, show top 10
                    top_cats = df.groupby(x_column)[y_column].mean().nlargest(10).index
                    filtered_df = df[df[x_column].isin(top_cats)]
                    sns.boxplot(x=x_column, y=y_column, data=filtered_df)
                    plt.text(0.5, -0.15, "Showing top 10 categories",
                            ha='center', va='center', fontsize=10, transform=plt.gca().transAxes)
                else:
                    sns.boxplot(x=x_column, y=y_column, data=df)

                # Add group_by as hue if provided
                if group_by and group_by in df.columns and df[group_by].nunique() <= 5:
                    sns.boxplot(x=x_column, y=y_column, hue=group_by, data=df)
            else:
                # Simple box plot without categories
                sns.boxplot(y=y_column, data=df)

            plt.title(title)
            if x_column and x_column in df.columns:
                plt.xlabel(x_column)
                plt.xticks(rotation=45, ha='right')
            plt.ylabel(y_column)
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()

            # Calculate statistics
            stats = df[y_column].describe()

            # Prepare chart data
            chart_data = {
                "y_column": y_column,
                "x_column": x_column if x_column and x_column in df.columns else None,
                "group_by": group_by if group_by and group_by in df.columns else None,
                "stats": {
                    "min": stats["min"],
                    "q1": stats["25%"],
                    "median": stats["50%"],
                    "q3": stats["75%"],
                    "max": stats["max"],
                    "mean": stats["mean"]
                }
            }

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data

    def _generate_correlation_matrix(self, df: "pd.DataFrame", title: str,
                                   x_column: Optional[str], y_column: Optional[str],
                                   group_by: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a correlation matrix visualization.

        Args:
            df: DataFrame to visualize
            title: Title for the chart
            x_column: Not used for correlation matrix
            y_column: Not used for correlation matrix
            group_by: Not used for correlation matrix

        Returns:
            Tuple of (base64-encoded image, chart data)
        """
        plt.figure(figsize=(12, 10))

        # Select numeric columns for correlation
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty or numeric_df.shape[1] < 2:
            # Not enough numeric columns for correlation
            plt.text(0.5, 0.5, "Not enough numeric columns for correlation matrix",
                    ha='center', va='center', fontsize=12)
            plt.title(title)
            chart_data = {"error": "Not enough numeric columns"}
        else:
            # Limit to 15 columns for readability
            if numeric_df.shape[1] > 15:
                # Select columns with highest variance
                variances = numeric_df.var().sort_values(ascending=False)
                selected_cols = variances.index[:15]
                numeric_df = numeric_df[selected_cols]
                plt.text(0.5, -0.05, "Showing 15 columns with highest variance",
                        ha='center', va='center', fontsize=10, transform=plt.figure().transFigure)

            # Generate correlation matrix
            corr_matrix = numeric_df.corr()

            # Create heatmap with correlation values
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Mask for upper triangle
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1,
                       mask=mask, linewidths=0.5, fmt=".2f", square=True)

            plt.title(f"{title} - Correlation Matrix")

            # Find strongest correlations
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]
                    corr_pairs.append((col1, col2, corr_val))

            # Sort by absolute correlation value
            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

            # Add text with top correlations
            if corr_pairs:
                top_corr_text = "Top Correlations:\n"
                for col1, col2, corr_val in corr_pairs[:5]:  # Show top 5
                    top_corr_text += f"{col1} & {col2}: {corr_val:.2f}\n"

                plt.figtext(0.15, 0.02, top_corr_text, fontsize=10,
                          bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            # Prepare chart data
            chart_data = {
                "columns": corr_matrix.columns.tolist(),
                "top_correlations": [(p[0], p[1], p[2]) for p in corr_pairs[:10]]  # Top 10 correlations
            }

        plt.tight_layout()

        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64, chart_data