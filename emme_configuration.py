﻿from input_configuration import *

###################################
# Assignment Criteria
################################### 
log_file_name = 'outputs/logs/skims_log.txt'
STOP_THRESHOLD = 0.026    # Global convergence criteria
parallel_instances = 12   # Number of simultaneous parallel processes. Must be a factor of 12.
max_iter = 50             # Max number of iterations for assignment
relative_gap = 0.0001      # Assignment Convergence Criteria
best_relative_gap = 0.00  # Set to zero, only using relative gap as criteria
normalized_gap = 0.00     # See above

pop_sample = [1, 1, 1, 1]
# Assignment Iterations (must be same length as pop_sample:
max_iterations_list = [100, 100, 100, 100, 100, 100, 100, 100, 100]
min_pop_sample_convergence_test = 10
shadow_work = [2, 1, 1, 1]
shadow_con = 30 #%RMSE for shadow pricing to consider being converged

###################################
# Zone Defintions
################################### 
MIN_EXTERNAL = 3733      #zone of externals (subtract 1 because numpy is zero-based)
MAX_EXTERNAL = 3750      #zone of externals (subtract 1 because numpy is zero-based)
HIGH_TAZ = 3700
LOW_PNR = 3751
HIGH_PNR = 4000

#####################################
# Network Import Settings
####################################
master_project = 'LoadTripTables'
project = 'Projects/LoadTripTables/LoadTripTables.emp'
network_summary_project = 'Projects/LoadTripTables/LoadTripTables.emp'
tod_networks = ['am', 'md', 'pm', 'ev', 'ni']
sound_cast_net_dict = {'5to6' : 'am', '6to7' : 'am', '7to8' : 'am', '8to9' : 'am', 
                       '9to10' : 'md', '10to14' : 'md', '14to15' : 'md', 
                       '15to16' : 'pm', '16to17' : 'pm', '17to18' : 'pm', 
                       '18to20' : 'ev', '20to5' : 'ni'}

transit_tod_list = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20']
extra_attributes_dict = {'@tveh' : 'total vehicles', 
                         '@mveh' : 'medium trucks', 
                         '@hveh' : 'heavy trucks', 
                         '@vmt' : 'vmt',
                         '@vht' : 'vht', 
                         '@trnv' : 'buses in auto equivalents',
                         '@ovol' : 'observed volume', 
                         '@bveh' : 'number of buses'}
                         
unit_of_length = 'mi'    # units of miles in Emme
rdly_factor = .25
coord_unit_length = 0.0001894    # network links measured in feet, converted to miles (1/5280)
main_log_file = 'soundcast_log.txt'

link_extra_attributes = ['@facilitytype', '@countyid', '@countid', '@is_managed', '@toll1', '@toll2', '@toll3', '@trkc1', '@trkc2', '@trkc3'] 
node_extra_attributes = ['@lr_walk','@hdwfr','@wait','@invt']

# VOT ranges for assignment classes
vot_1_max = 13.07    # VOT for User Class 1 < vot_1_max
vot_2_max = 26.14    # vot_1_max < VOT for User Class 2 < vot_2_max

# TNC fraction to assign
# Based on survey data from SANDAG for now
tnc_occupancy = {
  11: 1,    # non-AV, 1 passenger (+ driver)
  12: 0.5,    # non-AV, 2 passengers
  13: 0.3,    # non-AV 3.33 passengers on average
  21: 1,    # AV, 1 passenger
  22: 0.5,    # AV, 2 passenger
  23: 0.4    # AV, 3+ passengers
}

feedback_list = ['Banks/7to8/emmebank','Banks/17to18/emmebank']

# Time of day periods
tods = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20', '20to5' ]
project_list = ['Projects/' + tod + '/' + tod + '.emp' for tod in tods]

emme_matrix_subgroups = ['Highway', 'Walk', 'Bike', 'Transit', 'LightRail','Ferry','CommuterRail','PassengerFerry']

# Skim for time, cost
skim_matrix_designation_all_tods = ['t','c']  # Time (t) and direct cost (c) skims
skim_matrix_designation_limited = ['d']    # Distance skim

# Skim for distance for only these time periods
distance_skim_tod = ['7to8', '17to18']
generalized_cost_tod = ['7to8', '17to18']
gc_skims = {'medium_trucks' : 'metrk', 'heavy_trucks' : 'hvtrk', 'sov' : 'sov_inc2'}
truck_trips_h5_filename = 'outputs/trucks/truck_trips.h5'

# Bike/Walk Skims
bike_walk_skim_tod = ['5to6']

# Transit Inputs:
transit_skim_tod = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20']
transit_submodes = ['b', 'c', 'f', 'p', 'r']

transit_node_attributes = {'headway_fraction' : {'name' : '@hdwfr', 'init_value': .5}, 
                           'wait_time_perception' :  {'name' : '@wait', 'init_value': 2},
                           'in_vehicle_time' :  {'name' : '@invt', 'init_value': 1}}

transit_tod = {'5to6' : {'4k_tp' : 'am', 'num_of_hours' : 1},
               '6to7' : {'4k_tp' : 'am', 'num_of_hours' : 1}, 
               '7to8' :  {'4k_tp' : 'am', 'num_of_hours' : 1}, 
               '8to9' :  {'4k_tp' : 'am', 'num_of_hours' : 1}, 
               '9to10' : {'4k_tp' : 'md', 'num_of_hours' : 1}, 
               '10to14' : {'4k_tp' : 'md', 'num_of_hours' : 4}, 
               '14to15' : {'4k_tp' : 'md', 'num_of_hours' : 1},
               '15to16' : {'4k_tp' : 'pm', 'num_of_hours' : 1},
               '16to17' : {'4k_tp' : 'pm', 'num_of_hours' : 1},
               '17to18' : {'4k_tp' : 'pm', 'num_of_hours' : 1},
               '18to20' : {'4k_tp' : 'ev', 'num_of_hours' : 2}}           

# Transit Fare:
zone_file = 'inputs/scenario/networks/fares/transit_fare_zones.grt'
fare_matrices_tod = ['6to7', '9to10']

# Intrazonals
intrazonal_dict = {'distance' : 'izdist', 'time auto' : 'izatim', 'time bike' : 'izbtim', 'time walk' : 'izwtim'}
taz_area_file = 'inputs/model/intrazonals/taz_acres.in'
origin_tt_file = 'inputs/model/intrazonals/origin_tt.in'
destination_tt_file = 'inputs/model/intrazonals/destination_tt.in'

#################################
# Supplementals Settings
#################################

trip_table_loc = 'outputs/supplemental/7_balance_trip_ends.csv'
supplemental_project = 'projects/supplementals/supplementals.emp'
supplemental_output_dir = 'outputs/supplemental'

# Define gravity model coefficients
autoop = 16.75    # Auto operation costs (in hundreds of cents per mile?)
avotda = 0.0303    # VOT

#This is what you get if the model runs cleanly, but it's random:
good_thing = ["a cookie", "a run", "a puppy", "a seal sighting",  "a beer", "some sunshine", "a nap"]

#################################
# Integrated Run Settings
#################################
# Only required for integrated Urbans runs; leave as default for standard runs

# Root dir for all Soundcast runs
urbansim_skims_dir = r'E:\soundcast_root'

# Urbansim outputs dir
urbansim_outputs_dir = r'E:\opusgit\urbansim_data\data\psrc_parcel\2014SoundCastData\urbansim_outputs'