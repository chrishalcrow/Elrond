import matplotlib.pylab as plt
import numpy as np
import PostSorting.open_field_firing_maps
import pandas as pd
import os
from scipy import signal
from Helpers import plot_utility, open_ephys_IO
import PostSorting.parameters
from PostSorting.load_firing_data import available_ephys_channels
import re
import Elrond.settings as settings
import matplotlib
from scipy import stats

def load_ephys_channel(recording_folder, ephys_channel):
    print('Extracting ephys data from channel ', str(ephys_channel))
    file_path = recording_folder + '/' + ephys_channel
    if os.path.exists(file_path):
        channel_data = open_ephys_IO.get_data_continuous(file_path)
    else:
        print('Movement data was not found.')
    return channel_data

def process_lfp(recording_folder, ephys_channels_list, output_path, dead_channels, sampling_rate=settings.sampling_rate):
    print("I am now processing the lfp")
    lfp_df = pd.DataFrame()

    frequencies = []
    power_spectra = []
    channels = []
    dead_channels_bool = []

    for i in range(len(ephys_channels_list)):
        dead_channel_bool = False

        ephys_channel = ephys_channels_list[i]
        ephys_channel_number = ephys_channel.split("_CH")[-1].split(".")[0]

        if ephys_channel_number in dead_channels:
            dead_channel_bool = True

        ephys_channel_data = load_ephys_channel(recording_folder, ephys_channel)
        f, power_spectrum_channel = signal.welch(ephys_channel_data, fs=sampling_rate, nperseg=50000, scaling='spectrum')

        frequencies.append(f)
        power_spectra.append(power_spectrum_channel)
        channels.append(int(ephys_channel_number))
        dead_channels_bool.append(dead_channel_bool)

    lfp_df["channel"] = channels
    lfp_df["frequencies"] = frequencies
    lfp_df["power_spectra"] = power_spectra
    lfp_df["dead_channel"] = dead_channels_bool

    plot_lfp(lfp_df, output_path)
    return lfp_df


def plot_lfp(lfp_df, output_path):

    save_path = output_path + '/Figures/lfp'
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)

    fig = plt.figure(figsize=(5,5))
    ax = fig.add_subplot(1, 1, 1)

    plt.ylabel('Power', fontsize=12, labelpad = 10)
    plt.xlabel('Frequency', fontsize=12, labelpad = 10)

    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    plot_utility.style_vr_plot(ax)
    cmap = matplotlib.cm.get_cmap('gnuplot2')
    max_y = 0
    for channel in np.unique(lfp_df["channel"]):
        channel_lfp = lfp_df[(lfp_df.channel == channel)].iloc[0]

        channel_freq = channel_lfp.frequencies
        channel_psd = channel_lfp.power_spectra

        if int(channel)%8==0:
            ax.plot(channel_freq[:35], (channel_psd*channel_freq)[:35], label="C"+str(channel), color=cmap(channel/len(lfp_df["channel"])))
        else:
            ax.plot(channel_freq[:35], (channel_psd * channel_freq)[:35], color=cmap(channel/len(lfp_df["channel"])))

        max_y_channel = np.max(channel_psd[:35]*channel_freq[:35])
        if max_y_channel > max_y:
            max_y = max_y_channel

    plt.legend(fontsize=8)
    plt.xlim(0, 20)
    plt.ylim(0, max_y)
    plt.subplots_adjust(hspace = .35, wspace = .35,  bottom = 0.2, left = 0.12, right = 0.87, top = 0.92)
    plt.savefig(output_path + '/Figures/lfp/channel_lfp.png', dpi=300)
    plt.close()

def process_batch_lfp(recordings):

    prm = PostSorting.parameters.Parameters()
    prm.set_sampling_rate(30000)
    prm.set_pixel_ratio(440)
    dead_channels = prm.get_dead_channels()
    prm.set_movement_channel('100_ADC2.continuous')
    prm.set_sync_channel('100_ADC1.continuous')

    for recording in recordings:

        prm.set_ephys_channels(PostSorting.load_firing_data.available_ephys_channels(recording_to_process=recording, prm=prm))
        directed_path = recording

        # flag dead channels
        prm.set_file_path(recording)
        prm.set_output_path(directed_path + "/MountainSort")
        dead_channel_txt_file_path = recording+"/dead_channels.txt"
        prm.set_dead_channel_from_txt_file(dead_channel_txt_file_path)
        prm.set_output_path(directed_path + "/MountainSort")
        empty_df_path = prm.get_output_path()+'/DataFrames/empty_df4.pkl'
        ephys_channels = prm.get_ephys_channels()
        output_path = directed_path + "/MountainSort"

        if os.path.exists(empty_df_path) is False:
            try:
                lfp_df = process_lfp(recording, ephys_channels, output_path, dead_channels)

                if os.path.exists(directed_path+"/MountainSort/DataFrames") is False:
                    os.makedirs(directed_path+"/MountainSort/DataFrames")
                lfp_df.to_pickle(directed_path+"/MountainSort/DataFrames/lfp_data.pkl")
                empty_df = pd.DataFrame()
                empty_df.to_pickle(empty_df_path)

            except:
                print("something is wrong with the file")
        else:
            print("lfp has already been processed, I won't do it again")

    print("============================================================Batch process is finished=========================================================")


