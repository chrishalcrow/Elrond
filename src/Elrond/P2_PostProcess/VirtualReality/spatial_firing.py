import numpy as np
import pandas as pd
import Elrond.settings as settings
from astropy.convolution import convolve, Gaussian1DKernel


def add_kinematics(spike_data, position_data):
    if "speed_as_read_by_blender" in list(position_data):
        position_data["speed_per200ms"] = position_data["speed_as_read_by_blender"]
    position_sampling_rate = float(1/np.mean(np.diff(position_data["time_seconds"])))

    x_position_cm = []
    speed_per200ms = []
    trial_number = []
    trial_type = []
    for _, cluster_data in spike_data.iterrows():
        cluster_firing_indices = np.asarray(cluster_data.firing_times)
        cluster_firing_seconds = cluster_firing_indices/settings.sampling_rate
        cluster_firing_position_data_indices = np.array(np.round(cluster_firing_seconds*position_sampling_rate), dtype=np.int64)
 
        x_position_cm.append(position_data["x_position_cm"][cluster_firing_position_data_indices].to_list())
        speed_per200ms.append(position_data["speed_per200ms"][cluster_firing_position_data_indices].to_list())
        trial_number.append(position_data["trial_number"][cluster_firing_position_data_indices].to_list())
        trial_type.append(position_data["trial_type"][cluster_firing_position_data_indices].to_list())

    spike_data["speed_per200ms"] = speed_per200ms
    spike_data["x_position_cm"] = x_position_cm
    spike_data["trial_number"] = trial_number
    spike_data["trial_type"] = trial_type
    return spike_data


def bin_fr_in_time(spike_data, position_data, track_length, smoothen=True):
    if smoothen:
        suffix="_smoothed"
    else:
        suffix=""

    gauss_kernel = Gaussian1DKernel(settings.guassian_std_for_smoothing_in_time_seconds/settings.time_bin_size)
    n_trials = max(position_data["trial_number"])

    # make an empty list of list for all firing rates binned in time for each cluster
    fr_binned_in_time = [[] for x in range(len(spike_data))]
    fr_binned_in_time_bin_centres = [[] for x in range(len(spike_data))]

    # extract spatial variables from position
    times = np.array(position_data['time_seconds'], dtype="float64")
    trial_numbers_raw = np.array(position_data['trial_number'], dtype=np.int64)
    x_position_elapsed_cm = (track_length*(trial_numbers_raw-1))+np.array(position_data['x_position_cm'], dtype="float64")

    # calculate the average fr in each 100ms time bin
    time_bins = np.arange(min(times), max(times), settings.time_bin_size) # 100ms time bins
    tn_time_bin_means = (np.histogram(times, time_bins, weights = trial_numbers_raw)[0] / np.histogram(times, time_bins)[0]).astype(np.int64)
    x_elapsed_bin_means = (np.histogram(times, time_bins, weights = x_position_elapsed_cm)[0] / np.histogram(times, time_bins)[0])
    x_bin_means = x_elapsed_bin_means%track_length
    
    for i, cluster_data in spike_data.iterrows():
        if len(time_bins)>1:
            spike_times = np.asarray(cluster_data.firing_times)/settings.sampling_rate # convert to seconds  

            # count the spikes in each time bin and normalise to seconds
            fr_time_bin_means, bin_edges = np.histogram(spike_times, time_bins)
            fr_time_bin_means = fr_time_bin_means/settings.time_bin_size

            # and smooth
            if smoothen:
                fr_time_bin_means = convolve(fr_time_bin_means, gauss_kernel)
 
            # fill in firing rate array by trial
            fr_binned_in_time_cluster = []
            fr_binned_in_time_bin_centres_cluster = []
            for trial_number in range(1, n_trials+1):
                fr_binned_in_time_cluster.append(fr_time_bin_means[tn_time_bin_means == trial_number].tolist())
                fr_binned_in_time_bin_centres_cluster.append(x_bin_means[tn_time_bin_means == trial_number].tolist())
            fr_binned_in_time[i] = fr_binned_in_time_cluster
            fr_binned_in_time_bin_centres[i] = fr_binned_in_time_bin_centres_cluster
        else:
            fr_binned_in_time[i] = []
            fr_binned_in_time_bin_centres[i] = []

    spike_data["fr_time_binned"+suffix] = fr_binned_in_time
    spike_data["fr_time_binned_bin_centres"] = fr_binned_in_time_bin_centres
    return spike_data


