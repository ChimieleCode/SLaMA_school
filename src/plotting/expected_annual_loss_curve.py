from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt

def plot_PAM(pam_dct: dict, color: Any, save_path: Path) -> None:
    """
    Plots the PAM starting from the output PAM dictionary
    
    :params pam_dct: PAM data as outputted by the compute_PAM foo

    :params color: color of the pam curve

    :params save_path: path where the figure is going to be saved, if omitted, figure will only be displayed
    """
    plt.plot(
        pam_dct['frequencies'],
        pam_dct['loss_ratios'],
        color=color
    )
    plt.title(f'PAM')
    plt.ylabel('CR [%]')
    plt.xlabel('MAF [-]')
    plt.xlim(left=0, right=0.1)
    plt.ylim(bottom=0, top=1.)
    plt.grid(
        True,
        linestyle='--'
    )
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()
    
    plt.clf()