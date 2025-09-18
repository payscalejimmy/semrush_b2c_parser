# PayScale URL Parser

A Python tool for parsing and analyzing PayScale URLs to extract traffic patterns, geographic data, and content categorization from large datasets.

## Features

- **Intelligent URL Parsing**: Automatically categorizes PayScale URLs by section (cost-of-living, research, etc.)
- **Geographic Extraction**: Extracts state/city data from cost-of-living URLs
- **Job/Employer Analysis**: Parses job titles, company names, and salary types from research URLs
- **Traffic Analysis**: Provides comprehensive traffic breakdowns by category, location, and content type
- **Scalable Processing**: Handles millions of URLs efficiently with batch processing
- **Export Ready**: Outputs parsed data and analysis reports to CSV files

## Quick Setup

### Option 1: Automated Setup (Recommended)

1. **Download all files to a folder**:
   - `payscale_parser.py` - Main parser code
   - `run_parser.py` - Command line interface
   - `requirements.txt` - Dependencies
   - `setup.py` - Automated setup script
   - `test_parser.py` - Test verification
   - `sample_data.csv` - Sample data for testing

2. **Run the setup script**:
   ```bash
   python setup.py
   ```
   This will:
   - Check Python version compatibility
   - Install required packages
   - Create output directories
   - Test the installation
   - Run a quick verification

3. **Test with sample data**:
   ```bash
   python run_parser.py sample_data.csv
   ```

### Option 2: Manual Setup

1. **Clone or download the project files**
   ```bash
   mkdir payscale-parser
   cd payscale-parser
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## File Structure

```
payscale-parser/
├── payscale_parser.py          # Main parser script
├── run_parser.py               # Command-line interface
├── setup.py                    # Automated setup script
├── test_parser.py              # Test verification script
├── requirements.txt            # Python dependencies
├── sample_data.csv             # Example input file (35 sample URLs)
├── README.md                   # This file
├── data/                       # Place your CSV files here
├── output/                     # Generated output files
│   ├── parsed_data.csv         # Main parsed results
│   └── analysis_*.csv          # Traffic analysis files
```

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup

## Quick Verification

After setup, verify everything works:

```bash
# Run the test suite
python test_parser.py

# Process the sample data
python run_parser.py sample_data.csv

# Check the results
ls output/
```

You should see output files like:
- `parsed_data.csv` - Your data with new parsing columns
- `analysis_by_section.csv` - Traffic breakdown by section
- `analysis_by_category.csv` - Traffic breakdown by category
- `analysis_cost_of_living_by_state.csv` - State-level analysis

## Usage

### Method 1: Command Line Interface

```bash
# Basic usage - parse CSV file
python run_parser.py input_file.csv

# Specify output directory
python run_parser.py input_file.csv --output-dir results/

# Process large file with custom batch size
python run_parser.py large_file.csv --batch-size 50000

# Specify URL column name (if different from 'URL')
python run_parser.py data.csv --url-column "Page_URL"
```

### Method 2: Python Script

```python
from payscale_parser import PayScaleURLParser

# Initialize parser
parser = PayScaleURLParser()

# Option A: Parse CSV file
df = parser.parse_csv_data('your_data.csv', url_column='URL')

# Option B: Parse list of URLs
urls = ['https://www.payscale.com/cost-of-living-calculator/California-San-Francisco', 
        'https://www.payscale.com/research/US/Job=Software_Engineer/Salary']
df = parser.parse_url_list(urls)

# Analyze traffic patterns
analyses = parser.analyze_traffic_by_category(df, traffic_column='Traffic')

# Export results
parser.export_parsed_data(df, 'output/parsed_results.csv')

# Export analysis reports
for name, analysis in analyses.items():
    analysis.to_csv(f'output/analysis_{name}.csv')
```

### Method 3: Large File Processing

For files with millions of rows:

```python
from payscale_parser import batch_process_large_file

# Process in batches to manage memory
df = batch_process_large_file('large_dataset.csv', 
                              batch_size=50000, 
                              url_column='URL')

