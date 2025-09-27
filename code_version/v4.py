import os
import re
import sys
import pandas as pd
from pathlib import Path
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsMapSettings,
    QgsMapRendererCustomPainterJob, QgsProperty, QgsFillSymbol, QgsSingleSymbolRenderer
)
from qgis.analysis import QgsNativeAlgorithms
from PyQt5.QtGui import QImage, QPainter, QColor, QPen
from PyQt5.QtCore import QSize, Qt
import processing
from processing.core.Processing import Processing

# === QGIS Setup ===
QGIS_PREFIX = os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.28.14\apps\qgis-ltr")
if not os.path.exists(QGIS_PREFIX):
    raise EnvironmentError(f"❌ QGIS path invalid: {QGIS_PREFIX}")
qgs = QgsApplication([], False)
QgsApplication.setPrefixPath(QGIS_PREFIX, True)
qgs.initQgis()

Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# === Load shapetools plugin ===
plugin_path = os.path.expanduser(r"C:\Users\anu07\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins")
if plugin_path not in sys.path:
    sys.path.append(plugin_path)
try:
    from shapetools import shapeToolsProcessing
    provider = shapeToolsProcessing.ShapeToolsProvider()
    QgsApplication.processingRegistry().addProvider(provider)
except Exception as e:
    sys.exit(f"❌ Failed to register shapetools provider: {e}")


csv_path = r"C:/Users/anu07/Documents/test2/cell_file/final_cell.csv"
site_data_root = r"C:/Users/anu07/Documents/test2/site_data"
output_dir = r"C:/Users/anu07/Documents/test2/Output"
csv_input = f"delimitedtext://file:///{csv_path.replace(os.sep, '/')}?delimiter=,&xField=Longitude&yField=Latitude&crs=EPSG:4326"

legend_images = [
    r"C:/Users/anu07/Documents/test2/legend/RSRP.png",
    r"C:/Users/anu07/Documents/test2/legend/RSRQ.png",
    r"C:/Users/anu07/Documents/test2/legend/SINR.png",
    r"C:/Users/anu07/Documents/test2/legend/DL.png"
]

image_names_by_band = {
    "700": ["RSRP_700.png", "RSRQ_700.png", "SINR_700.png", "DL_700.png"],
    "850": ["RSRP_850.png", "RSRQ_850.png", "SINR_850.png", "DL_850.png"]
}

def clean_site_id(site_id):
    # Remove all non-alphanumeric characters
    return re.sub(r'[^A-Za-z0-9]', '', site_id)

def get_user_site_ids():
    t = int(input("🟢 No. of Site IDs to process: ").strip())

    site_ids = []
    for i in range(t):
        raw_sid = input(f"🔹 Enter Site ID {i+1}: ").strip()
        site_ids.append(raw_sid)

    return site_ids

# === Function to get .tab files from site ID ===
def get_tab_files(site_id, csv_path, site_data_root):
    df = pd.read_csv(csv_path)
    df['SITE ID'] = df['SITE ID'].astype(str).str.strip().str.upper()
    site_id = site_id.strip().upper()

    row = df[df['SITE ID'] == site_id]
    if row.empty:
        print(f"❌ SITE ID '{site_id}' not found in CSV.")
        return {}, None, None

    site_id_700 = row.iloc[0].get('Site ID_L700')
    site_id_850 = row.iloc[0].get('Site ID_L850')

    tabs_by_band = {}
    for band, folder_name in [('700', site_id_700), ('850', site_id_850)]:
        if not folder_name or pd.isna(folder_name):
            print(f"⚠️ No folder name found for {band} MHz band.")
            continue

        tab_folder = Path(site_data_root) / band / folder_name
        if not tab_folder.exists():
            print(f"❌ Folder does not exist for {band} MHz: {tab_folder}")
            continue

        band_tabs = list(tab_folder.glob("*.tab"))
        if not band_tabs:
            print(f"⚠️ No .tab files found in {tab_folder}")
        else:
            # print(f"✅ Found {len(band_tabs)} .tab files in {band} MHz: {tab_folder}")
            tabs_by_band[band] = band_tabs

    return tabs_by_band, site_id_700, site_id_850


