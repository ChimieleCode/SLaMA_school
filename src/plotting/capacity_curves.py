from pathlib import Path
from typing import Any, List
import matplotlib.pyplot as plt

from src.capacity.capacity import FrameCapacity
from src.hazard import SeismicHazard

def plot_base_shear(capacity_curves: List[FrameCapacity],
                    colors: List[Any] = list(),
                    save_path: Path = None) -> None:
    """
    Plots the capacity curves
    
    :params capacity_curves: list of capacity curves to be plotted
    
    :paramns colors: list of colors for each curve, colors must be defined according to pyplot lib

    :params save_path: path where the figure is going to be saved, if omitted, figure will only be displayed
    """
    
    for capacity, color in zip(capacity_curves, colors):
        plt.plot(
            [0, capacity.yielding, capacity.ultimate],
            [0, capacity.base_shear, capacity.base_shear],
            label=capacity.name,
            color=color
        )
    
    plt.title(f'Capacity Curves')
    plt.ylabel('Base Shear [kNm]')
    plt.xlabel('Displacement [m]')
    plt.legend()
    plt.xlim(left = 0)
    plt.ylim(bottom = 0)
    plt.grid(
        True,
        linestyle='--'
    )
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()

    plt.clf()


def plot_ADRS(capacity: FrameCapacity, 
              SLV_spectra: SeismicHazard, 
              IS_V: float, 
              SLD_spectra: SeismicHazard = None, 
              IS_D: float = 1.,
              save_path: Path = None) -> None:
    """
    Plots the ADRS spectra for the capacity curve
    
    :params capacity_curve: Capacity curve object containing the data to plot
    
    :params SLV_spectra: SismicHazard object containing data on SLV spectra

    :params IS_V: IS-V ratio for the given capacity curve
    
    :params SLD_spectra: SismicHazard object containing data on SLD spectra

    :params IS_D: IS-D ratio for the given capacity curve

    :params save_path: path where the figure is going to be saved, if omitted, figure will only be displayed
    """
    # Plot capacity curve
    plt.plot(
        [0, capacity.yielding, capacity.ultimate],
        [0, capacity.acc_capacity, capacity.acc_capacity],
        label='SLaMA',
        color='r'
    )
    periods_SLV = SLV_spectra.periods_array(
        max_period=3.,
        npoints=40
    )
    disp_SLV = [SLV_spectra.get_spectral_displacement(period, 0.1) for period in periods_SLV]
    disp_SLV.append(disp_SLV[-1])
    acc_SLV = [SLV_spectra.get_spectral_acceleration(period, 0.1) for period in periods_SLV] + [0.]
    # Plot SLV unscaled
    plt.plot(
        disp_SLV,
        acc_SLV,
        label='SLV unscaled',
        color='0.6',
        linestyle='--'
    )
    plt.plot(
        [disp * IS_V for disp in disp_SLV],
        [acc * IS_V for acc in acc_SLV],
        label='SLV scaled',
        color='k'
    )
    if SLD_spectra is not None:
        periods_SLD = SLD_spectra.periods_array(
            max_period=3.,
            npoints=40
        )
        disp_SLD = [SLD_spectra.get_spectral_displacement(period, 0.1) for period in periods_SLD]
        disp_SLD.append(disp_SLD[-1])
        acc_SLD = [SLD_spectra.get_spectral_acceleration(period, 0.1) for period in periods_SLD] + [0.]
        plt.plot(
            disp_SLD,
            acc_SLD,
            label='SLD unscaled',
            color='0.8',
            linestyle='--'
        )
        plt.plot(
            [disp * IS_V for disp in disp_SLD],
            [acc * IS_V for acc in acc_SLD],
            label='SLD scaled',
            color='k'
        )
    
    plt.title(f'ADRS')
    plt.ylabel('Spectral Acceleration [g]')
    plt.xlabel('Spectral Displacement [m]')
    plt.legend()
    plt.xlim(left = 0)
    plt.ylim(bottom = 0)

    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()
    
    plt.clf()