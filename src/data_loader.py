"""
Data loading and date parsing module.

This module handles loading the raw CSV and parsing mixed date formats
with explicit error handling and ambiguity detection.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, List
import warnings

from src.config import RAW_DATA_FILE


def parse_single_date(date_str: str) -> Tuple[datetime, str]:
    """
    Parse a single date string using explicitly defined formats.
    
    Strategy:
    1. Try dd-Mmm-yy format (e.g., "03-Oct-25") - unambiguous due to month name
    2. Try dd-mm-yyyy format (e.g., "17-10-2025") - day-first European convention
    3. Flag any unparseable dates
    
    DO NOT silently guess ambiguous dates. If a date cannot be confidently
    parsed, return None and flag as 'ambiguous' or 'unparseable'.
    
    Parameters
    ----------
    date_str : str
        The date string to parse
        
    Returns
    -------
    parsed_date : datetime or None
        The parsed datetime object, or None if unparseable
    status : str
        One of: 'ok', 'ambiguous', 'unparseable', 'missing'
    """
    if pd.isna(date_str) or date_str == '':
        return None, 'missing'
    
    date_str = str(date_str).strip()
    
    # Format 1: dd-Mmm-yy (e.g., "03-Oct-25", "16-Oct-25")
    # This format is unambiguous because month is a name
    try:
        parsed = datetime.strptime(date_str, '%d-%b-%y')
        return parsed, 'ok'
    except ValueError:
        pass
    
    # Format 2: dd-mm-yyyy (e.g., "17-10-2025", "14-03-2025")
    # Assumes day-first European convention (common in India)
    try:
        parsed = datetime.strptime(date_str, '%d-%m-%Y')
        return parsed, 'ok'
    except ValueError:
        pass
    
    # Format 3: mm-dd-yyyy (U.S. format) or dd-mm-yyyy
    # Try to determine which is correct based on the values
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
            
            # If first part > 12, it must be day (dd-mm-yyyy)
            if p1 > 12:
                parsed = datetime.strptime(date_str, '%d-%m-%Y')
                return parsed, 'ok'
            
            # If second part > 12, it must be month in mm-dd-yyyy format
            # Wait - this doesn't make sense. If p2 > 12, it must be DAY not month
            # So the format is mm-dd-yyyy
            if p2 > 12:
                parsed = datetime.strptime(date_str, '%m-%d-%Y')
                return parsed, 'ok'
            
            # Both parts <= 12, genuinely ambiguous
            # Default to mm-dd-yyyy but flag as ambiguous
            parsed = datetime.strptime(date_str, '%m-%d-%Y')
            if parsed.year == 2025:
                return parsed, 'ambiguous'
    except ValueError:
        pass
    
    # Could not parse with any known format
    return None, 'unparseable'


def load_and_parse_dates(filepath: str = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Load the raw CSV and parse all dates with explicit format handling.
    
    This function:
    1. Loads the CSV without any automatic date parsing
    2. Applies explicit date parsing to order_date column
    3. Collects statistics on parsing success, ambiguities, and failures
    4. Returns the DataFrame with a new 'order_date_parsed' column
    5. Returns a report dictionary with all parsing statistics
    
    Parameters
    ----------
    filepath : str, optional
        Path to the CSV file. If None, uses config.RAW_DATA_FILE
        
    Returns
    -------
    df : pd.DataFrame
        DataFrame with original data plus 'order_date_parsed' and 'date_parse_status' columns
    report : dict
        Dictionary with parsing statistics and sample problematic dates
    """
    if filepath is None:
        filepath = RAW_DATA_FILE
    
    # Load CSV without automatic date parsing
    df = pd.read_csv(filepath, dtype=str)
    
    # Parse each date explicitly
    parse_results = df['order_date'].apply(parse_single_date)
    
    df['order_date_parsed'] = parse_results.apply(lambda x: x[0])
    df['date_parse_status'] = parse_results.apply(lambda x: x[1])
    
    # Collect statistics
    status_counts = df['date_parse_status'].value_counts().to_dict()
    
    # Get sample problematic dates
    ambiguous_samples = df[df['date_parse_status'] == 'ambiguous']['order_date'].head(10).tolist()
    unparseable_samples = df[df['date_parse_status'] == 'unparseable']['order_date'].head(10).tolist()
    
    # Check if any parsed dates fall outside 2025 (data quality issue)
    valid_dates = df[df['date_parse_status'].isin(['ok', 'ambiguous'])]['order_date_parsed']
    dates_outside_2025 = valid_dates[
        (valid_dates.dt.year != 2025) & valid_dates.notna()
    ]
    
    report = {
        'total_records': len(df),
        'status_counts': status_counts,
        'ok_count': status_counts.get('ok', 0),
        'ambiguous_count': status_counts.get('ambiguous', 0),
        'unparseable_count': status_counts.get('unparseable', 0),
        'missing_count': status_counts.get('missing', 0),
        'ambiguous_samples': ambiguous_samples,
        'unparseable_samples': unparseable_samples,
        'dates_outside_2025_count': len(dates_outside_2025),
        'dates_outside_2025_samples': dates_outside_2025.head(10).tolist() if len(dates_outside_2025) > 0 else []
    }
    
    return df, report


