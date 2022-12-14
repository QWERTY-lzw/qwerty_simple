# Copyright (c) Open-MMLab. All rights reserved.
import os.path as osp
import platform
import shutil
import time
import warnings

import torch

import mmcv
from mmcv.runner import EpochBasedRunner, save_checkpoint, get_host_info, RUNNERS
import numpy as np
from random import choice
import random

torch.manual_seed(0)
torch.cuda.manual_seed_all(0)
np.random.seed(0)
random.seed(0)


@RUNNERS.register_module()
class EpochBasedRunnerSuper(EpochBasedRunner):
    """Epoch-based Runner.

    This runner train models epoch by epoch.
    """

    def __init__(self,
                 backbone_widen_factor_range,
                 backbone_deepen_factor_range,
                 neck_widen_factor_range, 
                 head_widen_factor_range, 
                 search=False,
                #  search_backbone=False,
                #  search_neck=False,
                #  search_head=False,
                 sandwich=False,
                 **kwargs):
        self.backbone_widen_factor_range = backbone_widen_factor_range
        self.backbone_deepen_factor_range = backbone_deepen_factor_range
        self.neck_widen_factor_range = neck_widen_factor_range
        self.head_widen_factor_range = head_widen_factor_range
        # self.search_backbone = search_backbone
        # self.search_neck = search_neck
        # self.search_head = search_head
        self.search = search
        self.sandwich = sandwich

        self.arch = None

        super(EpochBasedRunnerSuper, self).__init__(**kwargs)

    def get_cand_arch(self, max_arch=False, min_arch=False):
        arch = {}
        if max_arch or min_arch:
            assert not max_arch or not min_arch
            fn = max if max_arch else min
            arch['widen_factor_backbone'] = tuple([fn(self.backbone_widen_factor_range)]*5)
            arch['deepen_factor_backbone'] = tuple([fn(self.backbone_deepen_factor_range)]*4)
            arch['widen_factor_neck'] = tuple([fn(self.neck_widen_factor_range)]*8)
            arch['widen_factor_neck_out'] = max(self.head_widen_factor_range)
        else:
            arch['widen_factor_backbone'] = tuple(random.choices(self.backbone_widen_factor_range, k=5))
            arch['deepen_factor_backbone'] = tuple(random.choices(self.backbone_deepen_factor_range, k=4))
            arch['widen_factor_neck'] = tuple(random.choices(self.neck_widen_factor_range, k=8))
            arch['widen_factor_neck_out'] = random.choice(self.head_widen_factor_range)
        return arch

    def set_grad_none(self, **kwargs):
        self.model.module.set_grad_none(**kwargs)

    def train(self, data_loader, **kwargs):
        self.model.train()
        self.mode = 'train'
        self.data_loader = data_loader
        self._max_iters = self._max_epochs * len(self.data_loader)
        self.call_hook('before_train_epoch')
        time.sleep(2)  # Prevent possible deadlock during epoch transition

        for i, data_batch in enumerate(self.data_loader):
            self._inner_iter = i
            self.call_hook('before_train_iter')

            # if self.search_backbone or self.search_neck or self.search_head:
            if self.search:
                self.arch = self.get_cand_arch()

                if self.sandwich:
                    self.archs = []
                    self.archs.append(self.get_cand_arch(max_arch=True))
                    self.archs.append(self.get_cand_arch(min_arch=True))
                    self.archs.append(self.get_cand_arch())
                    self.archs.append(self.arch)
                    self.model.module.set_archs(self.archs, **kwargs)
                else:
                    self.model.module.set_arch(self.arch, **kwargs)

            if i % 50 == 0:
                self.logger.info(f'arch: {self.archs}')
            self.run_iter(data_batch, train_mode=True, **kwargs)
            self.call_hook('after_train_iter')
            self._iter += 1

        self.call_hook('after_train_epoch')
        self._epoch += 1


