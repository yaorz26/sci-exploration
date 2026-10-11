# P78：配置源与文件名模板的跨组件任务候选

具体未知：真实PR #126的跨组件语义能否压缩成一个可执行、可独立复查的功能级任务，并保留“配置源元数据会改变后续文件名解析”这一阶段依赖？这直接推进数据集成果：它给出有真实历史来源的跨组件任务候选，避免用单函数数量代替项目功能覆盖。

竞争解释：H1 任务必须把源文件目录、应用目录和模板选项接起来，阶段依赖明确；H2 只看路径字符串就能完成，源的 `base_for_paths` 与模板标志只是冗余字段；H3 PR语义依赖操作系统路径或完整Confuse对象，抽取成固定POSIX行为会失真，候选不应进入研究池。

最低成本验证：六个公开锚点、三种参考各六次，共18次solve；不读取上游测试。任务输入是 `app_dir`、带 `filename/base_for_paths` 的 `sources`、以及带 `source_index/path/cwd/in_app_dir/in_source_dir` 的 `queries`。只要求合法POSIX绝对目录和相对路径，输出按query顺序给出绝对POSIX `resolved` 路径；输入不得修改。规则来自当前公开 `Filename.value` 分支：cwd优先；其次 `in_source_dir` 或 `base_for_paths且未in_app_dir` 用源文件目录；否则有filename或in_app_dir用app目录；绝对输入保持不变。

锚点：A默认源`/workspace/app/default.yaml`, base=false, path`assets/a.txt`, flags全false→`/workspace/app/assets/a.txt`；B本地源`/workspace/app/sub/local.yaml`, base=true, 同path→`/workspace/app/sub/assets/a.txt`；C同B但in_app_dir=true→`/workspace/app/assets/a.txt`；D同B但base=false、in_source_dir=true→`/workspace/app/sub/assets/a.txt`；E同B且cwd`/tmp/job`→`/tmp/job/assets/a.txt`；F同B、绝对path`/var/data/x`→原绝对path。每个输入另含一个第二query以证明同一source元数据可供后续查询使用。

参考：`whole`一次递归处理sources和queries；`helpers`先建source索引再解析queries；`public_logic_adapter`按当前 `Filename.value` 的公开条件顺序实现POSIX路径适配。三者由同一助手编写，适配器不是独立oracle，也不把源码分支顺序当唯一合法内部实现。只读当前confuse非测试源码与PR #126的公开元数据。

执行预算：20分钟、两次实质尝试、18solve；模型/API/付费/下载/private/人工0。标签、切分null，候选状态research_pool_only。若三参考无法在POSIX抽取语义上相符，保留失败并回退PR #142的环境变量跨来源任务；若通过，下一步只审查跨组件任务的阶段依赖字段，不再扩同一候选的边界格。
