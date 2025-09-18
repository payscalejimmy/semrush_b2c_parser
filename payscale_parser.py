import pandas as pd
import re
from urllib.parse import urlparse, unquote
import numpy as np
from collections import defaultdict

class PayScaleURLParser:
    def __init__(self):
        # More specific patterns for better parsing
        self.url_patterns = {
            'cost_of_living': re.compile(r'/cost-of-living-calculator/([^/]+)(?:/(.+))?'),
            'research_job': re.compile(r'/research/([^/]+)/Job=([^/]+)/(.+)'),
            'research_employer': re.compile(r'/research/([^/]+)/Employer=([^/]+)/(.+)'),
            'research_country': re.compile(r'/research/([^/]+)/Country=([^/]+)/(.+)'),
            'research_skill': re.compile(r'/research/([^/]+)/Skill=([^/]+)/(.+)'),
            'general_research': re.compile(r'/research/([^/]+)/?$'),
        }
        
        # Patterns for parsing the metric portion of URLs
        self.metric_patterns = {
            # Salary/Page-3, Hourly_Rate/Page-2, etc.
            'pagination': re.compile(r'^([^/]+)/Page-(\d+)$'),
            
            # Hourly_Rate/0a9d4bb0/H.E.B., Salary/ffed3159/Additional_Info
            'with_id_and_extra': re.compile(r'^([^/]+)/([^/]+)/(.+)$'),
            
            # Just the metric type: Salary, Hourly_Rate, etc.
            'simple': re.compile(r'^([^/]+)$'),
            
            # City/State pattern: City/Washington-DC/Page-2
            'city_location': re.compile(r'^City/([^/]+)(?:/Page-(\d+))?$'),
        }
    
    def safe_int_conversion(self, value):
        """
        Safely convert a value to integer, handling URL-encoded and malformed values
        """
        if not value:
            return None
            
        try:
            # First, try to decode if it's URL encoded
            decoded_value = unquote(str(value))
            
            # Check if it looks like a template variable (e.g., {Page}, %7BPage%7D)
            if '{' in decoded_value or '}' in decoded_value:
                return None
                
            # Extract just the numeric part if it exists
            numeric_match = re.search(r'\d+', decoded_value)
            if numeric_match:
                return int(numeric_match.group())
            else:
                return None
                
        except (ValueError, TypeError):
            return None
    
    def parse_metric_portion(self, metric_portion):
        """
        Parse the metric portion of research URLs to extract:
        - metric_type (Salary, Hourly_Rate, etc.)
        - page_number (if pagination exists)
        - additional_employer (if present)
        - location_info (if present)
        - unique_id (if present)
        """
        result = {
            'metric_type': None,
            'page_number': None,
            'additional_employer': None,
            'location_info': None,
            'unique_id': None,
            'raw_metric': metric_portion
        }
        
        if not metric_portion:
            return result
        
        # Check for pagination pattern first (Salary/Page-3)
        pagination_match = self.metric_patterns['pagination'].match(metric_portion)
        if pagination_match:
            result['metric_type'] = pagination_match.group(1)
            result['page_number'] = self.safe_int_conversion(pagination_match.group(2))
            return result
        
        # Check for city location pattern (City/Washington-DC/Page-2)
        city_match = self.metric_patterns['city_location'].match(metric_portion)
        if city_match:
            result['metric_type'] = 'City'  # This is a location-based research page
            result['location_info'] = unquote(city_match.group(1)).replace('-', ' ')
            if city_match.group(2):
                result['page_number'] = self.safe_int_conversion(city_match.group(2))
            return result
        
        # Check for pattern with ID and additional info (Hourly_Rate/0a9d4bb0/H.E.B.)
        id_extra_match = self.metric_patterns['with_id_and_extra'].match(metric_portion)
        if id_extra_match:
            result['metric_type'] = id_extra_match.group(1)
            
            # The middle part could be an ID or location
            middle_part = id_extra_match.group(2)
            extra_part = unquote(id_extra_match.group(3)).replace('_', ' ').replace('%2C', ',')
            
            # If middle part looks like an ID (alphanumeric), treat as ID
            if re.match(r'^[a-f0-9]{8,}$', middle_part, re.I):
                result['unique_id'] = middle_part
                result['additional_employer'] = extra_part
            # If it looks like a location pattern (contains dashes or state codes)
            elif '-' in middle_part or len(middle_part) == 2:
                result['location_info'] = middle_part.replace('-', ' ')
                # The extra part might be additional location or employer info
                if any(word in extra_part.lower() for word in ['page', 'salary', 'hourly']):
                    # This might be additional URL structure
                    pass
                else:
                    result['additional_employer'] = extra_part
            else:
                # Default: treat as additional employer info
                result['additional_employer'] = f"{middle_part} {extra_part}".replace('_', ' ')
            
            return result
        
        # Simple metric type only
        simple_match = self.metric_patterns['simple'].match(metric_portion)
        if simple_match:
            result['metric_type'] = simple_match.group(1)
            return result
        
        # Fallback: split on / and try to parse components
        parts = metric_portion.split('/')
        if len(parts) >= 1:
            result['metric_type'] = parts[0]
            
            if len(parts) >= 2:
                # Check if second part is a page number
                if parts[1].startswith('Page-'):
                    page_part = parts[1].split('-', 1)
                    if len(page_part) > 1:
                        result['page_number'] = self.safe_int_conversion(page_part[1])
                else:
                    result['unique_id'] = parts[1]
            
            if len(parts) >= 3:
                result['additional_employer'] = unquote(parts[2]).replace('_', ' ').replace('%2C', ',')
        
        return result
    
    def parse_url(self, url):
        """
        Parse a PayScale URL and extract relevant components
        Returns a dictionary with enhanced categorization info
        """
        if not url or pd.isna(url):
            return self._empty_result(url)
            
        try:
            parsed = urlparse(str(url).strip())
        except Exception:
            return self._empty_result(url)
            
        path = parsed.path
        
        result = {
            'url': url,
            'domain': parsed.netloc,
            'full_path': path,
            'section': None,
            'subsection': None,
            'location_state': None,
            'location_city': None,
            'country': None,
            'job_title': None,
            'employer': None,
            'skill': None,
            'metric_type': None,
            'page_number': None,
            'additional_employer': None,
            'location_info': None,
            'unique_id': None,
            'category': 'other'
        }
        
        # Cost of living calculator
        if '/cost-of-living-calculator' in path:
            result['section'] = 'cost_of_living'
            result['category'] = 'cost_of_living'
            
            match = self.url_patterns['cost_of_living'].search(path)
            if match:
                location = match.group(1)
                if location:
                    # Parse state-city format
                    parts = location.split('-', 1)
                    if len(parts) >= 2:
                        result['location_state'] = parts[0].replace('-', ' ')
                        result['location_city'] = parts[1].replace('-', ' ')
                    else:
                        result['location_state'] = parts[0].replace('-', ' ')
        
        # Research sections
        elif '/research/' in path:
            result['section'] = 'research'
            
            # Job research
            match = self.url_patterns['research_job'].search(path)
            if match:
                result['category'] = 'research_job'
                result['country'] = match.group(1)
                result['job_title'] = unquote(match.group(2)).replace('_', ' ').replace('%2C', ',')
                
                # Parse the metric portion with enhanced logic
                metric_info = self.parse_metric_portion(match.group(3))
                result.update(metric_info)
            
            # Employer research
            elif self.url_patterns['research_employer'].search(path):
                match = self.url_patterns['research_employer'].search(path)
                result['category'] = 'research_employer'
                result['country'] = match.group(1)
                result['employer'] = unquote(match.group(2)).replace('_', ' ').replace('%2C', ',')
                
                # Parse the metric portion with enhanced logic
                metric_info = self.parse_metric_portion(match.group(3))
                result.update(metric_info)
            
            # Country research
            elif self.url_patterns['research_country'].search(path):
                match = self.url_patterns['research_country'].search(path)
                result['category'] = 'research_country'
                result['country'] = match.group(1)
                result['subsection'] = unquote(match.group(2)).replace('_', ' ')
                
                # Parse the metric portion
                metric_info = self.parse_metric_portion(match.group(3))
                result.update(metric_info)
            
            # Skill research
            elif self.url_patterns['research_skill'].search(path):
                match = self.url_patterns['research_skill'].search(path)
                result['category'] = 'research_skill'
                result['country'] = match.group(1)
                result['skill'] = unquote(match.group(2)).replace('_', ' ').replace('%2C', ',')
                
                # Parse the metric portion
                metric_info = self.parse_metric_portion(match.group(3))
                result.update(metric_info)
            
            # General research
            elif self.url_patterns['general_research'].search(path):
                match = self.url_patterns['general_research'].search(path)
                result['category'] = 'research_general'
                result['country'] = match.group(1)
        
        # Other sections (unchanged)
        elif path == '/' or path == '':
            result['section'] = 'homepage'
            result['category'] = 'homepage'
        elif '/salary-calculator' in path:
            result['section'] = 'salary_calculator'
            result['category'] = 'tools'
        elif '/products/' in path:
            result['section'] = 'products'
            result['category'] = 'commercial'
        elif '/careers' in path:
            result['section'] = 'careers'
            result['category'] = 'corporate'
        elif '/compensation-trends/' in path:
            result['section'] = 'compensation_trends'
            result['category'] = 'content'
        else:
            result['section'] = 'other'
            result['category'] = 'other'
            
        return result
    
    def _empty_result(self, url):
        """Return an empty result structure for invalid URLs"""
        return {
            'url': url,
            'domain': None,
            'full_path': None,
            'section': None,
            'subsection': None,
            'location_state': None,
            'location_city': None,
            'country': None,
            'job_title': None,
            'employer': None,
            'skill': None,
            'metric_type': None,
            'page_number': None,
            'additional_employer': None,
            'location_info': None,
            'unique_id': None,
            'category': 'other'
        }
    
    def parse_csv_data(self, csv_data, url_column='URL'):
        """
        Parse CSV data and add URL categorization with enhanced metric parsing
        """
        # If csv_data is a string, convert to DataFrame
        if isinstance(csv_data, str):
            # Handle the case where data might be tab or comma separated
            if '\t' in csv_data:
                df = pd.read_csv(pd.StringIO(csv_data), sep='\t')
            else:
                df = pd.read_csv(pd.StringIO(csv_data))
        else:
            df = csv_data.copy()
        
        # Parse each URL
        parsed_data = []
        for idx, row in df.iterrows():
            try:
                url = row[url_column] if url_column in row else row.iloc[0]
                parsed_url = self.parse_url(url)
                
                # Combine original data with parsed data
                combined = dict(row)
                combined.update(parsed_url)
                parsed_data.append(combined)
            except Exception as e:
                print(f"Warning: Error parsing row {idx}: {e}")
                # Add the original row with empty parsed fields
                combined = dict(row)
                combined.update(self._empty_result(row.get(url_column, 'ERROR')))
                parsed_data.append(combined)
        
        return pd.DataFrame(parsed_data)
    
    def analyze_traffic_by_category(self, df, traffic_column='Traffic'):
        """
        Enhanced traffic analysis including new fields
        """
        analyses = {}
        
        # Traffic by main section
        section_traffic = df.groupby('section')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
        section_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
        analyses['by_section'] = section_traffic.sort_values('Total_Traffic', ascending=False)
        
        # Traffic by category
        category_traffic = df.groupby('category')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
        category_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
        analyses['by_category'] = category_traffic.sort_values('Total_Traffic', ascending=False)
        
        # Traffic by metric type (now properly parsed)
        metric_df = df[df['metric_type'].notna()].copy()
        if not metric_df.empty:
            metric_traffic = metric_df.groupby('metric_type')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            metric_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['by_metric_type'] = metric_traffic.sort_values('Total_Traffic', ascending=False)
        
        # Traffic by page number (pagination analysis)
        page_df = df[df['page_number'].notna()].copy()
        if not page_df.empty:
            page_traffic = page_df.groupby('page_number')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            page_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['by_page_number'] = page_traffic.sort_values('page_number')
        
        # Cost of living by state
        col_df = df[df['category'] == 'cost_of_living'].copy()
        if not col_df.empty:
            state_traffic = col_df.groupby('location_state')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            state_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['cost_of_living_by_state'] = state_traffic.sort_values('Total_Traffic', ascending=False)
        
        # Research by country
        research_df = df[df['section'] == 'research'].copy()
        if not research_df.empty:
            country_traffic = research_df.groupby('country')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            country_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['research_by_country'] = country_traffic.sort_values('Total_Traffic', ascending=False)
        
        # Top employers by traffic (now includes additional_employer)
        employer_df = df[df['category'] == 'research_employer'].copy()
        if not employer_df.empty:
            employer_traffic = employer_df.groupby('employer')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            employer_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['top_employers'] = employer_traffic.sort_values('Total_Traffic', ascending=False).head(20)
        
        # Additional employers analysis (from the parsed additional_employer field)
        additional_emp_df = df[df['additional_employer'].notna()].copy()
        if not additional_emp_df.empty:
            add_emp_traffic = additional_emp_df.groupby('additional_employer')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            add_emp_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['additional_employers'] = add_emp_traffic.sort_values('Total_Traffic', ascending=False).head(20)
        
        # Top jobs by traffic
        job_df = df[df['category'] == 'research_job'].copy()
        if not job_df.empty:
            job_traffic = job_df.groupby('job_title')[traffic_column].agg(['sum', 'count', 'mean']).round(2)
            job_traffic.columns = ['Total_Traffic', 'URL_Count', 'Avg_Traffic']
            analyses['top_jobs'] = job_traffic.sort_values('Total_Traffic', ascending=False).head(20)
        
        return analyses
    
    def export_parsed_data(self, df, filename='parsed_payscale_data.csv'):
        """
        Export parsed data to CSV with all new columns
        """
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")
        return filename

