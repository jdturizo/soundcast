import array as _array
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb
import json
import numpy as np
import time
import os,sys
import h5py
import Tkinter, tkFileDialog
import multiprocessing as mp
import subprocess
from multiprocessing import Pool

#Hard-coded paths/data will be moved to a Config file
# Number of Global Interations
global_iterations = 1
# Assignment Convergence Criteria
max_iter = 50
b_rel_gap = 0.0001

if '-use_seed_trips' in sys.argv:
	seed_trips = True
else:
	seed_trips = False

if seed_trips:
	print 'Using SEED TRIPS.'
	hdf5_file_path = 'inputs/seed_trips.h5'
else:
	print 'Using DAYSIM OUTPUTS'
	hdf5_file_path = 'outputs/daysim_outputs.h5'


#HDF5 Groups and Subgroups
hdf5_maingroups=["Daysim","Emme","Truck Model","UrbanSim"]

hdf5_emme_subgroups=["5to6","6to7","7to8","8to9","9to10","10to14",
                     "14to15","15to16","16to17","17to18","18to20","20to5"]

emme_matrix_subgroups = ["Highway", "Walk", "Bike", "Transit"]

hdf5_urbansim_subgroups=["Households","Parcels","Persons"]
hdf5_freight_subgroups=["Inputs","Outputs","Rates"]
hdf5_daysim_subgroups=["Household","Person","Trip","Tour"]

#Skim for time, cost
skim_matrix_designation_all_tods=['t','c']
skim_matrix_designation_limited = ['d']



#skim for distance for only these time periods
distance_skim_tod = ['5to6']

#bike/walk
bike_walk_skim_tod = ['5to6']
bike_walk_matrix_dict = {'walk':{'time' : 'walkt', 'description' : 'walk time',
                                 'demand' : 'walk', 'modes' : ["w", "x"],
                                 'intrazonal_time' : 'izwtim'},
                         'bike':{'time' : 'biket', 'description' : 'bike time',
                                 'demand' : 'bike', 'modes' : ["k", "l", "q"],
                                 'intrazonal_time' : 'izbtim'}}

#transit inputs:
transit_skim_tod = ['6to7', '7to8', '8to9', '9to10']
transit_submodes=['b', 'c', 'f', 'p', 'r']

#fare
zone_file = 'inputs/Fares/transit_fare_zones.grt'
peak_fare_box = 'inputs/Fares/am_fares_farebox.in'
peak_monthly_pass = 'inputs/Fares/am_fares_monthly_pass.in'
offpeak_fare_box = 'inputs/Fares/md_fares_farebox.in'
offpeak_monthly_pass = 'inputs/Fares/md_fares_monthly_pass.in'

