from copy import deepcopy

import torch


class ModelEMA(object):

    def __init__(self, model: torch.nn.Module, decay: float, device):
        self.ema = deepcopy(model).to(device)
        self.ema.eval()
        self.decay = decay
        self.ema_has_module = hasattr(self.ema, "module")
        # Fix EMA. https://github.com/valencebond/FixMatch_pytorch
        self.param_keys = [k for k, _ in self.ema.named_parameters()]
        self.buffer_keys = [k for k, _ in self.ema.named_buffers()]
        for p in self.ema.parameters():
            p.requires_grad_(False)

    def update(self, model: torch.nn.Module):
        needs_module = hasattr(model, "module") and not self.ema_has_module
        with torch.no_grad():
            msd = model.state_dict()
            esd = self.ema.state_dict()
            for k in self.param_keys:
                if needs_module:
                    j = "module." + k
                else:
                    j = k
                model_v = msd[j].detach()
                ema_v = esd[k]
                esd[k].copy_(ema_v * self.decay + (1. - self.decay) * model_v)

            for k in self.buffer_keys:
                if needs_module:
                    j = "module." + k
                else:
                    j = k
                esd[k].copy_(msd[j])
