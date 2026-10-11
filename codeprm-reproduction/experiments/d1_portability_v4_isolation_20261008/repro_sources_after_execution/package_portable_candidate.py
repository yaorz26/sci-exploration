"""保留任务/案例，只为候选管理端包增加固定依赖和路径补丁。"""
from __future__ import annotations
import base64
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import shutil
import zipfile

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, obj): path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
def record(path, base): return {'path':path.relative_to(base).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}

def main():
    root = Path(__file__).resolve().parents[2]
    parent = root/'experiments/d1_candidate_delivery_v2_20261008'
    source = parent/'dataset'
    out = root/'experiments/d1_candidate_delivery_v4_portable_20261008'
    out.mkdir(exist_ok=False)
    dataset = out/'dataset'
    shutil.copytree(source, dataset)
    tasks = json.loads((source/'manifest.json').read_text(encoding='utf-8'))['tasks']
    patched = []
    for filename in ('task_specs_snapshot.py','task_specs_expansion.py'):
        target = dataset/'private/_curator'/filename
        old = target.read_text(encoding='utf-8')
        original = out/'ORIGINALS/private/_curator'/filename
        original.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,original)
        find = 'EXPERIMENT_ROOT = Path(__file__).resolve().parents[5]\nSOURCE_ROOT = EXPERIMENT_ROOT / "data/raw/d1_project_v1_20261008/repositories"'
        replacement = 'SOURCE_ROOT = Path(__file__).resolve().parents[1] / "_runtime/vendor"'
        if old.count(find)!=1: raise RuntimeError('路径补丁预期不符')
        new = old.replace(find,replacement)
        find_paths = 'SOURCE_ROOT / "cachetools/src", SOURCE_ROOT / "confuse"]:'
        if new.count(find_paths)!=1: raise RuntimeError('依赖补丁预期不符')
        new = new.replace(find_paths, 'SOURCE_ROOT / "cachetools/src", SOURCE_ROOT / "confuse",\n                  SOURCE_ROOT / "pyyaml"]:')
        # 原始CRLF仅由write_text标准换行输出；原字节另存在ORIGINALS。
        target.write_text(new,encoding='utf-8')
        patched.append({'path':target.relative_to(out).as_posix(),'original_sha256':sha(original),
                        'patched_sha256':sha(target),'original_copy':original.relative_to(out).as_posix(),
                        'change':'只替换工作区定位与库搜索目录；功能/测试代码不改'})
    vendor = dataset/'private/_runtime/vendor'
    dependency_rows = []
    configurations = [('boltons','boltons','boltons','LICENSE'),
                      ('more_itertools','more_itertools','more_itertools','LICENSE'),
                      ('cachetools','src/cachetools','cachetools','LICENSE'),
                      ('confuse','confuse','confuse','LICENSE')]
    raw = root/'data/raw/d1_project_v1_20261008/repositories'
    for directory, package_path, import_name, license_name in configurations:
        repo = raw/directory
        info = next(t['source'] for t in tasks if t['source']['repository'].split('/')[-1].replace('-','_')==directory)
        acquisition=json.loads((raw.parent/'manifests'/(directory+'.json')).read_text(encoding='utf-8'))
        commit=acquisition['commit']
        if commit != info['commit']: raise RuntimeError('固定来源commit不符')
        original_archive=raw.parent/'archives'/(directory+'_'+commit+'.zip')
        if sha(original_archive)!=acquisition['archive_sha256']: raise RuntimeError('原始下载ZIP哈希不符')
        target = vendor/directory/package_path
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(repo/package_path,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
        license_target = vendor/directory/'UPSTREAM_LICENSE.txt'; shutil.copy2(repo/license_name,license_target)
        if sha(license_target)!=info['license_sha256']: raise RuntimeError('运行库许可字节不符')
        # 原来源为codeload归档而非git checkout；逐文件与已存下载ZIP核对。
        copied=[]
        with zipfile.ZipFile(original_archive) as z:
            prefix=z.namelist()[0].split('/')[0]+'/'
            for f in sorted(target.rglob('*')):
                if f.is_file():
                    original = repo/package_path/f.relative_to(target)
                    rel = original.relative_to(repo).as_posix()
                    archive_bytes = z.read(prefix+rel)
                    if hashlib.sha256(archive_bytes).hexdigest()!=sha(f) or sha(f)!=acquisition['source_hashes'][rel]:
                        raise RuntimeError('上游依赖偏离固定commit下载归档')
                    copied.append(record(f,out))
        dependency_rows.append({'name':import_name,'repository':info['repository'],'commit':commit,
                                'license':info['license'],'license_file':license_target.relative_to(out).as_posix(),
                                'license_sha256':sha(license_target),'files':copied,'provenance':'与固定commit的已存codeload ZIP及获取清单逐文件核对',
                                'archive_url':acquisition['archive_url'],'archive_sha256':acquisition['archive_sha256']})
    distribution = md.distribution('PyYAML')
    if distribution.version!='6.0.3': raise RuntimeError('未登记的PyYAML版本')
    yaml_target = vendor/'pyyaml/yaml'; yaml_target.mkdir(parents=True)
    yaml_files = [f for f in distribution.files if str(f).startswith('yaml/') and str(f).endswith('.py')]
    license_file = next(f for f in distribution.files if str(f).endswith('dist-info/licenses/LICENSE'))
    installed_records = []
    for f in yaml_files+[license_file]:
        installed = Path(distribution.locate_file(f))
        digest = base64.urlsafe_b64encode(hashlib.sha256(installed.read_bytes()).digest()).decode().rstrip('=')
        if not f.hash or f.hash.mode!='sha256' or digest!=f.hash.value: raise RuntimeError('PyYAML安装文件与RECORD不符')
        target = yaml_target/Path(str(f)).name if f in yaml_files else vendor/'pyyaml/UPSTREAM_LICENSE.txt'
        shutil.copy2(installed,target); installed_records.append(record(target,out))
    dist_metadata = next(f for f in distribution.files if str(f).endswith('dist-info/METADATA'))
    metadata_target = vendor/'pyyaml/DISTRIBUTION_METADATA.txt'; shutil.copy2(distribution.locate_file(dist_metadata),metadata_target)
    dependency_rows.append({'name':'PyYAML','version':distribution.version,'license':'MIT',
                            'license_file':'dataset/private/_runtime/vendor/pyyaml/UPSTREAM_LICENSE.txt',
                            'files':installed_records,'provenance':'本机已安装发行版纯Python文件，逐项RECORD校验；未下载/核验发行版原始wheel，不冒称上游commit冻结',
                            'binary_extension_included':False,'distribution_metadata_sha256':sha(metadata_target)})
    write(out/'RUNTIME_DEPENDENCIES.json',dependency_rows)
    write(out/'PORTABILITY_PATCHES.json',{'parent_archive_sha256':sha(parent/'d1_project_initial20_v5_candidate.zip'),
                                        'patches':patched,'original_dataset_files':287,'unchanged_original_files':285,
                                        'unchanged_scope':'全部题面、案例、切分、评分器、参考/另一结构入口和旧审计；仅管理端两份依赖定位变化',
                                        'authoring_snapshot_status':'build_dataset_snapshot.py等原始作者脚本为历史材料，不承诺离线重建生成'})
    shutil.copy2(parent/'SOURCE_LICENSE_INDEX.json',out/'SOURCE_LICENSE_INDEX.json')
    card=(parent/'DATA_CARD.md').read_text(encoding='utf-8')+'''\n\n## v4可迁移交付补充\n\n本版修复v2缺失运行依赖问题。两份管理端定义改用包内相对路径；固定commit的四个上游Python库及PyYAML 6.0.3纯Python运行文件和许可已随包提供。题面、案例、切分、评分器、参考/另一结构入口与旧审计字节均保留；两份原始定义位于ORIGINALS，补丁见PORTABILITY_PATCHES.json。运行依赖只供管理端，不得进入模型提示或盲审交付。\n\n建议使用Python 3.13.7（当前验证环境）；其他Python版本/操作系统尚未验证。不需要pip安装即可进行本包参考/另一结构案例复跑，但历史作者构建快照不等于可离线从头构建工具。PyYAML采用本机发行版17个纯Python文件，经RECORD核对；不包含平台二进制扩展，不将安装文件核对冒称供应链安全审计。\n\n完整性和运行检查报告在包外保存，生成ZIP后不追溯填入假定通过结果。本版仍为候选、人工0、未正式冻结/未发布。v3打包时误用git HEAD检查codeload来源，失败中间目录保留；v4改为已存下载归档逐文件核对。\n'''
    (out/'DATA_CARD.md').write_text(card,encoding='utf-8')
    (out/'RUN_REFERENCE_CHECKS.md').write_text('''# 离线复跑说明（管理端）\n\n解压后，在包的根目录使用Python 3.13.7。以下命令保持评分器原约定：\n\n```powershell\npython -I -S -B -X utf8 dataset/private/_curator/evaluate_candidate.py --candidate dataset/private/D1_B01/reference.py --cases dataset/private/D1_B01/all_tests.json\npython -I -S -B -X utf8 dataset/private/_curator/evaluate_candidate.py --candidate dataset/private/D1_B01/alternate.py --cases dataset/private/D1_B01/all_tests.json\n```\n\n对manifest中的20个task_id各跑reference.py与alternate.py，总40次，307案例每实现一次。不要把private文件发给生成模型或盲审人类。上述命令仅用于可信参考/另一结构实现，不是未知代码的操作系统沙箱。评估被测候选须继续使用具有20秒/1MiB限制及冻结校验的项目执行器。\n''',encoding='utf-8')
    original_hashes=json.loads((parent/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))['file_hashes']
    changes={p['path'].removeprefix('dataset/'):p for p in patched}
    for r in original_hashes:
        actual=sha(dataset/r['path'])
        if actual!=r['sha256'] and r['path'] not in changes: raise RuntimeError('未登记的原始文件改动')
    before_manifest=[record(f,out) for f in sorted(out.rglob('*')) if f.is_file()]
    write(out/'PACKAGE_MANIFEST.json',{'status':'candidate_not_frozen_not_published','files':before_manifest,
                                      'dataset_version':'d1_project_initial20_v5_20261008','task_count':20,
                                      'public_case_count':40,'private_case_count':267,'human_review_count':0,
                                      'self_hash_policy':'清单不含自身，ZIP哈希仅在包外登记'})
    archive=out/'d1_project_initial20_v5_portable_candidate.zip'
    files=[f for f in sorted(out.rglob('*')) if f.is_file()]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(f,f.relative_to(out).as_posix())
    write(out/'DELIVERY_CHECKSUMS_EXTERNAL.json',{'archive':archive.name,'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,
                                              'zip_members':len(files),'package_manifest_sha256':sha(out/'PACKAGE_MANIFEST.json'),
                                              'package_status':'candidate_not_frozen_not_published'})
    print(json.dumps({'archive':str(archive),'sha256':sha(archive),'members':len(files),'unchanged_original_files':285,'path_only_patches':2},ensure_ascii=False))

if __name__=='__main__':main()
