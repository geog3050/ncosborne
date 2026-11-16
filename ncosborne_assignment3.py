def hawkid():
    return ["Nina Osborne", "ncosborne"]

import csv #Reads CSV
from pathlib import Path #Can split file paths
import arcpy #Python library

######################### Problem 1 (20 points)
#Here, we will take one input dataset, copy it into a gdb, and project it. 
#This will not alter the priginal file.
#Input_fc is the shapefile that you want to prep.
#Output_geodatabase is where it will be written into. This can be created if missing or reused if present
#out_coordinate_system is an EPSG code for a prj system in meters. These can be found easily online
#There is also the option of using polygons. If you do this, fill out the join_table, join_field, and value_field
#You input the CSV, the ID field shared by the CSV and the polygons, and the column you want them to share
#You put in all three, or none, because otherwise your join will fail.


def prepare_data(input_fc, output_geodatabase, out_coordinate_system,
                 join_table=None, join_field=None, value_field=None):

    #About 90% of the following code is for handling errors. The executable code for functions is short and sweet
    #We first want to anticipate and solve errors before starting. This means this code is replicable and easy to independently fix

    #One note: arcpy allows the user to write to the memory.
    #Not everything needs to be stored in your gdb. For steps that are repeated or just not necessary to save, putting them in the memory is efficient.
    #https://pro.arcgis.com/en/pro-app/3.5/help/analysis/geoprocessing/basics/the-in-memory-workspace.htm

    ##general outline and flow
    #1. input exists with known coordinate system
    #2. coordinate system is projected and in meters
    #3. if doing a join, check the CSV before writing
    #4. make or euse the gdb, and do not overwrite outputs
    #5. project the input into the gdb, or copy it in if you don't need to reproject
    #6. if you are joining, load the csv values into table in memory and then join to projected copy
    #yielding . . . path of new feature clas for user to access
    
     #This first section will be solving errors that may emerge if you do not align your inputs.
    #This includes duplicate files, nonexistent files, and fixing the types of inputs
    #In many cases, your files as downloaded may not be ready-to-go
    #This code will produce error messages if an error is reached, so the user realizes their files must be changed.
    try: 
        input_fc = Path(input_fc) #turns the input into a path
        gdb = Path(output_geodatabase) #turns the gdb into a path
        
        #check the input and target coordinate systems
        if not arcpy.Exists(str(input_fc)):
            raise FileNotFoundError(f"Input {input_fc} not found.") #stops if the file is missing
        in_sr = arcpy.Describe(str(input_fc)).spatialReference #read the file's coordintae system
        if in_sr.name == "Unknown": #Unknown means no prj file or no defined system
            raise ValueError(f"{input_fc.name} needs a coordinate system")
        out_sr = arcpy.SpatialReference(int(out_coordinate_system)) #This specifies the target system 
        if out_sr.type != "Projected" or out_sr.linearUnitName.lower() not in ("meter", "metre"): #Must be both prjected and in meters
            raise ValueError(f"{out_coordinate_system} is not projected and/or in meters.")
        if gdb.suffix.lower() != ".gdb": #Specifies output must be a file gdb
            raise ValueError(f"Your geodatabase does not end in .gdb. Please correct this.")

        #Check of the CSV
        values = {} #Will hold the ID value if the CSV is used. If there is no join, it will be empty
        if any([join_table, join_field, value_field]):
            if not all([join_table, join_field, value_field]): #All three are required. Otherwise logically you lack the files or the info . . .
                raise ValueError("You need to supply join_table, join_field, and value_field all together.")
            if arcpy.Describe(str(input_fc)).shapeType != "Polygon": #joins only make sense for polygons. here, census polygons
                raise ValueError("Your CSV join has to be a polygon")
            id_fields = arcpy.ListFields(str(input_fc), join_field)
            if not id_fields: #empty list means the field is not there
                raise ValueError(f"Field {join_field} not found inside {input_fc.name}")
            if arcpy.ListFields(str(input_fc), value_field): #the value field shouldn't already exist
                raise ValueError(f"{input_fc.name} already has a field named {value_field}") #avoids duplication errors. this adds a file like appending _1 at the end, which complicated re-runs of the code to troubleshoot. it is easier to just prevent duplications.

            join_table = Path(join_table) #Makes CSV into a path
            if not join_table.exists():
                raise FileNotFoundError(f"{join_table} CSV not found")


            #CSV: The GEOID can be loaded in without all of the leading zeroes.
            #This needs to be fixed into the code to keep it as a string, otherwise it can be read numerically.
            #This is important when reading workbook-type files, as Excel is notorious for changing the format of numbers.
            id_is_text = id_fields[0].type == "String" #Match CSV ID type to the polygon ID type
            with open(join_table, newline="", encoding="utf-8-sig") as file: 
                reader = csv.DictReader(file) #The row is a dictionary which has a column name as key
                if join_field not in reader.fieldnames or value_field not in reader.fieldnames: #Both columsn msut exist
                    raise ValueError(f"Your CSV needs to include {join_field} and {value_field}")
                for row in reader:
                    key = row[join_field] if id_is_text else int(row[join_field]) #text ID stays as text. Can also have integer ID as int
                    value = float(row[value_field]) #pop must be a number
                    if key in values:
                        raise ValueError(f"Duplicate {join_field} in CSV: {key}") #a duyplicate key makes the join ambigious
                    if value < 0: #population can't be negative. if tis negative for the census, that means they marked it as missing data
                        raise ValueError(f"Your value {value_field} for {key} is negative")
                    values[key] = value #stores the ID and its value
                with arcpy.da.SearchCursor(str(input_fc), [join_field]) as rows: #read every polygon ID
                    missing = [row[0] for row in rows if row[0] not in values] #If ID in the polygon but not CSV
                if missing: #flag, because the estimate of pop will be wrong if not every polygon has a population
                    raise ValueError(f"{len(missing)} features have no match in the CSV.")

                #Create or reuse the geodatbase
                if not arcpy.Exists(str(gdb)): #create if not there
                    arcpy.management.CreateFileGDB(str(gdb.parent), gdb.name) #parent folder and name
                out_fc = gdb / arcpy.ValidateTableName(input_fc.stem, str(gdb)) #base name. so if it had .shp, it is stripped
                if arcpy.Exists(str(out_fc)): #do not overwrite if already exists in the gdb
                    raise ValueError(f"{out_fc.name} already exists in {gdb.name}")

                #Project into the gdb, if already in the target coordinate system
                if in_sr.factoryCode == out_sr.factoryCode: #if same EPSG code, you have nothing to project
                    arcpy.management.CopyFeatures(str(input_fc), str(out_fc)) #so just copy it into the gdb
                else: #the system is different so it needs projected
                    transforms = arcpy.ListTransformations(in_sr, out_sr) #can and will be empty if not needed
                    arcpy.management.Project(str(input_fc), str(out_fc), out_sr, transforms[0] if transforms else "") #write projected copy

                    #Joiin CSV value through typed table
                if values: #only runs if join is requested and previously passes checks from code above
                    table = "memory\\csv_values" #temporary table in the memory
                    arcpy.management.CreateTable("memory", "csv_values")
                    arcpy.management.AddField(table, join_field, "TEXT" if id_is_text else "LONG") #ID field needs matching type
                    arcpy.management.AddField(table, value_field, "DOUBLE") #numeric field
                    with arcpy.da.InsertCursor(table, [join_field, value_field]) as rows: #add the new rows
                        for row in values.items():
                            rows.insertRow(row) #write a row
                        arcpy.management.JoinField(str(out_fc), join_field, table, join_field, [value_field]) #attach the value
                    return str(out_fc) #give user the path of the new feature class
    except Exception as error:
        raise RuntimeError("Prepare_data failed") from error #any other errors
    finally:
        arcpy.management.Delete("memory") #clear temporary memory workspace. otherwise it bogs down your computer performance

        



