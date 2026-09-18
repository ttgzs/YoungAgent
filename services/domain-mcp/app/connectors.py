import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from connectors.project.connector import ProjectConnector
from connectors.bim.connector import BIMConnector
from connectors.iot.connector import IoTConnector
