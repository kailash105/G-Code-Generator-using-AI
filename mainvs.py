import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def parse_gcode(file_path):
    """Extract X, Y, Z coordinates from G-code."""
    x_coords, y_coords, z_coords = [], [], []
    current_x, current_y, current_z = None, None, 0.0  # Track last known positions

    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('G1'):
                parts = line.split()
                x, y, z = None, None, None
                
                for part in parts:
                    if part.startswith('X'):
                        x = float(part[1:])
                    elif part.startswith('Y'):
                        y = float(part[1:])
                    elif part.startswith('Z'):
                        z = float(part[1:])
                
                # Use last known values if missing
                current_x = x if x is not None else current_x
                current_y = y if y is not None else current_y
                current_z = z if z is not None else current_z

                if current_x is not None and current_y is not None:
                    x_coords.append(current_x)
                    y_coords.append(current_y)
                    z_coords.append(current_z)

    return x_coords, y_coords, z_coords

def plot_gcode_3d(file_path):
    """Plot the G-code toolpath in 3D."""
    x_coords, y_coords, z_coords = parse_gcode(file_path)
    
    if not x_coords or not y_coords:
        print("❌ No valid X/Y movement detected in G-code! Check input file.")
        return
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.plot(x_coords, y_coords, z_coords, marker='o', linestyle='-', markersize=2, color='blue')  # ✅ Finer visualization

    ax.set_xlabel('X-axis (mm)')
    ax.set_ylabel('Y-axis (mm)')
    ax.set_zlabel('Z-axis (mm)')
    ax.set_title('3D G-code Toolpath Visualization')

    plt.show()

# Example usage
gcode_file = "output.gcode"
plot_gcode_3d(gcode_file)
