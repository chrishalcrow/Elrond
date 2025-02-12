import pandas as pd
import Elrond.settings as settings
import warnings
import numpy as np
import umap
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE, Isomap
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy import interpolate
import joblib as jl
import cebra.datasets
from cebra import CEBRA
import cebra.integrations.plotly

from matplotlib.collections import LineCollection
from Helpers.array_utility import list_of_list_to_1d_numpy_array

def extract_fr_column(spike_data, column):
    column_data = []
    for i in range(len(spike_data)):
        column_data.append(list_of_list_to_1d_numpy_array(spike_data[column].iloc[i]))
    return np.array(column_data)


def compare_ldm(spike_data):
    fr_time_binned = extract_fr_column(spike_data, column="fr_time_binned_smoothed")
    x_time_binned = extract_fr_column(spike_data, column="fr_time_binned_bin_centres")

    # flip axis so its in form (n_samples, n_features)
    fr_time_binned = np.transpose(fr_time_binned)
    x_time_binned = np.transpose(x_time_binned)

    # Assuming the third column of X is the third variable
    third_variable = x_time_binned[:, 0]
    # Standardize the data
    scaler = StandardScaler()
    X_standardized = scaler.fit_transform(fr_time_binned)

    # Initialize PCA, t-SNE, UMAP, and Isomap
    pca = PCA(n_components=20)
    tsne = TSNE(n_components=2, random_state=0, perplexity=5)
    reducer = umap.UMAP(n_components=2)
    isomap = Isomap(n_components=2)

    # Fit and transform the data
    X_pca = pca.fit_transform(X_standardized)
    X_tsne = tsne.fit_transform(X_standardized)
    X_umap = reducer.fit_transform(X_standardized)
    X_isomap = isomap.fit_transform(X_standardized)
    X_pca_then_umap = reducer.fit_transform(X_pca)

    # Define the custom colormap using discrete colors
    colors = ['grey', 'yellow', 'green', 'orange', 'black']
    boundaries = [0, 30, 90, 110, 170, 200]
    custom_cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(boundaries, custom_cmap.N, clip=True)

    # Create a figure with 2x2 subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Plot PCA
    scatter_pca = axes[0, 0].scatter(X_pca[:, 0], X_pca[:, 1], c=third_variable, cmap=custom_cmap, norm=norm,alpha=0.05)
    axes[0, 0].set_title('PCA')
    axes[0, 0].set_xlabel('Component 1')
    axes[0, 0].set_ylabel('Component 2')
    axes[0, 0].set_xlim(-3, 2)

    # Plot t-SNE
    scatter_tsne = axes[0, 1].scatter(X_tsne[:, 0], X_tsne[:, 1], c=third_variable, cmap=custom_cmap, norm=norm,alpha=0.05)
    axes[0, 1].set_title('t-SNE')
    axes[0, 1].set_xlabel('Component 1')
    axes[0, 1].set_ylabel('Component 2')

    # Plot UMAP
    scatter_umap = axes[1, 0].scatter(X_umap[:, 0], X_umap[:, 1], c=third_variable, cmap=custom_cmap, norm=norm,alpha=0.05)
    axes[1, 0].set_title('UMAP')
    axes[1, 0].set_xlabel('Component 1')
    axes[1, 0].set_ylabel('Component 2')

    # Plot Isomap
    scatter_isomap = axes[1, 1].scatter(X_isomap[:, 0], X_isomap[:, 1], c=third_variable, cmap=custom_cmap, norm=norm,alpha=0.05)
    axes[1, 1].set_title('Isomap')
    axes[1, 1].set_xlabel('Component 1')
    axes[1, 1].set_ylabel('Component 2')

    # Plot PCA then UMAP
    scatter_pca_then_umap = axes[0,2].scatter(X_pca_then_umap[:, 0], X_pca_then_umap[:, 1], c=third_variable, cmap=custom_cmap, norm=norm,alpha=0.05)
    axes[0,2].set_title('PCA then UMAP')
    axes[0,2].set_xlabel('Component 1')
    axes[0,2].set_ylabel('Component 2')

    # Add a colorbar with alpha=1
    divider = make_axes_locatable(axes[1, 1])
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = plt.colorbar(scatter_pca_then_umap, cax=cax, label='Third Variable')
    cbar.set_alpha(1)
    cbar.draw_all()

    # Adjust the position of the colorbar
    cbar.ax.yaxis.set_ticks_position('left')
    cbar.ax.yaxis.set_label_position('left')

    # Show the plot
    plt.tight_layout()
    plt.savefig("/mnt/datastore/Harry/compare_pca_umap_tsne_discrete_colorbar.png", dpi=400)
    plt.close()

    # Create a figure with 2x2 subplots
    fig, axes = plt.subplots(2,3, figsize=(18, 12))

    # Plot PCA
    scatter_pca = axes[0, 0].scatter(X_pca[:, 0], X_pca[:, 1], c=third_variable, cmap='twilight_shifted',alpha=0.05)
    axes[0, 0].set_title('PCA')
    axes[0, 0].set_xlabel('Component 1')
    axes[0, 0].set_ylabel('Component 2')
    axes[0, 0].set_xlim(-3, 2)

    # Plot t-SNE
    scatter_tsne = axes[0, 1].scatter(X_tsne[:, 0], X_tsne[:, 1], c=third_variable, cmap='twilight_shifted',alpha=0.05)
    axes[0, 1].set_title('t-SNE')
    axes[0, 1].set_xlabel('Component 1')
    axes[0, 1].set_ylabel('Component 2')

    # Plot UMAP
    scatter_umap = axes[1, 0].scatter(X_umap[:, 0], X_umap[:, 1], c=third_variable, cmap='twilight_shifted',alpha=0.05)
    axes[1, 0].set_title('UMAP')
    axes[1, 0].set_xlabel('Component 1')
    axes[1, 0].set_ylabel('Component 2')

    # Plot Isomap
    scatter_isomap = axes[1, 1].scatter(X_isomap[:, 0], X_isomap[:, 1], c=third_variable, cmap='twilight_shifted',alpha=0.05)
    axes[1, 1].set_title('Isomap')
    axes[1, 1].set_xlabel('Component 1')
    axes[1, 1].set_ylabel('Component 2')

    # Plot PCA then UMAP
    scatter_pca_then_umap = axes[0,2].scatter(X_pca_then_umap[:, 0], X_pca_then_umap[:, 1], c=third_variable, cmap='twilight_shifted', norm=norm,alpha=0.05)
    axes[0,2].set_title('PCA then UMAP')
    axes[0,2].set_xlabel('Component 1')
    axes[0,2].set_ylabel('Component 2')

    # Add a colorbar with alpha=1
    divider = make_axes_locatable(axes[1, 1])
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = plt.colorbar(scatter_pca_then_umap, cax=cax, label='Pos(cm)')
    cbar.set_alpha(1)
    cbar.draw_all()

    # Adjust the position of the colorbar
    cbar.ax.yaxis.set_ticks_position('left')
    cbar.ax.yaxis.set_label_position('left')

    # Show the plot
    plt.tight_layout()
    plt.savefig("/mnt/datastore/Harry/compare_pca_umap_tsne.png", dpi=400)
    plt.close()
    return

