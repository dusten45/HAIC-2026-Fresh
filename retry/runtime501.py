"""Isolated original397/417 graph for the registered501 screen.

Reuses namespace-only loader infrastructure. No491 projection/executor opt-in,
no495 source/root authority, and no automatic reference injection.
"""
import ast,hashlib
from pathlib import Path
from retry.runtime492 import Graph,Rewrite,G

class Graph501(Graph):
    def exec_module(self,module):
        name=module.__name__
        if name==self.prefix:
            module.__path__=[str(G/'retry')];module.__file__=str(G/'retry/__init__.py');return
        suffix=name[len(self.prefix)+1:];path=(G/'retry'/Path(*suffix.split('.'))).with_suffix('.py')
        if module.__spec__.submodule_search_locations is not None:
            path=path.with_suffix('')/'__init__.py';module.__path__=[str(path.parent)]
        source=path.read_text();tree=Rewrite().visit(ast.parse(source));ast.fix_missing_locations(tree)
        module.__file__=str(path);module.__cached__=None;module.__private_clone492__=True
        exec(compile(tree,str(path)+'#isolated501-original417','exec'),module.__dict__)
        if suffix=='paired417_common':self.policy_original=module.policy
        if suffix in ('racing258_plan','racing258_feasibility','pace268_profile','analyze466','select485'):
            def forbidden(*a,**k):raise RuntimeError('501_RECOMPUTATION_SELECTION_FORBIDDEN')
            for key in ('solve','profile','project','multipliers','project_four','select','geometry','basis'):
                if key in vars(module):setattr(module,key,forbidden)
        self.modules[suffix]=module
        self.records[suffix]=dict(path=str(path),source_sha256=hashlib.sha256(source.encode()).hexdigest(),AST_sha256=hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),projection491_optin=False,original397_417=True)
        if self.codec is not None:self.codec.install()
    def audit(self):
        originals=[self.import_module(n) for n in ('executor397','signed417_executor')]
        projections=[m.canonical_projection for m in originals];executors=[m.CoherentExecutor for m in originals]
        slots=[]
        for name,m in self.modules.items():
            if hasattr(m,'canonical_projection'):
                if not any(m.canonical_projection is x for x in projections):raise RuntimeError('501_WRONG_PROJECTION:'+name)
                slots.append(name)
            if hasattr(m,'CoherentExecutor') and not any(m.CoherentExecutor is x for x in executors):raise RuntimeError('501_WRONG_EXECUTOR:'+name)
        return dict(passed=True,projection491_optin=False,original397_417=True,projection_slots=slots,modules=len(self.modules))