########################### Problem 2 (40 points)
        #Here, we will estimate how many people live in the study zone.
        #This uses aereal interpolation. There is a buffer around a study zone. Some census polygons are only partly within this buffer
        #So, the function figures out the proportion of the blcok group's area that is inside the zone.
        #That proportion is given its population
        #So if a block group with 1k people is 30% inside the study zone, the zone is counted to have 300 people.

        #source_polygons are the census polygons that have pop counts
        #population_field is the field with the counts. COUNTS  . . not rates or medians. so check the census readme.
        #study_zone is the study area. 
        #output_fc is where to save to

        ##general outline and flow:
        #1. inputs exist, are polygons, are prj in meters, and in same coord system.
        #2. pop field exists, as numeric, and has no missing values
        #3. the output gdb exists and the name is available
        #4. make the study area into one shape, incase it is multiple areas. buffers will be dissolved. note the weird buffer issue from this version of arc
        #5. source polygons are copied into the memory. the full area is stored as src_km2. 
        #6. the copy is intersected with the dissolved zone. then you keep only the parts inside the zone. and all its attributes
        #7. each part is saved as part_km2
        #8. calculate pop as (pop * (part_km2 / src_km2)
        #9. add all of the pop values 
        #yielding . . . overlap pieces with the src_km2, part_km2, and est_pop.
        #yielding . . . unrounded estimate
        #if nothing overlaps you have zero 
        
