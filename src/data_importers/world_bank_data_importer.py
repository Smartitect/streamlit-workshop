import requests
import polars as pl
import logging
from typing import List, Dict, Any

class WorldBankDataImporter:
    BASE_URL = "https://data360api.worldbank.org/data360/data"
    V2_BASE_URL = "https://api.worldbank.org/v2"

    def __init__(self):
        self.session = requests.Session()
        logging.basicConfig(level=logging.INFO)

    def get_countries(self) -> pl.DataFrame:
        """
        Fetches the list of countries from the World Bank V2 API.
        Returns a Polars DataFrame containing country metadata.
        """
        url = f"{self.V2_BASE_URL}/country"
        params = {
            'format': 'json',
            'per_page': 1000,
            'page': 1
        }
        
        all_data = []
        
        while True:
            logging.info(f"Fetching countries page {params['page']}...")
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # API returns [metadata, data]
                if not isinstance(data, list) or len(data) < 2:
                    break
                    
                page_data = data[1]
                if not page_data:
                    break
                    
                all_data.extend(page_data)
                
                metadata = data[0]
                if params['page'] >= metadata['pages']:
                    break
                    
                params['page'] += 1
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching countries: {e}")
                break
        
        countries = []
        for entry in all_data:
            countries.append({
                'country_code': entry['id'],
                'iso2_code': entry['iso2Code'],
                'country_name': entry['name'],
                'region': entry['region']['value'],
                'region_id': entry['region']['id'],
                'income_level': entry['incomeLevel']['value'],
                'capital_city': entry['capitalCity'],
                'longitude': entry['longitude'],
                'latitude': entry['latitude']
            })
            
        return pl.DataFrame(countries)

    def get_indicator_metadata(self, indicators: List[str]) -> pl.DataFrame:
        """
        Fetches metadata for a list of indicator codes from the Data360 API.
        
        Args:
            indicators: List of indicator codes (e.g., 'SP.POP.TOTL').
        """
        url = "https://data360api.worldbank.org/data360/metadata"
        
        # Format indicators
        formatted_indicators = []
        for ind in indicators:
            if "." in ind and not ind.startswith("WB_WDI_"):
                formatted = "WB_WDI_" + ind.replace(".", "_")
                formatted_indicators.append(formatted)
            else:
                formatted_indicators.append(ind)
        
        # Construct filter query
        # query: "&$filter=series_description/idno eq 'WB_WDI_SP_POP_TOTL' or series_description/idno eq '...'"
        filter_clauses = [f"series_description/idno eq '{ind}'" for ind in formatted_indicators]
        filter_query = " or ".join(filter_clauses)
        
        payload = {
            "query": f"&$filter={filter_query}"
        }
        
        logging.info(f"Fetching metadata for {len(indicators)} indicators...")
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            metadata_list = []
            for item in data.get('value', []):
                desc = item.get('series_description', {})
                metadata_list.append({
                    'indicator_code': desc.get('idno'),
                    'indicator_name': desc.get('name'),
                    'aggregation_method': desc.get('aggregation_method'),
                    'definition_long': desc.get('definition_long'),
                    'statistical_concept': desc.get('statistical_concept'),
                    'methodology': desc.get('methodology'),
                    'limitation': desc.get('limitation'),
                    'relevance': desc.get('relevance')
                })
                
            return pl.DataFrame(metadata_list)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching metadata: {e}")
            return pl.DataFrame()

    def get_data(self, start_year: int, end_year: int, countries: List[str], indicators: List[str]) -> pl.DataFrame:
        """
        Fetches data from the World Bank Data360 API.
        
        Args:
            start_year: Start year (inclusive).
            end_year: End year (inclusive).
            countries: List of ISO3 country codes.
            indicators: List of indicator codes (e.g., 'SP.POP.TOTL'). 
                        Will automatically format to 'WB_WDI_...' if needed.
        """
        # Format indicators to match Data360 API requirements (WB_WDI_ prefix and underscores)
        formatted_indicators = []
        for ind in indicators:
            if "." in ind and not ind.startswith("WB_WDI_"):
                # Convert 'SP.POP.TOTL' -> 'WB_WDI_SP_POP_TOTL'
                formatted = "WB_WDI_" + ind.replace(".", "_")
                formatted_indicators.append(formatted)
            else:
                formatted_indicators.append(ind)
        
        params = {
            "DATABASE_ID": "WB_WDI",
            "INDICATOR": ",".join(formatted_indicators),
            "REF_AREA": ",".join(countries),
            "timePeriodFrom": start_year,
            "timePeriodTo": end_year,
            "skip": 0
        }
        
        all_data = []
        
        while True:
            logging.info(f"Fetching data with skip={params['skip']}...")
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                values = data.get('value', [])
                if not values:
                    break
                    
                all_data.extend(values)
                
                # Check if we have fetched all available data
                total_count = data.get('count', 0)
                if len(all_data) >= total_count:
                    break
                    
                params['skip'] += len(values)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching data: {e}")
                break
        
        if not all_data:
            logging.warning("No data found.")
            return pl.DataFrame()
            
        df = pl.DataFrame(all_data)
        
        # Select and rename relevant columns
        # The API returns: REF_AREA, TIME_PERIOD, OBS_VALUE, INDICATOR, etc.
        
        df = df.select([
            pl.col("REF_AREA").alias("country_code"),
            pl.col("TIME_PERIOD").cast(pl.Int64).alias("year"),
            pl.col("INDICATOR").alias("indicator_code"),
            pl.col("OBS_VALUE").cast(pl.Float64).alias("value")
        ])
        
        return df
