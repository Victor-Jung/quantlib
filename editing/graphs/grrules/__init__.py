from collections import OrderedDict

from .seeker import Seeker
from .dporules import *
from .hlprrules import *
from .. import traces


def load_rescoping_rules(modules=None):

    libtraces = traces.load_traces_library(modules=modules)

    librules = OrderedDict()
    for mod_name, (L, K) in libtraces.items():
        if mod_name == 'ViewFlattenNd':
            librules[mod_name] = ManualRescopingRule(L, K, 'torch.view')  # TODO: mind quantlib.editing.graphs/graphs/graphs.py:L205
        else:
            librules[mod_name] = AutoRescopingRule(L, K)

    return librules
