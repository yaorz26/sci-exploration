实现solve(data)。data包含app_dir、sources、queries。
app_dir是POSIX绝对目录。sources按列表保存配置源元数据，每项含filename（POSIX绝对文件名或null）
和base_for_paths（bool）。queries按输入顺序给出source_index、path（POSIX路径字符串）、
cwd（POSIX绝对目录或null）、in_app_dir（bool）、in_source_dir（bool）。只要求合法域，
source_index有效且path为字符串；不得修改输入。
对每个query返回一个resolved绝对POSIX路径，组成{"resolved": [...]}。
解析规则：path本身为绝对路径时保持其规范化绝对路径；否则若cwd非null，使用cwd；否则若
对应source有filename且in_source_dir为true，或source.base_for_paths为true且in_app_dir为false，
使用source.filename所在目录；否则若对应source有filename或in_app_dir为true，使用app_dir；
最后无上述基准时使用app_dir。路径连接后规范化。queries顺序必须保持。
此任务抽取自confuse PR #126的ConfigSource/Filename跨组件行为，不要求复现完整Config类。
内部helper数量、调用次序和是否先建索引自由。
