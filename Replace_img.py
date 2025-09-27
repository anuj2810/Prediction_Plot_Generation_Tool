
# === Replacement Control Flags ===
REPLACE_STANDARD_IMAGES = False     # Set to False to skip standard images
REPLACE_CURRENT_IMAGE = True      # Set to True only when replacing 'current'


import os
import re
import pandas as pd
from pathlib import Path
from docx import Document

# === Constants ==========================================================
DEFAULT_OUTPUT_DIR = r"E:/Part Time job/Report Gen Soft/OUTPUTS/new_cl3"

# ===============================================================
# Root directory for input DOCX files always check this before running this automation 
INPUT_DOCX_ROOT = r"Input/new_cl3" 

# === Helper Functions ===
def clean_site_id(site_id):
    return re.sub(r'[^A-Za-z0-9]', '', site_id)

# def replace_selected_images(docx_path, new_images_map, output_path):
#     doc = Document(docx_path)
#     rels = doc.part._rels
#     image_rels = [rel for rel in rels.values() if "image" in rel.target_ref]
#     image_rels_sorted = sorted(image_rels, key=lambda r: r.rId)

#     replacement_keys = ["rsrp", "rsrq", "sinr", "throughput"]

#     for i, rel in enumerate(image_rels_sorted):
#         if 0 <= i <= 3:
#             new_key = replacement_keys[i - 4]
#             new_image_path = new_images_map.get(new_key)
#             if new_image_path and os.path.exists(new_image_path):
#                 with open(new_image_path, 'rb') as f:
#                     rel._target._blob = f.read()
#                 print(f"✅ Replaced {new_key} image")
#             else:
#                 print(f"❌ Missing image for '{new_key}'")

#     doc.save(output_path)
#     print(f"📄 Saved DOCX to: {output_path}")


def replace_selected_images(docx_path, new_images_map, output_path):
    

    doc = Document(docx_path)
    rels = doc.part._rels
    image_rels = [rel for rel in rels.values() if "image" in rel.target_ref]
    image_rels_sorted = sorted(image_rels, key=lambda r: r.rId)
    


    replacements = []

    if REPLACE_STANDARD_IMAGES:
        replacements += [
            (0, "rsrp"),
            (1, "rsrq"),
            (2, "sinr"),
            (3, "throughput"),
        ]

    # Uncomment the following lines if you want to replace the 'LAYOUT' image FOR THE NORMAL SITE
    # if REPLACE_CURRENT_IMAGE:
    #     replacements += [
    #         (11, "current"),
    #     ]

    # Uncomment the following lines if you want to replace the 'LAYOUT' image FOR THE CLUSTER SITE
    if REPLACE_CURRENT_IMAGE:
        replacements += [
            (0, "current"),
        ]

    for idx, key in replacements:
        if 0 <= idx < len(image_rels_sorted):
            rel = image_rels_sorted[idx]
            new_image_path = new_images_map.get(key)
            if new_image_path and os.path.exists(new_image_path):
                with open(new_image_path, 'rb') as f:
                    rel._target._blob = f.read()
                print(f"✅ Replaced {key.upper()} image")
            else:
                print(f"❌ Missing image for '{key}'")
        else:
            print(f"⚠️ Invalid index {idx} for key '{key}' in document.")

    doc.save(output_path)
    print(f"📄 Saved DOCX to: {output_path}")



def get_site_code_from_csv(csv_path, input_site_id, band):
    df = pd.read_csv(csv_path, dtype=str)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    filtered = df[df['SITE ID'].str.contains(input_site_id, case=False, na=False)]

    if filtered.empty:
        return None

    if band == "700":
        return filtered["Site ID_L700"].iloc[0]
    elif band == "850":
        return filtered["Site ID_L850"].iloc[0]
    return None

def get_user_site_ids():
    t = int(input("🟢 No. of Site IDs to process: ").strip())
    site_ids = []
    for i in range(t):
        raw_sid = input(f"🔹 Enter Site ID {i+1}: ").strip()
        site_ids.append(raw_sid)
    return site_ids

# === Main Flow ===
def main():
    site_ids = get_user_site_ids()
    # csv_path = input("📄 Enter CSV file path (e.g., input.csv): ").strip()
    csv_path = r"cell_file/final_cell.csv"

    for site_id in site_ids:
        cleaned_id = clean_site_id(site_id)
        print(f"\n🛠 Processing Site ID: {cleaned_id}")

        for band in ["700", "850"]:
            output_name_from_csv = get_site_code_from_csv(csv_path, site_id, band)
            if not output_name_from_csv:
                print(f"❌ Site ID '{cleaned_id}' with band '{band}' not found in CSV")
                continue

            # === Paths ===
            image_input_folder = os.path.join("E:/Part Time job/Report Gen Soft/Predictio_Automation/Prediction_plot/44 SITE SCFT", cleaned_id)
            image_input_folder1 = os.path.join("E:/Part Time job/Report Gen Soft/Predictio_Automation/Layout/cluster-3", cleaned_id)
            
            new_images_map = {
                "rsrp": os.path.join(image_input_folder, f"RSRP_{band}.png"),
                "rsrq": os.path.join(image_input_folder, f"RSRQ_{band}.png"),
                "sinr": os.path.join(image_input_folder, f"SINR_{band}.png"),
                "throughput": os.path.join(image_input_folder, f"DL_{band}.png"),
                "current": os.path.join(image_input_folder1, f"layout.png")
            }

            # new_images_map = {
            #     "rsrp": os.path.join(image_input_folder, f"RSRP_final.png"),
            #     "rsrq": os.path.join(image_input_folder, f"RSRQ_final.png"),
            #     "sinr": os.path.join(image_input_folder, f"SINR_final.png"),
            #     "throughput": os.path.join(image_input_folder, f"THRPT_final.png"),
            #     "current": os.path.join(image_input_folder1, f"layout.png")
            # }

            docx_path = os.path.join(INPUT_DOCX_ROOT, cleaned_id, f"{band}.docx")
            output_folder = os.path.join(DEFAULT_OUTPUT_DIR, cleaned_id)
            os.makedirs(output_folder, exist_ok=True)
            output_docx_path = os.path.join(output_folder, f"{output_name_from_csv}_AT_REPORT.docx")
            # output_docx_path = os.path.join(output_folder, f"{output_name_from_csv}_2500_report.docx")

            if os.path.exists(docx_path):
                replace_selected_images(docx_path, new_images_map, output_docx_path)
            else:
                print(f"❌ DOCX file not found: {docx_path}")

    print("\n✅ All replacements completed successfully!")

if __name__ == "__main__":
    main()