def computer_behaviour_kinematics(position_data, xnew_length, xnew_time_bin_size, track_length):
    resampled_behavioural_data = pd.DataFrame()
    trial_numbers = np.array(position_data['trial_number'], dtype=np.int64)
    x_position_cm = np.array(position_data['x_position_cm'], dtype="float64")
    time_seconds = np.array(position_data['time_seconds'], dtype="float64")
    x_position_elapsed_cm = (track_length*(trial_numbers-1))+x_position_cm

    x = time_seconds
    y = x_position_elapsed_cm
    f = interpolate.interp1d(x, y)
    xnew = np.arange(xnew_time_bin_size/2, (xnew_length*xnew_time_bin_size)+xnew_time_bin_size, xnew_time_bin_size)
    xnew = xnew[:xnew_length]
    ynew = f(xnew)
    x_position_cm = ynew%track_length
    speed = np.append(0, np.diff(ynew))
    acceleration = np.append(0, np.diff(speed))
    trial_numbers = (ynew//track_length).astype(np.int64)+1

    resampled_behavioural_data["time_seconds"] = xnew
    resampled_behavioural_data["x_position_cm"] = x_position_cm
    resampled_behavioural_data["speed"] = speed
    resampled_behavioural_data["acceleration"] = acceleration
    resampled_behavioural_data["trial_numbers"] = trial_numbers
    return resampled_behavioural_data

def cebra_test(spike_data, position_data):
    fr_time_binned = extract_fr_column(spike_data, column="fr_time_binned")

    # extract spatial variables from position
    times = np.array(position_data['time_seconds'], dtype="float64")
    trial_numbers_raw = np.array(position_data['trial_number'], dtype=np.int64)

    # calculate the average fr in each 100ms time bin
    time_bins = np.arange(min(times), max(times), settings.time_bin_size) # 100ms time bins
    tn_time_bin_means = (np.histogram(times, time_bins, weights = trial_numbers_raw)[0] / np.histogram(times, time_bins)[0]).astype(np.int64)

    # extract y locations
    image_IDs = []
    for i in range(len(tn_time_bin_means)):
        image_IDs.append(position_data[position_data["trial_number"] == tn_time_bin_means[i]]["image_ID"].iloc[0])
    image_IDs = np.array(image_IDs, dtype=np.int64)[:len(fr_time_binned[0])]+118

    # flip axis so its in form (n_samples, n_features)
    fr_time_binned = np.transpose(fr_time_binned)
    image_IDs = np.transpose(image_IDs)

    hippocampus_pos = cebra.datasets.init('rat-hippocampus-single-achilles')

    max_iterations = 10000
    output_dimension = 32  # here, we set as a variable for hypothesis testing below.
    cebra_posdir3_model = CEBRA(model_architecture='offset10-model',
                                batch_size=512,
                                learning_rate=3e-4,
                                temperature=1,
                                output_dimension=3,
                                max_iterations=max_iterations,
                                distance='cosine',
                                conditional='time_delta',
                                device='cuda_if_available',
                                verbose=True,
                                time_offsets=10)
    cebra_posdir3_model.fit(fr_time_binned, image_IDs)
    cebra_posdir3 = cebra_posdir3_model.transform(fr_time_binned)

    cebra_posdir_shuffled3_model = CEBRA(model_architecture='offset10-model',
                                         batch_size=512,
                                         learning_rate=3e-4,
                                         temperature=1,
                                         output_dimension=3,
                                         max_iterations=max_iterations,
                                         distance='cosine',
                                         conditional='time_delta',
                                         device='cuda_if_available',
                                         verbose=True,
                                         time_offsets=10)
    x_position_cm_shuffled = np.random.permutation(image_IDs)
    cebra_posdir_shuffled3_model.fit(fr_time_binned, x_position_cm_shuffled)
    cebra_posdir_shuffled3 = cebra_posdir_shuffled3_model.transform(fr_time_binned)

    cebra_time3_model = CEBRA(model_architecture='offset10-model',
                              batch_size=512,
                              learning_rate=3e-4,
                              temperature=1.12,
                              output_dimension=3,
                              max_iterations=max_iterations,
                              distance='cosine',
                              conditional='time',
                              device='cuda_if_available',
                              verbose=True,
                              time_offsets=10)
    cebra_time3_model.fit(fr_time_binned)
    cebra_time3 = cebra_time3_model.transform(fr_time_binned)

    cebra_hybrid_model = CEBRA(model_architecture='offset10-model',
                               batch_size=512,
                               learning_rate=3e-4,
                               temperature=1,
                               output_dimension=3,
                               max_iterations=max_iterations,
                               distance='cosine',
                               conditional='time_delta',
                               device='cuda_if_available',
                               verbose=True,
                               time_offsets=10,
                               hybrid=True)
    #cebra_hybrid_model.fit(fr_time_binned, image_IDs)
    #cebra_hybrid = cebra_posdir3_model.transform(fr_time_binned)


    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(3, 4, 1, projection="3d")
    ax2 = fig.add_subplot(3, 4, 2, projection="3d")
    ax3 = fig.add_subplot(3, 4, 3, projection="3d")
    ax4 = fig.add_subplot(3, 4, 4, projection="3d")
    ax5 = fig.add_subplot(3, 4, 5, projection="3d")
    ax6 = fig.add_subplot(3, 4, 6, projection="3d")
    ax7 = fig.add_subplot(3, 4, 7, projection="3d")
    ax8 = fig.add_subplot(3, 4, 8, projection="3d")
    ax9 = fig.add_subplot(3, 4, 9, projection="3d")
    ax10 = fig.add_subplot(3, 4, 10, projection="3d")
    ax11 = fig.add_subplot(3, 4, 11, projection="3d")
    ax12 = fig.add_subplot(3, 4, 12, projection="3d")
    ax1 = plot_embeddings(ax1, cebra_posdir3, image_IDs, cmap="cool", viewing_angle=1)
    ax2 = plot_embeddings(ax2, cebra_posdir_shuffled3, image_IDs, cmap="cool", viewing_angle=1)
    ax3 = plot_embeddings(ax3, cebra_time3, image_IDs, cmap="cool", viewing_angle=1)
    #ax4 = plot_embeddings(ax4, cebra_hybrid, image_IDs, cmap="cool", viewing_angle=1)
    ax5 = plot_embeddings(ax5, cebra_posdir3, image_IDs, cmap="cool", viewing_angle=2)
    ax6 = plot_embeddings(ax6, cebra_posdir_shuffled3, image_IDs, cmap="cool", viewing_angle=2)
    ax7 = plot_embeddings(ax7, cebra_time3, image_IDs, cmap="cool", viewing_angle=2)
    #ax8 = plot_embeddings(ax8, cebra_hybrid, image_IDs, cmap="cool", viewing_angle=2)
    ax9 = plot_embeddings(ax9, cebra_posdir3, image_IDs, cmap="cool", viewing_angle=3)
    ax10 = plot_embeddings(ax10, cebra_posdir_shuffled3, image_IDs, cmap="cool", viewing_angle=3)
    ax11 = plot_embeddings(ax11, cebra_time3, image_IDs, cmap="cool", viewing_angle=3)
    #ax12 = plot_embeddings(ax12, cebra_hybrid, image_IDs, cmap="cool", viewing_angle=3)
    ax1.set_title('CEBRA-Behavior')
    ax2.set_title('CEBRA-Shuffled')
    ax3.set_title('CEBRA-Time')
    ax4.set_title('CEBRA-Hybrid')
    plt.savefig("/mnt/datastore/Harry/plot_viewer/ABO_cebra-behaviour-position.png", dpi=400)
    plt.close()
    print("plotted some cebra stuff")


def plot_embeddings(ax, embedding, label, idx_order = (0,1,2), cmap="", viewing_angle=1):
    idx1, idx2, idx3 = idx_order
    if cmap=="track":
        # Define the custom colormap using discrete colors
        colors = ['grey', 'yellow', 'green', 'orange', 'black']
        boundaries = [0, 30, 90, 110, 170, 200]
        custom_cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(boundaries, custom_cmap.N, clip=True)
        r=ax.scatter(embedding[:,idx1],embedding[:, idx2], embedding[:, idx3], c=label, cmap=custom_cmap, norm=norm, s=0.5)
    else:
        r=ax.scatter(embedding[:,idx1],embedding[:, idx2], embedding[:, idx3], c=label, cmap=cmap, s=0.5)
    ax.grid(False)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('w')
    ax.yaxis.pane.set_edgecolor('w')

    # Remove tick labels
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])

    # Transparent spines
    ax.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

    # Transparent panes
    ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

    # No ticks
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    if viewing_angle == 1:
        ax.view_init(elev=0, azim=0)
    elif viewing_angle == 2:
        ax.view_init(elev=30, azim=45)
    elif viewing_angle == 3:
        ax.view_init(elev=60, azim=30)
    return ax


def main():

    if settings.suppress_warnings:
        warnings.filterwarnings("ignore")

    spike_data = pd.read_pickle("/mnt/datastore/Harry/Cohort11_april2024/allen_brain_observatory_visual_coding/"
                                "M21_D28_2024-05-30_18-24-56_VID1/processed/mountainsort5/spikes.pkl")
    position_data = pd.read_csv("/mnt/datastore/Harry/Cohort11_april2024/allen_brain_observatory_visual_coding/"
                                "M21_D28_2024-05-30_18-24-56_VID1/processed/position_data.csv")

    cebra_test(spike_data, position_data)
    compare_ldm(spike_data)




if __name__ == '__main__':
    main()