def bin_fr_in_space(spike_data, position_data, track_length, smoothen=True):
    if smoothen:
        suffix="_smoothed"
    else:
        suffix=""

    vr_bin_size_cm = settings.vr_bin_size_cm
    gauss_kernel = Gaussian1DKernel(settings.guassian_std_for_smoothing_in_space_cm/vr_bin_size_cm)

    # make an empty list of list for all firing rates binned in time for each cluster
    fr_binned_in_space = [[] for x in range(len(spike_data))]
    fr_binned_in_space_bin_centres = [[] for x in range(len(spike_data))]

    elapsed_distance_bins = np.arange(0, (track_length*max(position_data["trial_number"]))+1, vr_bin_size_cm) # might be buggy with anything but 1cm space bins
    trial_numbers_raw = np.array(position_data['trial_number'], dtype=np.int64)
    x_position_elapsed_cm = (track_length*(trial_numbers_raw-1))+np.array(position_data['x_position_cm'], dtype="float64")
    x_dwell_time = np.array(position_data['dwell_time_ms'], dtype="float64")
 
    for i, cluster_data in spike_data.iterrows():
        if len(elapsed_distance_bins)>1:
            spikes_x_position_cm = np.asarray(cluster_data.x_position_cm)
            trial_numbers = np.asarray(cluster_data.trial_number)

            # convert spike locations into elapsed distance
            spikes_x_position_elapsed_cm = (track_length*(trial_numbers-1))+spikes_x_position_cm

            # count the spikes in each space bin and normalise by the total time spent in that bin for the trial
            fr_hist, bin_edges = np.histogram(spikes_x_position_elapsed_cm, elapsed_distance_bins)
            fr_hist = fr_hist/(np.histogram(x_position_elapsed_cm, elapsed_distance_bins, weights=x_dwell_time)[0])

            # get location bin centres and ascribe them to their trial numbers
            bin_centres = 0.5*(bin_edges[1:]+bin_edges[:-1])
            bin_centres_trial_numbers = (bin_centres//track_length).astype(np.int64)+1

            # nans to zero and smooth
            if smoothen:
                fr_hist = convolve(fr_hist, gauss_kernel)

            # fill in firing rate array by trial
            fr_binned_in_space_cluster = []
            fr_binned_in_space_bin_centres_cluster = []
            for trial_number in range(1, max(position_data["trial_number"]+1)):
                fr_binned_in_space_cluster.append(fr_hist[bin_centres_trial_numbers==trial_number].tolist())
                fr_binned_in_space_bin_centres_cluster.append(bin_centres[bin_centres_trial_numbers==trial_number].tolist())

            fr_binned_in_space[i] = fr_binned_in_space_cluster
            fr_binned_in_space_bin_centres[i] = fr_binned_in_space_bin_centres_cluster
        else:
            fr_binned_in_space[i] = []
            fr_binned_in_space_bin_centres[i] = []

    spike_data["fr_binned_in_space"+suffix] = fr_binned_in_space
    spike_data["fr_binned_in_space_bin_centres"] = fr_binned_in_space_bin_centres

    return spike_data 


def add_stops(spike_data, processed_position_data, track_length):
    trial_numbers = []
    stop_locations = []
    for tn in processed_position_data["trial_number"]:
        trial_processed_position_data = processed_position_data[processed_position_data["trial_number"] == tn]
        trial_stops = np.array(trial_processed_position_data["stop_location_cm"].iloc[0])
        trial_numbers_repeated = np.repeat(tn, len(trial_stops))

        stop_locations.extend(trial_stops.tolist())
        trial_numbers.extend(trial_numbers_repeated.tolist())

    cluster_trial_numbers = []
    cluster_stop_locations = []
    for index, row in spike_data.iterrows():
        cluster_trial_numbers.append(trial_numbers)
        cluster_stop_locations.append(stop_locations)

    spike_data["stop_locations"] = cluster_stop_locations
    spike_data["stop_trial_numbers"] = cluster_trial_numbers

    return spike_data


def add_location_and_task_variables(spike_data, position_data, processed_position_data, track_length):
    spike_data = add_kinematics(spike_data, position_data)
    spike_data = add_stops(spike_data, processed_position_data, track_length)
    spike_data = bin_fr_in_time(spike_data, position_data, track_length, smoothen=True)
    spike_data = bin_fr_in_time(spike_data, position_data, track_length, smoothen=False)
    spike_data = bin_fr_in_space(spike_data, position_data, track_length, smoothen=True)
    spike_data = bin_fr_in_space(spike_data, position_data, track_length, smoothen=False)
    return spike_data

#  for testing
def main():
    print('-------------------------------------------------------------')

if __name__ == '__main__':
    main()