# Additional functions for backward compatibility and large file processing
def batch_process_large_file(filename, batch_size=10000, url_column='URL'):
    """
    Process large CSV files in batches for memory efficiency
    """
    parser = PayScaleURLParser()
    
    # Process file in chunks
    chunk_list = []
    chunk_count = 0
    
    print(f"Processing file in batches of {batch_size:,} rows...")
    
    try:
        for chunk in pd.read_csv(filename, chunksize=batch_size):
            chunk_count += 1
            print(f"Processing batch {chunk_count} ({len(chunk):,} rows)...")
            parsed_chunk = parser.parse_csv_data(chunk, url_column)
            chunk_list.append(parsed_chunk)
        
        print(f"Combining {len(chunk_list)} batches...")
        # Combine all chunks
        full_df = pd.concat(chunk_list, ignore_index=True)
        return full_df
        
    except Exception as e:
        print(f"Error processing file in batches: {e}")
        raise

def process_url_list(url_list):
    """
    Process a list of URLs and return a DataFrame with parsed information
    Standalone function for backward compatibility
    """
    parser = PayScaleURLParser()
    return parser.parse_url_list(url_list)

def parse_url_list_standalone(url_list):
    """
    Process a list of URLs and return a DataFrame with parsed information
    Optimized for large datasets
    """
    parser = PayScaleURLParser()
    parsed_data = []
    
    for url in url_list:
        parsed_url = parser.parse_url(url.strip() if isinstance(url, str) else str(url))
        parsed_data.append(parsed_url)
    
    return pd.DataFrame(parsed_data)

# Monkey patch the method to the class for backward compatibility
PayScaleURLParser.parse_url_list = lambda self, url_list: parse_url_list_standalone(url_list)