"""Private opt-in492 import graph. Original retry modules/files remain untouched.

Research imports execute as retry492.* with identical source except import
namespace rewriting. Both old executor export slots in THIS graph expose491.
Runtime AST/source hashes and alias audits are retained by the caller.
"""
import ast,hashlib,importlib,importlib.abc,importlib.util,sys,types
from pathlib import Path
import numpy as np
from retry.projection491 import canonical_projection,CoherentExecutor491
from retry.signed417_executor import ExecutorDomainError

G=Path(__file__).resolve().parents[1]
class Rewrite(ast.NodeTransformer):
    def module(self,name):return 'retry492'+name[5:] if name=='retry' or name.startswith('retry.') else name
    def visit_ImportFrom(self,node):
        if node.module:node.module=self.module(node.module)
        return node
    def visit_Import(self,node):
        for a in node.names:a.name=self.module(a.name)
        return node
    def visit_Name(self,node):
        if node.id=='retry':node.id='retry492'
        return node
    def visit_Constant(self,node):
        # Dynamic import names are rewritten; diagnostic/source paths are not.
        if isinstance(node.value,str) and (node.value=='retry' or node.value.startswith('retry.')) and all(x.isidentifier() for x in node.value.split('.')):node.value=self.module(node.value)
        return node

class Graph(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    prefix='retry492'
    def __init__(self,binding,fixed,pace,nodes):
        self.binding=binding;self.fixed=fixed;self.pace=np.asarray(pace);self.nodes=np.asarray(nodes);self.modules={};self.records={};self.policy_original=None;self.codec=None
        self.line_sha=hashlib.sha256(np.asarray(fixed['line'],dtype='<f8').tobytes()).hexdigest()
    def find_spec(self,fullname,path=None,target=None):
        if fullname==self.prefix:return importlib.util.spec_from_loader(fullname,self,is_package=True)
        if not fullname.startswith(self.prefix+'.'):return None
        suffix=fullname[len(self.prefix)+1:];p=G/'retry'/Path(*suffix.split('.'))
        if p.is_dir():return importlib.util.spec_from_loader(fullname,self,is_package=True)
        if p.with_suffix('.py').is_file():return importlib.util.spec_from_loader(fullname,self,is_package=False)
        raise ImportError('492_clone_missing:'+fullname)
    def create_module(self,spec):return None
    def exec_module(self,module):
        name=module.__name__
        if name==self.prefix:module.__path__=[str(G/'retry')];module.__file__=str(G/'retry/__init__.py');return
        suffix=name[len(self.prefix)+1:];path=(G/'retry'/Path(*suffix.split('.'))).with_suffix('.py')
        if module.__spec__.submodule_search_locations is not None:path=path.with_suffix('')/'__init__.py';module.__path__=[str(path.parent)]
        source=path.read_text();tree=Rewrite().visit(ast.parse(source));ast.fix_missing_locations(tree)
        module.__file__=str(path);module.__cached__=None;module.__private_clone492__=True
        exec(compile(tree,str(path)+'#isolated492','exec'),module.__dict__)
        if suffix in ('executor397','signed417_executor'):
            module.canonical_projection=canonical_projection;module.CoherentExecutor=CoherentExecutor491;module.ExecutorDomainError=ExecutorDomainError
        if suffix=='paired417_common':
            old=module.policy;self.policy_original=old
            def policy(fixed,pace):
                self.check_input(fixed,pace);c=old(fixed,pace);self.bind_policy(c);return c
            module.policy=policy
        # Forbid new optimization/profile/seed selection in this graph.
        if suffix in ('racing258_plan','racing258_feasibility','pace268_profile','analyze466','select485'):
            def forbidden(*args,**kwargs):raise RuntimeError('492_RECOMPUTATION_OR_SELECTION_FORBIDDEN')
            for key in ('solve','profile','project','multipliers','project_four','select','geometry','basis'):
                if key in vars(module):setattr(module,key,forbidden)
        self.modules[suffix]=module
        self.records[suffix]=dict(path=str(path),source_sha256=hashlib.sha256(source.encode()).hexdigest(),AST_sha256=hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),projection491_optin=True)
        if self.codec is not None:self.codec.install()
    def install(self):sys.meta_path.insert(0,self);return self
    def import_module(self,name):
        if name.startswith('retry.'):name=name[6:]
        if name.startswith('retry492.'):name=name[9:]
        return importlib.import_module(self.prefix+'.'+name)
    def check_input(self,fixed,pace):
        assert hashlib.sha256(np.asarray(fixed['line'],dtype='<f8').tobytes()).hexdigest()==self.line_sha
        assert np.asarray(pace,dtype='<f8').tobytes()==self.pace.astype('<f8').tobytes()
        for key in ('speed','ds','curvature'):assert np.asarray(fixed['free_profile'][key],dtype='<f8').tobytes()==np.asarray(self.fixed['free_profile'][key],dtype='<f8').tobytes()
        assert fixed['model']==self.fixed['model']
    def bind_policy(self,c):
        assert isinstance(c,CoherentExecutor491);c.nodes=self.nodes.copy();c.nodes.setflags(write=False)
        assert c.nodes.tobytes()==self.nodes.tobytes();return c
    def audit(self):
        bad=[];bound=[]
        for name,m in self.modules.items():
            for key,value in vars(m).items():
                if key=='canonical_projection':
                    bound.append(name)
                    if value is not canonical_projection:bad.append(name+':canonical')
                if key=='CoherentExecutor' and value is not CoherentExecutor491:bad.append(name+':executor')
        if bad:raise RuntimeError('492_BINDING_AUDIT:'+','.join(bad))
        return dict(modules=len(self.modules),canonical_bound_modules=bound,source_records=self.records,all_canonical_exports_491=True,original_modules_unchanged=True)
