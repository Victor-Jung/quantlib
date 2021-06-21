from torch import nn
from torch.optim import SGD, Adam, Adagrad

import inspect

from . import pact_ops
from quantlib.editing.lightweight.rules.filters import TypeFilter, VariadicOrFilter
from quantlib.editing.lightweight.graph import LightweightGraph


__all__ = [
    'PACTSGD',
    'PACTAdam',
    'PACTAdagrad',
]


_PACT_CLASSES = [cl[1] for cl in inspect.getmembers(pact_ops, inspect.isclass) if issubclass(cl[1], nn.Module)]


class PACTOptimizerFactory(object):  # https://stackoverflow.com/questions/21060073/dynamic-inheritance-in-python

    def __init__(self):
        self._created_classes = {}

    def __call__(self, base_opt_type: type):

        rep = "PACT" + base_opt_type.__name__

        if rep in self._created_classes.keys():

            optimizer_class = self._created_classes[rep]

        else:

            class PACTOptimizer(base_opt_type):

                def __init__(self, net, pact_decay, *opt_args, **opt_kwargs):

                    net_nodes   = LightweightGraph.build_nodes_list(net)
                    pact_filter = VariadicOrFilter(*[TypeFilter(t) for t in _PACT_CLASSES])
                    learnable_clipping_params = [b for n in pact_filter(net_nodes) for b in n.module.clipping_params.values() if b.requires_grad]

                    # initialize the base class with configured weight decay for the
                    # clipping parameters and any other supplied parameters

                    other_params = [p for p in net.parameters() if p.requires_grad and all(pp is not p for pp in learnable_clipping_params)]
                    # Note: when the learnable clipping parameters are not used
                    # (e.g., while quantization is disabled), the weight decay
                    # will have NO effect on them. This fact is very handy,
                    # since it prevents us from having to update their
                    # 'requires_grad' flags when turning quantization on/off.
                    base_opt_type.__init__(self,
                                           ({'params':       learnable_clipping_params,
                                             'weight_decay': pact_decay},
                                            {'params':       other_params}),
                                           *opt_args,
                                           **opt_kwargs)

            # Change the `name` and `qualname` of the newly-created class to
            # hide the fact that it was dynamically created. The perfect crime...
            PACTOptimizer.__name__     = rep
            PACTOptimizer.__qualname__ = rep
            self._created_classes[rep] = PACTOptimizer

            optimizer_class = PACTOptimizer

        return optimizer_class


opt_factory = PACTOptimizerFactory()

PACTSGD     = opt_factory(SGD)
PACTAdam    = opt_factory(Adam)
PACTAdagrad = opt_factory(Adagrad)
