import trimesh
import numpy as np
import math

# Function to slice the STL model
def slice_model(stl_path, layer_height):
    mesh = trimesh.load_mesh(stl_path)
    min_z, max_z = mesh.bounds[:, 2]  # Get model height
    model_height = max_z - min_z
    print(f"Model height: {model_height:.2f} mm")

    layers = np.arange(min_z, max_z, layer_height)  # Generate slice heights
    sliced_layers = []

    for z in layers:
        section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if section and len(section.entities) > 0:  # Ensure valid slices
            sliced_layers.append(section)

    print(f"Generated {len(sliced_layers)} layers")
    return sliced_layers

# Function to generate grid infill pattern within bounds
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
    
    extrusion_multiplier = 0.1  # Adjust for correct extrusion

    for i, layer in enumerate(layers):
        path_2d, _ = layer.to_2D()  # Extract 2D slice
        gcode.append(f"; Layer {i}")
        gcode.append(f"G1 Z{i * layer_height:.2f} F500")  # Move Z up for each layer

        if not path_2d.entities:
            print(f"Warning: No valid paths for Layer {i}")
            continue
        
        # Generate solid bottom layer
        if i == 0:
            gcode.append("; Solid bottom layer")
        
        # Generate perimeter walls
        gcode.append("; Perimeter walls")
        for entity in path_2d.entities:  # Extract perimeter paths
            points = path_2d.vertices[entity.points]

            if len(points) < 4:
                print(f"Skipping incomplete path at Layer {i}")
                continue

            for x, y in points:
                extrusion_amount = extrusion_width * extrusion_multiplier
                gcode.append(f"G1 X{x:.2f} Y{y:.2f} F{speed} E{extrusion_amount:.2f}")
            
            # Close the loop
            start_x, start_y = points[0]
            gcode.append(f"G1 X{start_x:.2f} Y{start_y:.2f} F{speed} E{extrusion_amount:.2f}")
        
        # Generate grid infill within bounds
        if i > 0 and i < len(layers) - 1:
            gcode.append("; Grid infill pattern")
            bounds = path_2d.bounds
            infill_lines = generate_grid(bounds, infill_spacing)

            for (x1, y1), (x2, y2) in infill_lines:
                if bounds[0][0] <= x1 <= bounds[1][0] and bounds[0][1] <= y1 <= bounds[1][1]:
                    gcode.append(f"G1 X{x1:.2f} Y{y1:.2f} F{speed}")  # Move to start of infill line
                    gcode.append(f"G1 X{x2:.2f} Y{y2:.2f} F{speed} E{extrusion_width * extrusion_multiplier:.2f}")
        
        # Generate solid top layer
        if i == len(layers) - 1:
            gcode.append("; Solid top layer")
    
    gcode.extend([
        "M104 S0 ; Turn off extruder heater",
        "M140 S0 ; Turn off bed heater",
        "M107 ; Turn off fan",
        "G28 X0 Y0 ; Home X and Y",
        "M84 ; Disable motors"
    ])
    
    return "\n".join(gcode)

# User inputs
stl_file_path = "sample1.stl"  # Replace with actual STL file path
layer_height = float(input("Enter layer height (mm, recommended: 0.5-1mm): "))
printing_speed = float(input("Enter printing speed (mm/min): "))
extrusion_width = float(input("Enter extrusion width: "))
infill_spacing = float(input("Enter infill spacing (mm): "))

# Load STL and process
layers = slice_model(stl_file_path, layer_height)
if not layers:
    print("Error: No valid slices were found! Check STL file and layer height.")
    exit()

# Generate and save G-code
gcode = generate_gcode(layers, printing_speed, extrusion_width, layer_height, infill_spacing)
gcode_file_path = "output.gcode"

with open(gcode_file_path, "w") as f:
    f.write(gcode)

print(f"G-code saved to {gcode_file_path}")

# Display G-code preview (first 10 lines)
print("\nG-code Preview:")
print("\n".join(gcode.split("\n")[:10]))
