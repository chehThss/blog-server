# About
This is the server-side application for the blogging system. And [here](https://github.com/sunziping2016/blog-client)
is the client-side web app.

## Todo
* Multi-user management
* Markdown renderer
* Comment system

# Structure
Nginx is used only to serve static files (mainly the client-side app). And all the dynamic contents is
passed from the python server to the client via reverse proxy and WebSocket.


          Client | Server
                 |
             websocket        reverse proxy     
    Vue App <----|-----> Nginx <--------> Python Server <---> MongoDB
                 |(static contents)     (dynamic contents)
                 |
                 |




## Python Server
* `aiohttp`: HTTP server
* `aiohttp-session`: Session provider
* `motor`: MongoDB driver

# API
所有的 WebSocket 连接都以 JSON 作为传输数据格式，连接规则如下所示。每一个请求对应一个响应：
* 请求：`{"id":..., "action":..., "data":... }`
  * `id`：字符串，随机产生的作为此次请求的唯一标识符
  * `action`：字符串，请求的操作名
  * `data`：可选，操作的参数
* 响应：`{"id":..., "action":"reply", "status":..., "data":... }`
  * `id`：字符串，与请求的一致
  * `status`: 数字，0或1，0表示成功，1表示出错。
  * `data`: 可选，如果`status`为1，则为字符串，出错的信息。

以下的所有 API，均给出了操作名，操作参数，成功返回参数和可能的失败情况。

## User
数据库中的用户信息包括如下字段：
* `_id`: MongoDB 自带ID
* `user`: 用户名
* `password`: 密码
* `role`: 类型，现在可能包括`'administrator'`和`'editor'`两种
* `settings`: 键值对对象，向客户端返回用户偏好，内容未定

对于服务端，包含如下操作：
* `user-add`: 
* `user-remove`:
* `user-set-role`:
* `user-get-settings`:
* `user-set-settings`:
* `user-set-password`:
* `user-login`:
* `user-logout`: 


## Content（Post，Static Files） 

## Log
