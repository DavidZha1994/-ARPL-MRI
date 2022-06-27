import os
import os.path as osp
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

import torch
from torch.autograd import Variable
import torch.nn.functional as F

from core import evaluation

def test(net, criterion, testloader, outloader, epoch=None, **options):
    net.eval()
    correct, total = 0, 0

    torch.cuda.empty_cache()

    _pred_k, _pred_u, _labels = [], [], []
    all_features_k, all_features_u = [], []

    with torch.no_grad():
        for batch_idx, (data, labels) in enumerate(testloader):
            if options['use_gpu']:
                print('test is using GPU')
                data, labels = data.cuda(), labels.cuda()
            
            with torch.set_grad_enabled(False):
                x, y = net(data, True)
                logits, _ = criterion(x, y)
                predictions = logits.data.max(1)[1]
                total += labels.size(0)
                correct += (predictions == labels.data).sum()
            
                all_features_k.append(x.data.cpu().numpy())
                _pred_k.append(logits.data.cpu().numpy())
                _labels.append(labels.data.cpu().numpy())
                print("Batch {}/{}\t)"
                    .format(batch_idx+1, len(testloader)))

        for batch_idx, (data, labels) in enumerate(outloader):
            if options['use_gpu']:
                data, labels = data.cuda(), labels.cuda()
            
            with torch.set_grad_enabled(False):
                x, y = net(data, True)
                logits, _ = criterion(x, y)

                all_features_u.append(x.data.cpu().numpy())
                _pred_u.append(logits.data.cpu().numpy())
                print("Batch {}/{}\t)"
                    .format(batch_idx+1, len(outloader)))

    # Accuracy
    acc = float(correct) * 100. / float(total)
    print('Acc: {:.5f}'.format(acc))

    all_features_k = np.concatenate(all_features_k, 0)
    all_features_u = np.concatenate(all_features_u, 0)
    _pred_k = np.concatenate(_pred_k, 0)
    _pred_u = np.concatenate(_pred_u, 0)
    _labels = np.concatenate(_labels, 0)

    plot_features(all_features_k, _labels, options['num_classes'], epoch, prefix='test_k')
    #plot_features(all_features_u, _labels, options['num_classes'], epoch, prefix='test_u')
    # Out-of-Distribution detction evaluation
    x1, x2 = np.max(_pred_k, axis=1), np.max(_pred_u, axis=1)
    results = evaluation.metric_ood(x1, x2)['Bas']
    
    # OSCR
    _oscr_socre = evaluation.compute_oscr(_pred_k, _pred_u, _labels)

    results['ACC'] = acc
    results['OSCR'] = _oscr_socre * 100.

    return results

def plot_features(features, labels, num_classes, epoch, prefix):
    """Plot features on 2D plane.

    Args:
        features: (num_instances, num_features).
        labels: (num_instances). 
    """
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11']
    for label_idx in range(num_classes):
        plt.scatter(
            features[labels==label_idx, 0],
            features[labels==label_idx, 1],
            c=colors[label_idx],
            s=1,
        )
    plt.legend(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'], loc='upper right')
    dirname = osp.join('log', prefix)
    if not osp.exists(dirname):
        os.mkdir(dirname)
    save_name = osp.join(dirname, 'epoch_' + str(epoch+1) + '.png')
    plt.savefig(save_name, bbox_inches='tight')
    plt.close()