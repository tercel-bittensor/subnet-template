# btcli subnets show --netuid 命令遇到 raw.githubusercontent.com 问题
 Fail to run btcli subnets show --netuid 2 --network local --verbose

## 准备
修改/etc/hosts
```sh
$ sudo echo "127.0.0.0 raw.githubusercontent.com >> /etc/hosts
```

把证书生成到与当前项目平级的nginx目录
```sh
cd ../nginx
```

## 生成自签 CA 并用它签发服务器证书
1. 生成带有 key usage 扩展的 CA 证书
 步骤一：创建 openssl 配置文件（如 ca.cnf）
```sh
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
x509_extensions    = v3_ca
prompt             = no

[ req_distinguished_name ]
C  = CN
ST = Test
L  = Test
O  = Test
OU = Test
CN = MyTestCA

[ v3_ca ]
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer:always
basicConstraints = critical,CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
```

步骤二： 生成新的 CA 证书
```sh
openssl req -x509 -newkey rsa:2048 -days 3650 -keyout ca.key -out ca.crt -config ca.cnf
```
## 生成带 SAN 的服务器证书
1. 创建 openssl 配置文件 server.cnf
```sh
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = req_ext

[ dn ]
C  = CN
ST = Test
L  = Test
O  = Test
OU = Test
CN = raw.githubusercontent.com

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = raw.githubusercontent.com
IP.1 = 127.0.0.1
```

2. 生成服务器私钥和 CSR
```sh
openssl genrsa -out nginx.key 2048
openssl req -new -key nginx.key -out nginx.csr -config server.cnf
```

3. 用 CA 签发服务器证书（带 SAN）
```sh
openssl x509 -req -in nginx.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out nginx.crt -days 3650 -sha256 -extfile server.cnf -extensions req_ext
```

4. 合并 fullchain.crt 并配置 nginx
```sh
  cat nginx.crt ca.crt > fullchain.crt
```

5. 配置 nginx 用新生成的 fullchain.crt 和 nginx.key
```sh
cat fullchain.crt > /opt/homebrew/etc/nginx/ssl/nginx.crt
cat nginx.key > /opt/homebrew/etc/nginx/ssl/nginx.key

brew services restart nginx 

cat /opt/homebrew/var/log/nginx/error.log 
```

## 执行 btcli subnets show --netuid
进入当前项目目录
1. 把 ca.crt 追加到 Python certifi 的 CA 文件 （只需要做一次）
```sh
cat ../nginx/ca.crt >> $(python -m certifi)
```

8. 运行 btcli
```sh
$ btcli subnets show --netuid 2 --network local --verbose
# 报错： ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate

#有时 aiohttp/ssl 只认 SSL_CERT_FILE，你可以：

$ export SSL_CERT_FILE=$(python -m certifi)
# 建议执行 echo 'export SSL_CERT_FILE=$(python -m certifi)' >> ./venv/bin/activate

$ btcli subnets show --netuid 2 --network local --verbose
```

9. 给浏览信任证书
```sh
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ca.crt

# 需要手工 右键“显示简介“->“信任” 选 始终信任
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain fullchain.crt

curl -v https://raw.githubusercontent.com
```