fare_matrices_tod = ['6to7', '9to10']
fare_dict = {'5to6':{'Files' : {'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass}, 'Names' : {'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
             '6to7':{'Files' : {'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass},'Names':{'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
            '7to8':{'Files' : {'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass}, 'Names':{'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
            '8to9':{'Files' :{'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass}, 'Names' :{'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
            '9to10':{'Files' :{'fare_box_file' : offpeak_fare_box, 'monthly_pass_file' : offpeak_monthly_pass}, 'Names':{'fare_box_matrix' : 'mfarbx',  'monthly_fare_matrix' : 'mfarps'}},
            '10to14':{'Files' :{'fare_box_file' : offpeak_fare_box, 'monthly_pass_file' : offpeak_monthly_pass}, 'Names':{'fare_box_matrix' : 'mfarbx',  'monthly_fare_matrix' : 'mfarps'}},
            '14to15':{'Files' :{'fare_box_file' : offpeak_fare_box, 'monthly_pass_file' : offpeak_monthly_pass}, 'Names':{'fare_box_matrix' : 'mfarbx',  'monthly_fare_matrix' : 'mfarps'}},
            '15to16':{'Files' :{'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass}, 'Names' :{'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
            '16to17':{'Files' :{'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass}, 'Names' : {'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
            '17to18':{'Files' :{'fare_box_file' : peak_fare_box, 'monthly_pass_file' : peak_monthly_pass}, 'Names' : {'fare_box_matrix' : 'afarbx',  'monthly_fare_matrix' : 'afarps'}},
            '18to20':{'Files' :{'fare_box_file' : offpeak_fare_box, 'monthly_pass_file' : offpeak_monthly_pass}, 'Names' : {'fare_box_matrix' : 'mfarbx',  'monthly_fare_matrix' : 'mfarps'}},
            '20to5':{'Files' :{'fare_box_file' : offpeak_fare_box, 'monthly_pass_file' : offpeak_monthly_pass}, 'Names' : {'fare_box_matrix' : 'mfarbx',  'monthly_fare_matrix' : 'mfarps'}}}

#intrazonals
intrazonal_dict = {'distance' : 'izdist', 'time auto' : 'izatim', 'time bike' : 'izbtim', 'time walk' : 'izwtim'}
taz_area_file = 'inputs/intrazonals/taz_acres.in'


def create_hdf5_container(hdf_name):

    start_time = time.time()

    # Create the HDF5 Container with subgroups
    # (only creates it if one does not already exist using "w-")
    # Currently uses the subgroups as shown in the "hdf5_subgroups" list hardcoded above,
    # this could be read from a control file.

    hdf_filename = os.path.join('HDF5',hdf_name +'.hdf5').replace("\\","/")
    print hdf_filename
    my_user_classes = json_to_dictionary('user_classes')

    #IOError will occur if file already exists with "w-", so in this case just prints it exists
    #If file does not exist, opens new hdf5 file and create groups based on the subgroup list above.

    try:
        my_store=h5py.File(hdf_filename, "w-")

        #First Create the Main Groups
        for x in range (0, len(hdf5_maingroups)):
            my_store.create_group(hdf5_maingroups[x])

        #Now Loop over the Emme Subgroups
        for x in range (0, len(hdf5_emme_subgroups)):
            my_store["Emme"].create_group(hdf5_emme_subgroups[x])

        #Now Loop over the UrbanSim Subgroups
        for x in range (0, len(hdf5_urbansim_subgroups)):
            my_store["UrbanSim"].create_group(hdf5_urbansim_subgroups[x])

        #Now Loop over the Daysim Subgroups
        for x in range (0, len(hdf5_daysim_subgroups)):
            my_store["Daysim"].create_group(hdf5_daysim_subgroups[x])

        print 'HDF5 File was successfully created'
        my_store.close()

    except IOError:
        print 'HDF5 File already exists - no file was created'

    end_time = time.time()
    print 'It took', round((end_time-start_time),2), 'seconds to create the HDF5 file.'

    return hdf_filename

def create_hdf5_skim_container(hdf5_name):
    #create containers for TOD skims
    start_time = time.time()

    hdf5_filename = os.path.join('HDF5',hdf5_name +'.hdf5').replace("\\","/")
    print hdf5_filename
    my_user_classes = json_to_dictionary('user_classes')

    #IOError will occur if file already exists with "w-", so in this case just prints it exists
    #If file does not exist, opens new hdf5 file and create groups based on the subgroup list above.

    #Create a sub groups with the same name as the container, e.g. 5to6, 7to8
    #These facilitate multi-processing and will be imported to a master HDF5 file at the end of the run
    try:
        my_store=h5py.File(hdf5_filename, "w-")
        my_store.create_group(hdf5_name)
        print 'HDF5 File was successfully created'
        my_store.close()

    except IOError:
        print 'HDF5 File already exists - no file was created'



    end_time = time.time()
    print 'It took', round((end_time-start_time),2), 'seconds to create the HDF5 file.'

    return hdf5_filename

def create_hdf5_skim_container2(hdf5_name):
    #create containers for TOD skims
    start_time = time.time()

    hdf5_filename = os.path.join('inputs', hdf5_name +'.h5').replace("\\","/")
    print hdf5_filename
    my_user_classes = json_to_dictionary('user_classes')

    # IOError will occur if file already exists with "w-", so in this case
    # just prints it exists. If file does not exist, opens new hdf5 file and
    # create groups based on the subgroup list above.

    # Create a sub groups with the same name as the container, e.g. 5to6, 7to8
    # These facilitate multi-processing and will be imported to a master HDF5 file
    # at the end of the run

    if os.path.exists(hdf5_filename):
        print 'HDF5 File already exists - no file was created'

    else:
        my_store=h5py.File(hdf5_filename, "w-")
        my_store.create_group(hdf5_name)
        print 'HDF5 File was successfully created'
        my_store.close()

    end_time = time.time()
    print 'It took', round((end_time-start_time),2), 'seconds to create the HDF5 file.'

    return hdf5_filename
def text_to_dictionary(dict_name):

    input_filename = os.path.join('inputs/skim_params/',dict_name+'.txt').replace("\\","/")
    my_file=open(input_filename)
    my_dictionary = {}

    for line in my_file:
        k, v = line.split(':')
        my_dictionary[eval(k)] = v.strip()

    return(my_dictionary)


def json_to_dictionary(dict_name):

    #Determine the Path to the input files and load them
    input_filename = os.path.join('inputs/skim_params/',dict_name+'.txt').replace("\\","/")
    my_dictionary = json.load(open(input_filename))

    return(my_dictionary)

def open_emme_project(my_project):

    #If you do not want the Emme window to show, change True to False
     #my_desktop = app.start_dedicated(False, "cth", project_name)
    my_desktop = app.start_dedicated(True, "PSRC", my_project)
    my_modeller = _m.Modeller(my_desktop)

    return(my_modeller)




def vdf_initial(my_project):

    start_vdf_initial = time.time()

    #Define the Emme Tools used in this function
    manage_vdfs = my_project.tool("inro.emme.data.function.function_transaction")

    #Point to input file for the VDF's and Read them in
    function_file = os.path.join(os.path.dirname(my_project.emmebank.path),"inputs/vdfs.txt").replace("\\","/")
    manage_vdfs(transaction_file = function_file,throw_on_error = True)

    end_vdf_initial = time.time()


def delete_matrices(my_project, matrix_type):

    start_delete_matrices = time.time()

    #Define the Emme Tools used in this function
    delete_matrix = my_project.tool("inro.emme.data.matrix.delete_matrix")


    data_explorer = my_project.desktop.data_explorer()
    for database in data_explorer.databases():
        emmebank = database.core_emmebank

        # find first non-empty scenario
        scenarios = list(emmebank.scenarios())
        for  scenario in scenarios:
            if len(scenario.zone_numbers) > 0:
                break

        #zone_numbers = scenario.zone_numbers
        for matrix in emmebank.matrices():
            if matrix.type == matrix_type:
                delete_matrix(matrix, emmebank)

    end_delete_matrices = time.time()


def define_matrices(my_project):
    print 'starting define matrices'

    start_define_matrices = time.time()

    #Define the Emme Tools used in this function
    create_matrix = my_project.tool("inro.emme.data.matrix.create_matrix")

    #Load in the necessary Dictionaries
    matrix_dict = json_to_dictionary("user_classes")

    data_explorer = my_project.desktop.data_explorer()
    for database in data_explorer.databases():
        my_bank = database.core_emmebank
        #get the tod for this bank, which should be it's title, e.g. 5to6
        tod = my_bank.title

        # find first non-empty scenario
        scenarios = list(my_bank.scenarios())
        for  scenario in scenarios:
            if len(scenario.zone_numbers) > 0:
                break
        current_scenario = scenario

    # Create the Full Demand Matrices in Emme
        for x in range (0, len(emme_matrix_subgroups)):

            for y in range (0, len(matrix_dict[emme_matrix_subgroups[x]])):
                create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= matrix_dict[emme_matrix_subgroups[x]][y]["Name"],
                          matrix_description= matrix_dict[emme_matrix_subgroups[x]][y]["Description"],
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)

    # Create the Highway Skims in Emme
        #Check to see if we want to make Distance skims for this period:
        if tod in distance_skim_tod:
            #overide the global skim matrix designation (time & cost most likely) to make sure distance skims are created for this tod
            my_skim_matrix_designation=skim_matrix_designation_limited + skim_matrix_designation_all_tods
        else:
            my_skim_matrix_designation = skim_matrix_designation_all_tods


        for x in range (0, len(my_skim_matrix_designation)):

            for y in range (0, len(matrix_dict["Highway"])):
                create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= matrix_dict["Highway"][y]["Name"]+my_skim_matrix_designation[x],
                          matrix_description= matrix_dict["Highway"][y]["Description"],
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)


    #Create empty Transit Skim matrices in Emme only for tod in transit_skim_tod list
    # Actual In Vehicle Times by Mode
    if tod in transit_skim_tod:
        for item in transit_submodes:
             create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= 'ivtwa' + item,
                          matrix_description= "Actual IVTs by Mode: " + item,
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)

        #Transit, All Modes:
        dct_aggregate_transit_skim_names = json_to_dictionary('transit_skim_aggregate_matrix_names')

        for key, value in dct_aggregate_transit_skim_names.iteritems():
            create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= key,
                          matrix_description= value,
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)
    #bike & walk, do not need for all time periods. most likely just 1:
    if tod in bike_walk_skim_tod:
        for key in bike_walk_matrix_dict.keys():
            create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= bike_walk_matrix_dict[key]['time'],
                          matrix_description= bike_walk_matrix_dict[key]['description'],
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)

    #transit fares, farebox & monthly matrices :
    if tod in fare_matrices_tod:
        for value in fare_dict[tod]['Names'].itervalues():
            create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= value,
                          matrix_description= 'transit fare',
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)
    #intrazonals:
    for key, value in intrazonal_dict.iteritems():
        create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= value,
                          matrix_description= key,
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)
    #origin matrix to hold TAZ Area:
    create_matrix(matrix_id= my_bank.available_matrix_identifier("ORIGIN"),
                          matrix_name= 'tazacr',
                          matrix_description= 'taz area',
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)

    end_define_matrices = time.time()

    print 'It took', round((end_define_matrices-start_define_matrices)/60,2), 'minutes to define all matrices in Emme.'

def create_fare_zones(my_project, zone_file, fare_file):
    my_bank = my_project.emmebank
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref


    init_partition = my_project.tool("inro.emme.data.zone_partition.init_partition")
    gt = my_bank.partition("gt")
    init_partition(partition=gt)

    process_zone_partition = my_project.tool("inro.emme.data.zone_partition.partition_transaction")
    process_zone_partition(transaction_file = zone_file,
                           throw_on_error = True,
                           scenario = current_scenario)



    matrix_transaction =  my_project.tool("inro.emme.data.matrix.matrix_transaction")
    matrix_transaction(transaction_file = fare_file,
                       throw_on_error = True,
                       scenario = current_scenario)


def populate_intrazonals(my_project):
    #populate origin matrix with zone areas:

    my_bank = my_project.emmebank
    print my_bank.title
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    matrix_transaction =  my_project.tool("inro.emme.data.matrix.matrix_transaction")
    matrix_transaction(transaction_file = taz_area_file,
                       throw_on_error = True,
                       scenario = current_scenario)

    matrix_calculator = json_to_dictionary("matrix_calculation")
    matrix_calc = my_project.tool("inro.emme.matrix_calculation.matrix_calculator")

    app.App.refresh_data

    taz_area_matrix = my_bank.matrix('tazacr').id
    distance_matrix = my_bank.matrix(intrazonal_dict['distance']).id

    #Hard coded for now, generalize later
    for key, value in intrazonal_dict.iteritems():
        if key == 'distance':

            mod_calc = matrix_calculator
            mod_calc["result"] = value
            mod_calc["expression"] = "sqrt(" +taz_area_matrix + "/640) * 45/60*(p.eq.q)"
            matrix_calc(mod_calc)
        if key == 'time auto':
            mod_calc = matrix_calculator
            mod_calc["result"] = value
            mod_calc["expression"] = distance_matrix + " *(60/15)"
            matrix_calc(mod_calc)
        if key == 'time bike':
            mod_calc = matrix_calculator
            mod_calc["result"] = value
            mod_calc["expression"] = distance_matrix + " *(60/10)"
            matrix_calc(mod_calc)
        if key == 'time walk':
            mod_calc = matrix_calculator
            mod_calc["result"] = value
            mod_calc["expression"] = distance_matrix + " *(60/3)"
            matrix_calc(mod_calc)




def intitial_extra_attributes(my_project):

    start_extra_attr = time.time()

    #Define the Emme Tools used in this function
    create_extras = my_project.tool("inro.emme.data.extra_attribute.create_extra_attribute")

    #Load in the necessary Dictionaries
    matrix_dict = json_to_dictionary("user_classes")

    # Create the link extra attributes to store volume results
    for x in range (0, len(matrix_dict["Highway"])):
        create_extras(extra_attribute_type="LINK",
                      extra_attribute_name= "@"+matrix_dict["Highway"][x]["Name"],
                      extra_attribute_description= matrix_dict["Highway"][x]["Description"],
                      overwrite=True)

    # Create the link extra attributes to store the auto equivalent of bus vehicles
    t22 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trnv3",extra_attribute_description="Transit Vehicles",overwrite=True)

    # Create the link extra attributes to store the toll rates in
    t23 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@toll1",extra_attribute_description="SOV Tolls",overwrite=True)
    t24 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@toll2",extra_attribute_description="HOV 2 Tolls",overwrite=True)
    t25 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@toll3",extra_attribute_description="HOV 3+ Tolls",overwrite=True)
    t26 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trkc1",extra_attribute_description="Light Truck Tolls",overwrite=True)
    t27 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trkc2",extra_attribute_description="Medium Truck Tolls",overwrite=True)
    t28 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trkc3",extra_attribute_description="Heavy Truck Tolls",overwrite=True)

    # Create the link extra attribute to store the arterial delay in
    t29 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@rdly",extra_attribute_description="Intersection Delay",overwrite=True)

    end_extra_attr = time.time()


def import_extra_attributes(my_project):

    start_extra_attr_import = time.time()

    #Define the Emme Tools used in this function
    import_attributes = my_project.tool("inro.emme.data.network.import_attribute_values")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    attr_file = os.path.join(os.path.dirname(my_project.emmebank.path),"Inputs/tolls.txt").replace("\\","/")


    import_attributes(attr_file, scenario = current_scenario,
              column_labels={0: "inode",
                             1: "jnode",
                             2: "@toll1",
                             3: "@toll2",
                             4: "@toll3",
                             5: "@trkc1",
                             6: "@trkc2",
                             7: "@trkc3"},
              revert_on_error=True)

    end_extra_attr_import = time.time()


def arterial_delay_calc(my_project):

    start_arterial_calc = time.time()

    #Define the Emme Tools used in this function
    create_extras = my_project.tool("inro.emme.data.extra_attribute.create_extra_attribute")
    network_calc = my_project.tool("inro.emme.network_calculation.network_calculator")
    delete_extras = my_project.tool("inro.emme.data.extra_attribute.delete_extra_attribute")

    #Load in the necessary Dictionaries
    link_calculator = json_to_dictionary("link_calculation")
    node_calculator = json_to_dictionary("node_calculation")

    # Create the temporary attributes needed for the signal delay calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl1",extra_attribute_description="temp link calc 1",overwrite=True)
    t2 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl2",extra_attribute_description="temp link calc 2",overwrite=True)
    t3 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn1",extra_attribute_description="temp node calc 1",overwrite=True)
    t4 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn2",extra_attribute_description="temp node calc 2",overwrite=True)
    t5 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@cycle",extra_attribute_description="Cycle Length",overwrite=True)
    t6 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@red",extra_attribute_description="Red Time",overwrite=True)

    # Set Temporary Link Attribute #1 to 1 for arterial links (ul3 .ne. 1,2)
    # Exclude links that intersect with centroid connectors
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpl1"
    mod_calc["expression"] = "1"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99"
    network_calc(mod_calc)

    # Set Temporary Link Attribute #2 to the minimum of lanes+2 or 5
    # for arterial links (ul3 .ne. 1,2)  - tmpl2 will equal either 3,4,5
    # Exclude links that intersect with centroid connectors
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpl2"
    mod_calc["expression"] = "(lanes+2).min.5"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99"
    network_calc(mod_calc)

    # Set Temporary Node Attribute #1 to sum of intersecting arterial links (@tmpl1)
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpn1"
    mod_calc["expression"] = "@tmpl1"
    mod_calc["aggregation"] = "+"
    network_calc(mod_calc)

    # Set Temporary Node Attribute #2 to sum of intersecting arterial links (@tmpl2)
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpn2"
    mod_calc["expression"] = "@tmpl2"
    mod_calc["aggregation"] = "+"
    network_calc(mod_calc)

    # Cycle Time at Every I-Node
    mod_calc = node_calculator
    mod_calc["result"] = "@cycle"
    mod_calc["expression"] = "(1+(@tmpn2/8)*(@tmpn1/4))*(@tmpn1.gt.2)"
    network_calc(mod_calc)

    link_calculator = json_to_dictionary("link_calculation")

    # Red Time at Every J-Node
    mod_calc = link_calculator
    mod_calc["result"] = "@red"
    mod_calc["expression"] = "1.2*@cyclej*(1-(@tmpn1j*@tmpl2)/(2*@tmpn2j))"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99 and @cyclej=0.01,999999"
    network_calc(mod_calc)

    # Calculate intersection delay factor for every link with a cycle time exceeding zero
    mod_calc = link_calculator
    mod_calc["result"] = "@rdly"
    mod_calc["expression"] = "((@red*@red)/(2*@cyclej).max.0.2).min.1.0"
    mod_calc["selections"]["link"] = "@cyclej=0.01,999999"
    network_calc(mod_calc)

    # Set intersection delay factor to 0 for links of 0.01 mile lenght or less
    mod_calc = link_calculator
    mod_calc["result"] = "@rdly"
    mod_calc["expression"] = "0"
    mod_calc["selections"]["link"] = "length=0,0.01"
    network_calc(mod_calc)

    #delete the temporary extra attributes
    delete_extras(t1)
    delete_extras(t2)
    delete_extras(t3)
    delete_extras(t4)
    delete_extras(t5)
    delete_extras(t6)

    end_arterial_calc = time.time()


def traffic_assignment(my_project):

    start_traffic_assignment = time.time()
    print 'starting traffic assignment for' +  my_project.emmebank.title
    #Define the Emme Tools used in this function
    assign_extras = my_project.tool("inro.emme.traffic_assignment.set_extra_function_parameters")
    assign_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_assignment")

    #Load in the necessary Dictionaries
    assignment_specification = json_to_dictionary("general_path_based_assignment")
    my_user_classes= json_to_dictionary("user_classes")

    # Modify the Assignment Specifications for the Closure Criteria and Perception Factors
    mod_assign = assignment_specification
    mod_assign["stopping_criteria"]["max_iterations"]= max_iter
    mod_assign["stopping_criteria"]["best_relative_gap"]= b_rel_gap

    for x in range (0, len(mod_assign["classes"])):
        vot = ((1/float(my_user_classes["Highway"][x]["Value of Time"]))*60)
        mod_assign["classes"][x]["generalized_cost"]["perception_factor"] = vot
        mod_assign["classes"][x]["generalized_cost"]["link_costs"] = my_user_classes["Highway"][x]["Toll"]
        mod_assign["classes"][x]["demand"] = "mf"+ my_user_classes["Highway"][x]["Name"]
        mod_assign["classes"][x]["mode"] = my_user_classes["Highway"][x]["Mode"]


    assign_extras(el1 = "@rdly", el2 = "@trnv3")



    assign_traffic(mod_assign)

    end_traffic_assignment = time.time()

    print 'It took', round((end_traffic_assignment-start_traffic_assignment)/60,2), 'minutes to run the assignment.'

def transit_assignment(my_project):

    start_transit_assignment = time.time()

    #Define the Emme Tools used in this function
    assign_transit = my_project.tool("inro.emme.transit_assignment.extended_transit_assignment")

    #Load in the necessary Dictionaries
    assignment_specification = json_to_dictionary("extended_transit_assignment")
    assign_transit(assignment_specification)

    end_transit_assignment = time.time()
    print 'It took', round((end_transit_assignment-start_transit_assignment)/60,2), 'minutes to run the assignment.'

def transit_assignment2(my_project, tod):

    start_transit_assignment = time.time()
    assign_transit = my_project.tool("inro.emme.transit_assignment.extended_transit_assignment")
    data_explorer = my_project.desktop.data_explorer()
    for database in data_explorer.databases():
        emmebank = database.core_emmebank
        if emmebank.title == tod:
            #Define the Emme Tools used in this function


            #Load in the necessary Dictionaries
            assignment_specification = json_to_dictionary("extended_transit_assignment")
            assign_transit(assignment_specification)

    end_transit_assignment = time.time()
    print 'It took', round((end_transit_assignment-start_transit_assignment)/60,2), 'minutes to run the assignment.'
def transit_skims(my_project):

    skim_transit = my_project.tool("inro.emme.transit_assignment.extended.matrix_results")
    #specs are stored in a dictionary where "spec1" is the key and a list of specs for each skim is the value
    skim_specs = json_to_dictionary("transit_skim_setup")
    my_spec_list = skim_specs["spec1"]
    for item in my_spec_list:
        skim_transit(item)
def transit_skims2(my_project, tod):
    start_time_skim = time.time()
    skim_transit = my_project.tool("inro.emme.transit_assignment.extended.matrix_results")
    data_explorer = my_project.desktop.data_explorer()
    for database in data_explorer.databases():
        emmebank = database.core_emmebank
        if emmebank.title == tod:
        #specs are stored in a dictionary where "spec1" is the key and a list of specs for each skim is the value
            skim_specs = json_to_dictionary("transit_skim_setup")
            my_spec_list = skim_specs["spec1"]
            for item in my_spec_list:
               skim_transit(item)

    end_time_skim = time.time()
    print 'It took', round((end_time_skim-start_time_skim)/60,2), 'minutes to calculate the transit skim'

def attribute_based_skims(my_project,my_skim_attribute):
    #Use only for Time or Distance!

    start_time_skim = time.time()

    #Define the Emme Tools used in this function
    create_extras = my_project.tool("inro.emme.data.extra_attribute.create_extra_attribute")
    network_calc = my_project.tool("inro.emme.network_calculation.network_calculator")
    skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
    delete_extras = my_project.tool("inro.emme.data.extra_attribute.delete_extra_attribute")

    #Load in the necessary Dictionaries
    skim_specification = json_to_dictionary("general_attribute_based_skim")
    link_calculator = json_to_dictionary("link_calculation")
    my_user_classes = json_to_dictionary("user_classes")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    #Figure out what skim matrices to use based on attribute (either time or length)
    if my_skim_attribute =="Time":
        my_attribute = "timau"
        my_extra = "@timau"
        skim_type = "Time Skims"
        skim_desig = "t"

        #Create the Extra Attribute
        t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name=my_extra,extra_attribute_description="copy of "+my_attribute,overwrite=True)

        # Store timau (auto time on links) into an extra attribute so we can skim for it
        mod_calcs = link_calculator
        mod_calcs["result"] = my_extra
        mod_calcs["expression"] = my_attribute
        mod_calcs["selections"]["link"] = "all"
        network_calc(mod_calcs)

    if my_skim_attribute =="Distance":
        my_attribute = "length"
        my_extra = "@dist"
        skim_type = "Distance Skims"
        skim_desig = "d"
        #Create the Extra Attribute
        t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name=my_extra,extra_attribute_description="copy of "+my_attribute,overwrite=True)

        # Store Length (auto distance on links) into an extra attribute so we can skim for it
        mod_calcs = link_calculator
        mod_calcs["result"] = my_extra
        mod_calcs["expression"] = my_attribute
        mod_calcs["selections"]["link"] = "all"
        network_calc(mod_calcs)

    mod_skim = skim_specification

    for x in range (0, len(mod_skim["classes"])):
        my_extra = my_user_classes["Highway"][x][my_skim_attribute]
        matrix_name= my_user_classes["Highway"][x]["Name"]+skim_desig
        matrix_id = my_bank.matrix(matrix_name).id
        mod_skim["classes"][x]["analysis"]["results"]["od_values"] = matrix_id
        mod_skim["path_analysis"]["link_component"] = my_extra

    skim_traffic(mod_skim)

    #add in intazonal values:
    matrix_calculator = json_to_dictionary("matrix_calculation")
    matrix_calc = my_project.tool("inro.emme.matrix_calculation.matrix_calculator")
    inzone_auto_time = my_bank.matrix(intrazonal_dict['time auto']).id
    inzone_distance = my_bank.matrix(intrazonal_dict['distance']).id
    if my_skim_attribute =="Time":
        for x in range (0, len(mod_skim["classes"])):
            matrix_name= my_user_classes["Highway"][x]["Name"]+skim_desig
            matrix_id = my_bank.matrix(matrix_name).id
            mod_calc = matrix_calculator
            mod_calc["result"] = matrix_id
            mod_calc["expression"] = inzone_auto_time + "+" + matrix_id
            matrix_calc(mod_calc)
    if my_skim_attribute =="Distance":
        for x in range (0, len(mod_skim["classes"])):
            matrix_name= my_user_classes["Highway"][x]["Name"]+skim_desig
            matrix_id = my_bank.matrix(matrix_name).id
            mod_calc = matrix_calculator
            mod_calc["result"] = matrix_id
            mod_calc["expression"] = inzone_distance + "+" + matrix_id
            matrix_calc(mod_calc)



    #json.dump(mod_skim, open('D://time_mod_skim.ems', 'wb'))

    #delete the temporary extra attributes
    delete_extras(t1)

    end_time_skim = time.time()

    print 'It took', round((end_time_skim-start_time_skim)/60,2), 'minutes to calculate the ' +skim_type+'.'

def attribute_based_toll_cost_skims(my_project, toll_attribute):
    #Function to calculate true/toll cost skims. Should fold this into attribute_based_skims function.

     start_time_skim = time.time()

     skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
     skim_specification = json_to_dictionary("general_attribute_based_skim")
     my_user_classes = json_to_dictionary("user_classes")

     current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
     my_bank = current_scenario.emmebank

     my_skim_attribute = "Toll"
     skim_desig = "c"
     #at this point, mod_skim is an empty spec ready to be populated with 21 classes. Here we are only populating the classes that
     #that have the appropriate occupancy(sv, hov2, hov3) to skim for the passed in toll_attribute (@toll1, @toll2, @toll3)
     #no need to create the extra attribute, already done in initial_extra_attributes
     mod_skim = skim_specification
     for x in range (0, len(mod_skim["classes"])):
        if my_user_classes["Highway"][x][my_skim_attribute] == toll_attribute:
            my_extra = my_user_classes["Highway"][x][my_skim_attribute]
            matrix_name= my_user_classes["Highway"][x]["Name"]+skim_desig
            matrix_id = my_bank.matrix(matrix_name).id
            mod_skim["classes"][x]["analysis"]["results"]["od_values"] = matrix_id
            mod_skim["path_analysis"]["link_component"] = my_extra
     skim_traffic(mod_skim)



def cost_skims(my_project):

    start_gc_skim = time.time()

    #Define the Emme Tools used in this function
    skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")

    #Load in the necessary Dictionaries
    skim_specification = json_to_dictionary("general_generalized_cost_skim")
    my_user_classes = json_to_dictionary("user_classes")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        matrix_name= 'mf'+my_user_classes["Highway"][x]["Name"]+'c'
        mod_skim["classes"][x]["results"]["od_travel_times"]["shortest_paths"] = matrix_name

    skim_traffic(mod_skim)

    end_gc_skim = time.time()

    print 'It took', round((end_gc_skim-start_gc_skim)/60,2), 'minutes to calculate the generalized cost skims.'

def class_specific_volumes(my_project):

    start_vol_skim = time.time()

    #Define the Emme Tools used in this function
    skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")

    #Load in the necessary Dictionaries
    skim_specification = json_to_dictionary("general_path_based_volume")
    my_user_classes = json_to_dictionary("user_classes")

    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        mod_skim["classes"][x]["results"]["link_volumes"] = "@"+my_user_classes["Highway"][x]["Name"]
    skim_traffic(mod_skim)

    end_vol_skim = time.time()

    print 'It took', round((end_vol_skim-start_vol_skim),2), 'seconds to generate class specific volumes.'




def skims_to_hdf5(my_project):
#This is for multiple banks in one project

    start_export_hdf5 = time.time()
    data_explorer = my_project.desktop.data_explorer()
    matrix_dict = text_to_dictionary('demand_matrix_dictionary')
    uniqueMatrices = set(matrix_dict.values())

    #Read the Time of Day File from the Dictionary File and Set Unique TOD List
    tod_dict = text_to_dictionary('time_of_day')
    uniqueTOD = set(tod_dict.values())
    uniqueTOD = list(uniqueTOD)

    #populate a dictionary of with key=bank name, value = emmebank object
    all_emmebanks = {}
    for database in data_explorer.databases():
        emmebank = database.core_emmebank
        all_emmebanks.update({emmebank.title: emmebank})



    #See if there is a group called Skims.IF so, it probably has old data in it. Delete the group and create a new one.




    for tod in uniqueTOD:
        print tod
        hdf5_filename = create_hdf5_skim_container2(tod)
        my_store=h5py.File(hdf5_filename, "r+")
        e = "Skims" in my_store
        if e:
            del my_store["Skims"]
            skims_group = my_store.create_group("Skims")
            print "Group Skims Exists. Group deleted then created"
            #If not there, create the group
        else:
            skims_group = my_store.create_group("Skims")
            print "Group Skims Created"

        my_bank = all_emmebanks[tod]
        #need a scenario, get the first one
        current_scenario = list(my_bank.scenarios())[0]
        #Determine the Path and Scenario File

        zones=current_scenario.zone_numbers
        bank_name = my_bank.title

        #Load in the necessary Dictionaries
        matrix_dict = json_to_dictionary("user_classes")


        # First Store a Dataset containing the Indicices for the Array to Matrix using mf01
        try:
            mat_id=my_bank.matrix("mf01")
            em_val=inro.emme.database.matrix.FullMatrix.get_data(mat_id,current_scenario)
            my_store["Skims"].create_dataset("indices", data=em_val.indices, compression='gzip')

        except RuntimeError:
            del my_store["Skims"]["indices"]
            my_store["Skims"].create_dataset("indices", data=em_val.indices, compression='gzip')


        # Loop through the Subgroups in the HDF5 Container
        #highway, walk, bike, transit
        #need to make sure we include Distance skims for TOD specified in distance_skim_tod
        if tod in distance_skim_tod:
            my_skim_matrix_designation = skim_matrix_designation_limited + skim_matrix_designation_all_tods
        else:
            my_skim_matrix_designation = skim_matrix_designation_all_tods

        for x in range (0, len(my_skim_matrix_designation)):

            for y in range (0, len(matrix_dict["Highway"])):
                matrix_name= matrix_dict["Highway"][y]["Name"]+my_skim_matrix_designation[x]
                matrix_id = my_bank.matrix(matrix_name).id
                if my_skim_matrix_designation[x] == 'c':
                    matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)
                else:
                    matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100

                print matrix_name

                my_store["Skims"].create_dataset(matrix_name, data=matrix_value.astype('uint16'),compression='gzip')
                print matrix_name+' was transferred to the HDF5 container.'
        #transit
        if tod in transit_skim_tod:
            for item in transit_submodes:
                matrix_name= 'ivtwa' + item
                matrix_id = my_bank.matrix(matrix_name).id
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
                my_store["Skims"].create_dataset(matrix_name, data=matrix_value.astype('uint16'),compression='gzip')
                print matrix_name+' was transferred to the HDF5 container.'

                #Transit, All Modes:
            dct_aggregate_transit_skim_names = json_to_dictionary('transit_skim_aggregate_matrix_names')

            for key, value in dct_aggregate_transit_skim_names.iteritems():
                matrix_name= key
                matrix_id = my_bank.matrix(matrix_name).id
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
                my_store["Skims"].create_dataset(matrix_name, data=matrix_value.astype('uint16'),compression='gzip')
                print matrix_name+' was transferred to the HDF5 container.'
        #bike/walk
        if tod in bike_walk_skim_tod:
            for key in bike_walk_matrix_dict.keys():
                matrix_name= bike_walk_matrix_dict[key]['time']
                matrix_id = my_bank.matrix(matrix_name).id
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
                my_store["Skims"].create_dataset(matrix_name, data=matrix_value.astype('uint16'),compression='gzip')
                print matrix_name+' was transferred to the HDF5 container.'
        #transit/fare
        if tod in fare_matrices_tod:
            for value in fare_dict[tod]['Names'].values():
                matrix_name= 'mf' + value
                print matrix_name
                print my_bank.matrix(matrix_name).id
                matrix_id = my_bank.matrix(matrix_name).id
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
                my_store["Skims"].create_dataset(matrix_name, data=matrix_value.astype('uint16'),compression='gzip')
                print matrix_name+' was transferred to the HDF5 container.'


        my_store.close()
    end_export_hdf5 = time.time()
    print 'It took', round((end_export_hdf5-start_export_hdf5)/60,2), 'minutes to import matrices to Emme.'

def skims_to_hdf5_concurrent(my_project):
#one project, one bank

    start_export_hdf5 = time.time()

    #Determine the Path and Scenario File
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank
    zones=current_scenario.zone_numbers
    bank_name = my_project.emmebank.title
    tod = bank_name

    #matrix_dict = text_to_dictionary('demand_matrix_dictionary')
    #uniqueMatrices = set(matrix_dict.values())
    #Load in the necessary Dictionaries
    my_user_classes = json_to_dictionary("user_classes")

    #Create the HDF5 Container if needed and open it in read/write mode using "r+"

    #hdf_filename = create_hdf5_container(bank_name)
    hdf5_filename = create_hdf5_skim_container(bank_name)

    my_store=h5py.File(hdf5_filename, "r+")


    #See if there is a group called Skims.IF so, it probably has old data in it. Delete the group and create a new one.
    e = "Skims" in my_store
    if e:
        del my_store["Skims"]
        skims_group = my_store.create_group("Skims")
        print "Group Skims Exists. Group deleted then created"
        #If not there, create the group
    else:
        skims_group = my_store.create_group("Skims")
        print "Group Skims Created"
        #Now create the TOD group inside the skims group:




    skims_group.create_group(tod)

        #need a scenario, get the first one
    current_scenario = list(my_bank.scenarios())[0]
        #Determine the Path and Scenario File

    zones=current_scenario.zone_numbers


        #Load in the necessary Dictionaries
    matrix_dict = json_to_dictionary("user_classes")


        # First Store a Dataset containing the Indicices for the Array to Matrix using mf01
    try:
        mat_id=my_bank.matrix("mf01")
        em_val=inro.emme.database.matrix.FullMatrix.get_data(mat_id,current_scenario)
        my_store.create_dataset("indices", data=em_val.indices, compression='gzip')

    except RuntimeError:
        del my_store["indices"]
        my_store.create_dataset("indices", data=em_val.indices, compression='gzip')


        # Loop through the Subgroups in the HDF5 Container
        #highway, walk, bike, transit
        #need to make sure we include Distance skims for TOD specified in distance_skim_tod
    if tod in distance_skim_tod:
        my_skim_matrix_designation = skim_matrix_designation_limited + skim_matrix_designation_all_tods
    else:
        my_skim_matrix_designation = skim_matrix_designation_all_tods

    for x in range (0, len(my_skim_matrix_designation)):

        for y in range (0, len(matrix_dict["Highway"])):
                matrix_name= matrix_dict["Highway"][y]["Name"]+my_skim_matrix_designation[x]
                matrix_id = my_bank.matrix(matrix_name).id
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
                my_store["Skims"][tod].create_dataset(matrix_name, data=matrix_value.astype('int16'),compression='gzip')
                print matrix_name+' was transferred to the HDF5 container.'
        #transit
    if tod in transit_skim_tod:
        for item in transit_submodes:
            matrix_name= 'ivtwa' + item
            matrix_id = my_bank.matrix(matrix_name).id
            matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
            print matrix_name
            my_store["Skims"][tod].create_dataset(matrix_name, data=matrix_value.astype('int16'),compression='gzip')
            print matrix_name+' was transferred to the HDF5 container.'

                #Transit, All Modes:
            dct_aggregate_transit_skim_names = json_to_dictionary('transit_skim_aggregate_matrix_names')

        for key, value in dct_aggregate_transit_skim_names.iteritems():
            matrix_name= key
            matrix_id = my_bank.matrix(matrix_name).id
            matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
            my_store["Skims"][tod].create_dataset(matrix_name, data=matrix_value.astype('int16'),compression='gzip')
            print matrix_name+' was transferred to the HDF5 container.'

    if tod in bike_walk_skim_tod:
        for key in bike_walk_matrix_dict.keys():
            matrix_name= bike_walk_matrix_dict[key]['time']
            matrix_id = my_bank.matrix(matrix_name).id
            matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100
            my_store["Skims"][tod].create_dataset(matrix_name, data=matrix_value.astype('int16'),compression='gzip')
            print matrix_name+' was transferred to the HDF5 container.'


    my_store.close()
    end_export_hdf5 = time.time()

    print 'It took', round((end_export_hdf5-start_export_hdf5)/60,2), 'minutes to export all skims to the HDF5 File.'
def hdf5_to_emme(my_project):

    start_import_hdf5 = time.time()

    #Determine the Path and Scenario File and Zone indicies that go with it
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank
    zones=current_scenario.zone_numbers
    bank_name = my_project.emmebank.title

    #Load in the necessary Dictionaries
    my_user_classes = json_to_dictionary("user_classes")

    #Open the HDF5 Container in read only mode using "r"
    hdf_filename = os.path.join(os.path.dirname(my_bank.path), 'Skims/Emme_Skims.hdf5').replace("\\","/")
    hdf_file = h5py.File(hdf_filename, "r")

    #Delimiter of a Demand Matrix in Emme - this could be part of a control file but hardcoded for now
    tod = bank_name

    for x in range (0, len(my_user_classes["Highway"])):
        matrix_name= my_user_classes["Highway"][x]["Name"]
        matrix_id = my_bank.matrix(matrix_name).id

        try:
            hdf_matrix = hdf_file['Emme']['Highway'][tod][matrix_name]
            np_matrix = np.matrix(hdf_matrix)
            np_matrix = np_matrix.astype(float)
            np_array = np.squeeze(np.asarray(np_matrix))
            emme_matrix = ematrix.MatrixData(indices=[zones,zones],type='f')
            emme_matrix.raw_data=[_array.array('f',row) for row in np_array]
            my_bank.matrix(matrix_id).set_data(emme_matrix,current_scenario)

        #If the HDF5 File does not have a matirx of that name
        except KeyError:

            print matrix_id+' does not exist in the HDF5 container - no matrix was imported'

    hdf_file.close()
    end_import_hdf5 = time.time()

    print 'It took', round((end_import_hdf5-start_import_hdf5)/60,2), 'minutes to import matrices to Emme.'



def hdf5_trips_to_Emme(my_project, hdf_filename):

    start_time = time.time()


    #Determine the Path and Scenario File and Zone indicies that go with it
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank
    zonesDim=len(current_scenario.zone_numbers)
    zones=current_scenario.zone_numbers
    bank_name = my_project.emmebank.title
    print bank_name

    #create an index of trips for this TOD. This prevents iterating over the entire array (all trips).
    tod_index = create_trip_tod_indices(bank_name)


    #Create the HDF5 Container if needed and open it in read/write mode using "r+"

    my_store=h5py.File(hdf_filename, "r+")


    #Read the Matrix File from the Dictionary File and Set Unique Matrix Names
    matrix_dict = text_to_dictionary('demand_matrix_dictionary')
    uniqueMatrices = set(matrix_dict.values())

    #Read the Time of Day File from the Dictionary File and Set Unique TOD List
    #tod_dict = text_to_dictionary('time_of_day')
    #uniqueTOD = set(tod_dict.values())
    #uniqueTOD = list(uniqueTOD)

    #Read the Mode File from the Dictionary File
    mode_dict = text_to_dictionary('modes')

    #Stores in the HDF5 Container to read or write to
    daysim_set = my_store['Trip']

    #Store arrays from Daysim/Trips Group into numpy arrays, indexed by TOD.
    #This means that only trip info for the current Time Period will be included in each array.
    otaz = np.asarray(daysim_set["otaz"])
    otaz = otaz.astype('int')
    otaz = otaz[tod_index]



    dtaz = np.asarray(daysim_set["dtaz"])
    dtaz = dtaz.astype('int')
    dtaz = dtaz[tod_index]


    mode = np.asarray(daysim_set["mode"])
    mode = mode.astype("int")
    mode = mode[tod_index]

    trexpfac = np.asarray(daysim_set["trexpfac"])
    trexpfac = trexpfac.astype('float')
    trexpfac = trexpfac[tod_index]

    if not seed_trips:
        vot = np.asarray(daysim_set["vot"])
        vot = vot[tod_index]


    deptm = np.asarray(daysim_set["deptm"])
    deptm =deptm[tod_index]

    dorp = np.asarray(daysim_set["dorp"])
    dorp = dorp.astype('int')
    dorp = dorp[tod_index]

    toll_path = np.asarray(daysim_set["pathtype"])
    toll_path = toll_path.astype('int')
    toll_path = toll_path[tod_index]

    my_store.close

    #create & store in-memory numpy matrices in a dictionary. Key is matrix name, value is the matrix
    demand_matrices={}
    if seed_trips:
        for matrices in uniqueMatrices:
             #demand_matrices.update({matrices:np.zeros( (zonesDim,zonesDim), np.float16 )})
             demand_matrices.update({matrices:np.zeros( (zonesDim,zonesDim), np.uint16 )})
    else: 
        for matrices in uniqueMatrices:
             demand_matrices.update({matrices:np.zeros( (zonesDim,zonesDim), np.uint16 )})

    #Start going through each trip & assign it to the correct Matrix. Using Otaz, but array length should be same for all
    #The correct matrix is determined using a tuple that consists of (mode, vot, toll path). This tuple is the key in matrix_dict.

    for x in range (0, len(otaz)):
        #Start building the tuple key, 3 VOT of categories...
        if seed_trips:
            vot = 2
            if mode[x]<7:
                mat_name = matrix_dict[mode[x], vot, toll_path[x]]

                if dorp[x] <= 1:
                    #account for zero based numpy matrices
                    myOtaz = otaz[x] - 1
                    myDtaz = dtaz[x] - 1
                    demand_matrices[mat_name][int(myOtaz), int(myDtaz)] = demand_matrices[mat_name][int(myOtaz), int(myDtaz)] + trexpfac[x]
            
        else:
            if vot[x] < 2.50: vot[x]=1
            elif vot[x] < 8.00: vot[x]=2
            else: vot[x]=3

        #get the matrix name from matrix_dict. Throw out school bus (8) for now.
            if mode[x]<8:
                #Only want drivers, transit trips.
                if dorp[x] <= 1:
                    mat_name = matrix_dict[(int(mode[x]),int(vot[x]),int(toll_path[x]))]
                    #account for zero based numpy matrices
                    myOtaz = otaz[x] - 1
                    myDtaz = dtaz[x] - 1
                    
                    #add the trip
                    demand_matrices[mat_name][int(myOtaz), int(myDtaz)] = demand_matrices[mat_name][int(myOtaz), int(myDtaz)] + 1

           #all in-memory numpy matrices populated, now write out to emme
    if seed_trips:
        for matrix in demand_matrices.itervalues():
            matrix = matrix.astype(np.uint16)
    for mat_name in uniqueMatrices:
        print mat_name
        matrix_id = my_bank.matrix(str(mat_name)).id
        np_array = demand_matrices[mat_name]
        emme_matrix = ematrix.MatrixData(indices=[zones,zones],type='f')
        emme_matrix.raw_data=[_array.array('f',row) for row in np_array]
        my_bank.matrix(matrix_id).set_data(emme_matrix,current_scenario)

    end_time = time.time()

    print 'It took', round((end_time-start_time)/60,2), 'minutes to export all skims to the HDF5 File.'

def create_trip_tod_indices(tod):
     #creates an index for those trips that belong to tod (time of day)

     tod_dict = text_to_dictionary('time_of_day')
     uniqueTOD = set(tod_dict.values())
     todIDListdict = {}
     #this creates a dictionary where the TOD string, e.g. 18to20, is the key, and the value is a list of the hours for that period, e.g [18, 19, 20]
     for k, v in tod_dict.iteritems():
        todIDListdict.setdefault(v, []).append(k)

     #Now for the given tod, get the index of all the trips for that Time Period
     my_store=h5py.File(hdf5_file_path, "r+")
     daysim_set = my_store["Trip"]
     #open departure time array
     deptm = np.asarray(daysim_set["deptm"])
     if seed_trips:
        deptm = deptm.astype('float')
        deptm = deptm / 60
        deptm = deptm.astype('int')
     else:
        #convert to hours
        deptm = deptm.astype('float')
        deptm = deptm/60
        deptm = deptm.astype('int')
     #Get the list of hours for this tod

     todValues = todIDListdict[tod]
     # ix is an array of true/false
     ix = np.in1d(deptm.ravel(), todValues)
     #An index for trips from this tod, e.g. [3, 5, 7) means that there are trips from this time period from the index 3, 5, 7 (0 based) in deptm
     indexArray = np.where(ix)

     return indexArray
     my_store.close


def start_pool(project_list):
    #An Emme databank can only be used by one process at a time. Emme Modeler API only allows one instance of Modeler and
    #it cannot be destroyed/recreated in same script. In order to run things con-currently in the same script, must have
    #seperate projects/banks for each time period and have a pool for each project/bank.
    #Fewer pools than projects/banks will cause script to crash.

    #Doing some testing on best approaches to con-currency
    pool = Pool(processes=12)
    pool.map(run_assignments_parallel,project_list[0:12])




def start_transit_pool(project_list):
    #Transit assignments/skimming seem to do much better running sequentially (not con-currently). Still have to use pool to get by the one
    #instance of modeler issue. Will change code to be more generalized later.
    pool = Pool(processes=1)
    pool.map(run_transit,project_list[1:2])

    pool = Pool(processes=1)
    pool.map(run_transit,project_list[2:3])

    pool = Pool(processes=1)
    pool.map(run_transit,project_list[3:4])

    pool = Pool(processes=1)
    pool.map(run_transit,project_list[4:5])


def run_transit(project_name):
    start_of_run = time.time()

    my_desktop = app.start_dedicated(True, "cth", project_name)
    print project_name
    m = _m.Modeller(my_desktop)
    my_bank = m.emmebank
    transit_assignment(m)
    transit_skims(m)

    #Calc Wait Times
    app.App.refresh_data
    matrix_calculator = json_to_dictionary("matrix_calculation")
    matrix_calc = m.tool("inro.emme.matrix_calculation.matrix_calculator")

    #Hard coded for now, generalize later
    total_wait_matrix = my_bank.matrix('twtwa').id
    initial_wait_matrix = my_bank.matrix('iwtwa').id
    transfer_wait_matrix = my_bank.matrix('xfrwa').id

    mod_calc = matrix_calculator
    mod_calc["result"] = transfer_wait_matrix
    mod_calc["expression"] = total_wait_matrix + "-" + initial_wait_matrix
    matrix_calc(mod_calc)

def export_to_hdf5_pool(project_list):

    pool = Pool(processes=1)
    pool.map(start_export_to_hdf5, project_list[0:1])
    pool.close()

def start_export_to_hdf5(test):

    my_desktop = app.start_dedicated(True, "cth", test)
    m = _m.Modeller(my_desktop)
    #app.App.refresh_data
    skims_to_hdf5(m)
    print 'done'


def bike_walk_assignment(my_project, tod, assign_for_all_tods):
    #One bank
    #this runs the assignment and produces a time skim as well, which we need is all we need- converted
    #to distance in Daysim.
    #Assignment is run for all time periods (at least it should be for the final iteration). Only need to
    #skim for one TOD. Skim is an optional output of the assignment.

    start_transit_assignment = time.time()
    my_bank = my_project.emmebank
    #Define the Emme Tools used in this function
    assign_transit = my_project.tool("inro.emme.transit_assignment.standard_transit_assignment")

    #Load in the necessary Dictionaries


    assignment_specification = json_to_dictionary("bike_walk_assignment")
    #get demand matrix name from here:
    user_classes = json_to_dictionary("user_classes")
    mod_assign = assignment_specification
    #only skim for time for certain tod
    #Also fill in intrazonals
    matrix_calculator = json_to_dictionary("matrix_calculation")
    matrix_calc = my_project.tool("inro.emme.matrix_calculation.matrix_calculator")
    intrazonal_dict

    if tod in bike_walk_skim_tod:
        for key in bike_walk_matrix_dict.keys():
            mod_assign['demand'] = 'mf' + bike_walk_matrix_dict[key]['demand']
            mod_assign['od_results']['transit_times'] = bike_walk_matrix_dict[key]['time']
            mod_assign['modes'] = bike_walk_matrix_dict[key]['modes']
            assign_transit(mod_assign)

            #intrazonal
            matrix_name= bike_walk_matrix_dict[key]['intrazonal_time']
            matrix_id = my_bank.matrix(matrix_name).id
            mod_calc = matrix_calculator
            mod_calc["result"] = 'mf' + bike_walk_matrix_dict[key]['time']
            mod_calc["expression"] = 'mf' + bike_walk_matrix_dict[key]['time'] + "+" + matrix_id
            matrix_calc(mod_calc)
    elif assign_for_all_tods == 'true':
        #Dont Skim
        for key in bike_walk_matrix_dict.keys():
            mod_assign['demand'] = bike_walk_matrix_dict[key]['demand']
            mod_assign['modes'] = bike_walk_matrix_dict[key]['modes']
            assign_transit(mod_assign)


    end_transit_assignment = time.time()
    print 'It took', round((end_transit_assignment-start_transit_assignment)/60,2), 'minutes to run the bike/walk assignment.'

def bike_walk_assignment_NonConcurrent(project_name):
    #One bank
    #this runs the assignment and produces a time skim as well, which we need is all we need- converted
    #to distance in Daysim.
    #Assignment is run for all time periods (at least it should be for the final iteration). Only need to
    #skim for one TOD. Skim is an optional output of the assignment.
    tod_dict = text_to_dictionary('time_of_day')
    uniqueTOD = set(tod_dict.values())
    uniqueTOD = list(uniqueTOD)

    #populate a dictionary of with key=bank name, value = emmebank object
    data_explorer = project_name.desktop.data_explorer()
    all_emmebanks = {}
    for database in data_explorer.databases():
        emmebank = database.core_emmebank
        all_emmebanks.update({emmebank.title: emmebank})
    start_transit_assignment = time.time()

    #Define the Emme Tools used in this function

    for tod in uniqueTOD:

        print tod
        my_bank = all_emmebanks[tod]
        #need a scenario, get the first one
        current_scenario = list(my_bank.scenarios())[0]
        #Determine the Path and Scenario File

        zones=current_scenario.zone_numbers
        bank_name = my_bank.title


        assign_transit = project_name.tool("inro.emme.transit_assignment.standard_transit_assignment")

    #Load in the necessary Dictionaries


        assignment_specification = json_to_dictionary("bike_walk_assignment")
        #get demand matrix name from here:
        user_classes = json_to_dictionary("user_classes")
        mod_assign = assignment_specification
        #only skim for time for certain tod
        if tod in bike_walk_skim_tod:
            for key in bike_walk_matrix_dict.keys():
                mod_assign['demand'] = bike_walk_matrix_dict[key]['demand']
                print bike_walk_matrix_dict[key]['time']
                mod_assign['od_results']['transit_times'] = bike_walk_matrix_dict[key]['time']
                mod_assign['modes'] = bike_walk_matrix_dict[key]['modes']
                assign_transit(mod_assign)
        else:
            #Dont Skim
            for key in bike_walk_matrix_dict.keys():
                mod_assign['demand'] = bike_walk_matrix_dict[key]['demand']
                mod_assign['modes'] = bike_walk_matrix_dict[key]['modes']
                assign_transit(mod_assign)


    end_transit_assignment = time.time()
    print 'It took', round((end_transit_assignment-start_transit_assignment)/60,2), 'minutes to run the bike/walk assignment.'

def run_assignments_parallel(project_name):

    start_of_run = time.time()


    my_desktop = app.start_dedicated(True, "cth", project_name)
    m = _m.Modeller(my_desktop)



    #delete and create new demand and skim matrices:
    delete_matrices(m, "FULL")
    delete_matrices(m, "ORIGIN")


    define_matrices(m)

    #Import demand/trip tables to emme. This is actually quite fast con-currently.
    hdf5_trips_to_Emme(m, hdf5_file_path)
    tod = m.emmebank.title
    populate_intrazonals(m)
    #create transit fare matrices:
    if tod in fare_matrices_tod:
        fare_file = fare_dict[tod]['Files']['fare_box_file']
        #fare box:
        create_fare_zones(m, zone_file, fare_file)
        #monthly:
        fare_file = fare_dict[tod]['Files']['monthly_pass_file']
        create_fare_zones(m, zone_file, fare_file)

    #set up for assignments
    intitial_extra_attributes(m)
    import_extra_attributes(m)
    arterial_delay_calc(m)
    vdf_initial(m)


    #run auto assignment/skims
    traffic_assignment(m)
    attribute_based_skims(m, "Time")

    #get tod from bank name.

    #bike/walk:
    bike_walk_assignment(m, tod, 'false')
    #Only skim for distance if in global distance_skim_tod list
    if tod in distance_skim_tod:
        attribute_based_skims(m,"Distance")

    #Toll skims
    attribute_based_toll_cost_skims( m, "@toll1")
    attribute_based_toll_cost_skims( m, "@toll2")
    attribute_based_toll_cost_skims( m, "@toll3")
    class_specific_volumes(m)


    #skims_to_hdf5_concurrent(m)
    app.App.refresh_data
    print tod + " finished"
    end_of_run = time.time()
    print 'It took', round((end_of_run-start_of_run)/60,2), 'minutes to execute all processes for ' + tod

def main():
    #Start Daysim-Emme Equilibration
    #This code is organized around the time periods for which we run assignments, often represented by the variable tod. This variable will always
    #represent a Time of Day string, such as 6to7, 7to8, 9to10, etc.
    for x in range(0, global_iterations):
        start_of_run = time.time()
        project_list=['Projects/5to6/5to6.emp',
                      'Projects/6to7/6to7.emp',
                      'Projects/7to8/7to8.emp',
                      'Projects/8to9/8to9.emp',
                      'Projects/9to10/9to10.emp',
                      'Projects/10to14/10to14.emp',
                      'Projects/14to15/14to15.emp',
                      'Projects/15to16/15to16.emp',
                      'Projects/16to17/16to17.emp',
                      'Projects/17to18/17to18.emp',
                      'Projects/18to20/18to20.emp',
                      'Projects/20to5/20to5.emp' ]



        #want pooled processes finished before executing more code in main:
       

        start_pool(project_list)
        start_transit_pool(project_list)


        #Tried exporting skims to hdf5 concurrently, by using a HDF5 file for each
        #time period, and then merging them all to one HDF5 file at the end, but
        #this was signigicantly slower than writing out sequentially. Below we are able to
        #launch another instance of modeler because the others were launched/closed
        #in their own pool/process.

        #This project points to all TOD Banks:
        export_project_list = ['Projects/LoadTripTables/LoadTripTables.emp']
        export_to_hdf5_pool(export_project_list)

        end_of_run = time.time()

        print "Emme Skim Creation and Export to HDF5 completed normally"
        print 'The Total Time for all processes took', round((end_of_run-start_of_run)/60,2), 'minutes to execute.'


if __name__ == "__main__":
    main()

