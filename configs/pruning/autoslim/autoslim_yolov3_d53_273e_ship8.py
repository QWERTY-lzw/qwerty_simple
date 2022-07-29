_base_ = ['../../_base_/default_runtime.py', '../../_base_/datasets/ship8.py']

custom_imports=dict(imports='mmdet_custom.datasets', allow_failed_imports=False) 

img_scale = (256, 320)
# model settings
model = dict(
    type='mmdet.YOLOV3',
    backbone=dict(
        type='Darknet',
        depth=53,
        out_indices=(3, 4, 5),
        init_cfg=dict(type='Pretrained', checkpoint='open-mmlab://darknet53')),
    neck=dict(
        type='YOLOV3Neck',
        num_scales=3,
        in_channels=[1024, 512, 256],
        out_channels=[512, 256, 128]),
    bbox_head=dict(
        type='YOLOV3Head',
        num_classes=8,
        in_channels=[512, 256, 128],
        out_channels=[1024, 512, 256],
        anchor_generator=dict(
            type='YOLOAnchorGenerator',
            base_sizes=[[(116, 90), (156, 198), (373, 326)],
                        [(30, 61), (62, 45), (59, 119)],
                        [(10, 13), (16, 30), (33, 23)]],
            strides=[32, 16, 8]),
        bbox_coder=dict(type='YOLOBBoxCoder'),
        featmap_strides=[32, 16, 8],
        loss_cls=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=1.0,
            reduction='sum'),
        loss_conf=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=1.0,
            reduction='sum'),
        loss_xy=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=2.0,
            reduction='sum'),
        loss_wh=dict(type='MSELoss', loss_weight=2.0, reduction='sum')),
    
    # training and testing settings
    train_cfg=dict(
        assigner=dict(
            type='GridAssigner',
            pos_iou_thr=0.5,
            neg_iou_thr=0.5,
            min_pos_iou=0)),
    test_cfg=dict(
        nms_pre=1000,
        min_bbox_size=0,
        score_thr=0.05,
        conf_thr=0.005,
        nms=dict(type='nms', iou_threshold=0.45),
        max_per_img=100))


# optimizer
optimizer = dict(type='SGD', lr=0.001, momentum=0.9, weight_decay=0.0005)
# optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2))
optimizer_config = None # for pruning algorithm https://github.com/open-mmlab/mmrazor/issues/117

# learning policy
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=2000,  # same as burn-in in darknet
    warmup_ratio=0.1,
    step=[218, 246])

# runtime settings
max_epochs = 273
runner = dict(type='EpochBasedRunner', max_epochs=max_epochs)
evaluation = dict(interval=50, metric=['bbox'])
num_last_epochs = 5
interval = 50
checkpoint_config = dict(interval=interval)
evaluation = dict(
    metric='mAP', 
    interval=interval,
    dynamic_intervals=[(max_epochs - num_last_epochs, 1)],
    save_best='mAP')

custom_hooks=[]

algorithm = dict(
    type='AutoSlim',
    architecture=dict(type='MMDetArchitecture', model=model),
    pruner=dict(
        type='RatioPruner',
        ratios=[1 / 8, 2 / 8, 3 / 8, 4 / 8, 5 / 8, 6 / 8, 7 / 8, 1.0]),
    retraining=False,
    bn_training_mode=True,
    input_shape=None)

# runner = dict(type='EpochBasedRunner', max_epochs=50)

use_ddp_wrapper = True