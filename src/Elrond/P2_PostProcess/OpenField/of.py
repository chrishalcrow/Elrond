from ..Shared.time_sync import *
from .spatial_data import *
from .spatial_firing import *
from .plotting import *

def process(recording_path, processed_path, **kwargs):

    # process and save position data
    position_data = process_position_data(recording_path, processed_path, **kwargs)
    position_data = synchronise_position_data_via_ADC_ttl_pulses(position_data, processed_path, recording_path)
    position_heat_map = get_position_heatmap(position_data)
    # save position data
    position_data.to_csv(processed_path + "position_data.csv")

    # process and save spatial spike data
    if "sorterName" in kwargs.keys():
        sorterName = kwargs["sorterName"]
    else:
        sorterName = settings.sorterName

    spike_data_path = processed_path + sorterName+"/spikes.pkl"
    if os.path.exists(spike_data_path):
        spike_data = pd.read_pickle(spike_data_path)
        spike_data = add_spatial_variables(spike_data, position_data)
        spike_data = add_scores(spike_data, position_data, position_heat_map)
        spike_data.to_pickle(spike_data_path)

        # make plots
        output_path = processed_path + sorterName + "/"
        plot_spikes_on_trajectory(spike_data, position_data, output_path)
        plot_coverage(position_heat_map, output_path)
        plot_firing_rate_maps(spike_data, output_path)
        plot_rate_map_autocorrelogram(spike_data, output_path)
        plot_polar_head_direction_histogram(spike_data, position_data, output_path)
        plot_firing_rate_vs_speed(spike_data, position_data, output_path)
        make_combined_figure(spike_data, output_path)
    else:
        print("I couldn't find spike data at ", spike_data_path)
    return
