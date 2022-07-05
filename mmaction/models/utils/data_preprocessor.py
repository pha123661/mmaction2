# Copyright (c) OpenMMLab. All rights reserved.
from typing import Sequence, Tuple, Union

import torch
from mmengine.model import BaseDataPreprocessor, stack_batch

from mmaction.registry import MODELS, TASK_UTILS


@MODELS.register_module()
class ActionDataPreprocessor(BaseDataPreprocessor):
    """Data pre-processor for action recognition tasks.

    Args:
        mean (Sequence[float or int): The pixel mean of channels of images
            or stacked optical flow. Defaults to None.
        std (Sequence[float or int]): The pixel standard deviation of channels
            of images or stacked optical flow. Defaults to None.
        pad_size_divisor (int): The size of padded image should be
            divisible by ``pad_size_divisor``. Defaults to 1.
        pad_value (float or int): The padded pixel value. Defaults to 0.
        to_rgb (bool): whether to convert image from BGR to RGB.
            Defaults to False.
        blending (dict): Config for batch blending. Defaults to None.
    """

    def __init__(self,
                 mean: Sequence[Union[float, int]] = None,
                 std: Sequence[Union[float, int]] = None,
                 pad_size_divisor: int = 1,
                 pad_value: Union[float, int] = 0,
                 to_rgb: bool = False,
                 blending: dict = None,
                 format_shape: str = 'NCHW'):
        super().__init__()
        self.pad_size_divisor = pad_size_divisor
        self.pad_value = pad_value
        self.to_rgb = to_rgb
        self.format_shape = format_shape

        if mean is not None:
            assert std is not None, 'To enable the normalization in ' \
                                    'preprocessing, please specify both `mean` and `std`.'
            # Enable the normalization in preprocessing.
            self._enable_normalize = True
            if self.format_shape == 'NCHW':
                normalizer_shape = (-1, 1, 1)
            elif self.format_shape == 'NCTHW' or self.format_shape == 'NCTVM':
                normalizer_shape = (-1, 1, 1, 1)
            else:
                raise ValueError(f'Invalid format shape: {format_shape}')

            self.register_buffer('mean',
                                 torch.tensor(mean).view(normalizer_shape), False)
            self.register_buffer('std',
                                 torch.tensor(std).view(normalizer_shape), False)
        else:
            self._enable_normalize = False

        if blending is not None:
            self.blending = TASK_UTILS.build(blending)
        else:
            self.blending = None

    def forward(self,
                data: Sequence[dict],
                training: bool = False) -> Tuple[torch.Tensor, list]:
        """Perform normalization, padding, bgr2rgb conversion and batch
        augmentation based on ``BaseDataPreprocessor``.

        Args:
            data (Sequence[dict]): data sampled from dataloader.
            training (bool): Whether to enable training time augmentation.

        Returns:
            Tuple[torch.Tensor, list]: Data in the same format as the model
            input.
        """
        inputs, batch_data_samples = self.collate_data(data)

        # --- Pad and stack --
        batch_inputs = stack_batch(inputs, self.pad_size_divisor,
                                   self.pad_value)

        # ------ To RGB ------
        if self.to_rgb:
            if self.format_shape == 'NCHW':
                batch_inputs = batch_inputs[..., [2, 1, 0], :, :]
            elif self.format_shape == 'NCTHW':
                batch_inputs = batch_inputs[..., [2, 1, 0], :, :, :]
            else:
                raise ValueError(f'Invalid format shape: {self.format_shape}')

        # -- Normalization ---
        if self._enable_normalize:
            batch_inputs = (batch_inputs - self.mean) / self.std
        else:
            batch_inputs = batch_inputs.to(torch.float32)

        # ----- Blending -----
        if training and self.blending is not None:
            batch_inputs, batch_data_samples = self.blending(
                batch_inputs, batch_data_samples)

        return batch_inputs, batch_data_samples