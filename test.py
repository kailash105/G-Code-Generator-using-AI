import argparse
import logging
import subprocess
import os
import time

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_slic3r(stl_file, layer_height, extrusion_width, perimeters, output_path):
    slic3r_path = r"C:\\PROGRA~1\\Slic3r\\slic3r.exe"  # Using 8.3 short path format
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Basic Slic3r command (only required parameters)
    slic3r_cmd = [
        slic3r_path,
        "--layer-height", str(layer_height),
        "--extrusion-width", str(extrusion_width),
        "--perimeters", str(perimeters),
        "--output", output_path,
        stl_file
    ]
    
    logging.info(f"🔹 Running Slic3r: {' '.join(slic3r_cmd)}")
    try:
        process = subprocess.Popen(slic3r_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if stdout:
            logging.info(stdout.strip())
        if stderr:
            logging.warning(stderr.strip())

        if process.returncode == 0:
            logging.info("✅ Slic3r completed successfully.")
        else:
            logging.error("❌ Slic3r encountered an error.")
            exit(1)
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Slic3r failed with error: {e.stderr}")
        exit(1)
    
    # Verify if output file was created
    if not os.path.exists(output_path):
        logging.error("❌ G-code file was not generated. Check Slic3r logs for errors.")
        exit(1)

def wait_for_file_unlock(file_path, max_retries=5, wait_time=2):
    """ Waits for file to be unlocked before trying to read it. """
    for i in range(max_retries):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.readlines()
        except PermissionError:
            logging.warning(f"⚠️ File is locked! Retrying in {wait_time} seconds... ({i+1}/{max_retries})")
            time.sleep(wait_time)
    logging.error("❌ Permission denied: Unable to read the G-code file after multiple attempts.")
    return None

def main():
    setup_logging()
    
    stl_file = input("Enter the STL file name (including extension): ").strip()
    if not os.path.exists(stl_file):
        logging.error("❌ STL file not found! Please provide a valid file.")
        exit(1)
    
    output_path = r"C:\Users\sathv\Desktop\output.gcode"  # Avoids OneDrive locking issues
    
    try:
        layer_height = float(input("Enter layer height (mm, recommended: 0.5-1mm): "))
        extrusion_width = float(input("Enter extrusion width: "))
        perimeters = int(input("Enter number of perimeter walls (default: 1): ") or 1)
    except ValueError:
        logging.error("❌ Invalid input! Please enter numerical values where required.")
        exit(1)
    
    run_slic3r(stl_file, layer_height, extrusion_width, perimeters, output_path)
    
    if os.path.exists(output_path):
        logging.info(f"✅ G-code saved to {output_path}")
        print(f"\n🔹 G-code Preview ({output_path}):")
        
        gcode_lines = wait_for_file_unlock(output_path)
        if gcode_lines:
            print("\n".join(gcode_lines[:10]))  # Show first 10 lines
    else:
        logging.error("❌ Error: G-code file not found after execution.")

if __name__ == "__main__":
    main()