def estimatePopulationInZone(source_polygons, population_field, study_zone,
                             output_fc):
    try:
        source_polygons, study_zone, output_fc = Path(source_polygons), Path(study_zone), Path (output_fc)

        #For inputs, ensure it exists, projected, same coordinate system
        #Most of this is similar if not the same checks as the first function.
        crs_names = []
        for fc in (source_polygons, study_zone):
            if not arcpy.Exists(str(fc)):
                raise FileNotFoundError(f"Input not found: {fc}")
            desc = arcpy.Describe(str(fc)) #describes the geometry type and coordinate system
            if desc.shapeType != "Polygon": #must be polygons for "area" to make sense as a check
                raise ValueError(f"{fc.name} must be polygons, not {desc.shapeType}")
            sr = desc.spatialReference
            if sr.type != "Projected" or sr.linearUnitName.lower() not in ("meter", "metre"): #meters, more importantly not degrees
                raise ValueError(f"{fc.name} msut use a projected coordinate system in meters.")
            crs_names.append(sr.name) #for below comparison
        if crs_names[0] != crs_names[1]: #inputs must be in same coordinate system, as geographic checks (like overlaps) are conducted
            raise ValueError(f"Inputs use different coordinate systems: {crs_names}")

        #Population fields checks
        pop_fields = arcpy.ListFields(str(source_polygons), population_field) #find the field
        if not pop_fields: #remind the user to check they typed it right. 
            raise ValueError(f"Field {population_field} not found in {source_polygons.name}")
        if pop_fields[0].type not in ("SmallInteger", "Integer", "Big Integer", "Single", "Double"): #every number type, just incase
            raise ValueError(f"You must use a numeric field for {population_field}")
        with arcpy.da.SearchCursor(str(source_polygons), [population_field]) as rows: #read the population value
            if any(row[0] is None or row[0] < 0 for row in rows): #blank or negative is not good
                raise ValueError(f"{population_field} is missing values or has negative values")
        for name in ("SRC_KM2", "PART_KM2", "EST_POP"): #the three fields the function will create
            if arcpy.ListFields(str(source_polygons), name): #we don't want duplicaes bc the function would just carry on with another name.
                raise ValueError(f"{source_polygons.name} already has a name field.")

        #Validates geodatabase
        if output_fc.parent.suffix.lower() != ".gdb" or not arcpy.Exists(str(output_fc.parent)): #folder must be gdb 
            raise ValueError(f"Output must go in an existing file geodatabase, {output_fc.parent}")
        if arcpy.ValidateTableName(output_fc.name, str(output_fc.parent)) != output_fc.name: #name has to be gdb name
            raise ValueError(f"Invalid output name in {output_fc.name}")
        if arcpy.Exists(str(output_fc)): #do not overwrite
            raise ValueError(f"The output {output_fc} already exists")

        #Dissolve the zone so overlapping zone areas are counted only once.
        zone = "memory\\zone" #stores the dissolved zone temporarily in the memory
        arcpy.management.Dissolve(str(study_zone), zone) #merges the zone polygons into one shape. 

        #The source area goes into a copy. This preserves the input, so the user cannot accidentally overwrite the input.
        sources = "memory\\sources" #temporarily copies the census polygons
        arcpy.management.CopyFeatures(str(source_polygons), sources) #copy so the original stays unedited
        arcpy.management.AddField(sources, "SRC_KM2", "DOUBLE") #field for each polygon's full area
        arcpy.management.CalculateGeometryAttributes(sources, [["SRC_KM2", "AREA"]], area_unit="SQUARE_KILOMETERS") #sqkm

        #Overlapping areas keep the source attributes. If they do not overlap, the output is empty
        arcpy.analysis.Intersect([sources, zone], str(output_fc), "NO_FID") #keeps the parts inside the zone. skip extra ID fields
        arcpy.management.AddField(str(output_fc), "PART_KM2", "DOUBLE") #field for each piece's area
        arcpy.management.AddField(str(output_fc), "EST_POP", "DOUBLE") #field for each piece's population
        arcpy.management.CalculateGeometryAttributes(str(output_fc), [["Part_KM2", "AREA"]], area_unit="SQUARE_KILOMETERS") #area in km2

        #Population calculation
        total = 0.0 #initialize the total of the estimate. start at zero
        fields = [population_field, "SRC_KM2", "PART_KM2", "EST_POP"] #read and then write in that order
        with arcpy.da.UpdateCursor(str(output_fc), fields) as rows: #cursor
            for population, src_km2, part_km2, _ in rows: #unpack the rows; _ is the empty estimate of pop for now
                estimate = population * part_km2 / src_km2 #calculate. pop * frac of the polygon within the zone
                rows.updateRow([population, src_km2, part_km2, estimate]) #save to the column
                total += estimate #add piece to total that began above
            return total #total for zone. stays as 0 if nothing overlaps.
    except Exception as error: #error catching
        raise RuntimeError("Estimation of population in zone failed.") from error
    finally: #even if it fails this runs, because we still wnat to get rid of this iteration's temporary storage. especially because it interferes with redos
        arcpy.management.Delete("memory")
        