# Continue with analysis...
```

## Input File Format

Your CSV file should have at minimum a URL column. Here's the expected format:

```csv
URL,Traffic,Number of Keywords,Traffic (%)
https://www.payscale.com/,335612,36652,2.59
https://www.payscale.com/cost-of-living-calculator/California-San-Francisco,15000,1200,1.2
https://www.payscale.com/research/US/Job=Software_Engineer/Salary,8500,950,0.8
https://www.payscale.com/research/US/Employer=Google_Inc/Salary,7200,850,0.7
```

**Required Column:**
- `URL`: The PayScale URL to parse

**Optional Columns** (will be preserved in output):
- `Traffic`: Traffic volume for analysis
- `Traffic (%)`: Traffic percentage
- `Number of Keywords`: Keyword count
- Any other columns you want to keep

## Output Files

### 1. Main Parsed Data (`parsed_data.csv`)
Contains original data plus these new columns:

| Column | Description | Example |
|--------|-------------|---------|
| `section` | Main URL section | `cost_of_living`, `research`, `homepage` |
| `category` | Specific category | `cost_of_living`, `research_job`, `research_employer` |
| `location_state` | State (for cost-of-living) | `California`, `Texas` |
| `location_city` | City (for cost-of-living) | `San Francisco`, `Austin` |
| `country` | Country (for research URLs) | `US`, `IN`, `UK` |
| `job_title` | Job title (for job research) | `Software Engineer`, `Data Scientist` |
| `employer` | Company name (for employer research) | `Google Inc`, `Microsoft Corporation` |
| `skill` | Skill name (for skill research) | `Python`, `Machine Learning` |
| `metric_type` | Salary, Hourly Rate, etc. | `Salary`, `Hourly_Rate` |

### 2. Analysis Reports
- `analysis_by_section.csv`: Traffic breakdown by main sections
- `analysis_by_category.csv`: Traffic breakdown by specific categories  
- `analysis_cost_of_living_by_state.csv`: Cost-of-living traffic by state
- `analysis_research_by_country.csv`: Research traffic by country
- `analysis_top_employers.csv`: Top 20 employers by traffic
- `analysis_top_jobs.csv`: Top 20 jobs by traffic

## Sample Analysis Output

### Traffic by Section
```csv
section,Total_Traffic,URL_Count,Avg_Traffic
cost_of_living,450000,85,5294.12
research,280000,45,6222.22
homepage,335612,1,335612.00
other,25000,12,2083.33
```

### Cost of Living by State  
```csv
location_state,Total_Traffic,URL_Count,Avg_Traffic
California,125000,25,5000.00
Texas,85000,18,4722.22
Washington,35000,8,4375.00
Florida,28000,12,2333.33
```

## Performance Tips

### For Large Datasets (1M+ URLs):

1. **Use Batch Processing**:
   ```python
   df = batch_process_large_file('huge_file.csv', batch_size=100000)
   ```

2. **Optimize Memory**:
   ```python
   # Only load necessary columns
   df = pd.read_csv('data.csv', usecols=['URL', 'Traffic'])
   ```

3. **Parallel Processing** (for very large files):
   ```python
   import multiprocessing as mp
   
   # Split file and process in parallel
   # (Advanced - implement based on your specific needs)
   ```

## Troubleshooting

### Common Issues:

1. **"URL column not found"**
   - Specify the correct column name: `--url-column "Your_URL_Column_Name"`

2. **Memory errors with large files**
   - Reduce batch size: `--batch-size 10000`
   - Use batch processing function

3. **Empty analysis results**
   - Check that your traffic column is named correctly
   - Ensure URLs are properly formatted

4. **Import errors**
   - Make sure you're in the correct directory
   - Verify virtual environment is activated
   - Reinstall requirements: `pip install -r requirements.txt`

## Examples

### Quick Start Example

1. **Create sample data file** (`sample_data.csv`):
   ```csv
   URL,Traffic
   https://www.payscale.com/cost-of-living-calculator/California-San-Francisco,15000
   https://www.payscale.com/research/US/Job=Software_Engineer/Salary,8500
   https://www.payscale.com/research/US/Employer=Google_Inc/Salary,7200
   ```

2. **Run the parser**:
   ```bash
   python run_parser.py sample_data.csv
   ```

3. **Check results** in the `output/` directory

### Advanced Usage Example

```python
# Custom analysis for specific needs
parser = PayScaleURLParser()
df = parser.parse_csv_data('my_data.csv')

# Filter for California cost-of-living pages
ca_col = df[(df['category'] == 'cost_of_living') & (df['location_state'] == 'California')]

# Analyze top California cities by traffic  
city_traffic = ca_col.groupby('location_city')['Traffic'].sum().sort_values(ascending=False)
print("Top California cities by traffic:")
print(city_traffic.head(10))

# Export California-specific results
ca_col.to_csv('output/california_cost_of_living.csv', index=False)
```

## Support

For issues or questions:
1. Check this README for common solutions
2. Verify your input data format matches the examples
3. Ensure all dependencies are properly installed

## License

This tool is provided as-is for URL parsing and analysis purposes.

# 1. Download all files to a folder, then:
python setup.py

# 2. Test with sample data:
python run_parser.py sample_data.csv

# 3. Use with your own data:
python run_parser.py your_data.csv

# Large file processing with batches
python run_parser.py large_file.csv --batch-size 100000

# Custom output location
python run_parser.py data.csv --output-dir results/

# Different column names  
python run_parser.py data.csv --url-column "Page_URL" --traffic-column "Sessions"