def add_tetrode(df):
    tetrodes = []

    for index, row in df.iterrows():
        channel_string = row.channel
        channel_int = int(channel_string.split("CH")[-1].split(".continuous")[0])
        tetrode = np.ceil(channel_int/4)
        tetrodes.append(tetrode)

    df["tetrode"] = tetrodes
    return df

def remove_dead_channels(df):

    for index, row in df.iterrows():
        dead_channel = row.dead_channel
        if dead_channel == 1:
            df.power_spectra.iloc[index] *= np.nan

    return df

def stack_collumn_into_np(df, collumn):
    collumn_tmp = []

    for index, row in df.iterrows():
        tmp = row[collumn]
        collumn_tmp.append(tmp)


    return np.array(collumn_tmp)

def correct_dead_channel(lfp_df, dead_channel_path):

    if os.path.exists(dead_channel_path):
        dead_channel_reader = open(dead_channel_path, 'r')
        dead_channels = dead_channel_reader.readlines()
        dead_channels = list([x.strip() for x in dead_channels])

        dead_channel = []
        for index, row in lfp_df.iterrows():
            channel_string = row.channel
            channel_int = str(channel_string.split("CH")[-1].split(".continuous")[0])
            if channel_int in dead_channels:
                dead_channel.append(1)
            else:
                dead_channel.append(0)

        lfp_df["dead_channel"] = dead_channel
    return lfp_df

def batch_summary_lfp(recordings, add_to=None, average_over_tetrode=True):

    lfp_summary_df = pd.DataFrame()
    mice_ids = []
    timestamps = []
    freqs = []
    pwr_specs = []
    lfp_data_paths = []
    tetrodes = []
    trial_numbers = []

    for recording in recordings:
        lfp_data_path = recording+"/MountainSort/DataFrames/lfp_data.pkl"

        # look for processed position data if the recording is a vr recording
        processed_position_data_path = recording+"/MountainSort/DataFrames/processed_position_data.pkl"
        n_trials=0
        if os.path.exists(processed_position_data_path):
            processed_position_data = pd.read_pickle(processed_position_data_path)
            n_trials = len(processed_position_data)

        dead_channel_path = recording+"/dead_channels.txt"

        if os.path.exists(lfp_data_path):
            lfp_df = pd.read_pickle(lfp_data_path)
            lfp_df = correct_dead_channel(lfp_df, dead_channel_path)

            if average_over_tetrode:
                lfp_df = add_tetrode(lfp_df)
                lfp_df = remove_dead_channels(lfp_df)

                for i in range(int(len(lfp_df)/4)):
                    tetrode = i+1

                    lfp_data_tetrode = lfp_df[(lfp_df.tetrode == tetrode)]

                    frequencies = lfp_data_tetrode.frequencies.iloc[0]

                    power_spec_tmp = stack_collumn_into_np(lfp_data_tetrode, collumn="power_spectra")
                    avg_power_spec = np.nanmean(power_spec_tmp, axis=0)

                    frequencies_to_interpolate = np.linspace(0, 20, 21)
                    spec_interp = np.interp(x=frequencies_to_interpolate, xp=frequencies, fp=avg_power_spec)

                    mouse_id = recording.split("/")[-1].split("_")[0]
                    timestamp_year = recording.split("/")[-1].split("-")[0].split("_")[-1]
                    time_stamp_month = recording.split(timestamp_year)[-1][0:15]
                    time_stamp = timestamp_year+time_stamp_month
                    time_stamp = re.findall("\d+", time_stamp)
                    time_stamp = "".join(time_stamp)

                    if time_stamp != "":
                        trial_numbers.append(n_trials)
                        mice_ids.append(mouse_id)
                        timestamps.append(time_stamp)
                        freqs.append(frequencies_to_interpolate)
                        pwr_specs.append(spec_interp)
                        lfp_data_paths.append(lfp_data_path)
                        tetrodes.append(tetrode)

            else:
                print("no lfp_data.pkl was found at "+lfp_data_path)

    lfp_summary_df["mice_id"] = mice_ids
    lfp_summary_df["timestamp"] = timestamps
    lfp_summary_df["freqs"] = freqs
    lfp_summary_df["pwr_specs"] = pwr_specs
    lfp_summary_df["lfp_path"] = lfp_data_paths
    lfp_summary_df["tetrode"] = tetrodes
    lfp_summary_df["trial_numbers"] = trial_numbers


    for unique_mouse_id in np.unique(lfp_summary_df["mice_id"]):
        mouse_lfp_summary_df = lfp_summary_df[(lfp_summary_df.mice_id == unique_mouse_id)]
        plot_lfp_summary(mouse_lfp_summary_df)

    if add_to is not None:
        return pd.concat([add_to, lfp_summary_df])
    else:
        return lfp_summary_df