# Problem 3 (40 points)
        #Here we will measure kms of lines (roads) that are inside the polygon
        #lines are the lines features. I would just do roads.
        #polygons are the polygons that are the grouping. block groups. 
        #polygon_id_field is the polygon identifier, like GEOID typically
        #output_fc is where to svae the result

        ##general outline and flow: 
        #1. lines are lines, polygons are polygons, and they exist. they are also prj identically in meters.
        #2. ID field exists and is valid: text or int, and every value is unique
        #3. output goes into free and existing gdb
        #4. polygons intersect with lines and keep line results. the line is cut where it hits a polygon edge. 
        #5. the line pieces are measured in km. most importantly, it remembers what polygon ID it is within
        #6. statistics are made for adding up segments within each polygon, by the polygon ID
        #7. polygons put into output and add up the total length.
        #yielding . . . the path of the output feature class of lines and polygons
        
def summarizeLineLength(lines, polygons, polygon_id_field, output_fc):
    try:
        lines, polygons, output_fc = Path(lines), Path(polygons), Path(output_fc)

        #Inputs checks. like above
        crs_names = [] #coordinate system names
        for fc, shape_type in ((lines, "Polyline"), (polygons, "Polygon")): #each input should have these geometries
            if not arcpy.Exists(str(fc)):
                raise FileNotFoundError(f"Input not found: {fc}") 
            desc = arcpy.Describe(str(fc)) #geometry type and coordinate system
            if desc.shapeType != shape_type: 
                raise ValueError(f"{fc.name} must be {shape_type}, not {desc.shapeType}") #corrects user
            sr = desc.spatialReference #input coordinate system
            if sr.type != "Projected" or sr.linearUnitName.lower() not in ("meter", "metre"): #same as always
                raise ValueError(f"{fc.name} must use a projected coordinate system in meters.")
            crs_names.append(sr.name) #for comparison below
        if crs_names[0] != crs_names[1]: #put inputs in the same system, or correct user below
            raise ValueError("Inputs use diferent coordinate systems.")

            #Polygons
        id_fields = arcpy.ListFields(str(polygons), polygon_id_field) #find ID field
        if not id_fields: #empty list is not correct ID
            raise ValueError(f"Field {polygon_id_field} not found in {polygons.name}")
        if id_fields[0].type not in ("String", "SmallInteger", "Integer", "BigInteger"): #text or whole numbers. no decimals
            raise ValueError(f"{polygon_id_field} must be a text or integer")
        with arcpy.da.SearchCursor(str(polygons), [polygon_id_field]) as rows: 
            ids = [row[0] for row in rows] #put into list
        if None in ids or len(ids) != len(set(ids)):  #drop duplicates
            raise ValueError(f"{polygon_id_field} values must all be unique and not empty") 
        if arcpy.ListFields(str(polygons), "LINE_KM"): #we create line_km below so it cant already exist
            raise ValueError(f"{polygons.name} already has a LINE_KM field")

        #Output
        if output_fc.parent.suffix.lower() != ".gdb" or not arcpy.Exists(str(output_fc.parent)): #existing gdb
            raise ValueError("Output must go into a file geodatabase")
        if arcpy.ValidateTableName(output_fc.name, str(output_fc.parent)) != output_fc.name:  #follow gdb naming conventions
            raise ValueError(f"{output_fc.name} is invalid.")
        if arcpy.Exists(str(output_fc)): #do not overwrite
            raise ValueError(f"{output_fc} already exists")

        #Line output. Point only touches do not add anything.
        #Polygons are input first
        pieces = "memory\\pieces" #temporary line pieces are put into the memory 
        arcpy.analysis.Intersect([str(polygons), str(lines)], pieces, "ALL", output_type="LINE") #lines are cut at the edges of polygons. the polygons are input first because the ID should keep the name of the polygon. otherwise, the line ID is preserved adn that is not useful for summarizing later.
        arcpy.management.AddField(pieces, "SEG_KM", "DOUBLE") #field for the piece length
        arcpy.management.CalculateGeometryAttributes(pieces, [["SEG_KM", "LENGTH"]], length_unit="KILOMETERS")

        #Total length per polygon
        totals = "memory\\totals" #temporary table in memory of the totals
        arcpy.analysis.Statistics(pieces, totals, [["SEG_KM", "SUM"]], polygon_id_field) #sum it up! one row for one ID

        #Copy the polygons and join the totals in
        arcpy.management.CopyFeatures(str(polygons), str(output_fc)) #copy all polygons so ones without lines are still kept
        arcpy.management.JoinField(str(output_fc), polygon_id_field, totals, polygon_id_field, ["SUM_SEG_KM"]) #attach totals by ID
        arcpy.management.AddField(str(output_fc), "LINE_KM", "DOUBLE") #final length field
        arcpy.management.CalculateField(str(output_fc), "LINE_KM", "!SUM_SEG_KM! or 0", "PYTHON3") #blanks are turned into 0
        arcpy.management.DeleteField(str(output_fc), "SUM_SEG_KM") #this field is not necessary because the line_km field will do the job
        return str(output_fc) #give user output path
    except Exception as error: #error display
        raise RuntimeError("Function failed") from error
    finally:  #work or not, delete memory to free up space adn be ready to rerun lines without worrying about leftover artifacts
        arcpy.management.Delete("memory")

     

######################################################################
# MAKE NO CHANGES BEYOND THIS POINT.
######################################################################
if __name__ == "__main__" and hawkid()[1] == "hawkid":
    print("### Error: YOU MUST provide your HawkID in the hawkid() function.")
