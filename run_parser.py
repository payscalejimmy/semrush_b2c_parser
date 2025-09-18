#!/usr/bin/env python3
"""
PayScale URL Parser - Command Line Interface

Usage:
    python run_parser.py input_file.csv
    python run_parser.py input_file.csv --output-dir results/
    python run_parser.py large_file.csv --batch-size 50000
"""

import argparse
import os
import sys
import time
from pathlib import Path
import pandas as pd

# Import the parser (assuming payscale_parser.py is in the same directory)
try:
    from payscale_parser import PayScaleURLParser, batch_process_large_file
except ImportError:
    print("Error: payscale_parser.py not found in current directory")
    print("Make sure payscale_parser.py is in the same folder as run_parser.py")
    sys.exit(1)

def create_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def detect_csv_format(filename, url_column=None):
    """
    Detect CSV format and find URL column
    """
    try:
        # Try to read first few rows to detect format
        sample = pd.read_csv(filename, nrows=5)
        
        if url_column and url_column in sample.columns:
            return url_column
        
        # Look for common URL column names
        url_candidates = ['URL', 'url', 'Url', 'Page_URL', 'page_url', 'Link', 'link']
        for candidate in url_candidates:
            if candidate in sample.columns:
                print(f"Found URL column: {candidate}")
                return candidate
        
        # If no standard name found, look for columns containing URLs
        for col in sample.columns:
            if sample[col].dtype == 'object':  # String column
                sample_values = sample[col].dropna().astype(str)
                if any('payscale.com' in str(val) for val in sample_values):
                    print(f"Detected URL column: {col}")
                    return col
        
        print(f"Available columns: {list(sample.columns)}")
        raise ValueError("Could not automatically detect URL column")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def print_progress(current, total, start_time):
    """Print progress bar"""
    if total == 0:
        return
    
    progress = current / total
    elapsed = time.time() - start_time
    eta = elapsed / progress - elapsed if progress > 0 else 0
    
    bar_length = 40
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    print(f'\rProgress: |{bar}| {progress:.1%} ({current:,}/{total:,}) '
          f'ETA: {eta:.1f}s', end='', flush=True)

def main():
    parser = argparse.ArgumentParser(
        description='Parse PayScale URLs and analyze traffic patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_parser.py data.csv
  python run_parser.py data.csv --output-dir results/
  python run_parser.py large_file.csv --batch-size 50000 --url-column "Page_URL"
  python run_parser.py data.csv --no-analysis  # Skip traffic analysis
        """
    )
    
    # Required arguments
    parser.add_argument('input_file', 
                       help='Input CSV file containing PayScale URLs')
    
    # Optional arguments
    parser.add_argument('--output-dir', '-o', 
                       default='output',
                       help='Output directory for results (default: output)')
    
    parser.add_argument('--url-column', '-u',
                       help='Name of the URL column (auto-detect if not specified)')
    
    parser.add_argument('--traffic-column', '-t',
                       default='Traffic',
                       help='Name of the traffic column for analysis (default: Traffic)')
    
    parser.add_argument('--batch-size', '-b',
                       type=int,
                       default=10000,
                       help='Batch size for processing large files (default: 10000)')
    
    parser.add_argument('--no-analysis', 
                       action='store_true',
                       help='Skip traffic analysis (faster processing)')
    
    parser.add_argument('--sample', '-s',
                       type=int,
                       help='Process only first N rows (for testing)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    # Create output directory
    output_dir = create_output_directory(args.output_dir)
    print(f"Output directory: {output_dir}")
    
    # Detect URL column
    url_column = detect_csv_format(args.input_file, args.url_column)
    print(f"Using URL column: {url_column}")
    
    # Initialize parser
    payscale_parser = PayScaleURLParser()
    start_time = time.time()
    
    try:
        print(f"\nProcessing file: {args.input_file}")
        
        # Determine file size for progress tracking
        total_rows = sum(1 for _ in open(args.input_file)) - 1  # Subtract header
        print(f"Total rows to process: {total_rows:,}")
        
        # Handle sampling
        if args.sample:
            print(f"Processing sample of {args.sample:,} rows")
            df = pd.read_csv(args.input_file, nrows=args.sample)
            df = payscale_parser.parse_csv_data(df, url_column)
        
        # Handle large files with batch processing
        elif total_rows > args.batch_size:
            print(f"Large file detected. Using batch processing (batch size: {args.batch_size:,})")
            df = batch_process_large_file(args.input_file, args.batch_size, url_column)
        
        # Handle regular files
        else:
            print("Loading and processing data...")
            df = pd.read_csv(args.input_file)
            df = payscale_parser.parse_csv_data(df, url_column)
        
        processing_time = time.time() - start_time
        print(f"\n✓ Processing completed in {processing_time:.1f} seconds")
        print(f"✓ Processed {len(df):,} URLs")
        
        # Export main parsed data
        output_file = os.path.join(output_dir, 'parsed_data.csv')
        df.to_csv(output_file, index=False)
        print(f"✓ Parsed data saved to: {output_file}")
        
        # Print summary statistics
        print(f"\n=== PARSING SUMMARY ===")
        print(f"Total URLs processed: {len(df):,}")
        
        section_counts = df['section'].value_counts()
        print(f"\nBy Section:")
        for section, count in section_counts.head(10).items():
            percentage = (count / len(df)) * 100
            print(f"  {section}: {count:,} ({percentage:.1f}%)")
        
        category_counts = df['category'].value_counts()
        print(f"\nBy Category:")
        for category, count in category_counts.head(10).items():
            percentage = (count / len(df)) * 100
            print(f"  {category}: {count:,} ({percentage:.1f}%)")
        
        # Traffic analysis (if requested and traffic column exists)
        if not args.no_analysis and args.traffic_column in df.columns:
            print(f"\n=== TRAFFIC ANALYSIS ===")
            print(f"Analyzing traffic patterns using column: {args.traffic_column}")
            
            analyses = payscale_parser.analyze_traffic_by_category(df, args.traffic_column)
            
            # Export analysis results
            for analysis_name, analysis_data in analyses.items():
                if not analysis_data.empty:
                    analysis_file = os.path.join(output_dir, f'analysis_{analysis_name}.csv')
                    analysis_data.to_csv(analysis_file)
                    print(f"✓ {analysis_name.replace('_', ' ').title()} analysis: {analysis_file}")
            
            # Print top-level traffic summary
            if 'by_section' in analyses and not analyses['by_section'].empty:
                print(f"\nTop Traffic Sections:")
                for section, row in analyses['by_section'].head(5).iterrows():
                    print(f"  {section}: {row['Total_Traffic']:,.0f} total traffic "
                          f"({row['URL_Count']:,} URLs)")
        
        elif args.traffic_column not in df.columns and not args.no_analysis:
            print(f"\n⚠ Traffic analysis skipped: Column '{args.traffic_column}' not found")
            print(f"Available columns: {list(df.columns)}")
            print("Use --traffic-column to specify the correct column name")
        
        total_time = time.time() - start_time
        print(f"\n✓ Complete! Total runtime: {total_time:.1f} seconds")
        print(f"📁 All results saved in: {output_dir}/")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        print(f"For help, run: python {sys.argv[0]} --help")
        sys.exit(1)

if __name__ == "__main__":
    main()