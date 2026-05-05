import requests
from datetime import date
from pathlib import Path

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LandRegistryDataImporter:

    HOUSE_PRICE_BASE_URL = "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/"
    EARLIEST_YEAR = 1995

    def __init__(self, download_path: Path):
        self.download_path = Path(download_path)

        if not self.download_path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {self.download_path.parent}")

        self.download_path.mkdir(exist_ok=True)

    def download_land_registry_data(self, start_year: int, end_year: int):
        current_year = date.today().year

        if start_year < self.EARLIEST_YEAR:
            raise ValueError(f"start_year must be >= {self.EARLIEST_YEAR}, got {start_year}")
        if end_year > current_year:
            raise ValueError(f"end_year must be <= {current_year}, got {end_year}")
        if start_year > end_year:
            raise ValueError(f"start_year ({start_year}) must be <= end_year ({end_year})")

        files_to_download = [f"pp-{year}.csv" for year in range(start_year, end_year + 1)]

        logger.info("Starting download of Land Registry data...")
        logger.info(f"Number of files to download: {len(files_to_download)}")

        for file_number, file_name in enumerate(files_to_download, start=1):
            remote_file_url = f"{self.HOUSE_PRICE_BASE_URL}{file_name}"
            path_to_save_file = self.download_path / file_name

            if path_to_save_file.exists():
                logger.info(f"File {file_name} already exists. Skipping download.")
                continue

            with requests.get(remote_file_url, stream=True) as response:
                response.raise_for_status()

                with open(path_to_save_file, mode='wb') as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)

            logger.info(f"Downloaded file {file_number} of {len(files_to_download)}: {file_name}")

        logger.info("Completed downloading Land Registry data.")
