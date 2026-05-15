import math

import torch
import torch.nn as nn
from torch.nn import init


class Conv2dInit(nn.Conv2d):
    def reset_parameters(self):
        init.xavier_normal_(self.weight)
        if self.bias is not None:
            fan_in, _ = init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in)
            init.uniform_(self.bias, -bound, bound)


class FeatureNorm(nn.Module):
    def __init__(self, num_features, feature_index=1, rank=4, reduce_dims=(2, 3), eps=0.001, include_bias=True):
        super().__init__()
        self.shape = [1] * rank
        self.shape[feature_index] = num_features
        self.reduce_dims = reduce_dims
        self.scale = nn.Parameter(torch.ones(self.shape, requires_grad=True, dtype=torch.float))
        self.bias = nn.Parameter(torch.zeros(self.shape, requires_grad=True, dtype=torch.float)) if include_bias else nn.Parameter(
            torch.zeros(self.shape, requires_grad=False, dtype=torch.float)
        )
        self.eps = eps

    def forward(self, features):
        f_std = torch.std(features, dim=self.reduce_dims, keepdim=True)
        f_mean = torch.mean(features, dim=self.reduce_dims, keepdim=True)
        return self.scale * ((features - f_mean) / (f_std + self.eps).sqrt()) + self.bias


def _conv_block(in_channels, out_channels, kernel_size, padding):
    return nn.Sequential(
        Conv2dInit(in_channels=in_channels, out_channels=out_channels, kernel_size=kernel_size, padding=padding, bias=False),
        FeatureNorm(num_features=out_channels, eps=0.001),
        nn.ReLU(),
    )


class OpticalConvBank(nn.Module):
    """
    Single optical kernel bank.
    This layer is the digital proxy of a metasurface PSF encoder.
    """

    def __init__(self, in_channels, out_channels, kernel_size):
        super().__init__()
        padding = kernel_size // 2
        self.conv = Conv2dInit(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            padding=padding,
            bias=False,
        )

    def forward(self, x):
        return self.conv(x)


class OpticalCalibration(nn.Module):
    """
    Minimal electronic calibration after the optical responses.
    This keeps the optical/electronic boundary clean while allowing
    channel-wise gain and bias compensation before the task heads.
    """

    def __init__(self, num_channels):
        super().__init__()
        self.norm = FeatureNorm(num_features=num_channels, eps=0.001)
        self.activation = nn.ReLU()

    def forward(self, x):
        return self.activation(self.norm(x))


class OpticalSegDecStudent(nn.Module):
    """
    Distilled SegDecNet student:
    input
      -> single optical convolution bank
      -> minimal calibration + fixed downsampling
      -> seg_head
      -> concat(volume_like_feature, seg_mask)
      -> lightweight extractor
      -> fc
    """

    def __init__(
        self,
        input_channels,
        optical_channels=32,
        optical_kernel_size=7,
        downsample_factor=8,
        extractor_channels=(8, 16, 24),
    ):
        super().__init__()
        if downsample_factor not in (2, 4, 8):
            raise ValueError("downsample_factor should be one of 2, 4 or 8 for the current DAGM sweep.")

        self.downsample_factor = downsample_factor
        self.optical_frontend = OpticalConvBank(
            in_channels=input_channels,
            out_channels=optical_channels,
            kernel_size=optical_kernel_size,
        )
        self.calibration = OpticalCalibration(num_channels=optical_channels)
        self.downsample = nn.AvgPool2d(kernel_size=downsample_factor, stride=downsample_factor)

        self.seg_head = nn.Sequential(
            Conv2dInit(in_channels=optical_channels, out_channels=1, kernel_size=1, padding=0, bias=False),
            FeatureNorm(num_features=1, eps=0.001, include_bias=False),
        )

        ext_c1, ext_c2, ext_c3 = extractor_channels
        self.extractor = nn.Sequential(
            nn.MaxPool2d(kernel_size=2),
            _conv_block(in_channels=optical_channels + 1, out_channels=ext_c1, kernel_size=5, padding=2),
            nn.MaxPool2d(kernel_size=2),
            _conv_block(in_channels=ext_c1, out_channels=ext_c2, kernel_size=5, padding=2),
            nn.MaxPool2d(kernel_size=2),
            _conv_block(in_channels=ext_c2, out_channels=ext_c3, kernel_size=5, padding=2),
        )

        self.fc = nn.Linear(in_features=2 * ext_c3 + 2, out_features=1)

    def architecture_summary(self):
        optical_params = sum(p.numel() for p in self.optical_frontend.parameters())
        calibration_params = sum(p.numel() for p in self.calibration.parameters())
        seg_head_params = sum(p.numel() for p in self.seg_head.parameters())
        extractor_params = sum(p.numel() for p in self.extractor.parameters())
        fc_params = sum(p.numel() for p in self.fc.parameters())
        total_params = sum(p.numel() for p in self.parameters())
        return {
            "input": "B x C x H x W",
            "optical_frontend": {
                "module": "single Conv2d PSF/kernel bank",
                "weight_shape": list(self.optical_frontend.conv.weight.shape),
                "params": optical_params,
            },
            "calibration": {
                "module": "FeatureNorm + ReLU",
                "params": calibration_params,
            },
            "downsample": f"AvgPool2d(kernel={self.downsample_factor}, stride={self.downsample_factor})",
            "downsample_factor": self.downsample_factor,
            "seg_head": {
                "module": "1x1 Conv2d + FeatureNorm",
                "params": seg_head_params,
            },
            "extractor": {
                "module": "three small Conv/FeatureNorm/ReLU blocks with MaxPool",
                "params": extractor_params,
            },
            "fc": {
                "module": "Linear(global max/avg features + global max/avg mask -> 1)",
                "params": fc_params,
            },
            "total_params": total_params,
            "optical_param_ratio": optical_params / total_params if total_params else 0.0,
        }

    def optical_kernels_numpy(self):
        return self.optical_frontend.conv.weight.detach().cpu().numpy()

    def forward(self, x):
        optical_maps = self.optical_frontend(x)
        calibrated_maps = self.calibration(optical_maps)
        volume = self.downsample(calibrated_maps)
        seg_mask = self.seg_head(volume)

        features = self.extractor(torch.cat([volume, seg_mask], dim=1))
        global_max_feat = torch.amax(features, dim=(-1, -2))
        global_avg_feat = torch.mean(features, dim=(-1, -2))
        global_max_seg = torch.amax(seg_mask, dim=(-1, -2))
        global_avg_seg = torch.mean(seg_mask, dim=(-1, -2))

        fc_in = torch.cat([global_max_feat, global_avg_feat, global_max_seg, global_avg_seg], dim=1)
        prediction = self.fc(fc_in)
        return prediction, seg_mask, volume, optical_maps
