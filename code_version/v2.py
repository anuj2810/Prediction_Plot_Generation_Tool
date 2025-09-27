import os
import sys
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsMapSettings,
    QgsMapRendererCustomPainterJob, QgsProperty, QgsFillSymbol, QgsSingleSymbolRenderer
)
from qgis.analysis import QgsNativeAlgorithms
from PyQt5.QtGui import QImage, QPainter, QColor, QPen
from PyQt5.QtCore import QSize, Qt

# --- QGIS Setup ---
QGIS_PREFIX = os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.28.14\apps\qgis-ltr")
if not os.path.exists(QGIS_PREFIX):
    raise EnvironmentError(f"❌ QGIS path invalid: {QGIS_PREFIX}")

qgs = QgsApplication([], False)
QgsApplication.setPrefixPath(QGIS_PREFIX, True)
qgs.initQgis()

import processing
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# --- Load shapetools Plugin ---
plugin_path = os.path.expanduser(r"C:\Users\anu07\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins")
if plugin_path not in sys.path:
    sys.path.append(plugin_path)

try:
    from shapetools import shapeToolsProcessing
    provider = shapeToolsProcessing.ShapeToolsProvider()
    QgsApplication.processingRegistry().addProvider(provider)
except Exception as e:
    sys.exit(f"❌ Failed to register shapetools provider: {e}")

# ✅ Constant input CSV
CSV_INPUT = r"delimitedtext://file:///C:/Users/anu07/Desktop/pv2/cell_file/final_cell.csv?delimiter=,&xField=Longitude&yField=Latitude&crs=EPSG:4326"
output_dir = "C:/Users/anu07/Documents/test2/Output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ✅ List of .tab files and legend images (modify as needed)
rsrp_tab_files = [
    r"C:/Users/anu07/Documents/test2/site_data/700/T4RJ28UDUPRP9UUD119/T4RJ28UDUPRP9UUD119_RSRP.tab",
    r"C:/Users/anu07/Documents/test2/site_data/700/T4RJ28UDUPRP9UUD119/T4RJ28UDUPRP9UUD119_RSRQ.tab",
    r"C:/Users/anu07/Documents/test2/site_data/700/T4RJ28UDUPRP9UUD119/T4RJ28UDUPRP9UUD119_SINR.tab",
    r"C:/Users/anu07/Documents/test2/site_data/700/T4RJ28UDUPRP9UUD119/T4RJ28UDUPRP9UUD119_Throughput.tab",
]

scraped_images = [
    r"C:/Users/anu07/Documents/test2/legend/RSRP.png",
    r"C:/Users/anu07/Documents/test2/legend/RSRQ.png",
    r"C:/Users/anu07/Documents/test2/legend/SINR.png",
    r"C:/Users/anu07/Documents/test2/legend/DL.png"
]

# ✅ Loop for 4 images
for i in range(4):
    print(f"\n🔄 Generating map {i+1}...")

    # --- Step 1: Run shapetools:createpie ---
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

    output_layer = result['OUTPUT']
    QgsProject.instance().addMapLayer(output_layer)

    symbol = QgsFillSymbol.createSimple({
        'color': 'white',
        'outline_color': 'black',
        'outline_width': '0.5'
    })
    output_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    output_layer.triggerRepaint()

    # --- Step 2: Load RSRP Layer ---
    rsrp_tab_path = rsrp_tab_files[i]
    rsrp_layer = QgsVectorLayer(rsrp_tab_path, "RSRP", "ogr")
    if not rsrp_layer.isValid():
        raise RuntimeError(f"❌ Failed to load RSRP layer for map {i+1}")
    QgsProject.instance().addMapLayer(rsrp_layer)

    # --- Step 3: Map Rendering ---
    map_settings = QgsMapSettings()
    map_settings.setLayers([output_layer, rsrp_layer])
    map_settings.setBackgroundColor(QColor("white"))
    map_settings.setOutputSize(QSize(1200, 900))
    map_settings.setExtent(rsrp_layer.extent())

    base_width, base_height, padding = 1200, 900, 25
    map_image = QImage(base_width, base_height, QImage.Format_ARGB32_Premultiplied)
    map_image.fill(Qt.white)

    painter = QPainter(map_image)
    job = QgsMapRendererCustomPainterJob(map_settings, painter)
    job.start()
    job.waitForFinished()
    painter.end()

    # --- Step 4: Load Legend Image ---
    scraped_image_path = scraped_images[i]
    scraped_image = QImage(scraped_image_path)
    if scraped_image.isNull():
        raise RuntimeError(f"❌ Failed to load scraped image for map {i+1}")

    # --- Step 5: Combine Images ---
    extra_width = scraped_image.width()
    final_width = base_width + 2 * padding + extra_width
    final_height = max(base_height + 2 * padding, scraped_image.height())

    final_image = QImage(final_width, final_height, QImage.Format_ARGB32_Premultiplied)
    final_image.fill(Qt.white)

    painter = QPainter(final_image)
    painter.drawImage(padding, padding, map_image)

    # Draw grid
    cell_size = final_width / 60
    rows = int(final_height / cell_size)
    pen = QPen(Qt.gray, 1)
    painter.setPen(pen)
    for j in range(61):
        x = int(j * cell_size)
        painter.drawLine(x, 0, x, final_height)
    for k in range(rows + 1):
        y = int(k * cell_size)
        painter.drawLine(0, y, final_width, y)

    painter.drawImage(base_width + (2 * padding - 8), 0, scraped_image)
    painter.end()

    # ✅ Output names for the 4 maps
    image_names = ["rsrp.png", "rsrq.png", "sinr.png", "dl_throughput.png"]

    # --- Step 6: Save Image ---
    image_name = image_names[i]
    output_path = os.path.join(output_dir, image_name)
    final_image.save(output_path)
    print(f"✅ Saved: {output_path}")

    # --- Step 7: Cleanup layers before next loop ---
    QgsProject.instance().removeAllMapLayers()

# --- Final Cleanup ---
qgs.exitQgis()
print("\n✅ All 4 maps generated successfully.")