def generate_maps(tab_files, legend_images, image_names, csv_input, output_dir, band_site_id, site_id, csv_path):

    print("📌 AZIMUTH values preview from CSV:")
    try:
        print(pd.read_csv(csv_path)['AZIMUTH'].head())
    except Exception as e:
        print(f"❌ Error reading AZIMUTH from CSV: {e}")
        
    for i in range(len(tab_files)):
        # print(f"\n🔄 Generating map {i+1}...")
        
        # Step 1: Create pie shape from CSV
        result = processing.run("shapetools:createpie", {
            'INPUT': csv_input,
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
        symbol = QgsFillSymbol.createSimple({'color': 'white', 'outline_color': 'black', 'outline_width': '0.5'})
        output_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        output_layer.triggerRepaint()

        # Step 2: Load RSRP/RSRQ/SINR/... tab layer
        tab_path = str(tab_files[i])
        layer = QgsVectorLayer(tab_path, f"Layer {i+1}", "ogr")
        if not layer.isValid():
            print(f"❌ Failed to load layer: {tab_path}")
            QgsProject.instance().removeAllMapLayers()
            continue
        QgsProject.instance().addMapLayer(layer)

        # Step 3: Map rendering setup
        map_settings = QgsMapSettings()
        map_settings.setLayers([output_layer, layer])
        map_settings.setBackgroundColor(QColor("white"))
        map_settings.setOutputSize(QSize(1200, 900))
        map_settings.setExtent(layer.extent())

        base_width, base_height, padding = 1200, 900, 25
        map_image = QImage(base_width, base_height, QImage.Format_ARGB32_Premultiplied)
        map_image.fill(Qt.white)

        painter = QPainter(map_image)
        job = QgsMapRendererCustomPainterJob(map_settings, painter)
        job.start()
        job.waitForFinished()
        painter.end()

        # Step 4: Load scraped image (legend)
        legend_image_path = legend_images[i]
        scraped_image = QImage(legend_image_path)
        if scraped_image.isNull():
            print(f"❌ Failed to load legend image: {legend_image_path}")
            QgsProject.instance().removeAllMapLayers()
            continue

        # Step 5: Final composition
        extra_width = scraped_image.width()
        final_width = base_width + 2 * padding + extra_width
        final_height = max(base_height + 2 * padding, scraped_image.height())

        final_image = QImage(final_width, final_height, QImage.Format_ARGB32_Premultiplied)
        final_image.fill(Qt.white)

        painter = QPainter(final_image)
        painter.drawImage(padding, padding, map_image)

        # ✅ Add site ID text using actual Site ID from CSV per band
        site_label = f"{band_site_id}"
        text_x = padding + 650
        text_y = padding + 375

        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("black"))
        painter.drawText(text_x, text_y, site_label)

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

        # Draw legend image slightly shifted left
        legend_x_offset = base_width + padding + 5
        # painter.drawImage(legend_x_offset, padding, scraped_image)
        legend_y_offset = padding - 18  # Shift upward slightly
        legend_y_offset = max(0, legend_y_offset)  # Prevent going negative
        painter.drawImage(legend_x_offset, legend_y_offset, scraped_image)
        painter.end()

        # Step 6: Save
        image_name = image_names[i]
        # ✅ Create site-specific subfolder
        site_output_dir = os.path.join(output_dir, clean_site_id( site_id ) )
        if not os.path.exists(site_output_dir):
            os.makedirs(site_output_dir)

        # ✅ Final output path inside site folder
        output_path = os.path.join(site_output_dir, image_name)
        
        final_image.save(output_path)
        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":



    # ✅ Get site IDs from user
    site_ids = get_user_site_ids()

    for site_id in site_ids:
        print(f"\n========== 🔁 Processing Site ID: {site_id} =============\n")
        
        tab_files_by_band, site_id_700, site_id_850 = get_tab_files(site_id, csv_path, site_data_root)

        for band in ["700", "850"]:
            band_site_id = site_id_700 if band == "700" else site_id_850

            if band in tab_files_by_band and len(tab_files_by_band[band]) >= 4:
                print(f"📍 Generating maps for {band_site_id} ({band} MHz)")
                generate_maps(
                    tab_files=tab_files_by_band[band][:4],
                    legend_images=legend_images,
                    image_names=image_names_by_band[band],
                    csv_input=csv_input,
                    output_dir=output_dir,
                    band_site_id=band_site_id,
                    site_id=site_id,
                    csv_path = csv_path
                )
            else:
                print(f"⚠️ Skipping {band} MHz for {site_id}: Not enough .tab files (required: 4)")

    print(f"\n====== ✅ Plot Genration for site id: {site_id} is DONE ✅ ======\n")

    qgs.exitQgis()
