# About
This is the server-side application for the blogging system. And [here](https://github.com/sunziping2016/blog-client)
is the client-side web app.

Nginx is used only to serve static files (mainly the client-side app). And all the dynamic contents is
passed from the python server to the client via reverse proxy and WebSocket.

                                 Client | Server
                                        |
                     (AJAX or static)   |
                |<=== Service Worker <==|            reverse proxy                |<==> MongoDB (Permanent Data)
    Vue App <==>|                       |<=====> Nginx <======> Python Server <==>|
                |<=====================>| (static contents)  (dynamic contents)   |<==> Redis (Cookie Session)
                      (WebSocket)       |
                                        |

## Todo
* Multi-user management
* Markdown renderer
* Comment system

## Dependency
* `aiohttp`: HTTP server
* `aiohttp-session`: Session provider
* `motor`: MongoDB driver

# 类


# API
所有的 API 被归为三类：
* 无状态的、单向的客户端请求服务端响应：符合 RESTful 要求，可被客户端缓存以离线使用，可通过 AJAX 或 WebSocket 使用。如获取文章内容等。
* 有状态的、单向的客户端请求服务端响应：不可被客户端缓存不可离线使用，可通过 AJAX 或 WebSocket 使用。如用户登录。
* 客户端服务端持续或双向地传输数据：不可被客户端缓存不可离线使用，只可通过 WebSocket 使用。如处理进度实时显示、私聊等。

AJAX 的路由路径为 `/api/{action}`，其中有状态的必须不能是`POST`请求，无状态的一般会支持`POST`。WebSocket 的路由路径为 `/ws`。

对于 AJAX 访问返回数据一律采用 JSON。每一个请求对应一个响应。如果请求数据格式不对或是不支持的`action`，则会返回 400。对于服务器出现内部错误的，返回 502。
响应也是 JSON，与 WebSocket 的结束响应的区别在于没有`id`和`action`字段。理论上来说`status`字段不可能为2（内部错误会返回502）

所有的 WebSocket 连接都以 JSON 作为传输数据格式。如果请求数据格式不是 JSON，或者缺乏`id`和`action`字段，或者`id`和`action`
字段不是字符串类型，则直接断开连接；对于`action`不存在或不支持的及无对应的`id`，返回出错响应。回话的生命周期从一方的开始信号一直到一方的结束信号。
任意一方都可在超时的情况下删除回话。
* 开始：`{"id":..., "action":..., "data":... }`
  * `id`：字符串，随机产生的作为此次回话的唯一标识符
  * `action`：字符串，请求的操作名
  * `data`：可选，操作的参数
* 持续：`{"id":..., "action":"$resume", "data":... }`
  * `id`：字符串，与原始请求的一致
  * `data`: 可选
* 结束：`{"id":..., "action":"$finish", "status":..., "data":... }`
  * `id`：字符串，与原始请求的一致
  * `status`: 数字，0，1或2，0表示成功，1表示错误（对方的非法请求），2表示自己的内部错误。
  * `data`: 可选，如果`status`为非0，则为字符串，出错的信息。

以上是所有 API 的共性部分，由`routes/ajax.py`和`routes/websocket.py`封装。具体的 API 实现则被进一步存放在`routes/handlers`下。

## API
* `apt-list`: 第一类，无参数，返回数据格式为`{"<action-name>": [<protocol-list>], ...}`

## User
数据库中的用户信息包括如下字段：
* `_id`: MongoDB 自带ID
* `user`: 用户名
* `password`: 密码
* `avator`: 字符串类型，到头像的路径
* `role`: 类型，现在可能包括`'administrator'`和`'editor'`两种
* `settings`: JSON 字符串，客户端决定

对于服务端，包含如下操作：
- [ ] `user-list`: 支持`ajax-get`和`ws`，返回用户`_id`的列表
- [x] `user-info`: 支持`ajax-get`和`ws`，返回用户的姓名、头像路径和
- [x] `user-add`: 支持`ajax-post`和`ws`，输入用户名和密码，返回`_id`，默认创建的为`'editor'`用户
- [x] `user-remove`: 支持`ajax-delete`和`ws`，输入为`id`，需要`'administrator'`权限，或者为`id`为用户本人
- [ ] `user-set-role`: 支持`ajax-post`和`ws`，输入为`id`和`role`，需要`'administrator'`权限
- [ ] `user-get-settings`: 支持`ajax-get`
- [ ] `user-set-settings`: 支持`ajax-post`
- [ ] `user-set-password`: 支持`ajax-post`

回话的登入登出：
- [x] `login`: 支持`ajax-post`和`ws`，输入为用户名密码 
- [x] `logout`: 支持`ajax-get`和`ws`


## Content（Post，Static Files） 

## Log