def plot_lfp_summary(mouse_lfp_summary_df):
    save_path_tmp1 = mouse_lfp_summary_df.lfp_path.iloc[0].split("/")[-4]
    save_path = mouse_lfp_summary_df.lfp_path.iloc[0].split(save_path_tmp1)[0]

    # order by time
    mouse_lfp_summary_df = mouse_lfp_summary_df.sort_values(by=["timestamp"], ascending=True)

    spec_per_tetrode = []
    for tetrode in np.unique(mouse_lfp_summary_df.tetrode):
        mouse_tetrode_lfp_summary_df = mouse_lfp_summary_df[(mouse_lfp_summary_df.tetrode == tetrode)]
        freqs = stack_collumn_into_np(mouse_tetrode_lfp_summary_df, collumn="freqs")
        pwr_specs = stack_collumn_into_np(mouse_tetrode_lfp_summary_df, collumn="pwr_specs").T
        # z score per data to see the relative power
        for i in range(len(pwr_specs[0])):
            pwr_specs[:, i] = stats.zscore(pwr_specs[:, i], nan_policy='omit')

        cmap = plt.cm.get_cmap("inferno")
        cmap.set_bad(color='white')
        fig = plt.figure(figsize=(10,5))
        ax = fig.add_subplot(1, 1, 1)
        c = ax.imshow(pwr_specs, interpolation='none', cmap=cmap, origin='lower')
        clb = fig.colorbar(c, ax=ax, shrink=0.8)
        clb.mappable.set_clim(np.min(pwr_specs), np.max(pwr_specs))
        clb.set_label(label='Z-scored Power',size=20)
        clb.set_ticks([np.min(pwr_specs),  np.max(pwr_specs)])
        #clb.set_ticklabels(["0", r'$\geq$'+str(max_power)])
        clb.ax.tick_params(labelsize=15)
        plt.ylabel('Frequency (Hz)', fontsize=20, labelpad = 10)
        plt.xlabel('Recording Session', fontsize=20, labelpad = 10)
        #plt.xlim(0,20)
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        ax.set_yticks([1, 10, 20])
        ax.set_yticklabels(["1", "10", "20"])
        ax.set_xticks([0, 5, 10, 15, 20, 25, 30, 35, 40])
        ax.set_xticklabels(["1", "5", "10", "15", "20", "25", "30", "35", "40"])
        ax.set_xlim(0, len(pwr_specs[0,:])-1)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.subplots_adjust(hspace = .35, wspace = .35,  bottom = 0.2, left = 0.12, right = 0.87, top = 0.92)
        path= save_path +mouse_tetrode_lfp_summary_df.mice_id.iloc[0] +'_lfp_tetrode_' + str(tetrode)+'moving.png'
        if not np.any(np.isnan(pwr_specs)):
            plt.savefig(path, dpi=300)
        plt.close()

        spec_per_tetrode.append(pwr_specs)

    # plot average across all tetrodes
    spec_per_tetrode = np.array(spec_per_tetrode)
    pwr_specs = np.nanmean(spec_per_tetrode, axis=0)
    # z score per data to see the relative power
    for i in range(len(pwr_specs[0])):
        pwr_specs[:, i] = stats.zscore(pwr_specs[:, i])
    cmap = plt.cm.get_cmap("inferno")
    cmap.set_bad(color='white')
    fig = plt.figure(figsize=(10,5))
    ax = fig.add_subplot(1, 1, 1)
    c = ax.imshow(pwr_specs, interpolation='none', cmap=cmap, origin='lower')
    clb = fig.colorbar(c, ax=ax, shrink=0.8)
    clb.mappable.set_clim(np.min(pwr_specs), np.max(pwr_specs))
    clb.set_label(label='Power',size=20)
    clb.set_ticks([np.min(pwr_specs), np.max(pwr_specs)])
    #clb.set_ticklabels(["0", r'$\geq$'+str(max_power)])
    clb.ax.tick_params(labelsize=15)
    plt.ylabel('Frequency (Hz)', fontsize=20, labelpad = 10)
    plt.xlabel('Recording Session', fontsize=20, labelpad = 10)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    ax.set_yticks([1, 10, 20])
    ax.set_yticklabels(["1", "10", "20"])
    ax.set_xticks([0, 5, 10, 15, 20, 25, 30, 35, 40])
    ax.set_xticklabels(["1", "5", "10", "15", "20", "25", "30", "35", "40"])
    ax.set_xlim(0, len(pwr_specs[0,:])-1)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.subplots_adjust(hspace = .35, wspace = .35,  bottom = 0.2, left = 0.12, right = 0.87, top = 0.92)
    plt.savefig(save_path +mouse_tetrode_lfp_summary_df.mice_id.iloc[0] +'_lfp_tetrode_avg_moving.png', dpi=300)
    plt.close()

def main():
    print("------------------------")
    process_batch_lfp(recordings=["/mnt/datastore/Harry/Cohort9_february2023/of/M17_2023-05-16_15-43-04"])

if __name__ == '__main__':
    main()