from src.performance.capacity_demand import compute_ISD, compute_ISV
from src.hazard import SeismicHazard
from src.capacity import Capacity

def compute_PAM(capacity: Capacity, hazard: SeismicHazard) -> dict():
    """
    Computes the PAM according to NTC2018
    """
    loss_ratios = (0., 0.07, 0.15, 0.5, 0.8, 1.)
    frequencies = (0.1,)
    SLD_freq = (50 * compute_ISD(capacity, hazard[0])**(1/0.41))**-1
    SLV_freq = (475 * compute_ISV(capacity, hazard[-1])**(1/0.41))**-1
    SLO_freq = 1.67 * SLD_freq
    SLC_freq = 0.49 * SLV_freq
    frequencies += (
        min(frequencies[0], SLO_freq), 
        min(frequencies[0], SLD_freq),
        SLV_freq,
        SLC_freq,
        SLC_freq
    )
    expected_annual_loss = sum(
        (frequencies[i] - frequencies[i + 1]) * (loss_ratios[i + 1] + loss_ratios[i]) * 0.5 
        for i in range(4)
        ) + frequencies[-1] * loss_ratios[-1]
    return {
        'frequencies' : frequencies,
        'loss_ratios' : loss_ratios,
        'PAM' : expected_annual_loss
    }