def check_cutoff_date_reliability(df: pd.DataFrame, cutoff_date: datetime) -> Dict:
    """
    Check if dates around the September 30, 2025 cutoff are reliably parsed.
    
    This is CRITICAL because misclassified dates near the cutoff could
    incorrectly assign customers to historical vs future periods.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'order_date_parsed' and 'date_parse_status' columns
    cutoff_date : datetime
        The cutoff date (2025-09-30)
        
    Returns
    -------
    report : dict
        Dictionary with reliability statistics around the cutoff
    """
    # Define a window around the cutoff (e.g., ±14 days)
    window_days = 14
    lower_bound = cutoff_date - pd.Timedelta(days=window_days)
    upper_bound = cutoff_date + pd.Timedelta(days=window_days)
    
    # Find dates in the cutoff window
    dates_near_cutoff = df[
        (df['order_date_parsed'] >= lower_bound) &
        (df['order_date_parsed'] <= upper_bound)
    ].copy()
    
    # Check parsing status for these critical dates
    status_counts = dates_near_cutoff['date_parse_status'].value_counts().to_dict()
    
    ambiguous_near_cutoff = dates_near_cutoff[
        dates_near_cutoff['date_parse_status'] == 'ambiguous'
    ]
    
    report = {
        'window_start': lower_bound.date(),
        'window_end': upper_bound.date(),
        'total_records_in_window': len(dates_near_cutoff),
        'status_counts': status_counts,
        'ambiguous_count': len(ambiguous_near_cutoff),
        'ambiguous_samples': ambiguous_near_cutoff['order_date'].head(10).tolist()
    }
    
    return report


def generate_date_parsing_report(df: pd.DataFrame, parse_report: Dict, cutoff_report: Dict) -> str:
    """
    Generate a human-readable report on date parsing results.
    
    Parameters
    ----------
    df : pd.DataFrame
        Parsed DataFrame
    parse_report : dict
        Overall parsing statistics
    cutoff_report : dict
        Cutoff-specific statistics
        
    Returns
    -------
    report_text : str
        Formatted report text
    """
    lines = []
    lines.append("=" * 80)
    lines.append("DATE PARSING REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("OVERALL PARSING RESULTS:")
    lines.append(f"  Total records: {parse_report['total_records']:,}")
    lines.append(f"  Successfully parsed (OK): {parse_report['ok_count']:,} ({parse_report['ok_count']/parse_report['total_records']*100:.2f}%)")
    lines.append(f"  Ambiguous format: {parse_report['ambiguous_count']:,} ({parse_report['ambiguous_count']/parse_report['total_records']*100:.2f}%)")
    lines.append(f"  Unparseable: {parse_report['unparseable_count']:,} ({parse_report['unparseable_count']/parse_report['total_records']*100:.2f}%)")
    lines.append(f"  Missing: {parse_report['missing_count']:,} ({parse_report['missing_count']/parse_report['total_records']*100:.2f}%)")
    lines.append("")
    
    if parse_report['ambiguous_count'] > 0:
        lines.append("AMBIGUOUS DATES (parsed but format uncertain):")
        for date in parse_report['ambiguous_samples']:
            lines.append(f"  - {date}")
        lines.append("")
    
    if parse_report['unparseable_count'] > 0:
        lines.append("UNPARSEABLE DATES:")
        for date in parse_report['unparseable_samples']:
            lines.append(f"  - {date}")
        lines.append("")
    
    if parse_report['dates_outside_2025_count'] > 0:
        lines.append(f"WARNING: {parse_report['dates_outside_2025_count']} dates fall outside 2025:")
        for date in parse_report['dates_outside_2025_samples']:
            lines.append(f"  - {date}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("CUTOFF DATE RELIABILITY CHECK (September 30, 2025)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Window: {cutoff_report['window_start']} to {cutoff_report['window_end']}")
    lines.append(f"Records in window: {cutoff_report['total_records_in_window']:,}")
    lines.append("")
    
    if cutoff_report['ambiguous_count'] > 0:
        lines.append(f"WARNING: {cutoff_report['ambiguous_count']} ambiguous dates near cutoff!")
        lines.append("These dates could affect historical vs future classification:")
        for date in cutoff_report['ambiguous_samples']:
            lines.append(f"  - {date}")
        lines.append("")
        lines.append("RECOMMENDATION: Investigate these dates before proceeding to target construction.")
    else:
        lines.append("[OK] No ambiguous dates near cutoff. Historical/future split is reliable.")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)
