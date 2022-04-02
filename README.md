# 一个用来下载exhentai里本子的插件

### 使用说明:

> 可以先按照 [opq-osc/OPQ-SetuBot](https://github.com/opq-osc/OPQ-SetuBot) Wiki里的说明配置好Bot,再把这个项目放进plugins里.
> 
> 注意: OPQBot要和这个插件在同一台机器上,下载的本子不会自动删除,会一直在botoy-cache里,记得删除

1. 在botoy的plugins文件夹下git clone本项目

2. botoy.json添加下面的配置参数并补全

3. 如果机子上不了外网的话要在botoy.json里配置代理([指南](https://github.com/opq-osc/OPQ-SetuBot/wiki/%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6#opq-setubotbotoyjson))

4. 启动Bot

**botoy.json中需要添加的参数**

```
  "exhentai.ONE_LINE_MAX": 3,
  "exhentai.cookies": {
    "ipb_member_id": "",
    "ipb_pass_hash": "",
    "yay": "louder",
    "igneous": ""
  }
```

### 功能:

- 搜索

- 翻页

- 下载

### TODO:

- 转换成PDF上传

- 选择页面增加页码显示

- 查看本子详细信息
  
  ### 演示:
  
  <img src="https://cube-resources.lenovo.com.cn/cube/a0a6feb0bb6196c9873e32cc010a5ba7.jpg" width="317">
