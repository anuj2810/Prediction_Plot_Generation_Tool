import os
import sys
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsMapSettings,
    QgsMapRendererCustomPainterJob, QgsProperty, QgsFillSymbol, QgsSingleSymbolRenderer
)
from qgis.analysis import QgsNativeAlgorithms
from PyQt5.QtGui import QImage, QPainter, QColor, QPen
from PyQt5.QtCore import QSize, Qt

# --- Configuration ---
QGIS_PREFIX = os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.28.14\apps\qgis-ltr")
CSV_INPUT = r"delimitedtext://file:///C:/Users/anu07/Desktop/pv2/cell_file/final_cell.csv?delimiter=,&xField=Longitude&yField=Latitude&crs=EPSG:4326"
RSRP_TAB = r"C:/Users/anu07/Documents/test2/site_data/700/T4RJ28UDUPRP9UUD119/T4RJ28UDUPRP9UUD119_RSRP.tab"
SCRAPED_IMAGE_PATH = r"C:/Users/anu07/Documents/test2/legend/RSRP.png"

# --- Step 1: QGIS Setup ---
if not os.path.exists(QGIS_PREFIX):
    raise EnvironmentError(f"❌ QGIS path invalid: {QGIS_PREFIX}")


qgs = QgsApplication([], False)
QgsApplication.setPrefixPath(QGIS_PREFIX, True)
qgs.initQgis()

# --- Step 2: Processing Setup ---
import processing
from processing.core.Processing import Processing

Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# --- Step 3: Load shapetools Plugin ---
plugin_path = os.path.expanduser(
    r"C:\Users\anu07\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins"
)
if plugin_path not in sys.path:
    sys.path.append(plugin_path)

try:
    from shapetools import shapeToolsProcessing
    provider = shapeToolsProcessing.ShapeToolsProvider()
    QgsApplication.processingRegistry().addProvider(provider)
except Exception as e:
    sys.exit(f"❌ Failed to register shapetools provider: {e}")

# --- Step 4: Run shapetools:createpie ---
result = processing.run("shapetools:createpie", {
    'INPUT': CSV_INPUT,
    'ShapeType': 0,
    'AzimuthMode': 1,
    'Azimuth1': QgsProperty.fromField("AZIMUTH"),
    'Azimuth2': 50,
    'Radius': 0.18,
    'UnitsOfMeasure': 0,
    'DrawingSegments': 36,
    'ExportInputGeometry': False,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})

# --- Step 5: Load Output Layer ---
output_layer = result['OUTPUT']
QgsProject.instance().addMapLayer(output_layer)

symbol = QgsFillSymbol.createSimple({
    'color': 'white',
    'outline_color': 'black',
    'outline_width': '0.5'
})
output_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
output_layer.triggerRepaint()

# --- Step 6: Load RSRP Layer ---
rsrp_layer = QgsVectorLayer(RSRP_TAB, "RSRP", "ogr")
if not rsrp_layer.isValid():
    raise RuntimeError("❌ Failed to load RSRP layer.")
QgsProject.instance().addMapLayer(rsrp_layer)

# --- Step 7: Map Rendering ---
map_settings = QgsMapSettings()
map_settings.setLayers([output_layer, rsrp_layer])
map_settings.setBackgroundColor(QColor("white"))
map_settings.setOutputSize(QSize(1200, 900))
map_settings.setExtent(rsrp_layer.extent())

base_width, base_height, padding = 1200, 900,25
map_image = QImage(base_width, base_height, QImage.Format_ARGB32_Premultiplied)
map_image.fill(Qt.white)

painter = QPainter(map_image)
job = QgsMapRendererCustomPainterJob(map_settings, painter)
job.start()
job.waitForFinished()
painter.end()

# --- Step 8: Load Scraped Image ---
scraped_image = QImage(SCRAPED_IMAGE_PATH)
if scraped_image.isNull():
    raise RuntimeError("❌ Failed to load scraped image.")

# --- Step 9: Prepare Final Canvas ---
extra_width = scraped_image.width()
final_width = base_width + 2 * padding + extra_width
final_height = max(base_height + 2 * padding, scraped_image.height())

final_image = QImage(final_width, final_height, QImage.Format_ARGB32_Premultiplied)
final_image.fill(Qt.white)

# --- Step 10: Composite Images & Draw Grid ---
painter = QPainter(final_image)
painter.drawImage(padding, padding, map_image)

# Draw square grid
cell_size = final_width / 60  # 60 columns
rows = int(final_height / cell_size)
pen = QPen(Qt.gray, 1)
painter.setPen(pen)

for i in range(61):
    x = int(i * cell_size)
    painter.drawLine(x, 0, x, final_height)

for j in range(rows + 1):
    y = int(j * cell_size)
    painter.drawLine(0, y, final_width, y)

painter.drawImage(base_width + 2 * padding, 0, scraped_image)
painter.end()


# ✅ Define output filename and output folder
image_name = "test.png"
output_dir = "C:/Users/anu07/Documents/test2/Output"
output_path = os.path.join(output_dir, image_name)

# ✅ Create folder if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ✅ Save the image
final_image.save(output_path)
print(f"✅ Final image saved at: {output_path}")




# --- Step 12: Cleanup ---
qgs.exitQgis()



# C:\Program Files\QGIS 3.28.14\apps\qgis-ltr\python;C:\Program Files\QGIS 3.28.14\apps\qgis-ltr\python\plugins;C:\Program Files\QGIS 3.28.14\apps\Qt5\plugins;C:\Program Files\QGIS 3.28.14\apps\gdal\share\gdal;