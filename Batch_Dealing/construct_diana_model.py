import math

def construct_diana_model(parameters):
    """
    Build a DIANA slab-column finite element model from input parameters.
    
    Parameters:
        parameters: list containing [length, width, effective_thickness, column_size,
                   reinforcement_ratio, yield_strength, compressive_strength,
                   corrosion_rate, corrosion_area_ratio, max_aggregate_size]
    """
    # Extract input parameters
    length = parameters[0]
    width = parameters[1]
    effective_thickness = parameters[2]
    column_size = parameters[3]

    # Steel ratio is given as percentage, convert to decimal for calculations
    reinforcement_ratio = parameters[4] / 100
    yield_strength = parameters[5]
    compressive_strength = parameters[6]
    corrosion_rate = parameters[7]
    corrosion_area_ratio = parameters[8]
    max_aggregate_size = parameters[9]

    # Calculate total slab thickness (effective thickness + cover + reinforcement diameter)
    thickness = effective_thickness + 20 + 13

    # Set global unit system to millimeters
    setUnit("Length", "mm")

    # Create geometric shape sets for organizing model components
    addSet("SHAPESET", "Main_Slab")
    addSet("SHAPESET", "Loading_Plate")
    addSet("SHAPESET", "Corroded_Concrete")
    addSet("SHAPESET", "Center_Column")
    addSet("SHAPESET", "Rebar_Top")
    addSet("SHAPESET", "Rebar_Bottom")

    # Create main concrete slab (rectangular block)
    createBlock("main_slab", [0, 0, 0], [length, width, thickness])
    moveToShapeSet(["main_slab"], "Main_Slab")

    # Calculate loading plate positions scaled from original 2200 mm test layout
    # Positions are based on the test specimen dimensions
    primaryUpperBoundary = length * (1 - 750 / 2200)
    primaryLowerBoundary = length * 750 / 2200
    secondaryUpperBoundary = width * (1 - 200 / 2200)
    secondaryLowerBoundary = width * 200 / 2200

    # Define the 8 loading plate positions (4 corner columns + 4 edge columns)
    # Naming: U=Upper, D=Down, L=Left, R=Right (based on 4-point + 8-point loading configuration)
    loading_plates = [
        ("col_U1", primaryLowerBoundary, secondaryUpperBoundary),
        ("col_U2", primaryUpperBoundary, secondaryUpperBoundary),
        ("col_D1", primaryLowerBoundary, secondaryLowerBoundary),
        ("col_D2", primaryUpperBoundary, secondaryLowerBoundary),
        ("col_L1", secondaryLowerBoundary, primaryLowerBoundary),
        ("col_L2", secondaryLowerBoundary, primaryUpperBoundary),
        ("col_R1", secondaryUpperBoundary, primaryLowerBoundary),
        ("col_R2", secondaryUpperBoundary, primaryUpperBoundary),
    ]

    # Loading plate dimensions and height
    loading_plate_top = 20  # Thickness of loading plate
    loading_plate_top_z = thickness  # Top surface position of loading plate
    loading_plate_size = 100  # Side length of square loading plate

    # Calculate center column position (centered on slab)
    center_column_x_start = (length - column_size) // 2
    center_column_y_start = (width - column_size) // 2

    # Create support boundary conditions
    # Support 1: Point supports on loading plates (fixed in X-Y directions)
    addSet("GEOMETRYSUPPORTSET", "Support 1")
    createPointSupport("Support 1", "Support 1")
    setParameter("GEOMETRYSUPPORT", "Support 1", "AXES", [1, 2])
    setParameter("GEOMETRYSUPPORT", "Support 1", "TRANSL", [0, 0, 1])
    setParameter("GEOMETRYSUPPORT", "Support 1", "ROTATI", [0, 0, 0])

    # Support 2: Surface support at bottom of center column (fully fixed)
    addSet("GEOMETRYSUPPORTSET", "Support 2")
    createSurfaceSupport("Support 2", "Support 2")
    setParameter("GEOMETRYSUPPORT", "Support 2", "AXES", [1, 2])
    setParameter("GEOMETRYSUPPORT", "Support 2", "TRANSL", [1, 1, 1])
    setParameter("GEOMETRYSUPPORT", "Support 2", "ROTATI", [0, 0, 0])

    # Create imposed displacement load
    # Applied as displacement-controlled loading on loading plates
    addSet("GEOMETRYLOADSET", "Load 1")
    createPointLoad("Load 1", "Load 1")
    setParameter("GEOMETRYLOAD", "Load 1", "LODTYP", "DEFORM")
    setParameter("GEOMETRYLOAD", "Load 1", "DEFORM/SUPP", "Support 1")
    setParameter("GEOMETRYLOAD", "Load 1", "DEFORM/TR/VALUE", -1)  # Downward displacement
    setParameter("GEOMETRYLOAD", "Load 1", "DEFORM/TR/DIRECT", 3)  # Z-direction

    # Create central support column (below the slab)
    createBlock("col_center", [center_column_x_start, center_column_y_start, -column_size], 
                [column_size, column_size, column_size])
    moveToShapeSet(["col_center"], "Center_Column")
    face_points = faces("col_center")
    # Find bottom face and attach support
    bottom_face_point = min(face_points, key=lambda p: p[2])
    attach("GEOMETRYSUPPORT", "Support 2", "col_center", [bottom_face_point])

    # Create 8 loading plates at the specified positions
    for col_name, x_center, y_center in loading_plates:
        x_start = x_center - loading_plate_size // 2
        y_start = y_center - loading_plate_size // 2
        # Create square loading plate with specified thickness
        createBlock(col_name, [x_start, y_start, loading_plate_top_z], 
                    [loading_plate_size, loading_plate_size, loading_plate_top])
        moveToShapeSet([col_name], "Loading_Plate")
        
        # Create load point at top of each loading plate for displacement application
        load_point_z = loading_plate_top_z + loading_plate_top
        point_name = f"load_point_{col_name}"
        createPointBody(point_name, [x_center, y_center, load_point_z])
        face_points = faces(col_name)
        top_face_point = max(face_points, key=lambda p: p[2])
        # Project load point to top face
        projection("SHAPEFACE", col_name, [top_face_point], [point_name], [0, 0, -1], True)
        removeShape(point_name)

        # Attach supports and loads to loading plates
        support_coord = [x_center, y_center, thickness + 20]
        attach("GEOMETRYSUPPORT", "Support 1", col_name, [support_coord])
        attach("GEOMETRYLOAD", "Load 1", col_name, [support_coord])

    # Create corroded concrete pit (if corrosion is present)
    # Pit is located at center of slab with depth proportional to corrosion damage
    if corrosion_rate != 0 and corrosion_area_ratio != 0:
        center_x = length / 2
        center_y = width / 2
        # Calculate pit size based on area ratio
        pit_size = (corrosion_area_ratio * length * width) ** 0.5
        pit_depth = 20
        pit_x_start = center_x - pit_size / 2
        pit_y_start = center_y - pit_size / 2
        pit_z_start = thickness - pit_depth
        createBlock("center_pit", [pit_x_start, pit_y_start, pit_z_start], [pit_size, pit_size, pit_depth])
        moveToShapeSet(["center_pit"], "Corroded_Concrete")
        # Subtract pit from main slab to create corroded region
        subtract("main_slab", ["center_pit"], keepTools=True, merge=False)

    # Calculate reinforcement bar spacing based on reinforcement ratio and concrete section
    # Top reinforcement (larger diameter = 13mm)
    rebar_spacing_top = (math.pi * 6.5 * 6.5) / (reinforcement_ratio * effective_thickness)
    num_rebar_top = int((width - 2 * 20) // rebar_spacing_top)
    edge_offset_top = (width - (num_rebar_top * rebar_spacing_top)) / 2
    extension_top = edge_offset_top - 20
    
    # Bottom reinforcement (smaller diameter = 10mm, different ratio)
    reinforcement_ratio_bottom = 0.28 / 100
    rebar_spacing_bottom = (math.pi * 5.0 * 5.0) / (reinforcement_ratio_bottom * (effective_thickness + 3))
    num_rebar_bottom = int((width - 2 * 20) // rebar_spacing_bottom)
    edge_offset_bottom = (width - (num_rebar_bottom * rebar_spacing_bottom)) / 2
    extension_bottom = edge_offset_bottom - 20
    
    # Reinforcement positioning (height from bottom)
    top_z = thickness - 13 - 20
    bottom_z = 30
    center_x = length / 2
    center_y = width / 2

    # Calculate X-positions for top reinforcement bars (bidirectional from center)
    x_positions_top = []
    x_left = edge_offset_top
    while x_left < center_x:
        x_positions_top.append(x_left)
        x_left += rebar_spacing_top
    x_right = length - edge_offset_top
    while x_right > center_x:
        x_positions_top.append(x_right)
        x_right -= rebar_spacing_top
    # Add center bar if even number of bars
    if num_rebar_top % 2 == 0 and center_x not in x_positions_top:
        x_positions_top.append(center_x)
    x_positions_top.sort()

    # Calculate Y-positions for top reinforcement bars (bidirectional from center)
    y_positions_top = []
    y_bottom = edge_offset_top
    while y_bottom < center_y:
        y_positions_top.append(y_bottom)
        y_bottom += rebar_spacing_top
    y_top = width - edge_offset_top
    while y_top > center_y:
        y_positions_top.append(y_top)
        y_top -= rebar_spacing_top
    # Add center bar if even number of bars
    if num_rebar_top % 2 == 0 and center_y not in y_positions_top:
        y_positions_top.append(center_y)
    y_positions_top.sort()

    # Calculate extension lengths for top reinforcement bars
    y_start_ext_top = edge_offset_top - extension_top
    y_end_ext_top = (width - edge_offset_top) + extension_top
    x_start_ext_top = edge_offset_top - extension_top
    x_end_ext_top = (length - edge_offset_top) + extension_top

    # Calculate X-positions for bottom reinforcement bars
    x_positions_bottom = []
    x_left = edge_offset_bottom
    while x_left < center_x:
        x_positions_bottom.append(x_left)
        x_left += rebar_spacing_bottom
    x_right = length - edge_offset_bottom
    while x_right > center_x:
        x_positions_bottom.append(x_right)
        x_right -= rebar_spacing_bottom
    if num_rebar_bottom % 2 == 0 and center_x not in x_positions_bottom:
        x_positions_bottom.append(center_x)
    x_positions_bottom.sort()

    # Calculate Y-positions for bottom reinforcement bars
    y_positions_bottom = []
    y_bottom = edge_offset_bottom
    while y_bottom < center_y:
        y_positions_bottom.append(y_bottom)
        y_bottom += rebar_spacing_bottom
    y_top = width - edge_offset_bottom
    while y_top > center_y:
        y_positions_bottom.append(y_top)
        y_top -= rebar_spacing_bottom
    if num_rebar_bottom % 2 == 0 and center_y not in y_positions_bottom:
        y_positions_bottom.append(center_y)
    y_positions_bottom.sort()

    # Calculate extension lengths for bottom reinforcement bars
    y_start_ext_bottom = edge_offset_bottom - extension_bottom
    y_end_ext_bottom = (width - edge_offset_bottom) + extension_bottom
    x_start_ext_bottom = edge_offset_bottom - extension_bottom
    x_end_ext_bottom = (length - edge_offset_bottom) + extension_bottom

    # Initialize lists to track reinforcement bar names
    top_rebars_name = []
    bottom_rebars_name = []
    corroded_rebars_name = []

    # Create top layer reinforcement bars (13mm diameter)
    # X-direction bars (perpendicular to primary loading direction)
    for x in x_positions_top:
        line_name = f"top_x_{x}"
        createLine(line_name, [x, y_start_ext_top, top_z], [x, y_end_ext_top, top_z])
        convertToReinforcement(line_name)
        moveToShapeSet([line_name], "Rebar_Top")
        top_rebars_name.append(line_name)
    
    # Y-direction bars (parallel to primary loading direction)
    for y in y_positions_top:
        line_name = f"top_y_{y}"
        createLine(line_name, [x_start_ext_top, y, top_z], [x_end_ext_top, y, top_z])
        convertToReinforcement(line_name)
        moveToShapeSet([line_name], "Rebar_Top")
        top_rebars_name.append(line_name)

    # Create bottom layer reinforcement bars (10mm diameter)
    # X-direction bars
    for x in x_positions_bottom:
        line_name = f"bottom_x_{x}"
        createLine(line_name, [x, y_start_ext_bottom, bottom_z], [x, y_end_ext_bottom, bottom_z])
        convertToReinforcement(line_name)
        moveToShapeSet([line_name], "Rebar_Bottom")
        bottom_rebars_name.append(line_name)
    
    # Y-direction bars
    for y in y_positions_bottom:
        line_name = f"bottom_y_{y}"
        createLine(line_name, [x_start_ext_bottom, y, bottom_z], [x_end_ext_bottom, y, bottom_z])
        convertToReinforcement(line_name)
        moveToShapeSet([line_name], "Rebar_Bottom")
        bottom_rebars_name.append(line_name)
    
    # Handle corroded reinforcement bars (split at corrosion pit location)
    if corrosion_rate != 0 and corrosion_area_ratio != 0:
        addSet("SHAPESET", "Rebar_Top_Corrosion")
        # Pit boundaries in X and Y directions
        rx1, rx2 = pit_x_start, pit_x_start + pit_size
        ry1, ry2 = pit_y_start, pit_y_start + pit_size

        def split(old_name, fixed, is_horiz, seg_start, seg_end, cut1, cut2):
            """
            Split a reinforcement bar into uncorroded and corroded segments.
            
            Parameters:
                old_name: Original bar name
                fixed: Fixed coordinate (x or y value)
                is_horiz: True if horizontal bar (y fixed), False if vertical (x fixed)
                seg_start: Start of bar segment
                seg_end: End of bar segment
                cut1, cut2: Start and end of corrosion region
            """
            if cut1 >= cut2:
                return
            # Helper function to create point coordinates based on bar orientation
            pts = lambda p1, p2: ([p1, fixed, top_z], [p2, fixed, top_z]) if is_horiz else ([fixed, p1, top_z], [fixed, p2, top_z])
            
            # Create uncorroded segment before pit
            if seg_start < cut1:
                createLine(f"{old_name}_a", *pts(seg_start, cut1))
                convertToReinforcement(f"{old_name}_a")
                moveToShapeSet([f"{old_name}_a"], "Rebar_Top")
                top_rebars_name.append(f"{old_name}_a")
            
            # Create corroded segment in pit region
            createLine(f"{old_name}_corr", *pts(cut1, cut2))
            moveToShapeSet([f"{old_name}_corr"], "Rebar_Top_Corrosion")
            convertToReinforcement(f"{old_name}_corr")
            corroded_rebars_name.append(f"{old_name}_corr")
            
            # Create uncorroded segment after pit
            if cut2 < seg_end:
                createLine(f"{old_name}_b", *pts(cut2, seg_end))
                convertToReinforcement(f"{old_name}_b")
                moveToShapeSet([f"{old_name}_b"], "Rebar_Top")
                top_rebars_name.append(f"{old_name}_b")
            
            # Remove original bar and its reference from list
            removeShape(old_name)
            if old_name in top_rebars_name:
                top_rebars_name.remove(old_name)

        # Add symmetry  
        # Split horizontal bars (Y-fixed) intersecting corrosion pit
        for y in y_positions_top:
            if ry1 <= y <= ry2:
                split(f"top_y_{y}", y, True, x_start_ext_top, x_end_ext_top, rx1, rx2)
        
        # Split vertical bars (X-fixed) intersecting corrosion pit
        for x in x_positions_top:
            if rx1 <= x <= rx2:
                split(f"top_x_{x}", x, False, y_start_ext_top, y_end_ext_top, ry1, ry2)

    # Define material properties based on concrete strength and aggregate size
    # Calculate fracture energy of concrete (Gf0) based on maximum aggregate size
    if max_aggregate_size <= 8:
        Gf0 = 25
    elif max_aggregate_size <= 16:
        Gf0 = 25 + (30 - 25) / (16 - 8) * (max_aggregate_size - 8)
    elif max_aggregate_size <= 32:
        Gf0 = 30 + (58 - 30) / (32 - 16) * (max_aggregate_size - 16)
    else:
        Gf0 = 58
    
    # Calculate fracture energy using empirical formula
    fracture_energy = 1.3 * Gf0 * (compressive_strength / 10) ** 0.7 * 0.001

    # Define normal concrete material properties
    addMaterial("Concrete", "CONCR", "TSCR", [])
    setParameter("MATERIAL", "Concrete", "LINEAR/ELASTI/YOUNG", 34000)  # Young's modulus (MPa)
    setParameter("MATERIAL", "Concrete", "LINEAR/ELASTI/POISON", 0.2)  # Poisson's ratio
    setParameter("MATERIAL", "Concrete", "MODTYP/TOTCRK", "ROTATE")  # Rotating crack model
    setParameter("MATERIAL", "Concrete", "TENSIL/TENCRV", "HORDYK")  # Tension softening curve
    # Tensile strength: 0.3 * sqrt(fc)
    setParameter("MATERIAL", "Concrete", "TENSIL/TENSTR", 0.3 * (compressive_strength) ** (2/3))
    setParameter("MATERIAL", "Concrete", "TENSIL/GF1", fracture_energy)  # Fracture energy
    setParameter("MATERIAL", "Concrete", "TENSIL/POISRE/POIRED", "DAMAGE")  # Poisson effect reduction
    setParameter("MATERIAL", "Concrete", "COMPRS/COMCRV", "THOREN")  # Compression hardening curve
    setParameter("MATERIAL", "Concrete", "COMPRS/COMSTR", compressive_strength)  # Compressive strength
    setParameter("MATERIAL", "Concrete", "COMPRS/NTHORE", 2)  # Thorenfeldt exponent
    setParameter("MATERIAL", "Concrete", "COMPRS/KTHORE", 4.5)  # Thorenfeldt K parameter
    setParameter("MATERIAL", "Concrete", "COMPRS/RESCST", 0)  # Residual compressive strength
    setParameter("MATERIAL", "Concrete", "COMPRS/REDUCT/REDCRV", "VC1993")  # Strength reduction curve
    setParameter("MATERIAL", "Concrete", "COMPRS/REDUCT/REDMIN", 0)  # Minimum reduction value
    setParameter("MATERIAL", "Concrete", "COMPRS/CONFIN/CNFCRV", "VECCHI")  # Confinement model

    # Define corroded concrete material properties (if corrosion exists)
    if corrosion_rate != 0 and corrosion_area_ratio != 0:
        # Calculate lateral strain due to corrosion expansion
        delta_w = math.pi * 13 * (1 - (1 - corrosion_rate) ** 0.5)
        epsilon_l = delta_w / rebar_spacing_top
        # Reduce concrete strength due to lateral tensile stress from corrosion products
        corroded_comp_strength = compressive_strength / (1 + 0.1 * (epsilon_l / 0.002))
        corroded_fracture_energy = 1.3 * Gf0 * (corroded_comp_strength / 10) ** 0.7 * 0.001
        
        addMaterial("Corroded_Concrete", "CONCR", "TSCR", [])
        setParameter("MATERIAL", "Corroded_Concrete", "LINEAR/ELASTI/YOUNG", 34000)
        setParameter("MATERIAL", "Corroded_Concrete", "LINEAR/ELASTI/POISON", 0.2)
        setParameter("MATERIAL", "Corroded_Concrete", "MODTYP/TOTCRK", "ROTATE")
        setParameter("MATERIAL", "Corroded_Concrete", "TENSIL/TENCRV", "HORDYK")
        # Reduce tensile strength proportionally to compressive strength reduction
        setParameter("MATERIAL", "Corroded_Concrete", "TENSIL/TENSTR", 
                    0.3 * (compressive_strength) ** (2/3) / compressive_strength * corroded_comp_strength)
        setParameter("MATERIAL", "Corroded_Concrete", "TENSIL/GF1", corroded_fracture_energy)
        setParameter("MATERIAL", "Corroded_Concrete", "TENSIL/POISRE/POIRED", "DAMAGE")
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/COMCRV", "THOREN")
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/COMSTR", corroded_comp_strength)
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/NTHORE", 2)
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/KTHORE", 4.5)
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/RESCST", 0)
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/REDUCT/REDCRV", "VC1993")
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/REDUCT/REDMIN", 0)
        setParameter("MATERIAL", "Corroded_Concrete", "COMPRS/CONFIN/CNFCRV", "VECCHI")
        
    # Define column (support) material - linear elastic
    addMaterial("Column", "CONCR", "LEI", [])
    setParameter("MATERIAL", "Column", "LINEAR/ELASTI/YOUNG", 350)
    setParameter("MATERIAL", "Column", "LINEAR/ELASTI/POISON", 0.2)
    # Define reinforcement steel properties
    addMaterial("Rebar", "REINFO", "VMISES", [])
    setParameter("MATERIAL", "Rebar", "LINEAR/ELASTI/YOUNG", 210000)  # Steel Young's modulus
    setParameter("MATERIAL", "Rebar", "PLASTI/YLDTYP", "KAPSIG")  # Yield criterion
    setParameter("MATERIAL", "Rebar", "PLASTI/HARDI2/KAPSIG", [])
    # Define hardening curve: [strain, stress] pairs for bilinear relationship
    setParameter("MATERIAL", "Rebar", "PLASTI/HARDI2/KAPSIG", 
                [0, yield_strength, 0.002, yield_strength, 0.1, yield_strength * 1.27, 0.2, 80])

    # Define corroded reinforcement properties
    addMaterial("Corroded_Rebar", "REINFO", "VMISES", [])
    setParameter("MATERIAL", "Corroded_Rebar", "LINEAR/ELASTI/YOUNG", 210000)
    setParameter("MATERIAL", "Corroded_Rebar", "PLASTI/YLDTYP", "KAPSIG")
    
    # Different hardening curves based on corrosion severity
    if corrosion_rate * 100 < 10:
        # Low corrosion: use linear reduction formula
        setParameter("MATERIAL", "Corroded_Rebar", "PLASTI/HARDI2/KAPSIG", 
                    [0, yield_strength * (1 - 0.0198 * corrosion_rate * 100), 
                     0.002, yield_strength * (1 - 0.0198 * corrosion_rate * 100), 
                     0.1 * (1 - 0.05 * corrosion_rate * 100), 
                     yield_strength * 1.27 * (1 - 0.0198 * corrosion_rate * 100), 
                     0.2 * (1 - 0.05 * corrosion_rate * 100), 80])
    else:
        # High corrosion: use simplified bilinear model
        setParameter("MATERIAL", "Corroded_Rebar", "PLASTI/HARDI2/KAPSIG", 
                    [0, yield_strength * (1 - 0.0198 * corrosion_rate * 100), 
                     0.03, yield_strength * (1 - 0.0198 * corrosion_rate * 100) * 0.1])

    # Define steel plate material (for loading plates)
    addMaterial("Steel", "MCSTEL", "ISOTRO", [])
    setParameter("MATERIAL", "Steel", "LINEAR/ELASTI/YOUNG", 210000)  # Young's modulus
    setParameter("MATERIAL", "Steel", "LINEAR/ELASTI/POISON", 0.3)  # Poisson's ratio

    # Assign materials to geometric elements
    # Central column (concrete)
    setCurrentShapeSet("Center_Column")
    setElementClassType("SHAPE", ["col_center"], "STRSOL")
    assignMaterial("Column", "SHAPE", ["col_center"])
    
    # Corroded concrete pit (if present)
    if corrosion_rate != 0 and corrosion_area_ratio != 0:
        setCurrentShapeSet("Corroded_Concrete")
        setElementClassType("SHAPE", ["center_pit"], "STRSOL")
        assignMaterial("Corroded_Concrete", "SHAPE", ["center_pit"])
    
    # Loading plates (steel)
    setCurrentShapeSet("Loading_Plate")
    setElementClassType("SHAPE", ["col_D1", "col_D2", "col_R1", "col_R2", "col_U1", "col_U2", "col_L2", "col_L1"], "STRSOL")
    assignMaterial("Steel", "SHAPE", ["col_D1", "col_D2", "col_R1", "col_R2", "col_U1", "col_U2", "col_L2", "col_L1"])
    
    # Main slab (normal concrete)
    setCurrentShapeSet("Main_Slab")
    setElementClassType("SHAPE", ["main_slab"], "STRSOL")
    assignMaterial("Concrete", "SHAPE", ["main_slab"])
    # Define reinforcement geometry (embedment properties)
    # Bottom reinforcement: 10mm diameter bars
    addGeometry("rebar_bottom", "RELINE", "REBAR", [])
    setParameter("GEOMET", "rebar_bottom", "REIEMB/RDITYP", "RDIAME")
    setParameter("GEOMET", "rebar_bottom", "REIEMB/DIAMET", 10)
    
    # Top reinforcement: 13mm diameter bars
    addGeometry("rebar_top", "RELINE", "REBAR", [])
    setParameter("GEOMET", "rebar_top", "REIEMB/RDITYP", "RDIAME")
    setParameter("GEOMET", "rebar_top", "REIEMB/DIAMET", 13)
    
    # Assign materials and geometry to bottom reinforcement bars
    if bottom_rebars_name:
        setCurrentShapeSet("Rebar_Bottom")
        assignMaterial("Rebar", "SHAPE", bottom_rebars_name)
        assignGeometry("rebar_bottom", "SHAPE", bottom_rebars_name)
        resetElementData("SHAPE", bottom_rebars_name)

    # Assign materials and geometry to top reinforcement bars
    if top_rebars_name:
        setCurrentShapeSet("Rebar_Top")
        assignMaterial("Rebar", "SHAPE", top_rebars_name)
        assignGeometry("rebar_top", "SHAPE", top_rebars_name)
        resetElementData("SHAPE", top_rebars_name)

    # Assign materials and geometry to corroded top reinforcement bars
    if corroded_rebars_name:
        setCurrentShapeSet("Rebar_Top_Corrosion")
        assignMaterial("Corroded_Rebar", "SHAPE", corroded_rebars_name)
        assignGeometry("rebar_top", "SHAPE", corroded_rebars_name) 
        resetElementData("SHAPE", corroded_rebars_name)
    
    # Create finite element mesh
    # List of all shapes requiring mesh generation
    required_mesh_shape = ["main_slab", "col_U1", "col_U2", "col_L2", "col_L1", "col_D1", "col_D2", "col_R1", "col_R2", "col_center"]
    
    # Add corroded pit to mesh if corrosion exists
    if corrosion_rate != 0 and corrosion_area_ratio != 0:
        required_mesh_shape.append("center_pit")
    
    # Set element size (50 mm) and mesher type (hexahedral/quadrilateral)
    setElementSize(required_mesh_shape, 50, -1, True)
    setMesherType(required_mesh_shape, "HEXQUAD")
    
    # Generate the finite element mesh
    generateMesh([])
