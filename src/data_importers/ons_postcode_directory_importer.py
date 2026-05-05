import requests
import zipfile
import io
from pathlib import Path

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OnsPostcodeDirectoryImporter:
    """
    OnsPostcodeDirectoryImporter is a class designed to facilitate the easy loading of postcode
    directory data from the Office for National Statistics (ONS).

    The ONS Postcode Directory (ONSPD) relates current and terminated postcodes in the United
    Kingdom to a range of current statutory administrative, electoral, health and other
    geographies.

    The data is downloaded as a ZIP file and a single CSV file is extracted from within it.

    For more information about the dataset, visit the official webpage:
    https://geoportal.statistics.gov.uk/search?categories=%2Fcategories%2Fpostcode%20products%2Fons%20postcode%20directory
    """

    BASE_URL = "https://www.arcgis.com/sharing/rest/content/items/"
    ITEM_ID = "3080229224424c9cb53c0b48f5a64d27"
    ZIP_FILE_NAME = "ONSPD_FEB_2026.zip"
    CSV_FILE_NAME = "ONSPD_FEB_2026_UK.csv"
    CSV_PATH_IN_ZIP = f"Data/{CSV_FILE_NAME}"

    def __init__(self, download_path: Path) -> None:
        self.download_path = download_path
        self._create_folder_if_not_exists()

    def import_data(self) -> None:
        file_path = self.download_path / self.CSV_FILE_NAME
        if file_path.exists():
            logger.info(f"File {self.CSV_FILE_NAME} already exists")
            return
        url = self._build_file_url()
        self._download_and_extract(file_path, url)

    def _create_folder_if_not_exists(self):
        self.download_path.mkdir(parents=True, exist_ok=True)

    def _build_file_url(self) -> str:
        return f"{self.BASE_URL}{self.ITEM_ID}/data"

    def _download_and_extract(self, file_path: Path, url: str) -> None:
        logger.info(f"Downloading {self.ZIP_FILE_NAME} from {url}")
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Download complete. Extracting {self.CSV_PATH_IN_ZIP}")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            with zf.open(self.CSV_PATH_IN_ZIP) as source, open(file_path, "wb") as target:
                target.write(source.read())
        logger.info(f"File {self.CSV_FILE_NAME} extracted successfully")
