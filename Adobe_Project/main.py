import numpy as np
import matplotlib.pyplot as plt
import svgwrite
import cairosvg


# Read CSV file
def read_csv(csv_path):
    np_path_XYs = np.genfromtxt(csv_path, delimiter=',')
    print(f"CSV data:\n{np_path_XYs}")  # Log the entire loaded CSV data

    if np_path_XYs.ndim == 1:  # If only one line, reshape to 2D array
        np_path_XYs = np_path_XYs.reshape(1, -1)

    path_XYs = []
    for i in np.unique(np_path_XYs[:, 0]):
        npXYs = np_path_XYs[np_path_XYs[:, 0] == i][:, 1:]
        XYs = []
        for j in np.unique(npXYs[:, 0]):
            XY = npXYs[npXYs[:, 0] == j][:, 1:]
            if XY.shape[0] > 1:  # Ensure we only take segments with more than one point
                XYs.append(XY)
        if XYs:
            path_XYs.append(XYs)

    print(f"Extracted paths:\n{path_XYs}")
    return path_XYs


# Group segments by orientation (horizontal or vertical)
def group_by_orientation(paths_XYs):
    horizontal_lines = []
    vertical_lines = []

    for path in paths_XYs:
        for segment in path:
            if segment.shape[1] == 2:  # Ensure segment is 2D
                x_diff = np.abs(segment[-1, 0] - segment[0, 0])
                y_diff = np.abs(segment[-1, 1] - segment[0, 1])
                if x_diff > y_diff:  # Horizontal line
                    horizontal_lines.append(segment)
                else:  # Vertical line
                    vertical_lines.append(segment)

    print(f"Grouped into {len(horizontal_lines)} horizontal lines and {len(vertical_lines)} vertical lines.")
    return horizontal_lines, vertical_lines


# Complete the lines by connecting endpoints
def complete_lines(segments):
    completed_segments = []

    for segment in segments:
        if len(completed_segments) == 0:
            completed_segments.append(segment)
        else:
            last_segment = completed_segments[-1]
            if np.allclose(last_segment[-1], segment[0]):
                # Connect the last segment's end to the current segment's start
                completed_segments[-1] = np.vstack((last_segment, segment[1:]))
            else:
                completed_segments.append(segment)

    print(f"Completed {len(completed_segments)} segments.")
    return completed_segments


# Plot shapes (for visualization)
def plot(paths_XYs, colours):
    fig, ax = plt.subplots(tight_layout=True, figsize=(8, 8))
    color_index = 0
    for i, XYs in enumerate(paths_XYs):
        c = colours[color_index % len(colours)]
        for XY in XYs:
            if XY.ndim == 2 and XY.shape[1] == 2:  # Ensure XY is 2-dimensional
                ax.plot(XY[:, 0], XY[:, 1], c=c, linewidth=2)
                print(f"Plotting line with color {c} from {XY[0]} to {XY[-1]}")
        color_index += 1
    ax.set_aspect('equal')
    plt.show()


# Convert polylines to SVG and rasterize
def polylines2svg(horizontal_lines, vertical_lines, svg_path, colours):
    W, H = 0, 0
    paths_XYs = horizontal_lines + vertical_lines

    for path_XYs in paths_XYs:
        for XY in path_XYs:
            if XY.ndim == 2:  # Ensure XY is 2-dimensional before processing
                W, H = max(W, np.max(XY[:, 0])), max(H, np.max(XY[:, 1]))

    padding = 0.1
    W, H = int(W + padding * W), int(H + padding * H)

    # Avoid division by zero
    if W == 0 or H == 0:
        W = H = 1024

    dwg = svgwrite.Drawing(svg_path, profile='tiny', shape_rendering='crispEdges')

    # Assign colors evenly among the lines
    all_lines = horizontal_lines + vertical_lines
    num_lines = len(all_lines)
    color_map = {}

    for i, path in enumerate(all_lines):
        assigned_color = colours[i % len(colours)]
        color_map[tuple(map(tuple, path))] = assigned_color

    # Draw horizontal lines
    for path in horizontal_lines:
        if path.ndim == 2:  # Ensure path is 2-dimensional
            path_data = [("M", (path[0, 0], path[0, 1]))]
            for XY in path[1:]:
                path_data.append(("L", (XY[0], XY[1])))
            print(f"Adding horizontal path: {path_data} with color {color_map[tuple(map(tuple, path))]}")
            dwg.add(dwg.path(d=path_data, fill='none', stroke=color_map[tuple(map(tuple, path))], stroke_width=2))

    # Draw vertical lines
    for path in vertical_lines:
        if path.ndim == 2:  # Ensure path is 2-dimensional
            path_data = [("M", (path[0, 0], path[0, 1]))]
            for XY in path[1:]:
                path_data.append(("L", (XY[0], XY[1])))
            print(f"Adding vertical path: {path_data} with color {color_map[tuple(map(tuple, path))]}")
            dwg.add(dwg.path(d=path_data, fill='none', stroke=color_map[tuple(map(tuple, path))], stroke_width=2))

    dwg.save()
    png_path = svg_path.replace('.svg', '.png')

    # Avoid division by zero
    if W > 0 and H > 0:
        fact = max(1, 1024 // min(H, W))
    else:
        fact = 1

    cairosvg.svg2png(url=svg_path, write_to=png_path, parent_width=W, parent_height=H, output_width=fact * W,
                     output_height=fact * H, background_color='white')
    print(f"Saved SVG and PNG to {svg_path} and {png_path}")
    return


# Example Usage
csv_path = 'frag2.csv'  # Replace with your actual CSV path
svg_output_path = 'output.svg'
colours = ['red', 'blue', 'green', 'yellow', 'purple']

# Reading the CSV file
paths_XYs = read_csv(csv_path)

# Check if any data is read
if not paths_XYs:
    print("No paths found. Please check the CSV content.")
else:
    # Group lines by orientation
    horizontal_lines, vertical_lines = group_by_orientation(paths_XYs)

    # Complete lines
    completed_horizontal_lines = complete_lines(horizontal_lines)
    completed_vertical_lines = complete_lines(vertical_lines)

    # Plotting results (optional)
    plot(completed_horizontal_lines + completed_vertical_lines, colours)

    # Saving results to SVG and PNG
    polylines2svg(completed_horizontal_lines, completed_vertical_lines, svg_output_path, colours)
