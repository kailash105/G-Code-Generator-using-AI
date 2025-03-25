import trimesh
import numpy as np

# Function to load and repair STL
def load_and_fix_stl(stl_path):
    mesh = trimesh.load_mesh(stl_path)
    
    # Fix common STL issues
    if not mesh.is_watertight:
        print("⚠ Warning: Model is not watertight! Attempting repair...")
        mesh.repair.fix_mesh()
    
    # Auto-snap model to Z=0
    min_z = mesh.bounds[0, 2]
    if min_z != 0:
        mesh.apply_translation([0, 0, -min_z])
        print("✅ Model snapped to Z=0")

    # Auto-scale small models
    min_x, min_y, min_z = mesh.bounds[0]
    max_x, max_y, max_z = mesh.bounds[1]
    model_height = max_z - min_z
    if model_height < 1.0:
        scale_factor = 10
        mesh.apply_scale(scale_factor)
        print(f"✅ Model scaled up by {scale_factor}x")

    return mesh

# Function to slice STL into layers
def slice_model(mesh, layer_height):
    min_z, max_z = mesh.bounds[:, 2]  
    layers = np.arange(min_z, max_z, layer_height)  # Slice at fixed intervals
    sliced_layers = []

    for z in layers:
        section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if section and hasattr(section, 'entities') and len(section.entities) > 0:
            sliced_layers.append(section)
        else:
            print(f"⚠ Warning: No valid cross-section at Z={z:.2f}")

    print(f"✅ Successfully generated {len(sliced_layers)} layers")
    return sliced_layers

# Function to generate grid infill pattern
def generate_grid(bounds, spacing):
    min_x, min_y = bounds[0]
    max_x, max_y = bounds[1]
    
    lines = []
    x = min_x
    while x <= max_x:
        lines.append([(x, min_y), (x, max_y)])
        x += spacing
    
    y = min_y
    while y <= max_y:
        lines.append([(min_x, y), (max_x, y)])
        y += spacing
    
    return lines

# Function to generate G-code
def generate_gcode(layers, speed, extrusion_width, layer_height, infill_spacing):
    gcode = [
        "G21 ; Set units to millimeters",
        "G90 ; Absolute positioning",
        "G28 ; Home all axes",
        "M104 S0 ; Turn off extruder heater",
        "M140 S0 ; Turn off bed heater",
        "M107 ; Turn off fan",
        "G28 X0 Y0 ; Home X and Y"
    ]
    
    extrusion_multiplier = 0.1  

    for i, layer in enumerate(layers):
        path_2d, _ = layer.to_2D()  
        gcode.append(f"; Layer {i}")
        gcode.append(f"G1 Z{i * layer_height:.2f} F500")  

        if not hasattr(path_2d, 'entities') or len(path_2d.entities) == 0:
            print(f"⚠ Warning: No valid paths for Layer {i}")
            continue

        gcode.append("; Perimeter walls")
        for entity in path_2d.entities:  
            points = path_2d.vertices[entity.points]

            if len(points) < 4:
                print(f"⚠ Skipping incomplete path at Layer {i}")
                continue

            for x, y in points:
                extrusion_amount = extrusion_width * extrusion_multiplier
                gcode.append(f"G1 X{x:.2f} Y{y:.2f} F{speed} E{extrusion_amount:.2f}")

            start_x, start_y = points[0]
            gcode.append(f"G1 X{start_x:.2f} Y{start_y:.2f} F{speed} E{extrusion_amount:.2f}")

        if i > 0 and i < len(layers) - 1:
            gcode.append("; Grid infill pattern")
            bounds = path_2d.bounds
            infill_lines = generate_grid(bounds, infill_spacing)

            for (x1, y1), (x2, y2) in infill_lines:
                if bounds[0][0] <= x1 <= bounds[1][0] and bounds[0][1] <= y1 <= bounds[1][1]:
                    gcode.append(f"G1 X{x1:.2f} Y{y1:.2f} F{speed}")  
                    gcode.append(f"G1 X{x2:.2f} Y{y2:.2f} F{speed} E{extrusion_width * extrusion_multiplier:.2f}")

    gcode.extend([
        "M104 S0 ; Turn off extruder heater",
        "M140 S0 ; Turn off bed heater",
        "M107 ; Turn off fan",
        "G28 X0 Y0 ; Home X and Y",
        "M84 ; Disable motors"
    ])
    
    return "\n".join(gcode)

# User inputs
stl_file_path = "sample1.stl"  
layer_height = float(input("Enter layer height (mm, recommended: 0.5-1mm): "))
printing_speed = float(input("Enter printing speed (mm/min): "))
extrusion_width = float(input("Enter extrusion width: "))
infill_spacing = float(input("Enter infill spacing (mm): "))

# Load and fix STL
mesh = load_and_fix_stl(stl_file_path)

# Slice model
layers = slice_model(mesh, layer_height)
if not layers:
    print("❌ Error: No valid slices were found! Check STL file and layer height.")
    exit()

# Generate and save G-code
gcode = generate_gcode(layers, printing_speed, extrusion_width, layer_height, infill_spacing)
gcode_file_path = "output.gcode"

with open(gcode_file_path, "w") as f:
    f.write(gcode)

print(f"✅ G-code saved to {gcode_file_path}")

# Display G-code preview (first 10 lines)
print("\n🔹 G-code Preview:")
print("\n".join(gcode.split("\n")[:10]))
